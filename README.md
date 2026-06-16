# The Value Premium, Replicated and Re-examined

A replication of the Fama–French (1993) three-factor model and an extension that
asks a sharper question: **did the value premium actually break, and if so, was it
ever the risk story the model claimed?**

The project does two things. First (`notebooks/01_replication.ipynb`) it rebuilds
the canonical result — that adding **SMB** (size) and **HML** (value) to the market
factor explains the cross-section of returns far better than CAPM. Second
(`notebooks/02_extension.ipynb`) it tracks the HML premium across three regimes and
uses the gap between *factor loadings* and *factor premia* to adjudicate the
risk-versus-behavioural debate.

## Headline findings

**The replication holds, cleanly.** Across the 25 size×book-to-market portfolios
over 1963–1991, mean R² rises from **0.79 under CAPM to 0.93 under FF3** (+0.14),
and pricing errors shrink: most alphas are economically tiny and statistically
indistinguishable from zero. The model does what it says on the tin.

**The premium, not the loading, is what moved.** This is the crux of the extension.
Take the small-value corner (`SMALL HiBM`), HML's natural home. Its HML *loading* is
essentially constant across eras — **h = 0.55 (t = 18.4)** in 1963–1991 and
**h = 0.57 (t = 12.8)** in the 2010s, R² = 0.96 in both. The portfolio is exactly as
much a "value" portfolio as it always was. What changed is the *reward* for that
exposure: the annualized HML premium runs **+5.06% (t = 2.54)** in the original
sample and **−4.87% (t = −1.52)** through the 2010s. Same beta, opposite sign on the
payoff.

**Value's risk-adjusted edge inverted.** Sharpe ratios for the value and growth legs
flip across regimes: value **0.55** vs growth **0.22** originally, then value
**0.34** vs growth **0.71** in the lost decade. Meanwhile the market premium roughly
*tripled* (4.99% → 12.59% annualized) — the 2010s were not a bad decade for beta,
only for value.

## Why this matters for the risk-vs-behavioural debate

Fama and French always framed HML as compensation for *risk*: value firms are
distressed, operationally inflexible, and dangerous to hold in bad states, so they
must offer a premium. The behavioural camp (Lakonishok–Shleifer–Vishny, and later
Daniel–Titman) countered that the premium is *mispricing* — investors over-extrapolate
glamour growth and under-price boring value, and arbitrage is too costly to close
the gap.

The loading-vs-premium split is exactly the evidence that discriminates between them.
A genuine risk factor can earn a low or negative *realized* return over a decade —
realized returns are noisy — but its *expected* premium should not vanish merely
because the asset got more expensive. Yet that is what the data look like: as value
spreads compressed through the 2010s, the premium didn't just shrink, it went
negative, while the structural loading never budged. That pattern is more naturally
read as **the price of the value characteristic getting bid up** than as a stable
risk price. The characteristic stayed; its compensation did not.

That said, the honest version of this argument resists a victory lap. A decade is one
draw. The same logic that lets a risk factor underperform for years also forbids us
from declaring it dead after one regime. The extension is built to *test* that, not to
assert it — which is why the data layer matters (below).

## Where the model breaks

Two omissions show up at the seams. **Momentum** (UMD) is absent, and much of HML's
2010s behaviour is entangled with momentum's dominance. **Intangibles** are the deeper
problem: book value increasingly mismeasures the capital base of asset-light firms, so
the book-to-market sort that *defines* HML has been quietly classifying R&D-heavy
compounders as "growth" when a capitalized-intangibles book value would call them
value. If the sorting variable is broken, the factor inherits the break. This is the
strongest case that the 2010s were a *measurement* failure as much as a risk-or-behaviour
one.

## Data and provenance — read this before quoting numbers

The cached results in this repo are computed on **real Ken French data running
1963-07 through 2020-04** (the "vintage" field in `results/summary.json`). The factor
and portfolio CSVs were sourced from the public
[omartinsky/FamaFrench](https://github.com/omartinsky/FamaFrench) mirror of the
Dartmouth files; monthly series are built from the daily files by compounding within
each month. Two honest caveats: (1) the bundled factor SMB comes from the 5-factor
file and differs marginally from the textbook FF3 SMB (Mkt-RF and HML are effectively
identical); (2) **the cached cache stops in 2020, so the "Value comeback (2022–present)"
period is intentionally blank** in every table here. It is not estimated, not
fabricated, not interpolated.

To populate the post-2020 value recovery, run the loader with `download=True`:

```python
from src.data_loader import load_all
factors, portfolios = load_all(download=True)   # fetches current files from Ken French
```

This pulls the live `F-F_Research_Data_Factors` and `25_Portfolios_5x5` zips straight
from Dartmouth and overwrites the cache, after which both notebooks fill in the 2022+
regime automatically. The empirical claim that the value premium *collapsed in the
2010s* is fully supported by the bundled data; the claim that it *recovered after 2022*
is what the live extension is there to check.

## Repository layout

```
src/data_loader.py     load_factors / load_portfolios / load_all  (download=False|True)
src/analysis.py        CAPM, FF3, loadings tables, period premia, rolling betas, Sharpes
run_analysis.py        regenerates every figure + results/  (add --download for live data)
notebooks/01_replication.ipynb   the canonical FF3 replication, executed with real output
notebooks/02_extension.ipynb     the value-breakdown study + commentary
data/                  cached real monthly factors & 25 portfolios (1963-07 → 2020-04)
figures/               publication figures (rolling HML, R² dumbbell, loading grid, …)
results/               summary.json + per-period CSVs
```

## Reproduce

```bash
pip install -r requirements.txt
python run_analysis.py                 # offline, cached 1963–2020 data
python run_analysis.py --download      # live refresh through the present
jupyter notebook notebooks/            # step through the analysis
```

## References

Fama, E. F., & French, K. R. (1993). *Common risk factors in the returns on stocks
and bonds.* Journal of Financial Economics, 33(1), 3–56.
Lakonishok, J., Shleifer, A., & Vishny, R. (1994). *Contrarian investment,
extrapolation, and risk.* Journal of Finance, 49(5), 1541–1578.
Data: Kenneth R. French Data Library, Tuck School of Business at Dartmouth.
