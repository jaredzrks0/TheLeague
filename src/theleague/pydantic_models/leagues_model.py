from __future__ import annotations
from typing import List
from pydantic import BaseModel


class League(BaseModel):
    sportID: str
    leagueID: str
    enabled: bool
    name: str
    shortName: str


class LeagueResponse(BaseModel):
    success: bool
    data: List[League]
