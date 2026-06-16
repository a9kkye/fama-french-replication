"""
Estimation tools for the Fama-French replication and extension.

Everything here takes *decimal* monthly returns (e.g. 0.012 == 1.2%) and uses
heteroskedasticity- and autocorrelation-consistent (Newey-West) standard errors
for factor-premium t-stats, which is standard practice in asset pricing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

FACTORS3 = ["Mkt-RF", "SMB", "HML"]


# --------------------------------------------------------------------------- #
# Core regressions
# --------------------------------------------------------------------------- #
def _excess(port: pd.Series, factors: pd.DataFrame) -> pd.DataFrame:
    """Align a portfolio with the factors and return excess returns + regressors."""
    data = factors.join(port.rename("port"), how="inner").dropna()
    data["excess"] = data["port"] - data["RF"]
    return data


def run_capm(port: pd.Series, factors: pd.DataFrame):
    d = _excess(port, factors)
    X = sm.add_constant(d[["Mkt-RF"]])
    return sm.OLS(d["excess"], X).fit()


def run_ff3(port: pd.Series, factors: pd.DataFrame):
    d = _excess(port, factors)
    X = sm.add_constant(d[FACTORS3])
    return sm.OLS(d["excess"], X).fit()


# --------------------------------------------------------------------------- #
# Replication: per-portfolio loadings table (CAPM vs FF3)
# --------------------------------------------------------------------------- #
def loadings_table(portfolios: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """One row per portfolio: FF3 loadings (a, b, s, h) with t-stats, and the
    R-squared from CAPM vs FF3."""
    out = []
    for name in portfolios.columns:
        capm = run_capm(portfolios[name], factors)
        ff3 = run_ff3(portfolios[name], factors)
        out.append({
            "portfolio": name,
            "alpha_%mo": ff3.params["const"] * 100,
            "alpha_t": ff3.tvalues["const"],
            "beta_MKT": ff3.params["Mkt-RF"],
            "s_SMB": ff3.params["SMB"],
            "h_HML": ff3.params["HML"],
            "t_HML": ff3.tvalues["HML"],
            "R2_CAPM": capm.rsquared,
            "R2_FF3": ff3.rsquared,
            "dR2": ff3.rsquared - capm.rsquared,
        })
    return pd.DataFrame(out).set_index("portfolio")


# --------------------------------------------------------------------------- #
# Factor premia (the direct "is the premium alive?" measure)
# --------------------------------------------------------------------------- #
def premium_stats(series: pd.Series, nw_lags: int = 6) -> dict:
    """Mean monthly premium, annualised premium, annualised Sharpe and a
    Newey-West t-stat for H0: mean == 0."""
    s = series.dropna()
    if len(s) < 12:
        return {"n": len(s), "mean_%mo": np.nan, "ann_%": np.nan,
                "sharpe_ann": np.nan, "t_NW": np.nan}
    X = np.ones((len(s), 1))
    res = sm.OLS(s.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags})
    mean_m = s.mean()
    return {
        "n": len(s),
        "mean_%mo": mean_m * 100,
        "ann_%": ((1 + mean_m) ** 12 - 1) * 100,
        "sharpe_ann": (mean_m / s.std()) * np.sqrt(12),
        "t_NW": res.tvalues[0],
    }


def premia_by_period(factors: pd.DataFrame, periods: dict, cols=FACTORS3) -> pd.DataFrame:
    """Factor premia for each sub-period. ``periods`` maps label -> (start, end)
    where either bound may be None."""
    frames = {}
    for label, (start, end) in periods.items():
        sub = factors.loc[start:end] if (start or end) else factors
        frames[label] = {c: premium_stats(sub[c]) for c in cols}
    rows = []
    for label, d in frames.items():
        for c, stats in d.items():
            rows.append({"period": label, "factor": c, **stats})
    return pd.DataFrame(rows)


def ff3_by_period(port: pd.Series, factors: pd.DataFrame, periods: dict) -> pd.DataFrame:
    """Run the FF3 regression of one test portfolio separately in each period."""
    rows = []
    for label, (start, end) in periods.items():
        sub = factors.loc[start:end] if (start or end) else factors
        p = port.loc[start:end] if (start or end) else port
        d = _excess(p, sub)
        if len(d) < 12:
            rows.append({"period": label, "n": len(d), "alpha_%mo": np.nan,
                         "beta_MKT": np.nan, "s_SMB": np.nan, "h_HML": np.nan,
                         "t_HML": np.nan, "R2": np.nan})
            continue
        m = run_ff3(p, sub)
        rows.append({
            "period": label, "n": int(m.nobs),
            "alpha_%mo": m.params["const"] * 100,
            "beta_MKT": m.params["Mkt-RF"],
            "s_SMB": m.params["SMB"],
            "h_HML": m.params["HML"],
            "t_HML": m.tvalues["HML"],
            "R2": m.rsquared,
        })
    return pd.DataFrame(rows).set_index("period")


# --------------------------------------------------------------------------- #
# Rolling estimates and portfolio helpers
# --------------------------------------------------------------------------- #
def rolling_premium(series: pd.Series, window: int = 60) -> pd.Series:
    """Rolling annualised premium (mean of the factor over ``window`` months)."""
    return ((1 + series).rolling(window).apply(lambda x: x.prod(), raw=True)
            ** (12 / window) - 1) * 100


def value_growth_legs(portfolios: pd.DataFrame):
    """Equal-weight a 'value' leg (highest-B/M column in each size quintile) and a
    'growth' leg (lowest-B/M column), returning (value, growth) monthly series."""
    cols = list(portfolios.columns)
    # Columns are ordered ME1..ME5 each with BM1..BM5; pick BM5 (value) and BM1 (growth).
    value_cols = [c for c in cols if c.endswith("HiBM") or c.endswith("BM5")]
    growth_cols = [c for c in cols if c.endswith("LoBM") or c.endswith("BM1")]
    value = portfolios[value_cols].mean(axis=1)
    growth = portfolios[growth_cols].mean(axis=1)
    return value.rename("value"), growth.rename("growth")


def sharpe(series: pd.Series, rf: pd.Series | None = None) -> float:
    s = series.dropna()
    if rf is not None:
        s = (s - rf.reindex(s.index)).dropna()
    if s.std() == 0 or len(s) < 12:
        return np.nan
    return (s.mean() / s.std()) * np.sqrt(12)
