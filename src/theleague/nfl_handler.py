import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime as dt
from multimodal_communication import CloudHelper


class NFLDailyStatsCollector:
    def __init__(
        self, start_date, end_date, gcloud_save: bool = True, local_save: bool = False
    ):
        self.dates = pd.date_range(start_date, end_date)
        season_years = pd.Series(self.dates).apply(
            lambda x: x.year - 1 if x.month <= 8 else x.year
        )
        self.season_years = set(season_years)
        self.gcloud_save = gcloud_save
        self.local_save = local_save

        assert len(self.dates) > 0, (
            f"start_date: {start_date} must be less than end_date: {end_date}"
        )

    def run(self):
        all_cleaned_offensive_dfs = []
        all_cleaned_fg_dfs = []

        for date in self.dates:
            print(f"Processing {date.date()}...")

            # Collect all the url suffixes for the games on the given day
            boxscore_urls = self._get_boxscore_urls_for_date(date)
            time.sleep(6.1)

        # Grab and clean all the individual box scores
        for suffix in boxscore_urls:
            url = "https://www.pro-football-reference.com" + suffix
            print(f"  Scraping {url}")
            try:
                boxscore_data = self._fetch_offensive_boxscore(url)
                all_cleaned_offensive_dfs.append(boxscore_data)
                fg_data = self._fetch_fg_boxscore()
                all_cleaned_fg_dfs.append(fg_data)
                time.sleep(6.1)
            except Exception as e:
                print(f"  Failed to scrape {url}: {e}")
            time.sleep(6.1)  # Wait between each game to respect rate limits

        offensive_boxscores = pd.concat(all_cleaned_offensive_dfs)
        fg_boxscores = pd.concat(all_cleaned_fg_dfs)

        # After collecting all the boxscore types, outer merge them

        # After merging, add in columns for home and away team with self.home team and self.away_team

        x = 1

    def _get_boxscore_urls_for_date(self, date):
        # Ensure the given date is in a compatable date format and grab the year
        date = pd.to_datetime(date) if isinstance(date, str) else date
        year = date.year

        games_url = f"https://www.pro-football-reference.com/years/{year}/games.htm"
        games_table = pd.read_html(games_url, extract_links="body")[0]

        # Compile the dates and suffixes from the full season for later date filtering
        games_table["dates"] = games_table["Date"].apply(lambda x: x[0])
        games_table["suffixes"] = games_table["Unnamed: 7"].apply(lambda x: x[1])

        # filter down to just the game suffixes that fall on the date
        suffixes = games_table[["dates", "suffixes"]].dropna()

        relevant_suffixes = suffixes[
            suffixes.dates == date.strftime("%Y-%m-%d")
        ].suffixes

        return relevant_suffixes

    def _fetch_offensive_boxscore(self, url):
        self.all_tables = pd.read_html(url, extract_links="body")
        main_table = self.all_tables[2]
        main_table.columns = main_table.columns.droplevel(0)

        # Break apart the player ids from the embedded player page links
        main_table["player_id"] = main_table.iloc[:, 0].apply(
            lambda x: x[1] if isinstance(x, tuple) else None
        )
        main_table["player_id"] = main_table.player_id.apply(
            lambda x: x.split("/")[-1].split(".")[0] if x else None
        )

        main_table = main_table.map(lambda x: x[0] if isinstance(x, tuple) else x)
        main_table = main_table.dropna(subset="player_id")

        # Determine the home and away team for later columns addition
        self.home_team = main_table.Tm.unique()[1]
        self.away_team = main_table.Tm.unique()[0]

        return main_table

    def _fetch_fg_boxscore(self):
        fg_boxscore = self.all_tables[1]
        # fg_boxscore.columns = fg_boxscore.columns.droplevel(0)

        # Break apart the player ids from the embedded player page links
        fg_boxscore["player_id"] = fg_boxscore.loc[:, "Detail"].apply(
            lambda x: x[1] if isinstance(x, tuple) else None
        )
        fg_boxscore["player_id"] = fg_boxscore.player_id.apply(
            lambda x: x.split("/")[-1].split(".")[0] if x else None
        )

        fg_boxscore = fg_boxscore.map(lambda x: x[0] if isinstance(x, tuple) else x)
        fg_boxscore = fg_boxscore.dropna(subset="player_id")
        fg_boxscore = fg_boxscore[
            (fg_boxscore.Detail.str.contains("field goal"))
            & (fg_boxscore.Detail.str.contains("field goal return") == False)
        ]
        fg_boxscore["kicker"] = fg_boxscore.Detail.apply(
            lambda x: " ".join(x.split("yard")[0].split(" ")[0:-2])
        )
        fg_boxscore["distance"] = fg_boxscore.Detail.apply(
            lambda x: (x.split("yard")[0].split(" ")[-2])
        )

        fg_boxscore["Quarter"] = fg_boxscore["Quarter"].replace("", np.nan)
        fg_boxscore["Quarter"] = fg_boxscore["Quarter"].ffill()
        fg_boxscore = fg_boxscore[["player_id", "kicker", "distance"]]
        fg_boxscore["distance"] = pd.to_numeric(
            fg_boxscore["distance"], errors="coerce"
        ).astype("Int64")

        # Try to find a way to count the number of game winning FGs base on a criteria from the full scoring table

        fg_agg = fg_boxscore.groupby(by=["player_id", "kicker"]).agg(["count", "sum"])
        fg_agg.columns = fg_agg.columns.droplevel(0)
        fg_agg = fg_agg.reset_index()
        fg_agg = fg_agg.rename(
            columns={"count": "num_fg_made", "sum": "total_made_fg_distance"}
        )

        return fg_agg


if __name__ == "__main__":
    collector = NFLDailyStatsCollector(start_date="2024-09-08", end_date="2024-09-08")
    collector.run()

    print("X")
