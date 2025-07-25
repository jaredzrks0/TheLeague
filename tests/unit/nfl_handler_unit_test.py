import pytest
from unittest.mock import patch, MagicMock
from functools import wraps
import io
import pandas as pd
import logging
import time

from theleague.handlers.nfl_handler import NFLDailyStatsCollector
from theleague.pydantic_models.nfl_model import NFLBoxscore
from theleague.constants.nfl_constants import (
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
def mock_read_local_html(request):
    """
    Fixture to read local HTML content from a specified file path.
    Used by parametrize_local_html decorator.
    Provides a default empty string if not parametrized (e.g., for tests
    that don't directly need HTML content but rely on fixtures that do).
    """
    if hasattr(request, "param"):
        fpath = request.param
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()
    else:
        # Provide a default HTML for tests that don't specify content
        # (like test_extract_ids) but still instantiate collector/driver.
        return "<html><body><p>Default Mock HTML</p></body></html>"


# --- New/Modified Fixtures for Selenium Mocking ---


# @pytest.fixture
# def mock_selenium_driver_setup(monkeypatch, mock_read_local_html):
#     """
#     Mocks the Selenium WebDriver and related functions.

#     - Patches `webdriver.Chrome` so that `NFLDailyStatsCollector.__init__`
#       gets a MagicMock instead of a real browser instance.
#     - Configures the mocked driver's `page_source` to return content
#       from `mock_read_local_html`.
#     - Patches `time.sleep` within the `nfl_handler` module to prevent
#       actual delays during tests.
#     """
#     # Create a MagicMock for the driver instance
#     mock_driver_instance = MagicMock()

#     # Set the return value for the 'page_source' property of the mocked driver
#     # Using type() is important for mocking properties
#     type(mock_driver_instance).page_source = mock_read_local_html

#     # Patch webdriver.Chrome where it's imported in nfl_handler.py
#     # This ensures that when NFLDailyStatsCollector() is instantiated,
#     # self.driver becomes our mock_driver_instance.
#     # Note: Adjust the path 'theleague.handlers.nfl_handler.webdriver'
#     # if your webdriver import path is different in nfl_handler.py
#     monkeypatch.setattr(
#         "theleague.handlers.nfl_handler.webdriver",
#         MagicMock(Chrome=MagicMock(return_value=mock_driver_instance)),
#     )

#     # Patch time.sleep within the nfl_handler module
#     # This prevents the test from actually waiting for 6 seconds.
#     monkeypatch.setattr("theleague.handlers.nfl_handler.time.sleep", MagicMock())

#     # Yield the mocked driver instance for direct assertions in tests if needed
#     yield mock_driver_instance


@pytest.fixture
def mock_selenium_driver_setup(monkeypatch, mock_read_local_html, request):
    mock_driver_instance = MagicMock()

    url_html_map = {
        "https://www.pro-football-reference.com/years/2023/games.htm": "tests/data/2023_games.html",
        "fakeurl": request.getfixturevalue("mock_read_local_html"),  # Existing
    }

    visited_urls = {}

    def get_side_effect(url):
        visited_urls["last_url"] = url  # track the URL requested

    def page_source_side_effect():
        url = visited_urls.get("last_url")
        if url in url_html_map:
            html_path = url_html_map[url]
            if isinstance(html_path, str) and html_path.endswith(".html"):
                with open(html_path, "r", encoding="utf-8") as f:
                    return f.read()
            return html_path  # fallback (e.g., default mock_read_local_html str)
        return "<html><body><p>Unknown URL</p></body></html>"

    mock_driver_instance.get.side_effect = get_side_effect
    type(mock_driver_instance).page_source = property(
        lambda self: page_source_side_effect()
    )

    monkeypatch.setattr(
        "theleague.handlers.nfl_handler.webdriver",
        MagicMock(Chrome=MagicMock(return_value=mock_driver_instance)),
    )

    monkeypatch.setattr("theleague.handlers.nfl_handler.time.sleep", MagicMock())

    yield mock_driver_instance


@pytest.fixture
def collector(mock_selenium_driver_setup):
    """
    Fixture to create an instance of NFLDailyStatsCollector.
    It depends on `mock_selenium_driver_setup` to ensure the Selenium driver
    is already mocked before the collector is initialized.
    """
    obj = NFLDailyStatsCollector(
        start_date="2023-09-10",
        end_date="2023-09-10",
        gcloud_save=False,
        local_save=False,
        caching=False,  # Set to False for tests unless testing cache logic
    )
    obj.str_date = "2023-09-10"
    obj.url = "https://fakeurl.com/sample_game"  # This URL might be used by driver.get
    obj.week = 1
    yield obj


# --- Existing Fixtures (mostly unchanged, ensure they work with new setup) ---


@pytest.fixture
def mock_read_html(monkeypatch, mock_read_local_html):
    """
    Mocks pandas.read_html to read from a StringIO object containing
    the local HTML content, instead of trying to parse a real URL or file.
    """
    original_read_html = pd.read_html

    def _mock_read_html(*args, **kwargs):
        # If the first argument is a string (URL or file path),
        # we assume it's the HTML content directly for mocking purposes.
        # Otherwise, pass through to original if it's a file-like object.
        if isinstance(args[0], str):
            html_io = io.StringIO(mock_read_local_html)
            return original_read_html(html_io, **kwargs)
        return original_read_html(*args, **kwargs)

    monkeypatch.setattr(pd, "read_html", _mock_read_html)
    yield


@pytest.fixture
def mock_requests_get(monkeypatch, mock_read_local_html):
    """
    Mocks the requests.get function to return a FakeResponse
    containing the local HTML content.
    """

    def _mocked_get(*args, **kwargs):
        return FakeResponse(mock_read_local_html)

    # Note: This mock is for `requests.get`. If your class primarily uses
    # Selenium for fetching, this might not be hit. Keep it if there are
    # other parts of your code that use `requests`.
    monkeypatch.setattr("requests.get", _mocked_get)
    yield


def parametrize_local_html(test_func):
    """
    Decorator to parametrize tests with different local HTML files.
    It uses `mock_read_local_html` as an indirect fixture.
    """

    @pytest.mark.parametrize(
        "mock_read_local_html",
        ["tests/data/old_sample_game.html", "tests/data/new_sample_game.html"],
        indirect=True,
        ids=["old_data", "new_data"],
    )
    @wraps(test_func)
    def wrapper(*args, **kwargs):
        return test_func(*args, **kwargs)

    return wrapper


### TESTS!!! ###
# Your existing tests should now work with the mocked Selenium driver
# and time.sleep, as the `collector` fixture sets up the mocked driver.


@pytest.mark.parametrize(
    "mock_read_local_html", ["tests/data/2023_games.html"], indirect=True
)
def test_get_boxscore_urls_for_date(collector):
    # Assuming this method does not directly use self.driver.get,
    # or if it does, it's mocked by the collector fixture.
    urls, weeks = collector._get_boxscore_urls_for_date("2023-09-10")
    assert isinstance(urls, pd.Series)
    assert isinstance(weeks, list)


@parametrize_local_html
def test_fetch_offensive_boxscore(collector, mock_read_html):
    # Assuming _fetch_offensive_boxscore internally calls self.driver.get
    # and then pd.read_html on self.driver.page_source.
    # The driver is mocked by the 'collector' fixture (via mock_selenium_driver_setup)
    # and pd.read_html is mocked by 'mock_read_html'.
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

    # Assert that driver.get was called with the URL
    # Access the mocked driver via the collector instance
    collector.driver.get.assert_called_once_with("fakeurl")
    # Assert that time.sleep was called
    # Access the mocked sleep function via the module where it's used
    from theleague.handlers import (
        nfl_handler,
    )  # Import the module to access its patched sleep

    nfl_handler.time.sleep.assert_called_once_with(6)


@parametrize_local_html
def test_fetch_fg_boxscore(collector, mock_read_html):
    # If _fetch_offensive_boxscore is called internally and then _fetch_fg_boxscore
    # uses the same driver instance, the mocks will persist.
    # If _fetch_fg_boxscore itself initiates a new Selenium call,
    # you'd need to ensure it's also covered by the mocking setup.
    # For this test, let's assume _fetch_offensive_boxscore sets up necessary state.
    collector._fetch_offensive_boxscore(
        url="fakeurl"
    )  # This will trigger driver.get and sleep mocks
    df = collector._fetch_fg_boxscore()
    assert not df.empty
    assert df.kicking_total_made_field_goals_distance.notnull().all()

    required_cols = {
        "player_id",
        "player",
        "kicking_num_field_goals_made",
        "kicking_total_made_field_goals_distance",
        "date",
        "team",
    }
    assert required_cols.issubset(df.columns), (
        f"Missing columns: {required_cols - set(df.columns)}"
    )


@parametrize_local_html
def test_fetch_commented_tables(collector, mock_read_html, mock_requests_get):
    # This test also relies on the driver being mocked.
    # If _fetch_commented_tables makes a new Selenium call, it will use the mocked driver.
    # mock_requests_get is included here in case _fetch_commented_tables has a fallback
    # or secondary path that uses requests.
    collector._fetch_commented_tables(url="fakeurl")

    # Ensure we now have a list of tables and only tables
    assert isinstance(collector.commented_out_tables, list)
    assert all([t.name == "table" for t in collector.commented_out_tables])

    # Assert driver.get was called again if _fetch_commented_tables makes its own call
    # Note: If multiple methods call driver.get, you might need to reset the mock
    # or use assert_any_call, or ensure each test only calls it once.
    # For simplicity, if this is the *second* call in the test, you might need:
    # collector.driver.get.assert_has_calls([call("fakeurl"), call("fakeurl")])
    # Or just check for call count if it's the only one in this specific test.
    # For now, let's assume it's the primary call for this test's purpose.
    # collector.driver.get.assert_called_with("fakeurl") # Use this if it's not the first call in the test session.


# Helper test generator (no changes needed here, as it uses collector and mock_read_html)
def generate_table_test(
    table_id,
    id_col,
    renaming_dict,
    required_keys,
    extra_assertions: list | None = None,
):
    @parametrize_local_html
    def test_func(
        collector,
        mock_read_html,
        mock_requests_get,
        request,  # Removed monkeypatch from args, it's global
    ):
        # Ensure that the driver has fetched the page before trying to get commented tables
        # This might be implicitly handled by the collector's internal logic,
        # or you might need to explicitly call a method that fetches the page.
        # For robustness, let's assume _fetch_commented_tables handles its own page fetch.
        collector._fetch_commented_tables(url="fakeurl")

        # In your original code, you had monkeypatch.setattr(pd, "read_html", READ_HTML) here.
        # This would *unmock* pd.read_html. If you want pd.read_html to remain mocked
        # by your fixture, remove this line. I'm assuming you want it mocked.
        # monkeypatch.setattr(pd, "read_html", READ_HTML) # Removed this line

        html_type = request.node.callspec.id

        collector._fetch_offensive_boxscore("fakeurl")

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
                    f'column "{col}" must be contain no missing data'
                )

            # Ensure unique player_ids
            assert df.player_id.is_unique

        else:
            assert df.empty

        # Go through extra table specific assertions
        if extra_assertions:
            for condition, message in extra_assertions:
                assert condition, message

    return test_func


