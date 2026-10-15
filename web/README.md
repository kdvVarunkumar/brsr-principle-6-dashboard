# React Dashboard + CopilotKit chat assistant

The Dashboard page of the BRSR Principle 6 report, drawn in React, with a CopilotKit chat sidebar. It is an addition: the static HTML pipeline
(`python flow.py ...`) and its pages do not use any of this and are unchanged. Step 1 covers the Dashboard's summary and topic sections; the
Safeguards, trust and glossary parts, and the other pages, are still the HTML pages.

```
browser: React page + chat (:8000)  --chat-->  CopilotKit runtime (Node, :8200)  --tools-->  data service (:8000/api/...)  -->  data/raw/ filings
                  `python flow.py serve` serves the page and the data service AND starts the runtime
```

- Python decides every number, sentence, verdict and warning (`brsr_p6/views/dashboard_view.py`). `/api/dashboard` serves that as JSON and React only draws it,
  using the same stylesheets as the HTML pages.
- The assistant can only quote what its tools return (`listFilings`, `getDashboard`), so its answers match the screen: units, "as filed" notes and the filing origin included.
  It can also switch the company/year on screen (`selectReport`) and scroll to a topic (`showTopic`).

## One-time setup (Node 20+)

```
cd web
npm install
npm run build                # builds the page into web/dist (about a minute)
copy .env.example .env       # then put your GOOGLE_API_KEY in web\.env (git ignores it); free key: https://aistudio.google.com/apikey
```

## Run it

- **PyCharm:** run `flow.py` with the parameter `serve` (Run > Edit Configurations > Python: Script path `flow.py`, Parameters `serve`).
- **Terminal:** `python flow.py serve`

Your browser opens http://127.0.0.1:8000/ . Click the chat button and ask, for example: "What were Tata Steel's Scope 1 emissions in 2023-24?" or "Show me Reliance 2023-24".
Stop with Ctrl+C (the runtime stops too). If the terminal says "Assistant not started: ...", it names the missing setup step; the page still opens without the chat.
After changing anything in `web/src`, run `npm run build` again.

## Notes

- Default model: Google Gemini (`google/gemini-3.5-flash`). Another model: set `COPILOT_MODEL` in `.env` (for example `openai:gpt-5-mini` with `OPENAI_API_KEY`).
- The npm scripts call Node directly because the `&` in this project's folder name breaks the `.cmd` shims that `npx` uses on Windows.
- `npm run typecheck` checks the TypeScript.
