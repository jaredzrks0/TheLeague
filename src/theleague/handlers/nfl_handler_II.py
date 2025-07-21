import requests

import polars as pl

from theleague.handlers.base_handler import BaseHandler


class NFLHandler(BaseHandler):
    def __init__(
        self,
        start_date: str,
        end_date: str,
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

        # If no end_date given, default to the start date for a 1 day pull
        if not end_date:
            end_date = start_date


    def fetch_season_schedule(self):