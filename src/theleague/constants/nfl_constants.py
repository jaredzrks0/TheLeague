OFFENSIVE_COLUMNS_LIST = [
    "player",
    "Tm",
    "Cmp",
    "Att",
    "Yds",
    "TD",
    "Int",
    "Sk",
    "Yds.1",
    "Lng",
    "Rate",
    "Att.1",
    "Yds.2",
    "TD.1",
    "Lng.1",
    "Tgt",
    "Rec",
    "Yds.3",
    "TD.2",
    "Lng.2",
    "Fmb",
    "FL",
    "player_id",
]

OFFENSIVE_RENAMING_DICT = {
    "player": "player",
    "Tm": "team",
    "Cmp": "passing_completions",
    "Att": "passing_attempts",
    "Yds": "passing_yards",
    "TD": "passing_touchdowns",
    "Int": "passing_interceptions",
    "Sk": "passing_sacks",
    "Yds.1": "passing_sacked_yards",
    "Lng": "passing_longest_pass",
    "Rate": "passing_passer_rating",
    "Att.1": "rushing_attempts",
    "Yds.2": "rushing_yards",
    "TD.1": "rushing_touchdowns",
    "Lng.1": "rushing_longest_rush",
    "Tgt": "receiving_targets",
    "Rec": "receiving_receptions",
    "Yds.3": "receiving_yards",
    "TD.2": "receiving_touchdowns",
    "Lng.2": "receiving_longest_reception",
    "Fmb": "offensive_fumbles",
    "FL": "offensive_fumbles_lost",
    "player_id": "player_id",
}

FG_RENAMING_DICT = {
    "Tm": "team",
    "kicker": "player",
}


PLAYER_DEFENSE_RENAMING_DICT = {
    "Player": "player",
    "Tm": "team",
    "Int": "defensive_interceptions",
    "Yds": "defensive_interception_return_yards",
    "TD": "defensive_interception_touchdowns",
    "Lng": "defensive_longest_interception_return",
    "PD": "defensive_passes_defended",
    "Sk": "defensive_sacks",
    "Comb": "defensive_total_tackles",
    "TFL": "defensive_tackles_for_loss",
    "QBHits": "defensive_qb_hits",
    "FR": "defensive_fumble_recoveries",
    "Yds.1": "defensive_fumble_return_yards",
    "TD.1": "defensive_fumble_touchdowns",
    "FF": "defensive_forced_fumbles",
    "Solo": "defensive_solo_tackles",
    "Ast": "defensive_assisted_tackles",
}

PUNT_KICK_RETURNS_RENAMING_DICT = {
    "Player": "player",
    "Tm": "team",
    "Rt": "kick_return_returns",
    "Ret": "punt_return_returns",
    "Y/Rt": "kick_return_yards_per_return",
    "Yds": "kick_return_yards",
    "Y/R": "punt_return_yards_per_return",
    "Yds.1": "punt_return_yards",
    "TD": "kick_return_touchdowns",
    "Lng": "kick_return_longest_return",
    "Lng.1": "punt_return_longest_return",
    "TD.1": "punt_return_touchdowns",
}

PUNT_KICK_RENAMING_DICT = {
    "Player": "player",
    "Tm": "team",
    "XPM": "kicking_extra_points_made",
    "XPA": "kicking_extra_points_attempted",
    "FGM": "kicking_field_goals_made",
    "FGA": "kicking_field_goals_attempted",
    "Pnt": "punting_num_punts",
    "Yds": "punting_punt_yards",
    "Y/P": "punting_yards_per_punt",
    "Lng": "punting_longest_punt",
}

PASSING_ADVANCED_RENAMING_DICT = {
    "Player": "player",
    "Tm": "team",
    "1D": "passing_first_downs_thrown",
    "1D%": "passing_first_down_pct",
    "IAY": "passing_intended_air_yards",
    "IAY/PA": "passing_intended_air_yards_per_att",
    "CAY": "passing_completed_air_yards",
    "CAY/Cmp": "passing_completed_air_yards_per_cmp",
    "CAY/PA": "passing_completed_air_yards_per_att",
    "YAC": "passing_yards_after_catch",
    "YAC/Cmp": "passing_yards_after_catch_per_cmp",
    "Drops": "passing_drops",
    "Drop%": "passing_drop_pct",
    "BadTh": "passing_bad_throws",
    "Bad%": "passing_bad_throw_pct",
    "Sk": "passing_sacks_taken",
    "Bltz": "passing_blitzes_taken",
    "Hrry": "passing_hurries_taken",
    "Hits": "passing_qb_hits_taken",
    "Prss": "passing_pressures_taken",
    "Prss%": "passing_pressure_pct_taken",
    "Scrm": "passing_scrambles",
    "Yds/Scr": "passing_yards_per_scramble",
}

RECEIVING_ADVANCED_RENAMING_DICT = {
    "Player": "player",
    "Tm": "team",
    "1D": "receiving_first_downs",
    "YBC": "receiving_yards_before_catch",
    "YBC/R": "receiving_yards_before_catch_per_reception",
    "YAC": "receiving_yards_after_catch",
    "YAC/R": "receiving_yards_after_catch_per_reception",
    "ADOT": "receiving_average_depth_of_target",
    "BrkTkl": "receiving_broken_tackles",
    "Rec/Br": "receiving_receptions_per_broken_tackle",
    "Drop": "receiving_drops",
    "Drop%": "receiving_drop_percentage",
    "Int": "receiving_interceptions",
    "Rat": "receiving_passer_rating",
}

RUSHING_ADVANCED_RENAMING_DICT = {
    "Player": "player",
    "Tm": "team",
    "1D": "rushing_first_downs",
    "YBC": "rushing_yards_before_contact",
    "YBC/Att": "rushing_yards_before_contact_per_attempt",
    "YAC": "rushing_yards_after_contact",
    "YAC/Att": "rushing_yards_after_contact_per_attempt",
    "BrkTkl": "rushing_broken_tackles",
    "Att/Br": "rushing_attempts_per_broken_tackle",
}

DEFENSE_ADVANCED_RENAMING_DICT = {
    "Player": "player",
    "Tm": "team",
    "Tgt": "defensive_targets",
    "Cmp": "defensive_completions_allowed",
    "Cmp%": "defensive_completion_percentage",
    "Yds/Cmp": "defensive_yards_per_completion",
    "Yds/Tgt": "defensive_yards_per_target",
    "Rat": "defensive_passer_rating",
    "DADOT": "defensive_average_depth_of_target",
    "Air": "defensive_air_yards_allowed",
    "YAC": "defensive_yards_after_catch_allowed",
    "Bltz": "defensive_blitzes",
    "Hrry": "defensive_hurries",
    "QBKD": "defensive_qb_hits",
    "Prss": "defensive_pressures",
    "Comb": "defensive_combined_tackles",
    "MTkl": "defensive_missed_tackles",
    "MTkl%": "defensive_missed_tackle_percentage",
}

SNAP_COUNT_RENAMING_DICT = {
    "Player": "player",
    "Pos": "position",
    "Num": "offensive_snaps",
    "Pct": "offensive_snaps_percentage",
    "Num.1": "defensive_snaps",
    "Pct.1": "defensive_snaps_percentage",
    "Num.2": "special_teams_snaps",
    "Pct.2": "special_teams_snaps_percentage",
}
