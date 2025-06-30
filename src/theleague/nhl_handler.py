import pandas as pd
import time




class NHLDailyStatsCollector:
    def __init__(
        self, start_date, end_date, gcloud_save: bool = True, local_save: bool = False
    ):
        self.dates = pd.date_range(start_date, end_date)
        season_years = pd.Series(self.dates).apply(
            lambda x: x.year + 1 if x.month >= 9 else x.year
        )
        self.season_years = set(season_years)
        self.gcloud_save = gcloud_save
        self.local_save = local_save

        assert len(self.dates) > 0, (
            f"start_date: {start_date} must be less than end_date: {end_date}"
        )

    def run(self):
        all_cleaned_main_stats = []
        all_cleaned_goalie_stats = []
        all_cleaned_advanced_stats = []

        for date in self.dates:
            print(f"Processing {date.date()}...")
            self.str_date = date.strftime("%Y-%m-%d")

            # Collect all the url suffixes for the games on the given day
            boxscore_urls, game_types, home_teams, away_teams = self._get_boxscore_urls_for_date(date)
            time.sleep(6.1)

            # Grab and clean all the individual box scores
            for suffix, game_type, home_team, away_team in zip(boxscore_urls, game_types, home_teams, away_teams):
                self.url = "https://www.hockey-reference.com" + suffix
                self.game_type = game_type
                self.home_team = home_team
                self.away_team = away_team

                print(f"  Scraping {self.url}")
                try:
                    self._fetch_boxscore_stats(self.url)

                    main_stats = self._extract_main_stats(self.boxscore_html)
                    main_stats = self._update_with_game_info(main_stats, game_type, home_team, away_team)
                    all_cleaned_main_stats.append(main_stats)

                    goalie_stats = self._extract_goalie_stats(self.boxscore_html)
                    goalie_stats = self._update_with_game_info(goalie_stats, game_type, home_team, away_team)
                    all_cleaned_goalie_stats.append(goalie_stats)

                    advanced_stats = self._extract_advanced_stats(self.boxscore_html)
                    advanced_stats = self._update_with_game_info(advanced_stats, game_type, home_team, away_team)
                    all_cleaned_advanced_stats.append(advanced_stats)
                except Exception as e:
                    print(f"  Failed to scrape {self.url}: {e}")



    def _get_boxscore_urls_for_date(self, date):
        # Ensure the given date is in a compatable date format and grab the year
        date = pd.to_datetime(date) if isinstance(date, str) else date
        season = date.year + 1 if date.month >= 9 else date.year
        
        games_url = f"https://www.hockey-reference.com/leagues/NHL_{season}_games.html"
        games_tables = pd.read_html(games_url, extract_links="body")
        reg_games_table = games_tables[0]
        playoff_games_table = games_tables[1]

        # Add the game type to each table 
        reg_games_table['game_type'] = 'R'
        playoff_games_table['game_type'] = 'P'

        # Concat the tables
        full_games_table = pd.concat([reg_games_table, playoff_games_table])

        # Compile the necessary info from the full season for later date filtering
        full_games_table["dates"] = full_games_table["Date"].apply(lambda x: x[0])
        full_games_table["suffixes"] = full_games_table["Date"].apply(lambda x: x[1])
        full_games_table['home_teams'] = full_games_table['Home'].apply(lambda x: x[0])
        full_games_table['away_teams'] = full_games_table['Visitor'].apply(lambda x: x[0])

        # filter down to just the game suffixes that fall on the date
        suffixes = full_games_table[["dates", "suffixes", 'game_type', 'home_teams', 'away_teams']].dropna()

        relevant_games = suffixes[
            suffixes.dates == date.strftime("%Y-%m-%d")
        ]

        relevant_suffixes = relevant_games.suffixes
        relevant_home_teams = relevant_games.home_teams
        relevant_away_teams = relevant_games.away_teams


        # Protects against some weird scenario where a game gets postponed into another week
        relevant_game_types = [game_tuple[0] for game_tuple in relevant_games.game_type]

        return relevant_suffixes, relevant_game_types, relevant_home_teams, relevant_away_teams
    
    def _fetch_boxscore_stats(self, url):
        self.boxscore_html = pd.read_html(url)

    def _update_with_game_info(self, table, game_type, home_team, away_team):
        table['game_type'] = game_type
        table['home_team'] = home_team
        table['away_team'] = away_team
        return table


if __name__ == '__main__':
    collector = NHLDailyStatsCollector(start_date = '2022-11-11', end_date = '2022-11-11')
    collector.run()