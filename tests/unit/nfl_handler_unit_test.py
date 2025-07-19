import pytest
from functools import wraps
import io
import pandas as pd
from theleague.nfl_handler import NFLDailyStatsCollector
from theleague.constants.nfl_constants import (
    OFFENSIVE_RENAMING_DICT,
    PLAYER_DEFENSE_RENAMING_DICT,
    PUNT_KICK_RETURNS_RENAMING_DICT,
    PUNT_KICK_RENAMING_DICT,
    PASSING_ADVANCED_RENAMING_DICT,
    RECEIVING_ADVANCED_RENAMING_DICT,
    RUSHING_ADVANCED_RENAMING_DICT,
    DEFENSE_ADVANCED_RENAMING_DICT,
    SNAP_COUNT_RENAMING_DICT,
)

READ_HTML = pd.read_html


class FakeResponse:
    def __init__(self, text):
        self.content = text.encode("utf-8")


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


@pytest.fixture
def mock_requests_get(monkeypatch, local_html):
    def _mocked_get(*args, **kwargs):
        return FakeResponse(local_html)

    monkeypatch.setattr("requests.get", _mocked_get)


def parametrize_local_html(test_func):
    @pytest.mark.parametrize(
        "local_html",
        ["tests/data/old_sample_game.html", "tests/data/new_sample_game.html"],
        indirect=True,
        ids=["old_data", "new_data"],
    )
    @wraps(test_func)
    def wrapper(*args, **kwargs):
        return test_func(*args, **kwargs)

    return wrapper


### TESTS!!! ###
def test_get_boxscore_urls_for_date(collector):
    urls, weeks = collector._get_boxscore_urls_for_date("2023-09-10")
    assert isinstance(urls, pd.Series)
    assert isinstance(weeks, list)


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
    assert df.total_made_fg_distance.notnull().all()

    required_cols = {
        "player_id",
        "kicker",
        "num_fg_made",
        "total_made_fg_distance",
        "date",
        "team",
    }
    assert required_cols.issubset(df.columns), (
        f"Missing columns: {required_cols - set(df.columns)}"
    )


@parametrize_local_html
def test_fetch_commented_tables(
    monkeypatch, collector, mock_read_html, local_html, mock_requests_get
):
    collector._fetch_commented_tables(url="fakeurl")

    # Ensure we now have a list of tables and only tables
    assert isinstance(collector.commented_out_tables, list)
    assert all([t.name == "table" for t in collector.commented_out_tables])


# Helper test generator
def generate_table_test(table_id, id_col, renaming_dict, required_keys):
    @parametrize_local_html
    def test_func(
        monkeypatch, collector, mock_read_html, local_html, mock_requests_get, request
    ):
        collector._fetch_commented_tables(url="fakeurl")
        monkeypatch.setattr(pd, "read_html", READ_HTML)

        html_type = request.node.callspec.id

        df = collector._fetch_commented_table(
            table_id=table_id,
            id_col=id_col,
            renaming_dict=renaming_dict,
        )
        assert isinstance(df, pd.DataFrame), "df must be a DataFrame"

        if html_type == "new_data" or "advanced" not in table_id:
            required_cols = set(renaming_dict.values())
            assert required_cols.issubset(df.columns), (
                f"Missing columns: {required_cols - set(df.columns)}"
            )
            for col in required_keys:
                assert df[col].isna().sum() == 0, (
                    f'column "{col}" must contain no missing data'
                )
        else:
            assert df.empty

    return test_func


test_fetch_basic_defense_table = generate_table_test(
    table_id="player_defense",
    id_col="Player",
    renaming_dict=PLAYER_DEFENSE_RENAMING_DICT,
    required_keys=["player", "team", "total_tackles", "solo"],
)

test_fetch_punt_kick_returns_table = generate_table_test(
    table_id="returns",
    id_col="Player",
    renaming_dict=PUNT_KICK_RETURNS_RENAMING_DICT,
    required_keys=["player", "team", "kick_return_yards", "punt_return_yards"],
)

test_fetch_punt_kick_table = generate_table_test(
    table_id="kicking",
    id_col="Player",
    renaming_dict=PUNT_KICK_RENAMING_DICT,
    required_keys=["player", "team", "extra_points_made", "punts", "longest_punt"],
)

test_fetch_passing_advanced_table = generate_table_test(
    table_id="passing_advanced",
    id_col="Player",
    renaming_dict=PASSING_ADVANCED_RENAMING_DICT,
    required_keys=["player", "team", "first_downs_thrown", "bad_throws", "sacks_taken"],
)

test_fetch_receiving_advanced_table = generate_table_test(
    table_id="receiving_advanced",
    id_col="Player",
    renaming_dict=RECEIVING_ADVANCED_RENAMING_DICT,
    required_keys=[
        "player",
        "team",
        "receiving_first_downs",
        "receiving_broken_tackles",
        "receiving_drops",
    ],
)

test_fetch_rushing_advanced_table = generate_table_test(
    table_id="rushing_advanced",
    id_col="Player",
    renaming_dict=RUSHING_ADVANCED_RENAMING_DICT,
    required_keys=[
        "player",
        "team",
        "rushing_first_downs",
        "rushing_yards_before_contact",
        "rushing_broken_tackles",
    ],
)

test_fetch_defense_advanced_table = generate_table_test(
    table_id="defense_advanced",
    id_col="Player",
    renaming_dict=DEFENSE_ADVANCED_RENAMING_DICT,
    required_keys=[
        "player",
        "team",
        "defense_targets",
        "defense_blitzes",
        "defense_qb_hits",
        "defense_missed_tackles",
    ],
)

test_fetch_snap_counts_table = generate_table_test(
    table_id="home_snap_counts",
    id_col="Player",
    renaming_dict=SNAP_COUNT_RENAMING_DICT,
    required_keys=[
        "player",
        "position",
        "offense_snaps",
        "defense_snaps",
        "special_teams_snaps",
    ],
)


def test_extract_ids(collector):
    df = pd.DataFrame(
        {
            "Detail": [
                (
                    "Justin Jefferson",
                    "https://www.pro-football-reference.com/players/J/JeffJu00.htm",
                ),
                (
                    "Another Kicker",
                    "https://www.pro-football-reference.com/players/M/McCaJJ00.htm",
                ),
            ]
        }
    )
    result = collector._extract_ids(df, "Detail")
    assert "player_id" in result.columns
    assert result["player_id"].iloc[0] == "JeffJu00"
    assert result["player_id"].iloc[1] == "McCaJJ00"


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
