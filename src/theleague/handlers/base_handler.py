import os
import requests

from dotenv import load_dotenv


class BaseHandler:
    API_KEY: str

    def __init__(self):
        # Load in the API Key
        load_dotenv()
        self.API_KEY = os.getenv("SPORTS_GAME_ODDS_API")

    def check_remaining_daily_requests(self):
        """Checks the number of requests completed for the month and compares to the allowance"""

        # Hit the API to check current daily requests used
        url = "https://api.sportsgameodds.com/v2/account/usage"
        headers = {
        "X-Api-Key": self.API_KEY
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            usage_data = response.json()
            entity_usage_data = usage_data['data']['rateLimits']['per-month']
            max_entities, current_entities = entity_usage_data['max-entities'], entity_usage_data['current-entities']


        # Compare to the user defined daily allowance and
        print(
            f"Total Requested Monthy Entities: {current_entities:,} --- Total Remaining Monthly Entities: {max_entities - current_entities:,}"
        )
