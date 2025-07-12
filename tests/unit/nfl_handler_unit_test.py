import pytest
from functools import wraps
import io
import pandas as pd
from theleague.nfl_handler import NFLDailyStatsCollector


# Make a fixture for the stats collector object (attributes are fake)
@pytest.fixture
def collector():
    obj = NFLDailyStatsCollector(
        start_date="2023-09-10",
        end_date="2023-09-10",
        gcloud_save=False,
        local_save=False,
    )
    obj.str_date = "2023-09-10"
    obj.url = "https://fakeurl.com/sample_game"
    obj.week = 1
    return obj


# Make a fixture function that reads in local HTML file
# This will be used in mocking pd.read_html
@pytest.fixture
def local_html(request):
    fpath = request.param
    with open(fpath, "r", encoding="utf-8") as f:
        return f.read()


# Fixture to mock pandas.read_html using the HTML loaded by local_html
@pytest.fixture
def mock_read_html(monkeypatch, local_html):
    # Save off the original function
    original_read_html = pd.read_html

    def _mock_read_html(*args, **kwargs):
        # Load in the html file with the local_html fixture and then
        # pd read the contents
        html_io = io.StringIO(local_html)
        return original_read_html(html_io, **kwargs)

    # Override the underlying pandas function with our mock function
    monkeypatch.setattr(pd, "read_html", _mock_read_html)
    yield
    # monkeypatch automatically reverts after the test


# Create a wrapper to parameterize both the new and old HTML paths for quick
# Parameterization for each test
def parametrize_local_html(test_func):
    @pytest.mark.parametrize(
        "local_html",
        ["tests/data/old_sample_game.html", "tests/data/new_sample_game.html"],
        indirect=True,
    )
    @wraps(test_func)
    def wrapper(*args, **kwargs):
        return test_func(*args, **kwargs)

    return wrapper


# === TESTS!!! ===
@parametrize_local_html
def test_fetch_offensive_boxscore(monkeypatch, collector, mock_read_html, local_html):
    # Fetch the offensive boxscore
    df = collector._fetch_offensive_boxscore(url="fakeurl")

    # Simple assertion to ensure the DataFrame isn't empty
    assert not df.empty
    assert len(df.team.value_counts()) == 2
    assert len(df.week.unique()) == 1
    assert len(df.date.unique()) == 1
    assert (df.home_team == df.away_team).mean() == 0

    required_cols = {
        "player",
        "team",
        "source_url",
        "player_id",
        "date",
        "home_team",
        "away_team",
        "home_away",
    }
    assert required_cols.issubset(df.columns), (
        f"Missing columns: {required_cols - set(df.columns)}"
    )


@parametrize_local_html
def test_fetch_fg_boxscore(monkeypatch, collector, mock_read_html, local_html):
    # Fetch the fg boxscore via initial offensive box pull
    collector._fetch_offensive_boxscore(url="fakeurl")
    df = collector._fetch_fg_boxscore()

    assert not df.empty
