// The Dashboard page, drawn in React. It is the same layout as brsr_p6/rendering/templates/dashboard.html (same class names, same CSS files),
// so it looks like the HTML page; the difference is that React draws it from JSON and the chat assistant can work with it.
import type { Card, DashboardData, Stack, Topic } from "./types";

const Chip = ({ cls, text }: { cls: string; text: string }) => <span className={`chip ${cls}`}>{text}</span>;

// The six icons the topics use (the same drawings as the HTML page), defined once and reused with <use>.
function Icons() {
  const common = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinejoin: "round" as const, strokeLinecap: "round" as const };
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true" focusable="false">
      <symbol id="i-bolt" {...common}><path d="M13 2 4 14h7l-1 8 9-12h-7z" /></symbol>
      <symbol id="i-cloud" {...common}><path d="M7 18a4 4 0 0 1-.5-7.97A6 6 0 0 1 18 9a4.5 4.5 0 0 1 0 9z" /></symbol>
      <symbol id="i-drop" {...common}><path d="M12 2.5s6 6.2 6 10.5a6 6 0 0 1-12 0c0-4.3 6-10.5 6-10.5z" /></symbol>
      <symbol id="i-wind" {...common}><path d="M3 8h10a3 3 0 1 0-3-3M3 12h14a3 3 0 1 1-3 3M3 16h7" /></symbol>
      <symbol id="i-bin" {...common}><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6" /></symbol>
      <symbol id="i-shield" {...common}><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /><path d="M8.5 12l2.5 2.5 4.5-5" /></symbol>
    </svg>
  );
}

const Icon = ({ id }: { id: string }) => <svg aria-hidden="true"><use href={`#${id}`} /></svg>;

function MetricCard({ c }: { c: Card }) {
  const big = c.size === "card";
  return (
    <article className={`${big ? "card" : "mini"}${c.css ? ` ${c.css}` : ""}`}>
      <div className="card-top">
        <h3>{c.title}{c.name && <> <span className="name">{c.name}</span></>}</h3>
        {big && <span className="better">{c.better_label}</span>}
      </div>
      <p className={`big${c.has_number ? "" : " none"}`}>
        <span className="v num">{c.big}</span>
        {c.unit && <span className="u">{c.unit}{c.trust === "doubtful" ? " · as filed" : ""}</span>}
      </p>
      <p className="trend"><Chip cls={c.chip_class} text={c.chip_text} /><span>{c.trend}</span></p>
      {c.caveat && <p className="caveat">{c.caveat}</p>}
      {c.bars.length > 0 && (
        <div className="bars" role="img" aria-label={c.bars.map((b) => `${b.label}: ${b.text}`).join("; ")}>
          {c.bars.map((b) => (
            <div key={b.label} className={`bar-row${b.is_previous ? " prev" : ""}`}>
              <span>{b.label}</span><span className="bar"><i style={{ width: `${b.percent.toFixed(2)}%` }} /></span><span className="bv">{b.text}</span>
            </div>
          ))}
        </div>
      )}
      <p className="what">{big && <b>What it is: </b>}{c.what}</p>
      {big && c.why && <p className="why"><b>Why it matters:</b> {c.why}</p>}
      {c.alerts.length > 0 && <p className="alert"><b>ⓘ {c.alert_title}</b> {c.alerts.join(" ")}</p>}
      {big && c.fine.length > 0 && (
        <details className="fine">
          <summary>Fine print</summary>
          {c.fine.map((line) => <p key={line}>{line}</p>)}
          {c.trace.length > 0 && <p className="trace-head"><b>Where it is in the filing:</b></p>}
          {c.trace.map((line) => <p key={line} className="trace">{line}</p>)}
        </details>
      )}
      <p className="badge" title={!big && c.trace.length ? `From the filing: ${c.trace.join(" | ")}` : undefined}>
        {!big && c.previous_text ? `${c.previous_text} · ` : ""}{c.badge}
      </p>
    </article>
  );
}

