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

## Error pages (what you see instead of a report when something goes wrong)

| File | What was asked | What it shows |
|---|---|---|
| [error_Xyzzy_Quux_2023-24.html](error_Xyzzy_Quux_2023-24.html) | Xyzzy Quux, 2023-24 | A company name NSE does not know. |
| [error_Reliance_2019-20.html](error_Reliance_2019-20.html) | Reliance, 2019-20 | A financial year before BRSR reporting began (FY 2021-22). |
| [error_Tata_Steel_2021-22.html](error_Tata_Steel_2021-22.html) | Tata Steel, 2021-22 | A real company and a valid year, but NSE has no filing for it: lists the years it does have. |
| [error_Infosys_2021-22.html](error_Infosys_2021-22.html) | Infosys, 2021-22 | A filing file on NSE that is damaged (here a deliberately broken file). |
