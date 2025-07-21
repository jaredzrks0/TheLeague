import pandas as pd
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
