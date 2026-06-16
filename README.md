# Data provenance

## What's here

| File | Contents | Shape | Span |
|------|----------|-------|------|
| `ff_factors_monthly.csv` | Monthly `Mkt-RF`, `SMB`, `HML`, `RF` (decimal returns) | 682 × 4 | 1963-07 → 2020-04 |
| `portfolios_25_monthly.csv` | Monthly value-weighted returns, 25 size×B/M portfolios | 682 × 25 | 1963-07 → 2020-04 |

## Source

Both files are derived from the **Kenneth R. French Data Library** (Tuck School of
Business, Dartmouth), obtained via the public mirror
[`omartinsky/FamaFrench`](https://github.com/omartinsky/FamaFrench). Specifically:

- Factors from `F-F_Research_Data_5_Factors_2x3_daily.CSV`. The market and HML series
  match the textbook FF3 file; the **SMB here comes from the 5-factor construction and
  differs marginally** from the 3-factor SMB. This does not affect the value-premium
  results.
- Portfolios from the bivariate `Size × Book-to-Market (5×5)` daily file, first
  (value-weighted) return block. Columns run `ME1..ME5 × BM1..BM5`; `SMALL HiBM` is
  small-value (BM5), `SMALL LoBM` is small-growth (BM1), and so on.

## How the monthly series were built

Daily returns are compounded within each calendar month:

```
monthly_return = (1 + daily_return).prod() - 1
```

`Mkt-RF` is reconstructed as compounded market minus compounded risk-free within the
month, rather than summed, to stay internally consistent.

## Vintage and refreshing

This cache **ends in April 2020**. That is why every "Value comeback (2022–present)"
row in `results/` is blank — it is deliberately not estimated from data that doesn't
exist here.

To refresh with current data straight from Dartmouth:

```python
from src.data_loader import load_all
factors, portfolios = load_all(download=True)
```

or from the project root:

```bash
python run_analysis.py --download
```

Either call fetches the live `F-F_Research_Data_Factors` and `25_Portfolios_5x5` zips,
rebuilds the monthly panels, and overwrites these CSVs.
