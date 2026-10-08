# The `data/` folder

| Folder | What it is | In the repository? |
|---|---|---|
| `raw/<SYMBOL>/<FY>/` | A company's BRSR filing as published on NSE (`*.xml`, the SEBI XBRL file) and a small `filing.json` (company name, dates, links). The tool downloads these itself. | **Only 11 filings**, listed below |
| `cache/` | Saved company searches (so a name is only searched once). | No (recreated automatically) |
| `parsed/` | The cleaned data of each filing as JSON, written every time a page is made. | No (generated) |

## Filings kept in the repository

The assignment allows hand-downloaded filings in the repository if they are documented. These eleven are kept so that a fresh clone can
rebuild the pages in `samples/` and run every test **without the internet** (`python flow.py samples`, `pytest`):

| Company | Financial years | Why it is here |
|---|---|---|
| Tata Steel (`TATASTEEL`) | 2022-23, 2023-24, 2024-25, 2025-26 (+ its list of filings) | sample page (a mis-scaled figure); the five-year trend sample (a basis change, restatements); the summary sample (FY 2025-26 against FY 2024-25); the "no filing for FY 2021-22" error sample |
| Reliance Industries (`RELIANCE`) | 2022-23, 2023-24 (+ its list of filings) | sample page (2023-24); the trend sample; the summary sample for FY 2022-23, where NSE has no FY 2021-22 filing; the `flow.py summary` "no filing for FY 2021-22" error sample (that one needs the list of filings); test of the older filing layout (2022-23) |
| Wipro (`WIPRO`) | 2023-24, 2024-25, 2025-26 | sample page (2025-26); the trend sample where the reporting basis flips; the summary sample (everything improved); test that the boundary can change from year to year |
| Infosys (`INFY`) | 2021-22 | sample page; a damaged XML file that has to be cleaned |
| HDFC Bank (`HDFCBANK`) | 2022-23 | sample page; the older layout with almost no environmental data |

They are public documents published by the companies on NSE (https://www.nseindia.com, "Corporate filings > Business Sustainability Reports").
Only the XML is kept; the PDF versions are not needed and are not committed.

Every other company is downloaded on demand: `python flow.py --company "<name>" --fy <year>`.
