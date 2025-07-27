import pydantic
import polars as pl

from pydantic import BaseModel


class LeaguesDataFrame(BaseModel):
    sport_id: str
    league_id: str
    league_name: str
    league_short_name: str
