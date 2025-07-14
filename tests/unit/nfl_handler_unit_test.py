import pytest
from functools import wraps
import io
import pandas as pd
from theleague.nfl_handler import NFLDailyStatsCollector


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


@pytest.fixture
def local_html(request):
    fpath = request.param
    with open(fpath, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def mock_read_html(monkeypatch, local_html):
    original_read_html = pd.read_html

    def _mock_read_html(*args, **kwargs):
        html_io = io.StringIO(local_html)
        return original_read_html(html_io, **kwargs)

    monkeypatch.setattr(pd, "read_html", _mock_read_html)
    yield


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


@parametrize_local_html
def test_fetch_offensive_boxscore(monkeypatch, collector, mock_read_html, local_html):
    df = collector._fetch_offensive_boxscore(url="fakeurl")
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
    collector._fetch_offensive_boxscore(url="fakeurl")
    df = collector._fetch_fg_boxscore()
    assert not df.empty
    assert "player_id" in df.columns
    assert "kicker" in df.columns
    assert "total_made_fg_distance" in df.columns
    assert df.total_made_fg_distance.notnull().all()


@parametrize_local_html
def test_fetch_commented_tables(monkeypatch, collector, mock_read_html, local_html):
    # Override requests.get to return mock HTML
    class FakeResponse:
        def __init__(self, text):
            self.content = text.encode("utf-8")

    monkeypatch.setattr("requests.get", lambda *a, **kw: FakeResponse(local_html))
    collector._fetch_commented_tables(url="fakeurl")
    assert isinstance(collector.commented_out_tables, list)
    assert all([t.name == "table" for t in collector.commented_out_tables])


@parametrize_local_html
def test_fetch_commented_table(monkeypatch, collector, mock_read_html, local_html):
    class FakeResponse:
        def __init__(self, text):
            self.content = text.encode("utf-8")

    monkeypatch.setattr("requests.get", lambda *a, **kw: FakeResponse(local_html))
    collector._fetch_commented_tables(url="fakeurl")
    df = collector._fetch_commented_table(
        table_id="player_defense",
        id_col="player_id",
        renaming_dict={"Tkl": "tackles", "Ast": "assists"},
    )
    assert isinstance(df, pd.DataFrame)
    assert "player_id" in df.columns
    assert "source_url" in df.columns or df.empty


@parametrize_local_html
def test_extract_ids(collector, mock_read_html, local_html):
    df = pd.DataFrame(
        {
            "Detail": [
                ("Some Kicker Link", "/players/S/SomeKi20.htm"),
                ("Another Kicker", "/players/A/AnotKi99.htm"),
            ]
        }
    )
    result = collector._extract_ids(df, "Detail")
    assert "player_id" in result.columns
    assert result["player_id"].iloc[0] == "SomeKi20"


@parametrize_local_html
def test_process_and_upload_data(monkeypatch, collector, mock_read_html, local_html):
    monkeypatch.setattr(collector, "_save_to_gcloud", lambda df: None)

    df = collector._fetch_offensive_boxscore(url="fakeurl")
    fg_df = collector._fetch_fg_boxscore()

    result = collector._process_and_upload_data(
        offensive_dfs=[df],
        fg_dfs=[fg_df],
        defense_dfs=[],
        punt_kick_return_dfs=[],
        punt_kick_dfs=[],
        passing_adv_dfs=[],
        receiving_adv_dfs=[],
        rushing_adv_dfs=[],
        defense_adv_dfs=[],
        snap_count_dfs=[],
        current_date=pd.to_datetime("2023-09-10"),
        is_cache=False,
    )

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert "player" in result.columns
    assert "team" in result.columns
    assert "season" in result.columns


def test_get_boxscore_urls_for_date(collector):
    urls, weeks = collector._get_boxscore_urls_for_date("2023-09-10")
    assert isinstance(urls, pd.Series)
    assert isinstance(weeks, list)


def test_save_to_gcloud_warns_on_empty(monkeypatch, collector):
    monkeypatch.setattr(collector, "full_boxscore", pd.DataFrame())
    collector._save_to_gcloud(df=None)  # Should log a warning and not raise


def test_gcloud_upload_helper_handles_failure(monkeypatch, collector):
    monkeypatch.setattr(
        "theleague.nfl_handler.CloudHelper",
        lambda *args, **kwargs: (_ for _ in ()).throw(Exception("mock fail")),
    )
    with pytest.raises(Exception):
        collector._gcloud_upload_helper(pd.DataFrame({"season": [2023]}), year=2023)


# import pytest
# from functools import wraps
# import io
# import pandas as pd
# from theleague.nfl_handler import NFLDailyStatsCollector


# # Make a fixture for the stats collector object (attributes are fake)
# @pytest.fixture
# def collector():
#     obj = NFLDailyStatsCollector(
#         start_date="2023-09-10",
#         end_date="2023-09-10",
#         gcloud_save=False,
#         local_save=False,
#     )
#     obj.str_date = "2023-09-10"
#     obj.url = "https://fakeurl.com/sample_game"
#     obj.week = 1
#     return obj


# # Make a fixture function that reads in local HTML file
# # This will be used in mocking pd.read_html
# @pytest.fixture
# def local_html(request):
#     fpath = request.param
#     with open(fpath, "r", encoding="utf-8") as f:
#         return f.read()


# # Fixture to mock pandas.read_html using the HTML loaded by local_html
# @pytest.fixture
# def mock_read_html(monkeypatch, local_html):
#     # Save off the original function
#     original_read_html = pd.read_html

#     def _mock_read_html(*args, **kwargs):
#         # Load in the html file with the local_html fixture and then
#         # pd read the contents
#         html_io = io.StringIO(local_html)
#         return original_read_html(html_io, **kwargs)

#     # Override the underlying pandas function with our mock function
#     monkeypatch.setattr(pd, "read_html", _mock_read_html)
#     yield
#     # monkeypatch automatically reverts after the test


# # Create a wrapper to parameterize both the new and old HTML paths for quick
# # Parameterization for each test
# def parametrize_local_html(test_func):
#     @pytest.mark.parametrize(
#         "local_html",
#         ["tests/data/old_sample_game.html", "tests/data/new_sample_game.html"],
#         indirect=True,
#     )
#     @wraps(test_func)
#     def wrapper(*args, **kwargs):
#         return test_func(*args, **kwargs)

#     return wrapper


# # === TESTS!!! ===
# @parametrize_local_html
# def test_fetch_offensive_boxscore(monkeypatch, collector, mock_read_html, local_html):
#     # Fetch the offensive boxscore
#     df = collector._fetch_offensive_boxscore(url="fakeurl")

#     # Simple assertion to ensure the DataFrame isn't empty
#     assert not df.empty
#     assert len(df.team.value_counts()) == 2
#     assert len(df.week.unique()) == 1
#     assert len(df.date.unique()) == 1
#     assert (df.home_team == df.away_team).mean() == 0

#     required_cols = {
#         "player",
#         "team",
#         "source_url",
#         "player_id",
#         "date",
#         "home_team",
#         "away_team",
#         "home_away",
#     }
#     assert required_cols.issubset(df.columns), (
#         f"Missing columns: {required_cols - set(df.columns)}"
#     )


# @parametrize_local_html
# def test_fetch_fg_boxscore(monkeypatch, collector, mock_read_html, local_html):
#     # Fetch the fg boxscore via initial offensive box pull
#     collector._fetch_offensive_boxscore(url="fakeurl")
#     df = collector._fetch_fg_boxscore()

#     assert not df.empty
