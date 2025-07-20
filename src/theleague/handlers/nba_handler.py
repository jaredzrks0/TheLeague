import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime as dt
from multimodal_communication import CloudHelper


class NBADailyStatsCollector:
    def __init__(
        self, start_date, end_date, gcloud_save: bool = True, local_save: bool = False
    ):
        self.dates = pd.date_range(start_date, end_date)
        self.years = set([date.year for date in self.dates])
        self.gcloud_save = gcloud_save
        self.local_save = local_save

        assert len(self.dates) > 0, (
            f"start_date: {start_date} must be less than end_date: {end_date}"
        )

    def run(self):
        all_cleaned_boxscores = []

        for date in self.dates:
            print(f"Processing {date.date()}...")
            boxscore_urls = self._get_boxscore_urls_for_date(date)

            for url in boxscore_urls:
                print(f"  Scraping {url}")
                try:
                    boxscore_data = self._scrape_and_clean_boxscore(url, date)
                    all_cleaned_boxscores.extend(boxscore_data)
                except Exception as e:
                    print(f"  Failed to scrape {url}: {e}")
                time.sleep(6.1)  # Wait between each game to respect rate limits

        # Here you could return or save `all_cleaned_boxscoe
        self.cleaned_data = pd.concat(all_cleaned_boxscores, ignore_index=True)

        # Save the cleaned data to cloud if requested
        if self.gcloud_save:
            self._save_to_gcloud()

    def _get_boxscore_urls_for_date(self, date):
        url = f"https://www.basketball-reference.com/boxscores/?month={date.month}&day={date.day}&year={date.year}"
        response = requests.get(url)
        time.sleep(6.1)  # Sleep between each date

        soup = BeautifulSoup(response.text, "html.parser")
        boxscore_links = soup.find_all("td", {"class": "right gamelink"})

        return [
            "https://www.basketball-reference.com" + td.a["href"]
            for td in boxscore_links
        ]

    def _scrape_and_clean_boxscore(self, url, date):
        all_tables = pd.read_html(url, extract_links="all")
        cleaned_tables = []

        def is_basic(table):
            flat = [
                col[1][0] if isinstance(col, tuple) else str(col)
                for col in table.columns
            ]

            mp_col = [col for col in table.columns if "MP" in col[1]][0]

            if "Starters" in flat and "FG" in flat:
                if "240" in table[mp_col].iloc[-1]:
                    return True
            return False

        def is_advanced(table):
            flat = [
                col[1][0] if isinstance(col, tuple) else str(col)
                for col in table.columns
            ]

            mp_col = [col for col in table.columns if "MP" in col[1]][0]

            if "Starters" in flat and "TS%" in flat:
                if "240" in table[mp_col].iloc[-1]:
                    return True
            return False

        basic_tables = [t for t in all_tables if is_basic(t)]
        advanced_tables = [t for t in all_tables if is_advanced(t)]

        for basic, advanced in zip(basic_tables, advanced_tables):
            basic_cleaned = self._clean_boxscore(basic)
            advanced_cleaned = self._clean_boxscore(advanced)
            # Skip the set of boxscores if they are empty (not full game)
            if basic_cleaned.empty or advanced_cleaned.empty:
                continue

            merged = pd.merge(
                basic_cleaned,
                advanced_cleaned,
                on=["player_id"],
                how="left",
                suffixes=("_basic", "_adv"),
            )

            # Determine the home and away teams from the boxscore page soup
            req = requests.get(url)
            soup = BeautifulSoup(req.content, "html.parser")
            scorebox = soup.find("div", class_="scorebox")
            teams = [
                team_info.text.strip() for team_info in scorebox.find_all("strong")
            ]
            home_team, away_team = teams[1], teams[0]

            merged["date"] = date
            merged["source_url"] = url
            merged["season_year"] = merged.date.apply(
                lambda x: x.year - 1 if x.month <= 8 else x.year
            )
            merged["home_team"] = home_team
            merged["away_team"] = away_team

            merged.drop(columns=["Name_adv", "MP_adv"], inplace=True)
            merged.rename(
                columns={"Name_basic": "name", "MP_basic": "MP"}, inplace=True
            )
            cleaned_tables.append(merged)

        return cleaned_tables

    def _clean_boxscore(self, boxscore):
        # Flatten multi-level columns to get clean names
        boxscore.columns = [
            col[1][0] if isinstance(col, tuple) else str(col)
            for col in boxscore.columns
        ]

        # Rename and extract player name + link
        if "Starters" in boxscore.columns:
            boxscore[["Name", "Link"]] = pd.DataFrame(
                boxscore["Starters"].tolist(), index=boxscore.index
            )
            boxscore.drop(columns=["Starters"], inplace=True)
        else:
            raise ValueError("Could not find 'Starters' column in boxscore")

        # Split the tuples remaining in each cell
        boxscore = boxscore.map(
            lambda cell: cell[0] if isinstance(cell, tuple) else cell
        )

        # Break and return empty df if not the full game boxscore. Change this line in the future if wanting to
        # Collect halftime or quarter stats.
        if int(boxscore.MP.iloc[-1]) != 240:
            return pd.DataFrame()

        # Filter out unwanted rows: Reserves, Team Totals, DNPs
        boxscore = boxscore[~boxscore["Name"].isin(["Reserves", "Team Totals"])]
        boxscore = boxscore[
            ~boxscore["MP"]
            .astype(str)
            .str.contains(
                "Did Not Play|Inactive|Not With Team|Suspended|Did Not Dress", na=False
            )
        ]

        # Extract player_id
        boxscore["player_id"] = boxscore["Link"].str.extract(
            r"/([a-z0-9]+)\.html$", expand=False
        )
        boxscore.drop(columns=["Link"], inplace=True)

        # Convert MP to float
        boxscore["MP"] = (
            boxscore["MP"]
            .astype(str)
            .str.extract(r"(\d+):(\d+)", expand=True)
            .astype(float)
            .apply(
                lambda x: x[0] + x[1] / 60
                if pd.notnull(x[0]) and pd.notnull(x[1])
                else None,
                axis=1,
            )
        )

        boxscore = boxscore[
            ["Name", "player_id"]
            + [col for col in boxscore.columns if col not in ["Name", "player_id"]]
        ]

        return boxscore

    def _save_to_gcloud(self):
        for year in self.years:
            df = self.cleaned_data[self.cleaned_data.date.dt.year == year]
            downloader = CloudHelper()
            download = downloader.download_from_cloud(
                f"gs://nba-data-collection/boxscores_{year}"
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
                bucket_name="nba-data-collection", file_name=f"boxscores_{year}"
            )


if __name__ == "__main__":
    collector = NBADailyStatsCollector(start_date="2025-01-05", end_date="2025-01-05")
    collector.run()

    # Optional: save result
    # collector.boxscores_df.to_csv("nba_boxscores.csv", index=False)
