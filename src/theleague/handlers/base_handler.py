import os
import requests
import json

import polars as pl

from dotenv import load_dotenv
from typing import Any, Type
from pydantic import BaseModel
from multimodal_communication import CloudHelper
from theleague.utilities import calculate_nfl_season, pydantic_convert_and_validate
from theleague.pydantic_models.response_models.league_response import LeagueResponse
from theleague.pydantic_models.processing_models.leagues import LeaguesDataFrame


class MissingParameterError(AttributeError):
    pass


class BaseHandler:
    API_KEY: str
    GCLOUD_PREFIX: str

    def __init__(self):
        # Load in the API Key
        load_dotenv()
        self.API_KEY = os.getenv("SPORTS_GAME_ODDS_API")
        self.GCLOUD_PROJECT_ID = os.getenv("GCLOUD_PROJECT_ID")
        self.GCLOUD_PREFIX = "jzirk"

    def check_remaining_requests(self):
        """Checks the number of requests completed for the month and compares to the allowance"""

        # Build the request pieces
        url = "https://api.sportsgameodds.com/v2/account/usage"
        headers = {"X-Api-Key": self.API_KEY}

        # Hit the API to check current daily requests used
        response = requests.get(url, headers=headers)

        # Validate response and calculate usage metrics
        if response.status_code == 200:
            usage_data = response.json()
            entity_usage_data = usage_data["data"]["rateLimits"]["per-month"]
            max_entities, current_entities = (
                entity_usage_data["max-entities"],
                entity_usage_data["current-entities"],
            )

        # Compare to the user defined daily allowance and
        print(
            f"Total Requested Monthy Entities: {current_entities:,} --- Total Remaining Monthly Entities: {max_entities - current_entities:,}"
        )

    def make_get_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        save_json: bool = True,
    ):
        # Define the base of the GET request
        self._create_request_base(endpoint)

        # Add any params
        self._add_request_parameters(parameters=params)

        # Ensure we have an ID for saving
        if "sportID" not in self.params or (
            endpoint != "leagues" and "leagueID" not in self.params
        ):
            raise MissingParameterError(
                "sportID must always be included, and leagueID is required unless the endpoint is 'leagues'."
            )

        try:
            response = requests.get(self.URL, params=self.params)
            response.raise_for_status()  # Raises HTTPError for bad status codes (4xx, 5xx)
            data = response.json()  # May raise ValueError if response is not valid JSON

        except requests.exceptions.HTTPError as http_err:
            raise RuntimeError(
                f"HTTP error occurred: {http_err} - URL: {response.url}"
            ) from http_err
        except requests.exceptions.RequestException as req_err:
            raise RuntimeError(f"Request failed: {req_err}") from req_err
        except ValueError as json_err:
            raise RuntimeError("Invalid JSON in response") from json_err

        # Save the json in gcloud if needed
        if save_json:
            self._gcloud_save_fetch(endpoint=endpoint, data=data)

        return data

    def _create_request_base(self, endpoint: str, version: str = "v2") -> None:
        """Creates the paramer-less (other than the API) url and param_dict for an API request given an endpoint."""
        self.URL = f"https://api.sportsgameodds.com/{version}/{endpoint}/"
        self.params = {"apiKey": self.API_KEY}

    def _add_request_parameters(self, parameters: dict[str, Any]) -> None:
        if not hasattr(self, "params"):
            raise AttributeError(
                "Handler must have parameters attribute set. Ensure self._create_request_base has been called"
            )
        if parameters:
            self.params = self.params | parameters

    def _gcloud_save_fetch(self, endpoint, data):
        uploader = CloudHelper(project_id=self.GCLOUD_PROJECT_ID, obj=data)

        # Grab the ID information
        sport = self.params["sportID"]

        # Build the uploader
        if endpoint == "leagues":
            season = calculate_nfl_season(self.start_date)
            self.leagues_gcloud_path = (
                f"sport={sport}/endpoint={endpoint}/season={season}/leagues.json"
            )

            uploader.upload_to_cloud(
                bucket_name=f"{self.GCLOUD_PREFIX}-raw-json",
                file_name=self.leagues_gcloud_path,
            )

        elif endpoint == "teams":
            league = self.params["leagueID"]
            season = calculate_nfl_season(self.start_date)
            self.teams_gcloud_path = f"sport={sport}/endpoint={endpoint}/league={league}/season={season}/teams.json"

            uploader.upload_to_cloud(
                bucket_name=f"{self.GCLOUD_PREFIX}-raw-json",
                file_name=self.teams_gcloud_path,
            )
        else:
            league = self.params["leagueID"]
            uploader.upload_to_cloud(
                bucket_name=f"{self.GCLOUD_PREFIX}-raw-json",
                file_name=f"sport={sport}/endpoint={endpoint}/league={league}/start_date={self.start_date}&end_date={self.end_date}.json",
            )

    ########## COMMON FETCHES ##########
    def fetch_leagues(self, max_entities: int = 100, save_json: bool = True):
        params = {"sportID": self.sport_id, "limit": max_entities}
        self.leagues_json = self.make_get_request(
            endpoint="leagues", params=params, save_json=save_json
        )

    def fetch_teams(
        self, leagueID: str = "NFL", max_entities: int = 100, save_json: bool = True
    ) -> None:
        params = {"sportID": self.sport_id, "leagueID": leagueID, "limit": max_entities}
        self.teams_json = self.make_get_request(
            endpoint="teams", params=params, save_json=save_json
        )

    ########## COMMON PROCESSING ##########
    def process_leagues(self, save_df: bool = True):
        # Grab raw json data either from self if exists or else from gcloud
        if not hasattr(self, "leagues_json"):
            raise ValueError("You must run self.fetch_leagues before processing")

        self.leagues_response = self._fit_response_to_pydantic(
            self.leagues_json, LeagueResponse
        )

        self.leagues_data = self.leagues_response.to_leagues_dict()
        self.leagues_df = pl.DataFrame(self.leagues_data)
        self.leagues_data = pydantic_convert_and_validate(
            self.leagues_df, LeaguesDataFrame
        )

        if save_df:
            self._gcloud_save_dataframe("leagues", self.leagues_df)

    ########## OTHER FUNCTIONS ##########

    def _fit_response_to_pydantic(
        self, json_response: dict[str, Any], pydantic_model: Type[BaseModel]
    ) -> type[BaseModel]:
        return pydantic_model(**json_response)

    def _gcloud_save_dataframe(self, endpoint, data):
        uploader = CloudHelper(project_id=self.GCLOUD_PROJECT_ID, obj=data)

        # Grab the ID information
        sport = self.params["sportID"]

        if endpoint == "leagues":
            season = calculate_nfl_season(self.start_date)

            # Upload with the dynamic path
            uploader.upload_to_cloud(
                bucket_name=self.GCLOUD_PREFIX + f"-{sport.lower()}-data",
                file_name=f"sport={sport}/endpoint={endpoint}/season={season}/leagues.parquet",
            )
