import { CopilotKitProvider, CopilotSidebar, useAgentContext, useFrontendTool } from "@copilotkit/react-core/v2";
import { useEffect, useState } from "react";
import { z } from "zod";
import { Dashboard } from "./Dashboard";
import type { DashboardData, Filings } from "./types";

// The data service and this page come from the same address (python flow.py serve), so paths are relative.
const API = import.meta.env.VITE_BRSR_API_URL ?? "";
// The CopilotKit runtime (web/server/runtime.ts) listens on its own port, so its address is absolute.
const RUNTIME_URL = import.meta.env.VITE_COPILOT_RUNTIME_URL ?? "http://127.0.0.1:8200/api/copilotkit";
const NO_SERVICE = "The data service is not running. Start it with: python flow.py serve";

function Page() {
  const [filings, setFilings] = useState<Filings>({});
  const [symbol, setSymbol] = useState("");
  const [fy, setFy] = useState("");
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/api/filings`)
      .then((r) => r.json())
      .then((found: Filings) => {
        setFilings(found);
        const first = found.TATASTEEL ? "TATASTEEL" : Object.keys(found)[0];
        if (first) {
          setSymbol(first);
          setFy(found[first].at(-1) ?? "");
        }
      })
      .catch(() => setError(NO_SERVICE));
  }, []);

  useEffect(() => {
    if (!symbol || !fy) return;
    setError("");
    fetch(`${API}/api/dashboard?symbol=${symbol}&fy=${fy}`)
      .then((r) => r.json())
      .then((body) => (body.error ? (setData(null), setError(body.error)) : setData(body)))
      .catch(() => setError(NO_SERVICE));
  }, [symbol, fy]);

  // Is the chat runtime reachable? Without it the chat box accepts typing but cannot send, so say so instead of looking broken.
  const [chatUp, setChatUp] = useState(true);
  useEffect(() => {
    const check = () => fetch(`${RUNTIME_URL}/info`).then((r) => setChatUp(r.ok)).catch(() => setChatUp(false));
    check();
    const timer = setInterval(check, 4000);
    return () => clearInterval(timer);
  }, []);

  // What the assistant is told about the screen ...
  useAgentContext({ description: "The company and financial year shown on the Dashboard right now", value: { symbol, fy } });

  // ... and the two things it may do on the screen.
  useFrontendTool({
    name: "selectReport",
    description: "Show another company and financial year on the Dashboard.",
    parameters: z.object({ symbol: z.string().describe("NSE symbol, e.g. TATASTEEL"), fy: z.string().describe("Financial year, e.g. 2023-24") }),
    handler: async ({ symbol: s, fy: y }) => {
      const key = s.toUpperCase();
      if (!filings[key]?.includes(y)) return `No saved filing for ${s} ${y}. Saved filings: ${JSON.stringify(filings)}`;
      setSymbol(key);
      setFy(y);
      return `Now showing ${key} ${y}.`;
    },
  });
  useFrontendTool({
    name: "showTopic",
    description: "Scroll the Dashboard to a topic section: energy, climate, water, air, waste or safeguards.",
    parameters: z.object({ topic: z.string() }),
    handler: async ({ topic }) => {
      const wanted = topic.toLowerCase();
      const found = data?.dashboard.topics.find((t) => t.id.toLowerCase() === wanted || t.name.toLowerCase().includes(wanted));
      if (!found) return `No topic called ${topic}. Topics: ${data?.dashboard.topics.map((t) => t.id).join(", ")}`;
      document.getElementById(`dash-${found.id}`)?.scrollIntoView({ behavior: "smooth" });
      return `Scrolled to ${found.name}.`;
    },
  });

  return (
    <>
      <header className="page-header">
        <div className="inner">
          <p className="eyebrow">Business Responsibility &amp; Sustainability Report · Principle 6 (environment)</p>
          <h1>{data ? <>{data.company_name} <span className="symbol">({data.symbol})</span></> : "BRSR Principle 6 Dashboard"}</h1>
          <p className="subtitle">{data ? `Financial year ${data.fy}, compared with ${data.previous_fy} · ${data.boundary || "boundary not stated"}` : "Choose a company and a year"}</p>
          <div className="picker">
            <label>Company <select value={symbol} onChange={(e) => { setSymbol(e.target.value); setFy(filings[e.target.value].at(-1) ?? ""); }}>
              {Object.keys(filings).map((s) => <option key={s}>{s}</option>)}
            </select></label>
            <label>Year <select value={fy} onChange={(e) => setFy(e.target.value)}>
              {(filings[symbol] ?? []).map((y) => <option key={y}>{y}</option>)}
            </select></label>
          </div>
        </div>
      </header>
      {!chatUp && (
        <p className="chat-down" role="alert">
          The chat assistant is not running, so messages cannot be sent. Stop this and start again with <code>python flow.py serve</code>; if the
          terminal says "Assistant not started", follow what it says (usually: put your <code>GOOGLE_API_KEY</code> in <code>web\.env</code>).
        </p>
      )}
      <main className="wrap">
        {error && <p className="error-line">{error}</p>}
        {data && <Dashboard data={data} />}
      </main>
    </>
  );
}

export default function App() {
  return (
    <CopilotKitProvider runtimeUrl={RUNTIME_URL}>
      <Page />
      <CopilotSidebar />
    </CopilotKitProvider>
  );
}
