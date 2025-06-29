from theleague.nfl_handler import NFLDailyStatsCollector


if __name__ == "__main__":
    collector = NFLDailyStatsCollector(start_date="2020-09-01", end_date="2024-03-01")
    collector.run()