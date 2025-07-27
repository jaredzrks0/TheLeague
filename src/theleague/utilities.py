import polars as pl
import pandas as pd
import numpy as np
import datetime
from datetime import datetime as dt
from pydantic import BaseModel
from typing import Type


########## SEASON CALCULATIONS ##########
def calculate_nfl_season(date: str | dt) -> int:
    if type(date) is str:
        date = dt.strptime(date, "%Y-%m-%d")

    if date.month < 8:
        return date.year - 1
    else:
        return date


########## DATA ENFORCEMENT ##########
def pydantic_convert_and_validate(
    df: pl.DataFrame, model: Type[BaseModel]
) -> pl.DataFrame:
    """
    Cleans a Polars DataFrame by converting to a
    given Pydantic model, validating, and converting back.
    """
    # Convert rows to dicts and validate
    model_entries = [model.model_validate(row) for row in df.to_dicts()]

    # Dump the validated models back to dicts and create a clean DataFrame
    clean_df = pl.DataFrame([entry.model_dump() for entry in model_entries])

    return clean_df


def enforce_schema(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """Enforces a specific schema. To be used for schema normalization before upload."""
    for col, dtype in schema.items():
        if col not in df.columns:
            # Fill with all nulls of the correct type
            if dtype.startswith("Int"):
                df[col] = pd.Series([pd.NA] * len(df), dtype=dtype)
            elif dtype.startswith("float"):
                df[col] = pd.Series([np.nan] * len(df), dtype=dtype)
            else:  # string or object
                df[col] = pd.Series([pd.NA] * len(df), dtype=dtype)
        else:
            df[col] = df[col].astype(dtype)
    return df[list(schema.keys())]  # enforce column order
