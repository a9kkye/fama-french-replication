"""
Data layer for the Fama-French three-factor replication.

The project runs in two modes:

* ``download=False`` (default) reads the bundled monthly CSVs in ``data/``.
  Those files are *real* Ken French data, built from his daily research files
  (vintage: see ``data/README.md``). This lets the whole repo run offline.

* ``download=True`` fetches the **current** official files straight from the
  Ken French Data Library, parses them, and overwrites the cache. Run it once
  to extend every table and chart to the present day -- including the
  post-2022 "value comeback" period that the offline cache does not yet cover.

Public API
----------
    load_factors(download=False)     -> monthly Mkt-RF, SMB, HML, RF (decimals)
    load_portfolios(download=False)  -> monthly 25 Size x B/M VW returns
    load_all(download=False)         -> (factors, portfolios) aligned on dates
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FACTORS_CSV = DATA_DIR / "ff_factors_monthly.csv"
PORTFOLIOS_CSV = DATA_DIR / "portfolios_25_monthly.csv"

_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"
FACTORS_URL = f"{_BASE}/F-F_Research_Data_Factors_CSV.zip"
PORTFOLIOS_URL = f"{_BASE}/25_Portfolios_5x5_CSV.zip"

_USER_AGENT = "Mozilla/5.0 (fama-french-replication; research/educational use)"


# --------------------------------------------------------------------------- #
# Public loaders
# --------------------------------------------------------------------------- #
def load_factors(download: bool = False) -> pd.DataFrame:
    """Monthly Fama-French factors as decimals, indexed by month-end date.

    Columns: ``Mkt-RF``, ``SMB``, ``HML``, ``RF``.
    """
    if download:
        df = _download_factors()
        df.round(6).to_csv(FACTORS_CSV, index_label="date")
        return df
    return _read_cache(FACTORS_CSV)


def load_portfolios(download: bool = False) -> pd.DataFrame:
    """Monthly value-weighted returns of the 25 Size x B/M portfolios (decimals)."""
    if download:
        df = _download_portfolios()
        df.round(6).to_csv(PORTFOLIOS_CSV, index_label="date")
        return df
    return _read_cache(PORTFOLIOS_CSV)


def load_all(download: bool = False):
    """Return ``(factors, portfolios)`` aligned on their common monthly index."""
    f = load_factors(download=download)
    p = load_portfolios(download=download)
    idx = f.index.intersection(p.index)
    return f.loc[idx], p.loc[idx]


# --------------------------------------------------------------------------- #
# Cache I/O
# --------------------------------------------------------------------------- #
def _read_cache(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{path.name} not found. Run with download=True to fetch it live "
            f"from the Ken French Data Library."
        )
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    df.index = df.index.to_period("M").to_timestamp("M")
    return df


# --------------------------------------------------------------------------- #
# Live download + parsing of the official French format
# --------------------------------------------------------------------------- #
def _fetch_zip_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(req, timeout=60) as resp:
        blob = resp.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        name = zf.namelist()[0]
        return zf.read(name).decode("latin-1")


def _to_month_end(yyyymm: pd.Index) -> pd.DatetimeIndex:
    return pd.to_datetime(yyyymm.astype(str), format="%Y%m").to_period("M").to_timestamp("M")


def _download_factors() -> pd.DataFrame:
    """Parse the official 'Fama/French 3 Factors' monthly CSV (already monthly)."""
    text = _fetch_zip_text(FACTORS_URL)
    rows = []
    for line in text.splitlines():
        # Monthly rows look like:  "192607,    2.96,   -2.30,   -2.87,    0.22"
        if re.match(r"^\s*\d{6}\s*,", line):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                rows.append(parts[:5])
        elif rows and re.match(r"^\s*\d{4}\s*,", line):
            # First 4-digit row marks the start of the annual section -> stop.
            break
    df = pd.DataFrame(rows, columns=["date", "Mkt-RF", "SMB", "HML", "RF"])
    df["date"] = _to_month_end(df["date"])
    df = df.set_index("date").astype(float) / 100.0
    return df


def _download_portfolios() -> pd.DataFrame:
    """Parse the first (value-weighted, monthly) block of the 25-portfolio file."""
    text = _fetch_zip_text(PORTFOLIOS_URL).splitlines()
    header, block, names = None, [], None
    for line in text:
        if re.match(r"^\s*,?\s*SMALL\s+LoBM", line):      # column-name row
            names = [c.strip() for c in line.split(",")][-25:]
            block = []                                     # start of a section
        elif re.match(r"^\s*\d{6}\s*,", line):
            parts = [p.strip() for p in line.split(",")]
            block.append(parts[:26])
        elif names is not None and block and not re.match(r"^\s*\d{6}", line):
            break                                          # end of first block
    df = pd.DataFrame(block, columns=["date"] + names)
    df["date"] = _to_month_end(df["date"])
    df = df.set_index("date").apply(pd.to_numeric, errors="coerce") / 100.0
    return df.replace(-0.9999, np.nan).dropna(how="all")


if __name__ == "__main__":
    f, p = load_all(download=False)
    print(f"factors:    {f.index.min():%Y-%m} -> {f.index.max():%Y-%m}  ({len(f)} months)")
    print(f"portfolios: {p.shape[1]} columns, {len(p)} months")
    print((f.mean() * 100).round(3).to_string())
