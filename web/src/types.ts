// The shape of /api/dashboard. It mirrors the Python dataclasses in brsr_p6/views/dashboard_view.py and dashboard_cards.py:
// Python decides every sentence, verdict and warning; React only draws them.

export type Bar = { label: string; percent: number; text: string; is_previous: boolean };

export type Card = {
  id: string;
  title: string;
  size: "card" | "mini";
  name: string;
  better_label: string;
  big: string;
  unit: string;
  has_number: boolean;
  chip_class: string;
  chip_text: string;
  trend: string;
  previous_text: string;
  bars: Bar[];
  what: string;
  why: string;
  fine: string[];
  alerts: string[];
  badge: string;
  trust: string;
  caveat: string;
  delta_words: string;
  quote: string;
  css: string;
  trace: string[];
  alert_title: string;
};

export type Note = { text: string; titles: string[] };
export type Segment = { label: string; percent: number; percent_text: string; amount_text: string; css: string };
export type Stack = { title: string; segments: Segment[]; missing: string[]; zero_note: string; footnote: string; aria: string };

export type Topic = {
  id: string;
  name: string;
  icon: string;
  sebi: string;
  intro: string;
  headline: string;
  chip_class: string;
  chip_text: string;
  stat: string;
  cards: Card[];
  minis: Card[];
  stack: Stack | null;
  notes: Note[];
};

export type Tile = { id: string; name: string; icon: string; chip_class: string; chip_text: string; stat: string };
export type Glance = { title: string; story: string; improved: number; same: number; worse: number; total: number; tiles: Tile[] };

export type DashboardData = {
  company_name: string;
  symbol: string;
  fy: string;
  previous_fy: string;
  boundary: string;
  submission_date: string;
  source_url: string;
  dashboard: { glance: Glance; topics: Topic[] };
};

export type Filings = Record<string, string[]>;
