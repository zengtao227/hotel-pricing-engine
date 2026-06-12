from __future__ import annotations

import pandas as pd

_FORMULA_PREFIXES = frozenset("=+-@\t\r")


def sanitize_excel_df(df: pd.DataFrame) -> pd.DataFrame:
    """Prefix dangerous leading characters to prevent Excel formula injection.

    Strings starting with = + - @ are treated as formulas by Excel when opened.
    A leading apostrophe tells Excel to treat the cell as plain text and is not
    displayed, so VLOOKUP lookups on the sanitised value still work correctly.
    """
    out = df.copy()
    for col in out.select_dtypes(include=["object", "string"]).columns:
        out[col] = out[col].map(
            lambda v: ("'" + v) if isinstance(v, str) and v and v[0] in _FORMULA_PREFIXES else v
        )
    return out
