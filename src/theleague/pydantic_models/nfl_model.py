from pydantic import BaseModel, Field
from typing import Optional
import datetime


class NFLBoxscore(BaseModel):
    """
    Pydantic model for NFL player statistics for a single game.
    Each field represents a specific statistic or player attribute.
    All fields are optional as not every stat will apply to every player in every game.
    """

    player: Optional[str] = Field(None, description="Name of the player.")
    player_id: Optional[int] = Field(
        None, description="Unique identifier for the player."
    )
    position: Optional[str] = Field(
        None, description="Player's primary position (e.g., 'QB', 'RB', 'WR', 'DB')."
    )
    team: Optional[str] = Field(None, description="The player's team for the game.")
    date: Optional[datetime.date] = Field(None, description="Date of the game.")
    week: Optional[int] = Field(None, description="Week number of the season.")
    season: Optional[int] = Field(None, description="Year of the season.")
    home_away: Optional[str] = Field(
        None, description="Indicates if the game was 'home' or 'away'."
    )
    home_team: Optional[str] = Field(None, description="Name of the home team.")
    away_team: Optional[str] = Field(None, description="Name of the away team.")

    # Passing Statistics
    passing_completions: Optional[int] = Field(
        None, description="Number of completed passes."
    )
    passing_attempts: Optional[int] = Field(
        None, description="Number of passing attempts."
    )
    passing_yards: Optional[float] = Field(None, description="Total passing yards.")
    passing_touchdowns: Optional[int] = Field(
        None, description="Number of passing touchdowns."
    )
    passing_interceptions: Optional[int] = Field(
        None, description="Number of interceptions thrown."
    )
    passing_sacks: Optional[int] = Field(None, description="Number of times sacked.")
    passing_sacked_yards: Optional[float] = Field(
        None, description="Yards lost from sacks."
    )
    passing_longest_pass: Optional[float] = Field(
        None, description="Longest completed pass in yards."
    )
    passing_passer_rating: Optional[float] = Field(None, description="Passer rating.")
    passing_first_downs_thrown: Optional[int] = Field(
        None, description="Number of passing first downs."
    )
    passing_first_down_pct: Optional[float] = Field(
        None, description="Percentage of passing first downs."
    )
    passing_intended_air_yards: Optional[float] = Field(
        None, description="Total intended air yards."
    )
    passing_intended_air_yards_per_att: Optional[float] = Field(
        None, description="Intended air yards per attempt."
    )
    passing_completed_air_yards: Optional[float] = Field(
        None, description="Total completed air yards."
    )
    passing_completed_air_yards_per_cmp: Optional[float] = Field(
        None, description="Completed air yards per completion."
    )
    passing_completed_air_yards_per_att: Optional[float] = Field(
        None, description="Completed air yards per attempt."
    )
    passing_yards_after_catch: Optional[float] = Field(
        None, description="Yards after catch from passes."
    )
    passing_yards_after_catch_per_cmp: Optional[float] = Field(
        None, description="Yards after catch per completion."
    )
    passing_drops: Optional[int] = Field(None, description="Number of dropped passes.")
    passing_drop_pct: Optional[float] = Field(
        None, description="Percentage of dropped passes."
    )
    passing_bad_throws: Optional[int] = Field(None, description="Number of bad throws.")
    passing_bad_throw_pct: Optional[float] = Field(
        None, description="Percentage of bad throws."
    )
    passing_sacks_taken: Optional[int] = Field(
        None, description="Number of sacks taken."
    )
    passing_blitzes_taken: Optional[int] = Field(
        None, description="Number of blitzes faced."
    )
    passing_hurries_taken: Optional[int] = Field(
        None, description="Number of hurries faced."
    )
    passing_qb_hits_taken: Optional[int] = Field(
        None, description="Number of QB hits taken."
    )
    passing_pressures_taken: Optional[int] = Field(
        None, description="Total pressures faced."
    )
    passing_pressure_pct_taken: Optional[float] = Field(
        None, description="Percentage of plays under pressure."
    )
    passing_scrambles: Optional[int] = Field(None, description="Number of scrambles.")
    passing_yards_per_scramble: Optional[float] = Field(
        None, description="Yards per scramble."
    )

    # Rushing Statistics
    rushing_attempts: Optional[int] = Field(
        None, description="Number of rushing attempts."
    )
    rushing_yards: Optional[float] = Field(None, description="Total rushing yards.")
    rushing_touchdowns: Optional[int] = Field(
        None, description="Number of rushing touchdowns."
    )
    rushing_longest_rush: Optional[float] = Field(
        None, description="Longest rush in yards."
    )
    rushing_first_downs: Optional[int] = Field(
        None, description="Number of rushing first downs."
    )
    rushing_yards_before_contact: Optional[float] = Field(
        None, description="Rushing yards before contact."
    )
    rushing_yards_before_contact_per_attempt: Optional[float] = Field(
        None, description="Rushing yards before contact per attempt."
    )
    rushing_yards_after_contact: Optional[float] = Field(
        None, description="Rushing yards after contact."
    )
    rushing_yards_after_contact_per_attempt: Optional[float] = Field(
        None, description="Rushing yards after contact per attempt."
    )
    rushing_broken_tackles: Optional[int] = Field(
        None, description="Number of broken tackles on rushes."
    )
    rushing_attempts_per_broken_tackle: Optional[float] = Field(
        None, description="Rushing attempts per broken tackle."
    )

    # Receiving Statistics
    receiving_targets: Optional[int] = Field(
        None, description="Number of times targeted for a pass."
    )
    receiving_receptions: Optional[int] = Field(
        None, description="Number of receptions."
    )
    receiving_yards: Optional[float] = Field(None, description="Total receiving yards.")
    receiving_touchdowns: Optional[int] = Field(
        None, description="Number of receiving touchdowns."
    )
    receiving_longest_reception: Optional[float] = Field(
        None, description="Longest reception in yards."
    )
    receiving_first_downs: Optional[int] = Field(
        None, description="Number of receiving first downs."
    )
    receiving_yards_before_catch: Optional[float] = Field(
        None, description="Receiving yards before catch."
    )
    receiving_yards_before_catch_per_reception: Optional[float] = Field(
        None, description="Receiving yards before catch per reception."
    )
    receiving_yards_after_catch: Optional[float] = Field(
        None, description="Receiving yards after catch."
    )
    receiving_yards_after_catch_per_reception: Optional[float] = Field(
        None, description="Receiving yards after catch per reception."
    )
    receiving_average_depth_of_target: Optional[float] = Field(
        None, description="Average depth of target for passes."
    )
    receiving_broken_tackles: Optional[int] = Field(
        None, description="Number of broken tackles after reception."
    )
    receiving_receptions_per_broken_tackle: Optional[float] = Field(
        None, description="Receptions per broken tackle."
    )
    receiving_drops: Optional[int] = Field(
        None, description="Number of dropped receptions."
    )
    receiving_drop_percentage: Optional[float] = Field(
        None, description="Percentage of dropped receptions."
    )
    receiving_interceptions: Optional[int] = Field(
        None, description="Number of interceptions thrown when targeted."
    )
    receiving_passer_rating: Optional[float] = Field(
        None, description="Passer rating when targeted."
    )

    # Offensive Fumbles
    offensive_fumbles: Optional[int] = Field(
        None, description="Number of offensive fumbles."
    )
    offensive_fumbles_lost: Optional[int] = Field(
        None, description="Number of offensive fumbles lost."
    )

    # Kicking Statistics
    kicking_num_field_goals_made: Optional[int] = Field(
        None, description="Number of field goals made."
    )
    kicking_total_made_field_goals_distance: Optional[float] = Field(
        None, description="Total distance of made field goals."
    )
    kicking_field_goals_made_average_distance: Optional[float] = Field(
        None, description="Average distance of made field goals."
    )
    kicking_extra_points_made: Optional[int] = Field(
        None, description="Number of extra points made."
    )
    kicking_extra_points_attempted: Optional[int] = Field(
        None, description="Number of extra points attempted."
    )
    kicking_field_goals_made: Optional[int] = Field(
        None, description="Number of field goals made."
    )
    kicking_field_goals_attempted: Optional[int] = Field(
        None, description="Number of field goals attempted."
    )

    # Defensive Statistics
    defensive_interceptions: Optional[int] = Field(
        None, description="Number of defensive interceptions."
    )
    defensive_interception_return_yards: Optional[float] = Field(
        None, description="Yards from interception returns."
    )
    defensive_interception_touchdowns: Optional[int] = Field(
        None, description="Number of interception return touchdowns."
    )
    defensive_longest_interception_return: Optional[float] = Field(
        None, description="Longest interception return in yards."
    )
    defensive_passes_defended: Optional[int] = Field(
        None, description="Number of passes defended."
    )
    defensive_sacks: Optional[int] = Field(
        None, description="Number of defensive sacks."
    )
    defensive_total_tackles: Optional[int] = Field(
        None, description="Total number of tackles."
    )
    defensive_solo_tackles: Optional[int] = Field(
        None, description="Number of solo tackles."
    )
    defensive_assisted_tackles: Optional[int] = Field(
        None, description="Number of assisted tackles."
    )
    defensive_tackles_for_loss: Optional[int] = Field(
        None, description="Number of tackles for loss."
    )
    defensive_qb_hits: Optional[int] = Field(None, description="Number of QB hits.")
    defensive_fumble_recoveries: Optional[int] = Field(
        None, description="Number of fumble recoveries."
    )
    defensive_fumble_return_yards: Optional[float] = Field(
        None, description="Yards from fumble returns."
    )
    defensive_fumble_touchdowns: Optional[int] = Field(
        None, description="Number of fumble return touchdowns."
    )
    defensive_forced_fumbles: Optional[int] = Field(
        None, description="Number of forced fumbles."
    )
    defensive_targets: Optional[int] = Field(
        None, description="Number of times targeted in coverage."
    )
    defensive_completions_allowed: Optional[int] = Field(
        None, description="Number of completions allowed in coverage."
    )
    defensive_completion_percentage: Optional[float] = Field(
        None, description="Completion percentage allowed in coverage."
    )
    defensive_yards_per_completion: Optional[float] = Field(
        None, description="Yards allowed per completion in coverage."
    )
    defensive_yards_per_target: Optional[float] = Field(
        None, description="Yards allowed per target in coverage."
    )
    defensive_passer_rating: Optional[float] = Field(
        None, description="Passer rating allowed in coverage."
    )
    defensive_average_depth_of_target: Optional[float] = Field(
        None, description="Average depth of target allowed in coverage."
    )
    defensive_air_yards_allowed: Optional[float] = Field(
        None, description="Air yards allowed in coverage."
    )
    defensive_yards_after_catch_allowed: Optional[float] = Field(
        None, description="Yards after catch allowed in coverage."
    )
    defensive_blitzes: Optional[int] = Field(None, description="Number of blitzes.")
    defensive_hurries: Optional[int] = Field(None, description="Number of hurries.")
    defensive_pressures: Optional[int] = Field(None, description="Total pressures.")
    defensive_combined_tackles: Optional[int] = Field(
        None, description="Number of combined tackles."
    )
    defensive_missed_tackles: Optional[int] = Field(
        None, description="Number of missed tackles."
    )
    defensive_missed_tackle_percentage: Optional[float] = Field(
        None, description="Percentage of missed tackles."
    )

    # Kick Return Statistics
    kick_return_returns: Optional[int] = Field(
        None, description="Number of kick returns."
    )
    kick_return_yards: Optional[float] = Field(
        None, description="Total kick return yards."
    )
    kick_return_yards_per_return: Optional[float] = Field(
        None, description="Average yards per kick return."
    )
    kick_return_touchdowns: Optional[int] = Field(
        None, description="Number of kick return touchdowns."
    )
    kick_return_longest_return: Optional[float] = Field(
        None, description="Longest kick return in yards."
    )

    # Punt Return Statistics
    punt_return_returns: Optional[int] = Field(
        None, description="Number of punt returns."
    )
    punt_return_yards: Optional[float] = Field(
        None, description="Total punt return yards."
    )
    punt_return_yards_per_return: Optional[float] = Field(
        None, description="Average yards per punt return."
    )
    punt_return_touchdowns: Optional[int] = Field(
        None, description="Number of punt return touchdowns."
    )
    punt_return_longest_return: Optional[float] = Field(
        None, description="Longest punt return in yards."
    )

    # Punting Statistics
    punting_num_punts: Optional[int] = Field(None, description="Number of punts.")
    punting_punt_yards: Optional[float] = Field(
        None, description="Total punting yards."
    )
    punting_yards_per_punt: Optional[float] = Field(
        None, description="Average yards per punt."
    )
    punting_longest_punt: Optional[float] = Field(
        None, description="Longest punt in yards."
    )

    # Snap Counts
    offensive_snaps: Optional[int] = Field(
        None, description="Number of offensive snaps played."
    )
    offensive_snaps_percentage: Optional[float] = Field(
        None, description="Percentage of offensive snaps played."
    )
    defensive_snaps: Optional[int] = Field(
        None, description="Number of defensive snaps played."
    )
    defensive_snaps_percentage: Optional[float] = Field(
        None, description="Percentage of defensive snaps played."
    )
    special_teams_snaps: Optional[int] = Field(
        None, description="Number of special teams snaps played."
    )
    special_teams_snaps_percentage: Optional[float] = Field(
        None, description="Percentage of special teams snaps played."
    )

    # Source URL
    source_url: Optional[str] = Field(None, description="URL of the data source.")
