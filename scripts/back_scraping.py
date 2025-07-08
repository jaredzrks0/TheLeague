from theleague.nfl_handler import NFLDailyStatsCollector


if __name__ == "__main__":
    collector = NFLDailyStatsCollector(start_date="2023-01-01", end_date="2025-02-18", cache_frequency=5, caching=True)
    collector.run()