function StackBar({ s }: { s: Stack }) {
  return (
    <figure className="stack">
      <figcaption>{s.title}</figcaption>
      <div className="stack-bar" role="img" aria-label={s.aria}>
        {s.segments.map((seg) => <span key={seg.label} className={seg.css} style={{ width: `${seg.percent.toFixed(2)}%` }} />)}
      </div>
      <ul className="key">
        {s.segments.map((seg) => (
          <li key={seg.label}><i className={`sw ${seg.css}`} /><span className="pct">{seg.percent_text}%</span><span>{seg.label} <span className="amt">· {seg.amount_text}</span></span></li>
        ))}
        {s.missing.map((label) => <li key={label}><i className="sw grey" /><span className="pct">—</span><span><em>{label}: not reported</em></span></li>)}
      </ul>
      {(s.zero_note || s.footnote) && <p className="stack-note">{s.zero_note} {s.footnote}</p>}
    </figure>
  );
}

function TopicSection({ t }: { t: Topic }) {
  return (
    <section className="topic" id={`dash-${t.id}`} aria-labelledby={`dash-${t.id}-h`}>
      <div className="topic-head"><Icon id={t.icon} /><h2 id={`dash-${t.id}-h`}>{t.name}</h2><span className="src">{t.sebi}</span></div>
      <p className="plain">{t.intro}</p>
      <p className="headline">{t.headline}</p>
      {t.cards.length > 0 && <div className="cards">{t.cards.map((c) => <MetricCard key={c.id} c={c} />)}</div>}
      {t.minis.length > 0 && <div className="minis">{t.minis.map((c) => <MetricCard key={c.id} c={c} />)}</div>}
      {t.notes.map((n) => <p key={n.text} className="alert shared"><b>ⓘ Note for {n.titles.join(", ")}:</b> {n.text}</p>)}
      {t.stack && <StackBar s={t.stack} />}
    </section>
  );
}

export function Dashboard({ data }: { data: DashboardData }) {
  const { glance, topics } = data.dashboard;
  return (
    <div className="dash">
      <Icons />
      <nav className="jump" aria-label="Jump to a topic">
        <ul>{topics.map((t) => <li key={t.id}><a href={`#dash-${t.id}`}>{t.name.split(":")[0]}</a></li>)}</ul>
      </nav>

      <section className="glance" aria-labelledby="dash-glance-h">
        <h2 id="dash-glance-h">{glance.title}</h2>
        <p className="story">{glance.story}</p>
        {glance.total > 0 ? (
          <p className="score">
            <span className="lbl">Of the {glance.total} headline figures we can compare with last year:</span>
            <Chip cls="chip-good" text={`✔ ${glance.improved} improved`} />
            <Chip cls="chip-same" text={`≈ ${glance.same} about the same`} />
            <Chip cls="chip-bad" text={`✖ ${glance.worse} got worse`} />
          </p>
        ) : (
          <p className="score"><span className="lbl">None of the headline figures can be compared with last year.</span></p>
        )}
        <div className="tiles">
          {glance.tiles.map((tile) => {
            const inner = (
              <>
                <span className="t-name"><Icon id={tile.icon} />{tile.name.split(":")[0]}</span>
                <Chip cls={tile.chip_class} text={tile.chip_text} />
                <span className="t-stat">{tile.stat}</span>
              </>
            );
            // Only the topics drawn on this page can be jumped to (the safeguards section is still on the HTML page).
            return topics.some((t) => t.id === tile.id)
              ? <a key={tile.id} className="tile" href={`#dash-${tile.id}`}>{inner}</a>
              : <div key={tile.id} className="tile">{inner}</div>;
          })}
        </div>
        <p className="fairness"><b>How to read “better” and “worse”:</b> it only compares the company with <b>itself last year</b>. It is not a rating against other companies or legal limits; the filing does not contain those. A bigger business can use more in total, so we always show the figure <b>per ₹ of sales</b> next to the total.</p>
      </section>

      {topics.map((t) => <TopicSection key={t.id} t={t} />)}
    </div>
  );
}
