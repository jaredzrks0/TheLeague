import os
import requests

from dotenv import load_dotenv


class BaseHandler:
    API_KEY: str
    daily_allowance: int

    def __init__(self):
        # Load in the API Key
        load_dotenv()
        self.API_KEY = os.getenv("STATPAL_API_KEY")

    def check_remaining_daily_requests(self, daily_allowance: int = 50000):
        """Checks the number of requests completed for the day and compares to the allowance"""

        # Hit the API to check current daily requests used
        url = f"https://statpal.io/api/user-request-count/?access_key={self.API_KEY}"
        response = requests.get(url)
        total_used_requests = response.json()["request_count"]

        # Compare to the user defined daily allowance and
        print(
            f"Total Used Requests: {total_used_requests:,} --- Total Remaining Requests: {daily_allowance - total_used_requests:,}"
        )
