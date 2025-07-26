from theleague.handlers.nfl_handler import NFLDailyStatsCollector


if __name__ == "__main__":
    collector = NFLDailyStatsCollector(
        start_date="2012-12-16", end_date="2016-02-18", cache_frequency=10, caching=True
    )
    collector.run()
