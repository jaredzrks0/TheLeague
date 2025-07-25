import pandas as pd
import numpy as np
from pydantic import BaseModel


def pydantic_convert_and_validate(df: pd.DataFrame, model: BaseModel) -> pd.DataFrame:
    """
    Cleans a Boxscore DataFrame by converting to a
    given pydantic model, validating, and converting back.
    """

    # Convert and validate
    model_entries = [model.model_validate(row) for row in df.to_dict(orient="records")]

    # Re-convert back to polars
    clean_df = pd.DataFrame([entry.model_dump() for entry in model_entries])

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
