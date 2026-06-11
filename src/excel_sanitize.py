from __future__ import annotations

import pandas as pd

_FORMULA_PREFIXES = frozenset("=+-@\t\r")


def sanitize_excel_df(df: pd.DataFrame) -> pd.DataFrame:
    """Prefix dangerous leading characters to prevent Excel formula injection.

    Strings starting with = + - @ are treated as formulas by Excel when opened.
    Prepending a space neutralises the formula trigger without altering the visible value
    in any meaningful way for hospitality data (hotel names, room types, comments).
    """
    out = df.copy()
    for col in out.select_dtypes(include="object").columns:
        out[col] = out[col].map(
            lambda v: (" " + v) if isinstance(v, str) and v and v[0] in _FORMULA_PREFIXES else v
        )
    return out
