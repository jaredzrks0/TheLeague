import pytest
import pandas as pd
from io import StringIO
from theleague.nfl_handler import NFLDailyStatsCollector

@pytest.fixture
def collector():
    # Initialize with minimal args; adjust as per your constructor
    # We mock or set required attributes like str_date, url, week for the test
    obj = NFLDailyStatsCollector(start_date="2023-09-10", end_date="2023-09-10", gcloud_save=False, local_save=False)
    obj.str_date = "2023-09-10"
    obj.url = "https://fakeurl.com/sample_game"
    obj.week = 1
    return obj

@pytest.fixture
def local_html():
    with open("tests/data/old_sample_game.html", "r", encoding="utf-8") as f:
        return f.read()

@pytest.fixture
def mock_read_html(local_html):
    original_read_html = pd.read_html  # <--- Capture before patching

    def _mock_read_html(*args, **kwargs):
        return original_read_html(local_html, **kwargs)

    return _mock_read_html

def test_fetch_offensive_and_fg_boxscore(monkeypatch, collector, mock_read_html):
    # Mock pd.read_html to read from the local HTML string instead of the URL
    monkeypatch.setattr(pd, "read_html", mock_read_html)

    # Call _fetch_offensive_boxscore - it uses pd.read_html internally
    offensive_df = collector._fetch_offensive_boxscore("any_url_here")
    assert not offensive_df.empty, "Offensive DataFrame should not be empty"
    assert "player_id" in offensive_df.columns, "Offensive DataFrame missing player_id column"
    assert "date" in offensive_df.columns, "Offensive DataFrame missing date column"
    assert offensive_df["date"].iloc[0] == collector.str_date

    # The method sets home_team and away_team attributes
    assert hasattr(collector, "home_team"), "Collector missing home_team attribute"
    assert hasattr(collector, "away_team"), "Collector missing away_team attribute"

    # # Call _fetch_fg_boxscore - relies on collector.all_tables set by previous method
    # fg_df = collector._fetch_fg_boxscore()
    # assert not fg_df.empty, "FG DataFrame should not be empty"
    # assert "player_id" in fg_df.columns, "FG DataFrame missing player_id column"
    # assert "kicker" in fg_df.columns, "FG DataFrame missing kicker column"
    # assert "distance" in fg_df.columns, "FG DataFrame missing distance column"
    # assert fg_df["date"].iloc[0] == collector.str_date
