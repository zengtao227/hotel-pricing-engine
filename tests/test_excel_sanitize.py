"""Tests for excel_sanitize.py."""
from __future__ import annotations

import pandas as pd
import pytest

from src.excel_sanitize import sanitize_excel_df


def test_formula_prefix_neutralised():
    df = pd.DataFrame({"a": ["=SUM(A1:A2)", "+1", "-1", "@user", "normal"]})
    out = sanitize_excel_df(df)
    assert out["a"].iloc[0] == "'=SUM(A1:A2)"
    assert out["a"].iloc[1] == "'+1"
    assert out["a"].iloc[2] == "'-1"
    assert out["a"].iloc[3] == "'@user"
    assert out["a"].iloc[4] == "normal"


def test_normal_strings_unchanged():
    df = pd.DataFrame({"room": ["Standard Double", "Superior Room", "Family Suite"]})
    out = sanitize_excel_df(df)
    assert list(out["room"]) == list(df["room"])


def test_numeric_columns_unchanged():
    df = pd.DataFrame({"price": [100.0, 200.0, 300.0], "count": [1, 2, 3]})
    out = sanitize_excel_df(df)
    assert list(out["price"]) == [100.0, 200.0, 300.0]


def test_none_and_nan_pass_through():
    df = pd.DataFrame({"a": [None, float("nan"), "=bad"]})
    out = sanitize_excel_df(df)
    assert out["a"].iloc[2] == "'=bad"


def test_tab_and_carriage_return_prefixes():
    df = pd.DataFrame({"a": ["\t=inject", "\r=inject"]})
    out = sanitize_excel_df(df)
    assert out["a"].iloc[0].startswith("'")
    assert out["a"].iloc[1].startswith("'")


def test_empty_string_unchanged():
    df = pd.DataFrame({"a": [""]})
    out = sanitize_excel_df(df)
    assert out["a"].iloc[0] == ""


def test_returns_copy_not_inplace():
    df = pd.DataFrame({"a": ["=formula"]})
    out = sanitize_excel_df(df)
    assert df["a"].iloc[0] == "=formula"
    assert out["a"].iloc[0] == "'=formula"