test_fetch_basic_defense_table = generate_table_test(
    table_id="player_defense",
    id_col="Player",
    renaming_dict=PLAYER_DEFENSE_RENAMING_DICT,
    required_keys=["player", "team"],
)

test_fetch_punt_kick_returns_table = generate_table_test(
    table_id="returns",
    id_col="Player",
    renaming_dict=PUNT_KICK_RETURNS_RENAMING_DICT,
    required_keys=["player", "team"],
)

test_fetch_punt_kick_table = generate_table_test(
    table_id="kicking",
    id_col="Player",
    renaming_dict=PUNT_KICK_RENAMING_DICT,
    required_keys=["player", "team"],
)

test_fetch_passing_advanced_table = generate_table_test(
    table_id="passing_advanced",
    id_col="Player",
    renaming_dict=PASSING_ADVANCED_RENAMING_DICT,
    required_keys=["player", "team"],
)

test_fetch_receiving_advanced_table = generate_table_test(
    table_id="receiving_advanced",
    id_col="Player",
    renaming_dict=RECEIVING_ADVANCED_RENAMING_DICT,
    required_keys=[
        "player",
        "team",
    ],
)

test_fetch_rushing_advanced_table = generate_table_test(
    table_id="rushing_advanced",
    id_col="Player",
    renaming_dict=RUSHING_ADVANCED_RENAMING_DICT,
    required_keys=[
        "player",
        "team",
    ],
)

