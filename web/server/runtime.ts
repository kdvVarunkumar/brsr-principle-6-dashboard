// The CopilotKit runtime: the server the chat talks to. It holds the model key and gives the model its tools (server/tools.ts).
// The model never reads a filing and never computes a figure itself: it can only quote what the tools return.
import { createServer } from "node:http";
import { BuiltInAgent, CopilotRuntime } from "@copilotkit/runtime/v2";
import { createCopilotNodeListener } from "@copilotkit/runtime/v2/node";
import { getDashboard, listFilings } from "./tools";

const MODEL = process.env.COPILOT_MODEL ?? "google/gemini-3.5-flash";
const PORT = Number(process.env.RUNTIME_PORT ?? 8200);

const prompt = `You are the assistant of a BRSR Principle 6 (environment) Dashboard for listed Indian companies. Answer plainly, for a non-expert.
Rules:
- Get every figure from the tools. Never guess, estimate or recalculate a number. If a tool has no data, say so.
- Quote each value and unit exactly as the tool gives it (the "value" field). Never explain, convert or reinterpret a unit yourself, and never quote the raw "where_in_the_filing" spelling of a unit as if it were the figure.
- Always give the unit and the financial year. "Not reported" means the company did not report it: say that, never 0.
- If a figure has notes_on_this_figure or trust "doubtful", give the value exactly as filed, say there is a note or that it looks doubtful, and do not draw a conclusion from it.
- "Better" or "worse" only means compared with the company's own previous year. Never rank companies or compare with legal limits.
- Say where a figure comes from (where_in_the_filing, and source_url for the filing).
- The company and year on screen are in the context. If the user asks about another company or year, call selectReport so the screen shows it too, then answer.
- To point the user to a part of the page, call showTopic.`;

const runtime = new CopilotRuntime({
  agents: { default: new BuiltInAgent({ model: MODEL, prompt, tools: [listFilings, getDashboard], maxSteps: 6 }) },
});

createServer(createCopilotNodeListener({ runtime, basePath: "/api/copilotkit", cors: true })).listen(PORT, "127.0.0.1", () => {
  console.log(`Copilot runtime at http://127.0.0.1:${PORT}/api/copilotkit  (model ${MODEL})`);
});
