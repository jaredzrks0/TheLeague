from __future__ import annotations
from typing import List, Any
from pydantic import BaseModel

LEAGUE_STAT_NAMES = ["sportID", "leagueID", "name", "shortName"]
LEAGUE_STAT_NAMES_MAP = {
    "sportID": "sport_id",
    "leagueID": "league_id",
    "name": "league_name",
    "shortName": "league_short_name",
}


class League(BaseModel):
    sportID: str
    leagueID: str
    enabled: bool
    name: str
    shortName: str


class LeagueResponse(BaseModel):
    success: bool
    data: List[League]

    def _collect_league_stat(self, stat_name):
        return [getattr(league, stat_name) for league in self.data]

    def to_leagues_dict(self):
        leagues_dict: dict[str, Any] = {
            LEAGUE_STAT_NAMES_MAP[stat_name]: self._collect_league_stat(stat_name)
            for stat_name in LEAGUE_STAT_NAMES
        }

        return leagues_dict
