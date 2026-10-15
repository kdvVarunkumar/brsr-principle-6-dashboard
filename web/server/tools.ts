// The two tools the chat assistant may call. They read the Python data service (python flow.py serve), so every figure the model
// sees is exactly what the Dashboard shows (same sentences, units, "as filed" notes and filing origins). Nothing is recalculated here.
import { defineTool } from "@copilotkit/runtime/v2";
import { z } from "zod";

const API = process.env.BRSR_API_URL ?? "http://127.0.0.1:8000";

async function getJson(path: string): Promise<any> {
  try {
    const response = await fetch(`${API}${path}`);
    return await response.json(); // a failure comes back as {"error": "..."}, which the model can read and explain
  } catch {
    return { error: `The data service is not reachable at ${API}. Start it with: python flow.py serve` };
  }
}

// One Dashboard card, cut down to what the model needs to answer. Every field is copied from the Python view.
export const cardForModel = (c: any) => ({
  title: c.title,
  value: c.has_number ? `${c.big} ${c.unit}`.trim() : c.big,
  verdict: c.chip_text,
  change: c.trend,
  last_year: c.previous_text,
  what_it_is: c.what,
  notes_on_this_figure: c.alerts,
  where_in_the_filing: c.trace,
  trust: c.trust, // ok | check | doubtful
});

export const listFilings = defineTool({
  name: "listFilings",
  description: "List which companies (NSE symbols) and financial years have a saved BRSR filing.",
  parameters: z.object({}),
  execute: async () => getJson("/api/filings"),
});

export const getDashboard = defineTool({
  name: "getDashboard",
  description:
    "Get the Dashboard of one company and financial year: the summary sentence, the improved/same/worse scoreboard and every figure by topic " +
    "(energy, climate, water, air, waste, safeguards) with its value, unit, change versus last year and any note about the figure. " +
    "Pass `topic` (for example 'water') to get only that topic.",
  parameters: z.object({
    symbol: z.string().describe("NSE symbol, e.g. TATASTEEL"),
    fy: z.string().describe("Financial year, e.g. 2023-24"),
    topic: z.string().optional().describe("Only this topic: energy, climate, water, air, waste or safeguards"),
  }),
  execute: async ({ symbol, fy, topic }) => {
    const data = await getJson(`/api/dashboard?symbol=${encodeURIComponent(symbol)}&fy=${encodeURIComponent(fy)}`);
    if (data.error) return data;
    const wanted = (topic ?? "").toLowerCase();
    const topics = data.dashboard.topics
      .filter((t: any) => !wanted || t.id.toLowerCase() === wanted || t.name.toLowerCase().includes(wanted))
      .map((t: any) => ({
        topic: t.name,
        headline: t.headline,
        shared_notes: t.notes.map((n: any) => n.text),
        figures: [...t.cards, ...t.minis].map(cardForModel),
      }));
    return {
      company: data.company_name,
      fy: data.fy,
      compared_with: data.previous_fy,
      boundary: data.boundary,
      source_url: data.source_url,
      summary: data.dashboard.glance.story,
      scoreboard: { improved: data.dashboard.glance.improved, about_the_same: data.dashboard.glance.same, got_worse: data.dashboard.glance.worse },
      topics,
    };
  },
});
