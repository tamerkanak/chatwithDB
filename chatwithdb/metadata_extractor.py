import pandas as pd
import os
from typing import List, Dict, Tuple

def get_column_type(dtype) -> str:
    if pd.api.types.is_numeric_dtype(dtype):
        return "numeric"
    elif pd.api.types.is_string_dtype(dtype):
        return "string"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "datetime"
    elif pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    else:
        return "unknown"

def extract_metadata_from_file(filepath: str) -> Dict:
    """
    Reads the file and returns metadata text and table information.
    """
    ext = os.path.splitext(filepath)[-1].lower()
    if ext == ".csv":
        df = pd.read_csv(filepath, nrows=100)
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(filepath, nrows=100)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    table_name = os.path.splitext(os.path.basename(filepath))[0]
    columns = list(df.columns)
    column_types = [get_column_type(df[col]) for col in columns]
    metadata_text = f"Table: {table_name}\nColumns:\n" + "\n".join([
        f"- {col}: {typ}" for col, typ in zip(columns, column_types)
    ])
    return {
        "table_name": table_name,
        "columns": columns,
        "column_types": column_types,
        "metadata_text": metadata_text,
        "source_file": os.path.basename(filepath)
    } 