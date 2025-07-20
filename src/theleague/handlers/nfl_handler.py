import time
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup, Comment
from io import StringIO
import numpy as np
from datetime import datetime as dt
from multimodal_communication import CloudHelper
from functools import reduce
import warnings
import logging
from theleague.constants.nfl_constants import (
    OFFENSIVE_COLUMNS_LIST,
    OFFENSIVE_RENAMING_DICT,
    FG_RENAMING_DICT,
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
        self,
        start_date: str,
        end_date: str | None = None,
        gcloud_save: bool = True,
        local_save: bool = False,
        caching: bool = False,
        cache_frequency: int = 5,
        log_level: str = "INFO",
    ):
        # If no end_date given, default to the start date for a 1 day pull
        if not end_date:
            end_date = start_date
        self.dates = pd.date_range(start_date, end_date)
        season_years = pd.Series(self.dates).apply(
            lambda x: x.year - 1 if x.month <= 8 else x.year
        )
        self.season_years = set(season_years)
        self.gcloud_save = gcloud_save
        self.local_save = local_save
        self.caching = caching
        self.cache_frequency = cache_frequency
        self.games_processed = 0

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Create console handler if it doesn't exist
        if not self.logger.handlers:
            # Logging formatter
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # File handler (optional)
            file_handler = logging.FileHandler("nfl_stats.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Set up the Selenium driver
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(options=options)

        assert len(self.dates) > 0, (
            f"start_date: {start_date} must be less than end_date: {end_date}"
        )

        self.logger.info(f"Initialized NFL Stats Collector for {len(self.dates)} dates")
        self.logger.info(f"Season years: {sorted(self.season_years)}")
        self.logger.info(
            f"Caching enabled: {self.caching}, Cache frequency: {self.cache_frequency}"
        )

    def run(self):
        self.logger.info("Starting NFL stats collection")

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

        total_games = 0
        for date in self.dates:
            # Don't scrape dates we are 100% certain will not have NFL games
            if date.month in [3, 4, 5, 6, 7, 8]:
                continue

            self.logger.info(f"Processing {date.date()}...")
            self.str_date = date.strftime("%Y-%m-%d")

            # Collect all the url suffixes for the games on the given day
            try:
                boxscore_urls, weeks = self._get_boxscore_urls_for_date(date)
                total_games += len(boxscore_urls)
                self.logger.info(f"Found {len(boxscore_urls)} games for {date.date()}")
            except Exception as e:
                self.logger.error(f"Failed to get boxscore URLs for {date.date()}: {e}")
                continue

            time.sleep(6.1)

            # Grab and clean all the individual box scores
            for suffix, week in zip(boxscore_urls, weeks):
                self.url = "https://www.pro-football-reference.com" + suffix
                self.week = week
                self.logger.info(f"Scraping {self.url}")

                try:
                    boxscore_data = self._fetch_offensive_boxscore(self.url)
                    all_cleaned_offensive_dfs.append(boxscore_data)
                    fg_data = self._fetch_fg_boxscore()
                    all_cleaned_fg_dfs.append(fg_data)

                    ### Get Commented tables ###
                    time.sleep(6.1)
                    self._fetch_commented_tables(self.url)

                    # Basic Defense
                    basic_defense = self._fetch_commented_table(
                        "player_defense", "Player", PLAYER_DEFENSE_RENAMING_DICT
                    )
                    all_cleaned_basic_defense_dfs.append(basic_defense)

                    # Punt and kick returns
                    punt_kick_returns = self._fetch_commented_table(
                        "returns", "Player", PUNT_KICK_RETURNS_RENAMING_DICT
                    )
                    all_cleaned_punt_kick_returns_dfs.append(punt_kick_returns)

                    # Punts and kicks
                    punts_kicks = self._fetch_commented_table(
                        "kicking", "Player", PUNT_KICK_RENAMING_DICT
                    )
                    all_cleaned_punt_kick_dfs.append(punts_kicks)

                    # Advanced passing
                    passing_advanced = self._fetch_commented_table(
                        "passing_advanced", "Player", PASSING_ADVANCED_RENAMING_DICT
                    )
                    all_cleaned_passing_advanced_dfs.append(passing_advanced)

                    # Advanced receiving
                    receiving_advanced = self._fetch_commented_table(
                        "receiving_advanced", "Player", RECEIVING_ADVANCED_RENAMING_DICT
                    )
                    all_cleaned_receiving_advanced_dfs.append(receiving_advanced)

                    # Advanced rushing
                    rushing_advanced = self._fetch_commented_table(
                        "rushing_advanced", "Player", RUSHING_ADVANCED_RENAMING_DICT
                    )
                    all_cleaned_rushing_advanced_dfs.append(rushing_advanced)

                    # Advanced Defense
                    defense_advanced = self._fetch_commented_table(
                        "defense_advanced", "Player", DEFENSE_ADVANCED_RENAMING_DICT
                    )
                    all_cleaned_defense_advanced_dfs.append(defense_advanced)

                    # Snap Counts
                    home_snap_counts = self._fetch_commented_table(
                        "home_snap_counts", "Player", SNAP_COUNT_RENAMING_DICT
                    )
                    home_snap_counts["team"] = self.home_team

                    away_snap_counts = self._fetch_commented_table(
                        "vis_snap_counts", "Player", SNAP_COUNT_RENAMING_DICT
                    )
                    away_snap_counts["team"] = self.away_team

                    all_cleaned_snap_counts.append(home_snap_counts)
                    all_cleaned_snap_counts.append(away_snap_counts)

                    self.games_processed += 1
                    self.logger.info(
                        f"Successfully processed game {self.games_processed}/{total_games}"
                    )

                    # Intermittent caching - upload current progress
                    if (
                        self.caching
                        and self.gcloud_save
                        and self.games_processed % self.cache_frequency == 0
                    ):
                        self.logger.info(
                            f"Caching progress after {self.games_processed} games..."
                        )
                        self._process_and_upload_data(
                            all_cleaned_offensive_dfs,
                            all_cleaned_fg_dfs,
                            all_cleaned_basic_defense_dfs,
                            all_cleaned_punt_kick_returns_dfs,
                            all_cleaned_punt_kick_dfs,
                            all_cleaned_passing_advanced_dfs,
                            all_cleaned_receiving_advanced_dfs,
                            all_cleaned_rushing_advanced_dfs,
                            all_cleaned_defense_advanced_dfs,
                            all_cleaned_snap_counts,
                            date,
                            is_cache=True,
                        )

                    time.sleep(6.1)
                except Exception as e:
                    self.logger.error(f"Failed to scrape {self.url}: {e}")
                time.sleep(6.1)  # Wait between each game to respect rate limits

        # Close the driver
        self.driver.quit()

        # Final processing and upload
        self.logger.info("Processing final data and uploading to cloud...")
        self.full_boxscore = self._process_and_upload_data(
            all_cleaned_offensive_dfs,
            all_cleaned_fg_dfs,
            all_cleaned_basic_defense_dfs,
            all_cleaned_punt_kick_returns_dfs,
            all_cleaned_punt_kick_dfs,
            all_cleaned_passing_advanced_dfs,
            all_cleaned_receiving_advanced_dfs,
            all_cleaned_rushing_advanced_dfs,
            all_cleaned_defense_advanced_dfs,
            all_cleaned_snap_counts,
            date,
            is_cache=False,
        )

        self.logger.info(f"Successfully processed {self.games_processed} games")
        return self.full_boxscore

    def _process_and_upload_data(
        self,
        offensive_dfs,
        fg_dfs,
        defense_dfs,
        punt_kick_return_dfs,
        punt_kick_dfs,
        passing_adv_dfs,
        receiving_adv_dfs,
        rushing_adv_dfs,
        defense_adv_dfs,
        snap_count_dfs,
        current_date,
        is_cache=False,
    ):
        """Process and optionally upload data to Google Cloud"""
        try:
            # Check if we have any data to process
            if not offensive_dfs:
                self.logger.warning("No offensive data found to process")
                return None if not is_cache else pd.DataFrame()

            self.logger.info(f"Processing {len(offensive_dfs)} offensive records...")

            # Concatenate and rename offensive data
            offensive_boxscores = pd.concat(offensive_dfs)

            # Process boxscores
            fg_boxscores = self._concat_and_drop(fg_dfs)
            basic_defense_boxscores = self._concat_and_drop(defense_dfs)
            punt_kick_return_boxscores = self._concat_and_drop(punt_kick_return_dfs)
            punts_kicks_boxscores = self._concat_and_drop(punt_kick_dfs)

            # Advanced stats with column dropping
            passing_advanced_boxscores = self._concat_and_drop(
                passing_adv_dfs, drop_cols=["Cmp", "Att", "Yds"]
            )
            receiving_advanced_boxscores = self._concat_and_drop(
                receiving_adv_dfs, drop_cols=["Tgt", "Rec", "Yds", "TD"]
            )
            rushing_advanced_boxscores = self._concat_and_drop(
                rushing_adv_dfs, drop_cols=["Att", "Yds", "TD"]
            )
            defense_advanced_boxscores = self._concat_and_drop(
                defense_adv_dfs,
                drop_cols=["Int", "Yds", "TD", "Sk", "defensive_qb_hits"],
            )
            snap_count_boxscores = self._concat_and_drop(snap_count_dfs)

            # Collect all dataframes for merging
            dfs_to_merge = [
                offensive_boxscores,
                fg_boxscores,
                basic_defense_boxscores,
                punt_kick_return_boxscores,
                punts_kicks_boxscores,
                passing_advanced_boxscores,
                receiving_advanced_boxscores,
                rushing_advanced_boxscores,
                defense_advanced_boxscores,
                snap_count_boxscores,
            ]

            # Filter out empty dataframes
            dfs_to_merge = [df for df in dfs_to_merge if not df.empty]

            if not dfs_to_merge:
                self.logger.warning("No data to merge")
                return None if not is_cache else pd.DataFrame()

            self.logger.info(f"Merging {len(dfs_to_merge)} dataframes...")

            # Extract source_url columns and drop from original
            source_urls = [
                df[["player_id", "player", "team", "date", "source_url"]]
                for df in dfs_to_merge
                if "source_url" in df.columns and not df.empty
            ]
            dfs_wo_source_url = [
                df.drop(columns=["source_url"], errors="ignore") for df in dfs_to_merge
            ]

            # Merge the main DataFrames
            merged = reduce(
                lambda left, right: pd.merge(
                    left,
                    right,
                    on=["player_id", "player", "team", "date", "week"],
                    how="outer",
                ),
                dfs_wo_source_url,
            )

            # Add source URLs back if they exist
            if source_urls:
                all_source_urls = pd.concat(source_urls)
                merged = pd.merge(
                    merged,
                    all_source_urls,
                    on=["player_id", "player", "team", "date"],
                    how="left",
                )
                self.logger.debug("Added source URLs back to merged data")

            # Add season and remove duplicates
            merged["season"] = (
                current_date.year if current_date.month > 7 else current_date.year - 1
            )
            merged = merged.drop_duplicates()

            # Reorder the columns with the identifiers at the front
            identifier_cols = [
                "player",
                "player_id",
                "team",
                "date",
                "week",
                "season",
                "home_away",
                "home_team",
                "away_team",
            ]

            merged = merged[
                identifier_cols
                + [col for col in merged.columns if col not in identifier_cols]
            ].drop(columns=["index"])

            self.logger.info(f"Final merged dataset shape: {merged.shape}")

            # Save to cloud if requested
            if self.gcloud_save:
                self.logger.info("Uploading to Google Cloud...")
                self._save_to_gcloud(merged)

            if is_cache:
                self.logger.info("Cache upload completed successfully")
            else:
                self.logger.info(
                    "Final data processing and upload completed successfully"
                )

            return merged

        except ValueError as e:
            if "No objects to concatenate" in str(e):
                self.logger.warning("No NFL games found in the requested date range")
                return None
            else:
                self.logger.error(f"ValueError during data processing: {e}")
                raise
        except Exception as e:
            error_msg = f"Failed to process data: {e}"
            if is_cache:
                self.logger.warning(f"Cache failed: {error_msg}")
                return pd.DataFrame()
            else:
                self.logger.error(error_msg)
                raise

    def _concat_and_drop(self, dfs, drop_cols=None):
        df = pd.concat(dfs) if dfs else pd.DataFrame()
        if drop_cols and not df.empty:
            df = df.drop(columns=drop_cols, errors="ignore")
        return df

    def _get_boxscore_urls_for_date(self, date):
        # Ensure the given date is in a compatable date format and grab the year
        date = pd.to_datetime(date) if isinstance(date, str) else date
        season = date.year if date.month > 8 else date.year - 1

        games_url = f"https://www.pro-football-reference.com/years/{season}/games.htm"
        self.logger.debug(f"Fetching games from: {games_url}")

        self.driver.get(games_url)
        time.sleep(3)
        games_html = self.driver.page_source
        games_table = pd.read_html(StringIO(str(games_html)), extract_links="body")[0]

        # Compile the dates and suffixes from the full season for later date filtering
        games_table["dates"] = games_table["Date"].apply(lambda x: x[0])
        games_table["suffixes"] = games_table["Unnamed: 7"].apply(lambda x: x[1])

        # filter down to just the game suffixes that fall on the date
        suffixes = games_table[["dates", "suffixes", "Week"]].dropna()

        relevant_games = suffixes[suffixes.dates == date.strftime("%Y-%m-%d")]

        relevant_suffixes = relevant_games.suffixes

        # Get the weeks
        relevant_weeks = [week_tuple[0] for week_tuple in relevant_games.Week]

        return relevant_suffixes, relevant_weeks

    def _fetch_commented_tables(self, url: str) -> None:
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

        self.logger.debug(f"Found {len(self.commented_out_tables)} commented tables")

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
        self.driver.get(url)
        time.sleep(3)
        html = self.driver.page_source
        self.all_tables = pd.read_html(StringIO(str(html)), extract_links="body")
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

        # Update the column names order
        main_table.columns = OFFENSIVE_COLUMNS_LIST

        # Add the date
        main_table["date"] = self.str_date

        # Determine the home and away team
        self.home_team = main_table.Tm.unique()[1]
        self.away_team = main_table.Tm.unique()[0]

        main_table["home_team"] = self.home_team
        main_table["away_team"] = self.away_team

        # Add a home_away column
        main_table["home_away"] = main_table.apply(
            lambda x: "H" if x.Tm == x.home_team else "A", axis=1
        )

        # Add the source URL
        main_table["source_url"] = self.url

        # Add the week
        main_table["week"] = self.week

        # Final rename of columns
        main_table = main_table.rename(columns=OFFENSIVE_RENAMING_DICT)

        self.logger.debug(f"Processed offensive data: {main_table.shape[0]} players")

        return main_table

    def _fetch_fg_boxscore(self):
        fg_boxscore = self.all_tables[1]

        # Break apart the player ids from the embedded player page links
        fg_boxscore = self._extract_ids(fg_boxscore, "Detail")

        fg_boxscore = fg_boxscore.dropna(subset="player_id")
        fg_boxscore = fg_boxscore[
            (fg_boxscore.Detail.str.contains("field goal"))
            & (fg_boxscore.Detail.str.contains("field goal return") == False)  # noqa: E712
        ]
        fg_boxscore["kicker"] = fg_boxscore.Detail.apply(
            lambda x: " ".join(x.split("yard")[0].split(" ")[0:-2])
        )
        fg_boxscore["distance"] = fg_boxscore.Detail.apply(
            lambda x: (x.split("yard")[0].split(" ")[-2])
        )

        fg_boxscore["Quarter"] = fg_boxscore["Quarter"].replace("", np.nan)
        fg_boxscore["Quarter"] = fg_boxscore["Quarter"].ffill()
        fg_boxscore = fg_boxscore[["player_id", "kicker", "distance", "Tm"]]
        fg_boxscore["distance"] = pd.to_numeric(
            fg_boxscore["distance"], errors="coerce"
        ).astype("Int64")

        # Try to find a way to count the number of game winning FGs base on a criteria from the full scoring table

        fg_agg = fg_agg = (
            fg_boxscore.groupby(["player_id", "kicker", "Tm"])
            .agg(
                kicking_num_field_goals_made=("distance", "count"),
                kicking_total_made_field_goals_distance=("distance", "sum"),
                kicking_field_goals_made_average_distance=(
                    "distance",
                    "mean",
                ),  # optional
            )
            .reset_index()
        )

        fg_agg = fg_agg.reset_index()
        fg_agg = fg_agg.rename(columns=FG_RENAMING_DICT)

        # Add the date as a column
        fg_agg["date"] = self.str_date

        # Add the week
        fg_agg["week"] = self.week

        # Add the source URL
        fg_agg["source_url"] = self.url

        self.logger.debug(f"Processed FG data: {fg_agg.shape[0]} kickers")

        return fg_agg

    def _fetch_commented_table(
        self,
        table_id: str,
        id_col: str,
        renaming_dict: dict | None = None,
    ) -> pd.DataFrame:
        try:
            table_html = [
                table
                for table in self.commented_out_tables
                if table.get("id") == table_id
            ][0]
        except IndexError:
            self.logger.warning(
                f"No {table_id} table found: Returning an empty DataFrame"
            )
            return pd.DataFrame()

        header = 0 if "advanced" in table_id else 1
        table = pd.read_html(
            StringIO(str(table_html)), header=header, extract_links="body"
        )[0]

        table = self._extract_ids(table, id_col)

        table = table.dropna(subset=["player_id"])

        if renaming_dict:
            table = table.rename(columns=renaming_dict)

        # Add the source URL
        table["source_url"] = self.url

        # Add the date and week to the table
        table["date"] = self.str_date
        table["week"] = self.week

        self.logger.debug(f"Processed {table_id} table: {table.shape[0]} records")

        return table

    def _save_to_gcloud(self, df: pd.DataFrame | None = None):
        if df is None:
            df = self.full_boxscore

        if not isinstance(df, pd.DataFrame) or df.empty:
            self.logger.warning("No data to save to Google Cloud")
            return

        try:
            for year in df.season.unique():
                upload_df = df[df.season == year]
                self.logger.info(
                    f"Uploading {upload_df.shape[0]} records for season {year}"
                )
                self._gcloud_upload_helper(df=upload_df, year=year)
        except Exception as e:
            self.logger.error(f"Failed to save to Google Cloud: {e}")
            raise

    def _gcloud_upload_helper(self, df, year):
        try:
            self.logger.debug(f"Downloading existing data for {year}")
            downloader = CloudHelper()
            download = downloader.download_from_cloud(
                f"nfl-data-collection/boxscores_{year}.parquet"
            )

            # If possible, drop duplicates from the download for a second pull on the same day and remove any
            # Unnamed columns from the upload/download process
            if isinstance(download, pd.DataFrame) and not download.empty:
                download = download[
                    [col for col in download.columns if "Unnamed:" not in col]
                ]
                self.logger.debug(f"Found existing data: {download.shape[0]} records")
            else:
                self.logger.debug("No existing data found")

            self.boxscores_df = pd.concat([download, df]).drop_duplicates(
                subset=["player_id", "source_url"]
            )

            self.logger.info(
                f"Final dataset for {year}: {self.boxscores_df.shape[0]} records"
            )

            uploader = CloudHelper(self.boxscores_df)
            uploader.upload_to_cloud(
                bucket_name="nfl-data-collection", file_name=f"boxscores_{year}.parquet"
            )
            self.logger.info(f"Successfully uploaded boxscores_{year}.parquet")

        except Exception as e:
            self.logger.error(f"Failed to upload data for year {year}: {e}")
            raise
