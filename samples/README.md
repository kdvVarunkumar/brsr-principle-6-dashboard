# Sample pages

Open any file in a web browser. They are made by `python make_samples.py` (do not edit them by hand).

## Report pages (Dashboard tab first, SEBI-format report second)

| File | Company and year | What it shows |
|---|---|---|
| [TATASTEEL_2025-26.html](TATASTEEL_2025-26.html) | Tata Steel, FY 2025-26 | Heavy industry (steel). The company's emissions are typed in the wrong scale: shown as filed, warned, never compared. |
| [RELIANCE_2023-24.html](RELIANCE_2023-24.html) | Reliance, FY 2023-24 | A large conglomerate and the cleanest example: almost every card has a better / worse verdict. |
| [WIPRO_2025-26.html](WIPRO_2025-26.html) | Wipro, FY 2025-26 | IT services. Energy is filed in megajoules and shown in GJ, marked 'unit changed by us'. |
| [INFY_2021-22.html](INFY_2021-22.html) | Infosys, FY 2021-22 | IT services, older filing layout: a damaged file that had to be cleaned, monthly air figures, energy with no unit. |
| [HDFCBANK_2022-23.html](HDFCBANK_2022-23.html) | HDFC Bank, FY 2022-23 | A bank (sparse data), older layout: many 'Not reported' and 'reported as 0', and the page still stays honest. |

## Trend pages (one company over several years: `python trends.py ...`)

| File | Company and years | What it shows |
|---|---|---|
| [TATASTEEL_trend_2021-22_to_2025-26.html](TATASTEEL_trend_2021-22_to_2025-26.html) | Tata Steel, FY 2021-22 to FY 2025-26 | Five years with everything the trend page handles: FY 2021-22 is not on NSE (shown from the next filing's previous-year column), the basis changes from consolidated to standalone, a later filing restates figures, and the emissions are mis-scaled. |
| [WIPRO_trend_2023-24_to_2025-26.html](WIPRO_trend_2023-24_to_2025-26.html) | Wipro, FY 2023-24 to FY 2025-26 | The reporting basis flips from year to year (standalone, consolidated, consolidated), so only years on the same basis are compared. |
| [RELIANCE_trend_2021-22_to_2023-24.html](RELIANCE_trend_2021-22_to_2023-24.html) | Reliance, FY 2021-22 to FY 2023-24 | A company on one basis throughout. FY 2021-22 is not on NSE, and FY 2022-23 uses the older SEBI layout with no energy unit. |

## Year-on-year summaries (the 3 biggest improvements and setbacks: `python summary.py ...`)

| File | Company and year | What it shows |
|---|---|---|
| [TATASTEEL_summary_2025-26.html](TATASTEEL_summary_2025-26.html) | Tata Steel, FY 2025-26 | A mixed year: one figure improved, three stayed about the same and four got worse. Last year's own report was checked and nothing was restated. |
| [WIPRO_summary_2025-26.html](WIPRO_summary_2025-26.html) | Wipro, FY 2025-26 | A year where all 9 figures that can be compared improved: the page shows the three biggest, says plainly that nothing got worse, and still lists every figure. |
| [RELIANCE_summary_2022-23.html](RELIANCE_summary_2022-23.html) | Reliance, FY 2022-23 | NSE has no filing for FY 2021-22, so there is no report of last year's own: the comparison uses the previous-year column of this filing, and the page says so. |

## Error pages (what you see instead of a report when something goes wrong)

| File | What was asked | What it shows |
|---|---|---|
| [error_Xyzzy_Quux_2023-24.html](error_Xyzzy_Quux_2023-24.html) | Xyzzy Quux, 2023-24 | A company name NSE does not know. |
| [error_Reliance_2019-20.html](error_Reliance_2019-20.html) | Reliance, 2019-20 | A financial year before BRSR reporting began (FY 2021-22). |
| [error_Tata_Steel_2021-22.html](error_Tata_Steel_2021-22.html) | Tata Steel, 2021-22 | A real company and a valid year, but NSE has no filing for it: lists the years it does have. |
| [error_Infosys_2021-22.html](error_Infosys_2021-22.html) | Infosys, 2021-22 | A filing file on NSE that is damaged (here a deliberately broken file). |
| [error_Reliance_2025-26_to_2021-22.html](error_Reliance_2025-26_to_2021-22.html) | Reliance, 2025-26 to 2021-22 | A trend request with the years the wrong way round (trends.py). |
| [error_Reliance_2021-22.html](error_Reliance_2021-22.html) | Reliance, 2021-22 | A summary request (summary.py) for a year NSE has no filing for: the suggested commands use summary.py. |
