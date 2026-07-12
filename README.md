<!-- 🇬🇧 English · 🇵🇱 [Wersja polska](README.pl.md) -->

# Credit Scoring Model — Excel Scorecard (WoE/IV + MLE Logistic Regression)

> An end-to-end credit scoring pipeline built **from scratch in Excel**: manual WoE/IV binning,
> logistic regression estimated by maximum likelihood (MLE) via Solver, scorecard scaling,
> and a full validation suite (AUC, KS, Gini, PSI).

*(Fill in the `TODO:` fields before publishing.)*

---

## 1. Objective

Build an interpretable scorecard that estimates the probability of default (PD) from loan
application data, together with a validation suite consistent with credit risk modelling practice.

The project deliberately **avoids ML libraries** — every step (binning, WoE, IV, likelihood
function, ROC, KS, PSI) is computed explicitly in the sheet, to demonstrate understanding of the
mechanics rather than a single `sklearn` call.

## 2. Data

- **Source:** *German Credit* dataset (`credit-g`) from OpenML, fetched in Python via
  `sklearn.datasets.fetch_openml("credit-g", version=1)`.
- **Size:** 1,000 observations, 20 explanatory features + `class` target.
- **Target encoding:** `good → 0`, `bad → 1`, so **the modelled event (1) is default**.
  This drives the WoE direction (`WoE = ln(GoodDist / BadDist)` → higher WoE = lower risk).
- **Ingestion pipeline:** the [`fetch_data.py`](fetch_data.py) script downloads the data, recodes
  the target and writes the raw file → the CSV is imported into Excel. The raw pull is included in
  this repo as [`credit_data.csv`](credit_data.csv) (1,000 × 21, no missing values).
- **Train/test split (700 / 300):** performed manually in Excel — a helper random column was added
  across all 1,000 rows, the rows were sorted by that column, then split into the first 700 (train)
  and remaining 300 (test). This reshuffles the records relative to the original CSV order, which is
  why the `Dev_sample` ordering differs from the source file.
- The two sets are **disjoint** — training and test share no records (no data leakage).

```python
# fetch_data.py (excerpt)
data = fetch_openml("credit-g", version=1, as_frame=True)
df = data.frame.copy()
df['class'] = df['class'].map({'good': 0, 'bad': 1})
df.to_csv("credit_data.csv", index=False)
```

> Methodological note: WoE/IV tables are derived **only on the training sample**
> (`Dev_sample` sheet = 700 development records) and then *applied* to the test sample.
> This is the correct approach — no leakage from test into the binning.

## 3. Workbook structure (sheets)

| Sheet | Contents |
|---|---|
| `Dev_sample` | Raw development sample (700 rows) — basis for WoE/IV derivation |
| `Binning_WOE_IV` | Manual binning: Good/Bad, GoodDist/BadDist, **WOE**, IV per bin, IV total; category-to-bin lookup tables |
| `TRAIN_DATA` | 700 training rows: raw features → WoE → partial score → PD → decision |
| `TEST_DATA` | 300 test rows, same scoring pipeline |
| `TRAIN_AUC` / `TEST_AUC` | ROC curve points (TPR/FPR) and AUC via the trapezoidal rule |
| `TRAIN_SUMMARY` / `TEST_SUMMARY` | β coefficients, log-likelihood, AUC, KS, Gini, PD statistics |
| `TRAIN_Histogram` / `TEST_Histogram` | Score / PD distributions |
| `SCORECARD_SCALLING` | Scaling parameters: PDO, Base score, Odds, Factor, Offset |
| `POINTS_TABLE` | Scorecard points per variable/bin |
| `PSI` | Population Stability Index (train vs test) by score band |
| `Summary` | Decision policy (cut-offs), counts and average PD per bucket |
| `Documentation` | (to be completed) |

## 4. Methodology

1. **Binning + WoE/IV.** Variables grouped into bins; per bin:
   `WoE = ln(GoodDist / BadDist)`, `IV_bin = (GoodDist − BadDist) · WoE`, `IV_total = Σ IV_bin`.
