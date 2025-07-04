from theleague.nfl_handler import NFLDailyStatsCollector


if __name__ == "__main__":
    collector = NFLDailyStatsCollector(start_date="2014-01-07", end_date="2014-01-15", cache_frequency=1, caching=True)
    collector.run()