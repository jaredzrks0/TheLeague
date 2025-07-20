from theleague.handlers.nfl_handler import NFLDailyStatsCollector
from theleague.pydantic_models.nfl_model import NFLBoxscore


boxscore = NFLBoxscore()
stats = NFLDailyStatsCollector(start_date="2025-02-09", gcloud_save=False).run()