2. **Logistic regression (MLE).** Linear model on the WoE variables; parameters β0…β12 obtained
   by **maximising the log-likelihood in Solver** (12 predictors + intercept).
3. **Scorecard scaling.** `Factor = PDO / ln(2)`, `Offset = Base − Factor · ln(Odds)`.
   Parameters: **PDO = 30, Base score = 600, Odds = 20:1**, hence Factor ≈ 43.28, Offset ≈ 470.34.
   Interpretation: at a score of 600 the good:bad odds are 20:1; every 30 points doubles the odds.
4. **Decision policy:** Reject `< 500` · Manual review `500–579` · Accept `≥ 580`.

## 5. Results (verified)

| Metric | Train (700) | Test (300) |
|---|---|---|
| **AUC** | 0.804 | 0.815 |
| **KS** | 0.493 | 0.540 |
| **Gini** | 0.608 | 0.631 |

- **PSI (train vs test) = 0.064** → below 0.10, populations are stable.
- Test slightly outperforms train — this is within noise at N_test = 300 and is not a warning
  sign (no leakage, confirmed by the disjoint sets).

Decision distribution:

| Bucket | Train | Test |
|---|---|---|
| Accept | 124 | 40 |
| Manual review | 304 | 141 |
| Reject | 272 | 119 |

## 6. How to open

> **Requires Microsoft Excel 2021 or Microsoft 365** (Google Sheets also works).
> The model uses the `XLOOKUP` and `LET` functions. These are standard functions in any modern
> spreadsheet — in the target environments (banks, enterprises) Microsoft 365 is the norm.
> Older Excel versions (≤ 2019) and LibreOffice do not support them and will display `#NAME?`.
> Open the file in a suitable version so the model logic evaluates correctly.

## 7. Limitations

The model is built on `credit-g` (OpenML), a classic benchmark whose properties bound how the
results should be read. It is an **application** scorecard (not behavioural, not segmented),
validated on a single random hold-out. Treat it as a demonstration of the modelling *process*,
not a production-ready component.

- **Small sample.** 1,000 observations (~300 bad) limit how tightly stability can be assessed,
  especially for the rarer BAD class.
- **No out-of-time validation.** The split is random, not temporal, so behaviour over time is unknown.
- **No behavioural variables.** Purely application data; production PD models also use transactional
  and account-history features.
- **No segmentation.** A single model covers the whole population; production setups often segment
  (by product, age band, pre-score, etc.).
- **No missing values.** The dataset is complete, so imputation quality and the impact of missingness
  cannot be assessed (some "absence" is encoded as a category, e.g. *no checking account*).
- **Unregularized logit.** In principle this raises overfitting risk on a small sample. Two facts
  argue against *material* overfitting here: test performance matches/exceeds train
  (AUC 0.815 vs 0.804), and the WoE coarse-binning step is itself a strong regularizer that reduces
  effective degrees of freedom. An L2-penalized fit remains a sensible robustness check.
- **Partial drift coverage.** Score-level PSI was computed (0.064, stable); per-variable
  characteristic stability (CSI) and any temporal drift were not assessed.
- **No fairness testing.** No bias assessment across protected attributes (the data encodes sex via
  `personal_status`, plus `age`) — increasingly expected in EU credit models.
- **No production validation.** Not tested on operational data or in a live scoring environment.
- **Benchmark data.** `credit-g` is educational; its variables are simplified and do not reflect the
  full structure of real credit data.

## 8. Reproducibility & next steps

Built and verified with:

| Component | Version |
|---|---|
| Python | 3.14 |
| pandas | 3.0.3 |
| scikit-learn | 1.9.0 |

`fetch_openml("credit-g", version=1)` pins the OpenML dataset version, so the raw pull is stable
across environments. Note: the 700/300 split was drawn manually in Excel (no fixed seed), so the
*exact* partition is not regenerable from the script alone — the resulting train/test sheets are
stored in the workbook.

Natural extensions: PD calibration, out-of-time validation, reject inference, per-variable CSI,
a fairness check, and an L2-regularized comparison.

---

*Author: [LukaszB-DA](https://github.com/LukaszB-DA) · Portfolio project — credit risk modelling / quantitative analytics.*
