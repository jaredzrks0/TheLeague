from theleague.nfl_handler import NFLDailyStatsCollector


if __name__ == "__main__":
    collector = NFLDailyStatsCollector(start_date="2012-09-01", end_date="2013-02-18")
    collector.run()