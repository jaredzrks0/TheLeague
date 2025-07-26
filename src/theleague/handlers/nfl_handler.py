import requests
import datetime
from datetime import datetime as dt

import polars as pl

from theleague.handlers.base_handler import BaseHandler


class NFLHandler(BaseHandler):
    sport_id: str

    def __init__(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        gcloud_save: bool = True,
        local_save: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        # Initialize instance vars
        self.start_date = start_date
        self.end_date = end_date
        self.gcloud_save = gcloud_save
        self.local_save = local_save
        self.sport_id = "FOOTBALL"

        # If no start date give, default to today
        if not start_date:
            self.start_date = dt.today().strftime("%Y-%m-%d")

        # If no end_date given, default to the start date for a 1 day pull
        if not end_date:
            self.end_date = self.start_date

    def fetch_leagues(self, max_entities: int = 100, save_json: bool = True):
        params = {"sportID": self.sport_id, "limit": max_entities}
        self.league_data = self.make_get_request(
            endpoint="leagues", params=params, save_json=save_json
        )

    def fetch_teams(
        self, leagueID: str = "NFL", max_entities: int = 100, save_json: bool = True
    ):
        params = {"sportID": self.sport_id, "leagueID": leagueID, "limit": max_entities}
        self.teams_data = self.make_get_request(
            endpoint="teams", params=params, save_json=save_json
        )


if __name__ == "__main__":
    handler = NFLHandler()

    handler.fetch_teams()

    x = 1
