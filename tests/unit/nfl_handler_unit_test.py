
import pytest
import io
import pandas as pd
from theleague.nfl_handler import NFLDailyStatsCollector

# === Fixture to create the collector ===
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

# === Fixture that loads the HTML from a local file ===
@pytest.fixture
def local_html(request):
    fpath = request.param
    with open(fpath, "r", encoding="utf-8") as f:
        return f.read()
    
# Fixture to mock pandas.read_html using the HTML loaded by local_html
@pytest.fixture
def mock_read_html(monkeypatch, local_html):
    original_read_html = pd.read_html

    def _mock_read_html(*args, **kwargs):
        # Always parse from the loaded local HTML string
        html_io = io.StringIO(local_html)
        return original_read_html(html_io, **kwargs)

    monkeypatch.setattr(pd, "read_html", _mock_read_html)
    yield
    # monkeypatch automatically reverts after the test

# === The test using monkeypatch and indirect HTML loading ===
@pytest.mark.parametrize(
    "local_html", 
    ["tests/data/old_sample_game.html", "tests/data/new_sample_game.html"], 
    indirect=True
)
def test_fetch_offensive_and_fg_boxscore(monkeypatch, collector, mock_read_html, local_html):
    # Backup the original function just in case
    original_read_html = pd.read_html

    # Run the function you're testing
    df = collector._fetch_offensive_boxscore(url='fakeurl')

    # Simple assertion to ensure the DataFrame isn't empty
    assert not df.empty