test_fetch_defense_advanced_table = generate_table_test(
    table_id="defense_advanced",
    id_col="Player",
    renaming_dict=DEFENSE_ADVANCED_RENAMING_DICT,
    required_keys=[
        "player",
        "team",
    ],
)

test_fetch_snap_counts_table = generate_table_test(
    table_id="home_snap_counts",
    id_col="Player",
    renaming_dict=SNAP_COUNT_RENAMING_DICT,
    required_keys=["player", "position"],
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
def test_process_data(
    collector,
    mock_read_html,
    mock_requests_get,
    mock_read_local_html,  # Removed monkeypatch, local_html
):
    # Fetch all relevant boxscores - these calls will now use the mocked Selenium driver
    # and the mocked pd.read_html.
    offensive_df = collector._fetch_offensive_boxscore(url="fakeurl")
    fg_df = collector._fetch_fg_boxscore()

    collector._fetch_commented_tables(url="fakeurl")

    # Mock _save_to_gcloud if it's a method that interacts with external services
    with patch.object(collector, "_save_to_gcloud") as mock_save_to_gcloud:
        mock_save_to_gcloud.return_value = None  # Or whatever is appropriate

        # The line `monkeypatch.setattr(pd, "read_html", READ_HTML)` was here.
        # Removing it ensures pd.read_html remains mocked by the fixture.
        # If you truly need to unmock it for this specific test, you'd need
        # to re-introduce a monkeypatch.setattr here, but it's generally
        # better to keep mocks consistent within a test's scope.

        defense_df = collector._fetch_commented_table(
            table_id="player_defense",
            id_col="Player",
            renaming_dict=PLAYER_DEFENSE_RENAMING_DICT,
        )

        returns_df = collector._fetch_commented_table(
            table_id="returns",
            id_col="Player",
            renaming_dict=PUNT_KICK_RETURNS_RENAMING_DICT,
        )

        kicking_df = collector._fetch_commented_table(
            table_id="kicking",
            id_col="Player",
            renaming_dict=PUNT_KICK_RENAMING_DICT,
        )
        passing_adv_df = collector._fetch_commented_table(
            table_id="passing_advanced",
            id_col="Player",
            renaming_dict=PASSING_ADVANCED_RENAMING_DICT,
        )
        receiving_adv_df = collector._fetch_commented_table(
            table_id="receiving_advanced",
            id_col="Player",
            renaming_dict=RECEIVING_ADVANCED_RENAMING_DICT,
        )
        rushing_adv_df = collector._fetch_commented_table(
            table_id="rushing_advanced",
            id_col="Player",
            renaming_dict=RUSHING_ADVANCED_RENAMING_DICT,
        )
        defense_adv_df = collector._fetch_commented_table(
            table_id="defense_advanced",
            id_col="Player",
            renaming_dict=DEFENSE_ADVANCED_RENAMING_DICT,
        )
        home_snap_counts_df = collector._fetch_commented_table(
            table_id="home_snap_counts",
            id_col="Player",
            renaming_dict=SNAP_COUNT_RENAMING_DICT,
        )
        home_snap_counts_df["team"] = collector.home_team
        home_snap_counts_df["date"] = collector.str_date
        home_snap_counts_df["week"] = collector.week
        away_snap_counts_df = collector._fetch_commented_table(
            table_id="vis_snap_counts",
            id_col="Player",
            renaming_dict=SNAP_COUNT_RENAMING_DICT,
        )
        away_snap_counts_df["team"] = collector.away_team
        away_snap_counts_df["date"] = collector.str_date
        away_snap_counts_df["week"] = collector.week
        snap_counts_df = [home_snap_counts_df, away_snap_counts_df]

        # Run full processing function
        result = collector._process_and_upload_data(
            offensive_dfs=[offensive_df],
            fg_dfs=[fg_df],
            defense_dfs=[defense_df],
            punt_kick_return_dfs=[returns_df],
            punt_kick_dfs=[kicking_df],
            passing_adv_dfs=[passing_adv_df],
            receiving_adv_dfs=[receiving_adv_df],
            rushing_adv_dfs=[rushing_adv_df],
            defense_adv_dfs=[defense_adv_df],
            snap_count_dfs=snap_counts_df,
            current_date=pd.to_datetime("2023-09-10"),
            is_cache=False,
        )

        # Basic output checks
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "player" in result.columns
        assert "team" in result.columns
        assert "season" in result.columns
