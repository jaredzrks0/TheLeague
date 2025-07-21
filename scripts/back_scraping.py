from theleague.handlers.nfl_handler import NFLDailyStatsCollector


if __name__ == "__main__":
    collector = NFLDailyStatsCollector(
        start_date="2012-09-09", cache_frequency=2, caching=True
    )
    collector.run()
