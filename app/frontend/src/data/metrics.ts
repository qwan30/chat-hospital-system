export const dailyQueries = [
  { d: "Mon", queries: 142, refused: 6 },
  { d: "Tue", queries: 168, refused: 9 },
  { d: "Wed", queries: 154, refused: 5 },
  { d: "Thu", queries: 191, refused: 11 },
  { d: "Fri", queries: 218, refused: 8 },
  { d: "Sat", queries: 96, refused: 3 },
  { d: "Sun", queries: 78, refused: 4 },
];

export const lookupTimeTrend = [
  { w: "W1", manual: 6.4, copilot: 3.1 },
  { w: "W2", manual: 6.2, copilot: 2.8 },
  { w: "W3", manual: 6.5, copilot: 2.6 },
  { w: "W4", manual: 6.1, copilot: 2.4 },
  { w: "W5", manual: 6.3, copilot: 2.3 },
  { w: "W6", manual: 6.0, copilot: 2.2 },
];

export const topSources = [
  { name: "ACC/AHA Guidelines", uses: 412 },
  { name: "Hospital Formulary", uses: 318 },
  { name: "HFrEF GDMT Protocol", uses: 256 },
  { name: "Sepsis Bundle", uses: 198 },
  { name: "DOAC Renal Dosing", uses: 174 },
  { name: "Stroke Workflow", uses: 121 },
];

export const latencyP95 = [
  { d: "Mon", ms: 1180 },
  { d: "Tue", ms: 1240 },
  { d: "Wed", ms: 1090 },
  { d: "Thu", ms: 1320 },
  { d: "Fri", ms: 1260 },
  { d: "Sat", ms: 980 },
  { d: "Sun", ms: 940 },
];

export const citationCoverage = [
  { name: "Cited", value: 946 },
  { name: "Refused", value: 46 },
  { name: "Uncited", value: 12 },
];

export const sparkQueries = [42, 51, 38, 65, 58, 72, 84];
export const sparkLatency = [1.2, 1.1, 1.3, 1.0, 0.9, 1.0, 0.95];
export const sparkDocs = [12200, 12380, 12510, 12640, 12720, 12800, 12842];
export const sparkCited = [91, 92, 93, 92, 94, 94, 95];
