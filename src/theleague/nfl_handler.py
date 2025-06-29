import time
import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment
from io import StringIO
import numpy as np
from datetime import datetime as dt
from multimodal_communication import CloudHelper
from functools import reduce
import warnings
from theleague.constants import (
    OFFENSIVE_COLUMNS_LIST,
    OFFENSIVE_RENAMING_DICT,
    PLAYER_DEFENSE_RENAMING_DICT,
    PUNT_KICK_RETURNS_RENAMING_DICT,
    PUNT_KICK_RENAMING_DICT,
    PASSING_ADVANCED_RENAMING_DICT,
    RECEIVING_ADVANCED_RENAMING_DICT,
    RUSHING_ADVANCED_RENAMING_DICT,
    DEFENSE_ADVANCED_RENAMING_DICT,
    SNAP_COUNT_RENAMING_DICT,
)


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
        all_cleaned_basic_defense_dfs = []
        all_cleaned_punt_kick_returns_dfs = []
        all_cleaned_punt_kick_dfs = []
        all_cleaned_passing_advanced_dfs = []
        all_cleaned_receiving_advanced_dfs = []
        all_cleaned_rushing_advanced_dfs = []
        all_cleaned_defense_advanced_dfs = []
        all_cleaned_snap_counts = []

        for date in self.dates:
            print(f"Processing {date.date()}...")
            self.str_date = date.strftime("%Y-%m-%d")

            # Collect all the url suffixes for the games on the given day
            boxscore_urls = self._get_boxscore_urls_for_date(date)
            time.sleep(6.1)

            # Grab and clean all the individual box scores
            for suffix in boxscore_urls:
                self.url = "https://www.pro-football-reference.com" + suffix
                print(f"  Scraping {self.url}")
                try:
                    boxscore_data = self._fetch_offensive_boxscore(self.url)
                    all_cleaned_offensive_dfs.append(boxscore_data)
                    fg_data = self._fetch_fg_boxscore()
                    all_cleaned_fg_dfs.append(fg_data)
                    ### Get Commented tables ###
                    self._get_commented_tables(self.url)
                    time.sleep(6.1)

                    # Basic Defense
                    basic_defense = self._fetch_commented_table(
                        "player_defense", "Player", PLAYER_DEFENSE_RENAMING_DICT
                    )
                    basic_defense["date"] = self.str_date
                    all_cleaned_basic_defense_dfs.append(basic_defense)

                    # Punt and kick returns
                    punt_kick_returns = self._fetch_commented_table(
                        "returns", "Player", PUNT_KICK_RETURNS_RENAMING_DICT
                    )
                    punt_kick_returns["date"] = self.str_date
                    all_cleaned_punt_kick_returns_dfs.append(punt_kick_returns)

                    # Punts and kicks
                    punts_kicks = self._fetch_commented_table(
                        "kicking", "Player", PUNT_KICK_RENAMING_DICT
                    )
                    punts_kicks["date"] = self.str_date
                    all_cleaned_punt_kick_dfs.append(punts_kicks)

                    # Advanced passing
                    passing_advanced = self._fetch_commented_table(
                        "passing_advanced", "Player", PASSING_ADVANCED_RENAMING_DICT
                    )
                    passing_advanced["date"] = self.str_date
                    all_cleaned_passing_advanced_dfs.append(passing_advanced)

                    # Advanced receiving
                    receiving_advanced = self._fetch_commented_table(
                        "receiving_advanced", "Player", RECEIVING_ADVANCED_RENAMING_DICT
                    )
                    receiving_advanced["date"] = self.str_date
                    all_cleaned_receiving_advanced_dfs.append(receiving_advanced)

                    # Advanced rushing
                    rushing_advanced = self._fetch_commented_table(
                        "rushing_advanced", "Player", RUSHING_ADVANCED_RENAMING_DICT
                    )
                    rushing_advanced["date"] = self.str_date
                    all_cleaned_rushing_advanced_dfs.append(rushing_advanced)

                    # Advanced Defense
                    defense_advanced = self._fetch_commented_table(
                        "defense_advanced", "Player", DEFENSE_ADVANCED_RENAMING_DICT
                    )
                    defense_advanced["date"] = self.str_date
                    all_cleaned_defense_advanced_dfs.append(defense_advanced)

                    # Snap Counts
                    home_snap_counts = self._fetch_commented_table(
                        "home_snap_counts", "Player", SNAP_COUNT_RENAMING_DICT
                    )
                    home_snap_counts["team"] = self.home_team
                    home_snap_counts["date"] = self.str_date

                    away_snap_counts = self._fetch_commented_table(
                        "vis_snap_counts", "Player", SNAP_COUNT_RENAMING_DICT
                    )
                    away_snap_counts["team"] = self.away_team
                    away_snap_counts["date"] = self.str_date

                    all_cleaned_snap_counts.append(home_snap_counts)
                    all_cleaned_snap_counts.append(away_snap_counts)

                    time.sleep(6.1)
                except Exception as e:
                    print(f"  Failed to scrape {url}: {e}")
                time.sleep(6.1)  # Wait between each game to respect rate limits

        offensive_boxscores = pd.concat(all_cleaned_offensive_dfs).rename(
            columns=OFFENSIVE_RENAMING_DICT
        )
        fg_boxscores = pd.concat(all_cleaned_fg_dfs).rename(
            columns={"kicker": "player"}
        )
        basic_defense_boxscores = pd.concat(all_cleaned_basic_defense_dfs)
        punt_kick_return_boxscores = pd.concat(all_cleaned_punt_kick_returns_dfs)
        punts_kicks_boxscores = pd.concat(all_cleaned_punt_kick_dfs)
        passing_advanced_boxscores = pd.concat(all_cleaned_passing_advanced_dfs).drop(
            columns=["Cmp", "Att", "Yds"]
        )
        receiving_advanced_boxscores = pd.concat(
            all_cleaned_receiving_advanced_dfs
        ).drop(columns=["Tgt", "Rec", "Yds", "TD"])
        rushing_advanced_boxscores = pd.concat(all_cleaned_rushing_advanced_dfs).drop(
            columns=["Att", "Yds", "TD"]
        )
        defense_adanced_boxscores = pd.concat(all_cleaned_defense_advanced_dfs).drop(
            columns=["Int", "Yds", "TD", "Sk"]
        )
        snap_count_boxscores = pd.concat(all_cleaned_snap_counts)

        fg_boxscores = pd.merge(
            fg_boxscores,
            snap_count_boxscores[["player_id", "team"]],
            on="player_id",
            how="left",
        )

        # After collecting all the boxscore types, outer merge them
        dfs_to_merge = [
            offensive_boxscores,
            fg_boxscores,
            basic_defense_boxscores,
            punt_kick_return_boxscores,
            punts_kicks_boxscores,
            passing_advanced_boxscores,
            receiving_advanced_boxscores,
            rushing_advanced_boxscores,
            defense_adanced_boxscores,
            snap_count_boxscores,
        ]

        # Extract source_url columns and drop from original
        source_urls = [df[["player_id", "player", "team", "date", "source_url"]] for df in dfs_to_merge]
        dfs_wo_source_url = [df.drop(columns=["source_url"]) for df in dfs_to_merge]

        # Merge the main DataFrames (without source_url)
        merged = reduce(
            lambda left, right: pd.merge(
                left, right, on=["player_id", "player", "team", "date"], how="outer"
            ),
            dfs_wo_source_url,
        )

        # Concatenate all source_urls into one DataFrame
        all_source_urls = pd.concat(source_urls)

        # Merge back into the full merged DataFrame
        self.full_boxscore = pd.merge(
            merged,
            all_source_urls,
            on=["player_id", "player", "team", "date"],
            how="left"
        )

        # The outer merge creates some duplicate columns for kickers because their IDs apperar in both 
        # The kicking agg table and the punts_kicks table. Thus we drop duplicates
        self.full_boxscore = self.full_boxscore.drop_duplicates()

        # After merging, add in columns for home and away team with self.home team and self.away_team. Also add season
        self.full_boxscore["season"] = date.year if date.month > 7 else date.year - 1

        # Save the cleaned data to cloud if requested
        if self.gcloud_save:
            self._save_to_gcloud()

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

    def _get_commented_tables(self, url: str) -> None:
        scraped_html = requests.get(url)
        soup = BeautifulSoup(scraped_html.content, "html.parser")

        # Get all html comments, then filter out everything that isn't a table
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        commented_out_tables = [
            BeautifulSoup(cmt, features="lxml").find_all("table") for cmt in comments
        ]

        # Some of the entries in `commented_out_tables` are empty lists. Remove them.
        self.commented_out_tables = [
            tab[0] for tab in commented_out_tables if len(tab) == 1
        ]

    def _extract_ids(self, table: pd.DataFrame, id_col: str):
        table["player_id"] = table.loc[:, id_col].apply(
            lambda x: x[1] if isinstance(x, tuple) else None
        )
        table["player_id"] = table.player_id.apply(
            lambda x: x.split("/")[-1].split(".")[0] if x else None
        )
        table = table.map(lambda x: x[0] if isinstance(x, tuple) else x)
        return table

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

        # Update the column names
        main_table.columns = OFFENSIVE_COLUMNS_LIST

        # Add the date
        main_table["date"] = self.str_date

        # Determine the home and away team
        self.home_team = main_table.Tm.unique()[1]
        self.away_team = main_table.Tm.unique()[0]

        main_table["home_team"] = self.home_team
        main_table["away_team"] = self.away_team

        # Add the source URL
        main_table['source_url'] = self.url

        return main_table

    def _fetch_fg_boxscore(self):
        fg_boxscore = self.all_tables[1]
        # fg_boxscore.columns = fg_boxscore.columns.droplevel(0)

        # Break apart the player ids from the embedded player page links
        fg_boxscore = self._extract_ids(fg_boxscore, "Detail")

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

        # Add the date as a column
        fg_agg["date"] = self.str_date

        # Add the source URL
        fg_agg['source_url'] = self.url

        return fg_agg

    def _fetch_commented_table(
        self, table_id: str, id_col: str, renaming_dict: dict
    ) -> pd.DataFrame:
        try:
            table_html = [
                table
                for table in self.commented_out_tables
                if table.get("id") == table_id
            ][0]
        except IndexError:
            warnings.warn(f"No {table_id} table found: Returning an empty DataFrame")
            return pd.DataFrame()

        header = 0 if "advanced" in table_id else 1
        table = pd.read_html(
            StringIO(str(table_html)), header=header, extract_links="body"
        )[0]

        table = self._extract_ids(table, id_col)

        table = table.dropna(subset=["player_id"]).rename(columns=renaming_dict)

        # Add the source URL
        table['source_url'] = self.url

        return table
    
    def _save_to_gcloud(self):
        for year in self.season_years:
            df = self.full_boxscore[self.full_boxscore.season == year]
            downloader = CloudHelper()
            download = downloader.download_from_cloud(
                f"gs://nfl-data-collection/boxscores_{year}"
            )

            # If possible, drop duplicates from the download for a second pull on the same day and remove any
            # Unnamed columns from the upload/download process
            if isinstance(download, pd.DataFrame) and not download.empty:
                download = download[
                    [col for col in download.columns if "Unnamed:" not in col]
                ]

            self.boxscores_df = pd.concat([download, df]).drop_duplicates(
                subset=["player_id", "source_url"]
            )

            uploader = CloudHelper(self.boxscores_df)
            uploader.upload_to_cloud_from_local(
                bucket_name="nfl-data-collection", file_name=f"boxscores_{year}"
            )



if __name__ == "__main__":
    collector = NFLDailyStatsCollector(start_date="2024-09-11", end_date="2024-09-13")
    collector.run()

    print("X")
