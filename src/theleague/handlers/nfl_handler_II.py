import requests
import datetime 
from datetime import datetime as dt

import polars as pl

from theleague.handlers.base_handler import BaseHandler


class NFLHandler(BaseHandler):
    def __init__(
        self,
        start_date: str|None = None,
        end_date: str|None = None,
        gcloud_save: bool = True,
        local_save: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)\

        # Initialize instance vars
        self.start_date = start_date
        self.end_date = end_date
        self.gcloud_save = gcloud_save
        self.local_save = local_save

        # If no start date give, default to today
        if not start_date:
            self.start_date = dt.today().strftime('%Y-%m-%d')

        # If no end_date given, default to the start date for a 1 day pull
        if not end_date:
            self.end_date = start_date


        


if __name__ == '__main__':
    handler = NFLHandler()

    handler.check_remaining_daily_requests()