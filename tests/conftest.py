# -*- coding: utf-8 -*-
"""pytest 公共配置：把项目根加进 sys.path，提供固定回测数据 fixture。"""
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "market_data")


def _load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(FIXTURES_DIR, name)
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df


@pytest.fixture(scope="session")
def aapl_fixture() -> pd.DataFrame:
    return _load_csv("AAPL_1d.csv")


@pytest.fixture(scope="session")
def msft_fixture() -> pd.DataFrame:
    return _load_csv("MSFT_1d.csv")


@pytest.fixture(scope="session")
def volatile_fixture() -> pd.DataFrame:
    return _load_csv("volatile_market.csv")
