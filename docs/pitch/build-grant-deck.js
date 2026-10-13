// Grant application deck generator (English). Gerekenler: npm i pptxgenjs react react-dom react-icons sharp; PPTX_SKILL_DIR = pptx skill klasörü (apply_theme.js için)
// Çalıştır: PPTX_SKILL_DIR=... node build-deck.js
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require(process.env.PPTX_SKILL_DIR + "/scripts/apply_theme.js");

const THEME = {
  name: "4PC Grant",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0F1222", lt1: "FFFFFF", dk2: "1C2244", lt2: "F2F4FB",
    accent1: "FFB020", accent2: "2DD4BF", accent3: "8B92FF",
    accent4: "FF6B6B", accent5: "9AA3C7", accent6: "5B6390",
    hlink: "8B92FF", folHlink: "9AA3C7",
  },
};
const HEX = { ink: "0F1222", panel: "1C2244", pale: "F2F4FB", amber: "FFB020", teal: "2DD4BF", indigo: "8B92FF", coral: "FF6B6B", muted: "9AA3C7", slate: "5B6390", white: "FFFFFF" };

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "4-Product One Community — Grant Application Deck";
pres.author = "Ali Çağlar Koçer";
const C = pres.SchemeColor;

const titleBox = { x: 0.6, y: 0.4, w: 8.8, h: 0.95, fontSize: 30, bold: true, align: "left", valign: "top", margin: 0 };
pres.defineSlideMaster({
  title: "DARK", background: { color: HEX.ink },
  objects: [{ placeholder: { options: { name: "title", type: "title", ...titleBox, color: C.background1 }, text: "" } }],
  slideNumber: { x: 9.2, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: HEX.muted },
});
pres.defineSlideMaster({
  title: "LIGHT", background: { color: HEX.pale },
  objects: [{ placeholder: { options: { name: "title", type: "title", ...titleBox, color: C.text1 }, text: "" } }],
  slideNumber: { x: 9.2, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: HEX.slate },
});
pres.defineSlideMaster({
  title: "COVER", background: { color: HEX.ink },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.35, w: 6.4, h: 1.9, fontSize: 38, bold: true, align: "left", valign: "top", margin: 0, color: C.background1 }, text: "" } }],
});

async function icon(name, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
const T = (s, text, o) => s.addText(text, { isTextBox: true, margin: 0, fontFace: "Calibri", ...o });
async function iconBadge(s, name, x, y, d, bg, fg, objectName) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg }, line: { type: "none" }, objectName: objectName + " badge" });
  const p = d * 0.5;
  s.addImage({ data: await icon(name, fg), x: x + (d - p) / 2, y: y + (d - p) / 2, w: p, h: p, objectName: objectName + " icon" });
}
function card(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { type: "none" }, objectName: name });
}
function chip(s, text, x, y, w, color, textColor = HEX.ink) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.28, rectRadius: 0.14, fill: { color }, line: { color, width: 0 }, objectName: "chip " + text });
  T(s, text, { x, y, w, h: 0.28, fontSize: 10, bold: true, color: textColor, align: "center", valign: "middle" });
}


const OUT = "4-product-one-community-grant-deck.pptx";
(async () => {
  let s;
  // 1 — Cover
  s = pres.addSlide({ masterName: "COVER" });
  s.addShape(pres.shapes.OVAL, { x: 6.3, y: -0.9, w: 5.2, h: 5.2, fill: { color: HEX.teal, transparency: 84 }, line: { type: "none" }, objectName: "glow 1" });
  s.addShape(pres.shapes.OVAL, { x: 7.4, y: 2.6, w: 3.6, h: 3.6, fill: { color: HEX.amber, transparency: 80 }, line: { type: "none" }, objectName: "glow 2" });
  T(s, "4-PRODUCT ONE COMMUNITY", { x: 0.7, y: 0.75, w: 6, h: 0.3, fontSize: 12, bold: true, color: HEX.amber, charSpacing: 4 });
  s.addText("Real experience for students, before they graduate.", { placeholder: "title" });
  T(s, "An open-source ecosystem that turns university students into proven, employable talent.", { x: 0.7, y: 3.55, w: 5.8, h: 0.8, fontSize: 18, color: HEX.muted, valign: "top" });
  chip(s, "GRANT APPLICATION · €31,000", 0.7, 4.6, 2.6, HEX.amber);
  chip(s, "Apache-2.0 · Open source", 3.45, 4.6, 2.1, HEX.panel, HEX.white);
  s.addNotes("Open with the impact, not the product: students graduate without proof of real work; we change that while they are still studying.");

  // 2 — Problem
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("A generation is locked out of its first job", { placeholder: "title" });
  const st = [
    ["28.2%", "of people aged 15–34 in Türkiye are neither in education nor employment (about 6.8 million, Q1 2026)", HEX.coral],
    ["~16%", "youth unemployment (ages 15–24) in 2025", HEX.amber],
    ["6.7M", "students enrolled in Turkish higher education (2024–25, incl. open and distance learning)", HEX.teal],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 3.0;
    card(s, x, 1.55, 2.8, 2.55, HEX.panel, "stat card " + i);
    T(s, st[i][0], { x: x + 0.25, y: 1.7, w: 2.3, h: 0.9, fontSize: 40, bold: true, fontFace: "Cambria", color: st[i][2], valign: "middle" });
    T(s, st[i][1], { x: x + 0.25, y: 2.65, w: 2.3, h: 1.35, fontSize: 12, color: HEX.white, valign: "top" });
  }
  T(s, [
    { text: "Employers ask for experience. Students have no way to get it. ", options: { color: HEX.white } },
    { text: "AI is now automating the entry-level tasks that used to be the first rung.", options: { color: HEX.amber } },
  ], { x: 0.6, y: 4.3, w: 8.8, h: 0.7, fontSize: 16, bold: true, valign: "top" });
  T(s, "Sources: TurkStat via press reports (NEET, Q1 2026); World Bank-based series (youth unemployment 2025); YÖK 2024–25 data.", { x: 0.6, y: 5.0, w: 8.2, h: 0.25, fontSize: 10, color: HEX.muted });
  s.addNotes("Verify each figure against the original TurkStat, World Bank and YÖK publications before submitting; age bands differ between series (15–24, 15–34), so they are not directly comparable.");

  // 3 — Answer
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("Four products, one student journey", { placeholder: "title" });
  const prods = [
    ["FIRST", "Build together", "Open-source projects, team building, visible contributions.", "LIVE", HEX.teal, "FaUsers"],
    ["STEP", "Earn first income", "Paid marketplace for verified students with payment protection.", "BUILT · PRE-LAUNCH", HEX.amber, "FaBriefcase"],
    ["INTO", "Learn from mentors", "Paid and volunteer mentoring for projects and careers.", "PILOT PLANNED", HEX.indigo, "FaLightbulb"],
    ["PATH", "Solve real problems", "Competitions on real organisational challenges.", "PILOT PLANNED", HEX.muted, "FaFlagCheckered"],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 2.2;
    card(s, x, 1.55, 2.05, 3.35, HEX.white, "product card " + prods[i][0]);
    await iconBadge(s, prods[i][5], x + 0.25, 1.8, 0.62, prods[i][4], HEX.ink, prods[i][0]);
    T(s, prods[i][0], { x: x + 0.25, y: 2.55, w: 1.6, h: 0.4, fontSize: 22, bold: true, fontFace: "Cambria", color: HEX.ink });
    T(s, prods[i][1], { x: x + 0.25, y: 2.95, w: 1.6, h: 0.3, fontSize: 13, bold: true, color: HEX.slate });
    T(s, prods[i][2], { x: x + 0.25, y: 3.3, w: 1.6, h: 1.05, fontSize: 12, color: HEX.slate, valign: "top" });
    chip(s, prods[i][3], x + 0.2, 4.45, 1.65, prods[i][4]);
  }
  s.addNotes("Each product produces evidence that feeds the next: contributions become portfolio, portfolio becomes paid work, mentoring accelerates both.");

  // 4 — Proof
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("The community already exists", { placeholder: "title" });
  const pr = [["200+", "community members"], ["100+", "approved contributors"], ["4", "product tracks"], ["Apache-2.0", "open-source licence"]];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 2.2;
    T(s, pr[i][0], { x, y: 1.5, w: 2.0, h: 0.8, fontSize: i === 3 ? 22 : 40, bold: true, fontFace: "Cambria", color: HEX.amber, valign: "middle" });
    T(s, pr[i][1], { x, y: 2.3, w: 2.0, h: 0.4, fontSize: 13, color: HEX.muted, valign: "top" });
  }
  card(s, 0.6, 3.0, 4.3, 2.0, HEX.panel, "live panel");
  T(s, "FIRST — implemented", { x: 0.85, y: 3.12, w: 3.8, h: 0.3, fontSize: 14, bold: true, color: HEX.teal });
  T(s, ["Google and GitHub sign-in", "GitHub repository linking", "Project listings, applications, invitations", "Teams and task discovery"].map((t, i, a) => ({ text: t, options: { breakLine: i < a.length - 1 } })), { x: 0.85, y: 3.5, w: 3.9, h: 1.4, fontSize: 13, color: HEX.white, valign: "top", paraSpaceAfter: 4 });
  card(s, 5.1, 3.0, 4.3, 2.0, HEX.panel, "step panel");
  T(s, "STEP — built, pre-launch", { x: 5.35, y: 3.12, w: 3.8, h: 0.3, fontSize: 14, bold: true, color: HEX.amber });
  T(s, ["Backend, web app and desktop work tracker", "Credit and escrow-style payment logic", "Awaiting company setup and live payment provider"].map((t, i, a) => ({ text: t, options: { breakLine: i < a.length - 1 } })), { x: 5.35, y: 3.5, w: 3.9, h: 1.4, fontSize: 13, color: HEX.white, valign: "top", paraSpaceAfter: 4 });
  s.addNotes("This is the traction slide: a real community and working software exist before any grant money. The grant moves FIRST and STEP from built to operating and opens INTO and PATH as pilots.");

  // 5 — Impact model
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("How the grant becomes impact", { placeholder: "title" });
  const cols = [
    ["INPUTS", "€31,000 grant\n400 hours of team work\nExisting FIRST and STEP code\n200+ member community", HEX.slate],
    ["ACTIVITIES", "Launch FIRST community\nMake STEP legally and financially ready\nRun INTO mentoring pilot\nOrganise first PATH challenge", HEX.indigo],
    ["OUTCOMES", "Students build a verified work history\nFirst paid assignments for students\nMentor access beyond personal networks\nEmployers see real work", HEX.teal],
    ["LONG-TERM IMPACT", "Lower barrier to a first job\nStudents ready for industry on graduation\nA reusable open-source model", HEX.amber],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 2.2;
    card(s, x, 1.55, 2.05, 3.4, HEX.white, "impact col " + i);
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: 1.75, w: 0.34, h: 0.34, fill: { color: cols[i][2] }, line: { type: "none" }, objectName: "impact dot " + i });
    T(s, cols[i][0], { x: x + 0.65, y: 1.75, w: 1.35, h: 0.34, fontSize: 11, bold: true, color: HEX.ink, valign: "middle" });
    T(s, cols[i][1].split("\n").map((t, k, a) => ({ text: t, options: { breakLine: k < a.length - 1 } })), { x: x + 0.2, y: 2.3, w: 1.7, h: 2.5, fontSize: 12, color: HEX.slate, valign: "top", paraSpaceAfter: 6 });
  }
  s.addNotes("A simple theory of change: the budget buys operational readiness and pilots; pilots produce verified experience; verified experience lowers the barrier to a first job.");

  // 6 — Indicators
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("How we will measure impact", { placeholder: "title" });
  const ind = [
    ["FIRST", "Active projects, accepted contributions, teams formed", HEX.teal, "FaUsers"],
    ["STEP", "Student pilot assignments completed, first-time student earners, employer repeat use", HEX.amber, "FaBriefcase"],
    ["INTO", "Mentors onboarded, sessions and project reviews held, mentee feedback", HEX.indigo, "FaLightbulb"],
    ["PATH", "Participants, solutions submitted, organisations and problem statements", HEX.coral, "FaFlagCheckered"],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * 4.4, y = 1.5 + Math.floor(i / 2) * 1.6;
    card(s, x, y, 4.2, 1.45, HEX.panel, "indicator card " + i);
    await iconBadge(s, ind[i][3], x + 0.25, y + 0.38, 0.68, ind[i][2], HEX.ink, "indicator " + i);
    T(s, ind[i][0], { x: x + 1.15, y: y + 0.18, w: 2.9, h: 0.35, fontSize: 16, bold: true, color: HEX.white });
    T(s, ind[i][1], { x: x + 1.15, y: y + 0.58, w: 2.9, h: 0.8, fontSize: 12, color: HEX.muted, valign: "top" });
  }
  T(s, "Results are reported at the end of each phase; all product code and findings stay public.", { x: 0.6, y: 4.8, w: 8.8, h: 0.35, fontSize: 13, bold: true, color: HEX.amber });
  s.addNotes("Numeric targets can be added here once the programme's reporting format is known.");

  // 7 — Market
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("A large, under-served market", { placeholder: "title" });
  const mk = [
    ["6.7M", "students in Turkish higher education — the primary audience (YÖK, 2024–25)", HEX.teal],
    ["$6–8B", "global freelance-platform market in 2025 across published estimates", HEX.amber],
    ["$16–30B", "projected for 2030–2034 by the same research firms", HEX.indigo],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 3.0;
    card(s, x, 1.55, 2.8, 2.4, HEX.white, "market card " + i);
    T(s, mk[i][0], { x: x + 0.25, y: 1.7, w: 2.3, h: 0.9, fontSize: 36, bold: true, fontFace: "Cambria", color: HEX.ink, valign: "middle" });
    s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: 2.65, w: 0.2, h: 0.2, fill: { color: mk[i][2] }, line: { type: "none" }, objectName: "market dot " + i });
    T(s, mk[i][1], { x: x + 0.25, y: 2.95, w: 2.35, h: 0.95, fontSize: 12, color: HEX.slate, valign: "top" });
  }
  T(s, "No mainstream platform combines student verification, open-source collaboration, mentoring and employer-visible work history in one journey. That combination is our focus.", { x: 0.6, y: 4.15, w: 8.8, h: 0.7, fontSize: 15, bold: true, color: HEX.ink, valign: "top" });
  T(s, "Estimates vary by firm and scope (Mordor Intelligence, The Business Research Company, Grand View Research, Fortune Business Insights).", { x: 0.6, y: 4.95, w: 8.2, h: 0.25, fontSize: 10, color: HEX.slate });
  s.addNotes("Present the global figure as context, not as our revenue claim. Our near-term reach is Turkish students; the open-source model is reusable elsewhere.");

  // 8 — Public good
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Built as a public good", { placeholder: "title" });
  const pg = [
    ["FaCodeBranch", "Open source", "Apache-2.0 licence; anyone can reuse, adapt and contribute."],
    ["FaEye", "Transparency", "Product and technical decisions are documented in the repository."],
    ["FaShieldAlt", "Security first", "Authentication, payments and private data designed for safety before speed."],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 3.0;
    card(s, x, 1.6, 2.8, 3.1, HEX.panel, "pg card " + i);
    await iconBadge(s, pg[i][0], x + 0.3, 1.85, 0.75, HEX.amber, HEX.ink, "pg " + i);
    T(s, pg[i][1], { x: x + 0.3, y: 2.8, w: 2.2, h: 0.4, fontSize: 18, bold: true, color: HEX.white });
    T(s, pg[i][2], { x: x + 0.3, y: 3.3, w: 2.25, h: 1.3, fontSize: 13, color: HEX.muted, valign: "top" });
  }
  s.addNotes("For funders that care about openness: the software, the decision records and the community process are all public.");

  // 9 — Budget overview
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("€31,000 across four phases", { placeholder: "title" });
  const phases = [["FIRST", 1000, HEX.teal], ["STEP", 15000, HEX.amber], ["INTO", 10000, HEX.indigo], ["PATH", 5000, HEX.coral]];
  phases.forEach((p, i) => {
    const y = 1.6 + i * 0.85, bw = 3.7 * p[1] / 15000;
    T(s, p[0], { x: 0.6, y, w: 0.9, h: 0.55, fontSize: 16, bold: true, fontFace: "Cambria", color: HEX.ink, valign: "middle" });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1.5, y: y + 0.05, w: Math.max(bw, 0.2), h: 0.45, rectRadius: 0.08, fill: { color: p[2] }, line: { type: "none" }, objectName: "bar " + p[0] });
    T(s, "€" + p[1].toLocaleString("en-US"), { x: 1.5 + Math.max(bw, 0.2) + 0.15, y, w: 1.0, h: 0.55, fontSize: 14, bold: true, color: HEX.ink, valign: "middle" });
  });
  card(s, 6.3, 1.5, 3.1, 3.35, HEX.white, "split card");
  T(s, "Where it goes", { x: 6.55, y: 1.65, w: 2.6, h: 0.3, fontSize: 12, bold: true, color: HEX.slate });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.55, y: 2.05, w: 2.6 * 8000 / 31000, h: 0.4, fill: { color: HEX.amber }, line: { type: "none" }, objectName: "own work share" });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.55 + 2.6 * 8000 / 31000, y: 2.05, w: 2.6 * 23000 / 31000, h: 0.4, fill: { color: HEX.slate }, line: { type: "none" }, objectName: "external share" });
  T(s, [
    { text: "€8,000", options: { bold: true, color: HEX.amber, breakLine: true, fontSize: 22 } },
    { text: "Own work: 400 h at €20/h", options: { color: HEX.ink, breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "€23,000", options: { bold: true, color: HEX.slate, breakLine: true, fontSize: 22 } },
    { text: "Company, professional services, hosting, outreach, mentor honoraria, incentives and prizes", options: { color: HEX.ink } },
  ], { x: 6.55, y: 2.65, w: 2.6, h: 2.1, fontSize: 12, valign: "top" });
  s.addNotes("FIRST and STEP already exist as software, so most development money refines and integrates rather than builds from scratch. The largest share goes to making STEP legally and financially operable.");

  // 10 — Budget FIRST + STEP
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Where the money goes: FIRST and STEP", { placeholder: "title" });
  const line = (o, t, v) => [{ text: t, options: { color: HEX.white } }, { text: "  " + v, options: { bold: true, color: HEX.amber, breakLine: true } }];
  card(s, 0.6, 1.4, 3.6, 3.6, HEX.panel, "first budget");
  T(s, "FIRST · €1,000", { x: 0.85, y: 1.55, w: 3.1, h: 0.35, fontSize: 17, bold: true, color: HEX.teal });
  T(s, [].concat(line(0, "Development and launch prep", "€400"), line(0, "Hosting and operations", "€300"), line(0, "Initial outreach", "€300")), { x: 0.85, y: 2.05, w: 3.2, h: 1.7, fontSize: 13, valign: "top", paraSpaceAfter: 8 });
  T(s, "Makes FIRST available to an initial community and supports early-user recruitment.", { x: 0.85, y: 3.9, w: 3.2, h: 1.0, fontSize: 12, color: HEX.muted, valign: "top" });
  card(s, 4.4, 1.4, 5.0, 3.6, HEX.panel, "step budget");
  T(s, "STEP · €15,000", { x: 4.65, y: 1.55, w: 4.5, h: 0.35, fontSize: 17, bold: true, color: HEX.amber });
  T(s, [].concat(
    line(0, "Company formation, accounting, admin", "€2,000"),
    line(0, "Tax, invoicing, contracts, payment-provider requirements", "€4,000"),
    line(0, "Development and payment integration", "€4,000"),
    line(0, "Student and employer pilot incentives", "€3,000"),
    line(0, "Hosting, storage, operations", "€2,000")), { x: 4.65, y: 2.05, w: 4.55, h: 2.2, fontSize: 13, valign: "top", paraSpaceAfter: 6 });
  T(s, "Establishes the organisational and financial basis to operate the marketplace; final arrangements follow professional advice and provider requirements.", { x: 4.65, y: 4.2, w: 4.55, h: 0.75, fontSize: 12, color: HEX.muted, valign: "top" });
  s.addNotes("STEP is the largest phase because paid work between students and employers needs a legal entity, tax and invoicing setup, and a payment provider.");

  // 11 — Budget INTO + PATH
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Where the money goes: INTO and PATH", { placeholder: "title" });
  card(s, 0.6, 1.4, 4.3, 3.6, HEX.panel, "into budget");
  T(s, "INTO · €10,000", { x: 0.85, y: 1.55, w: 3.8, h: 0.35, fontSize: 17, bold: true, color: HEX.indigo });
  T(s, [].concat(
    line(0, "Mentoring workflows (development)", "€2,400"),
    line(0, "Mentor honoraria for pilot sessions and reviews", "€4,000"),
    line(0, "Mentor recruitment and onboarding", "€1,600"),
    line(0, "Hosting, scheduling, communication", "€2,000")), { x: 0.85, y: 2.05, w: 3.9, h: 2.1, fontSize: 13, valign: "top", paraSpaceAfter: 6 });
  T(s, "Recruits an initial mentor group and pilots project mentoring and personal-development support.", { x: 0.85, y: 4.15, w: 3.9, h: 0.8, fontSize: 12, color: HEX.muted, valign: "top" });
  card(s, 5.1, 1.4, 4.3, 3.6, HEX.panel, "path budget");
  T(s, "PATH · €5,000", { x: 5.35, y: 1.55, w: 3.8, h: 0.35, fontSize: 17, bold: true, color: HEX.coral });
  T(s, [].concat(
    line(0, "Competition prototype (development)", "€1,200"),
    line(0, "Participant prizes and pilot incentives", "€2,000"),
    line(0, "Outreach to companies and evaluators", "€1,000"),
    line(0, "Hosting and evaluation resources", "€800")), { x: 5.35, y: 2.05, w: 3.9, h: 2.1, fontSize: 13, valign: "top", paraSpaceAfter: 6 });
  T(s, "Defines the format and runs a small first challenge to learn problem statements and evaluation criteria.", { x: 5.35, y: 4.15, w: 3.9, h: 0.8, fontSize: 12, color: HEX.muted, valign: "top" });
  s.addNotes("These are pilots. They validate the model before broader development; eligibility of prizes and incentives will be checked against the programme rules before spending.");

  // 12 — Work plan
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("Work plan and effort", { placeholder: "title" });
  const hd = (t, al = "left") => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: HEX.ink }, align: al, fontSize: 13 } });
  const cl = (t, al = "left", b = false) => ({ text: t, options: { color: HEX.ink, align: al, bold: b, fontSize: 13 } });
  s.addTable([
    [hd("Phase"), hd("Planned work"), hd("Effort", "right")],
    [cl("FIRST", "left", true), cl("Refinements, deployment configuration, launch preparation"), cl("20 h", "right")],
    [cl("STEP", "left", true), cl("Marketplace refinement, payment integration, administrative coordination, pilot preparation"), cl("200 h", "right")],
    [cl("INTO", "left", true), cl("Mentoring workflows, mentor onboarding, pilot coordination"), cl("120 h", "right")],
    [cl("PATH", "left", true), cl("Competition specification, prototype, first challenge coordination"), cl("60 h", "right")],
    [cl("Total", "left", true), cl("50 eight-hour days · €20/h (€160/day) · €8,000"), cl("400 h", "right", true)],
  ], { x: 0.6, y: 1.5, w: 8.8, colW: [1.3, 6.2, 1.3], rowH: [0.4, 0.5, 0.65, 0.5, 0.5, 0.45], fontFace: "Calibri", border: { type: "solid", color: "D9DCEB", pt: 0.75 }, fill: { color: HEX.white }, valign: "middle", objectName: "work plan table" });
  T(s, "Effort covers the applicant's own work only. Accounting, professional advice and mentor services are budgeted separately. Elapsed time also depends on provider onboarding and participant availability.", { x: 0.6, y: 4.5, w: 8.8, h: 0.6, fontSize: 12, color: HEX.slate, valign: "top" });
  s.addNotes("No separate monthly salary is included. Figures are planning estimates, not supplier quotations.");

  // 13 — Team
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("The team: ACK Techs, Istanbul", { placeholder: "title" });
  const team = [
    ["Ali Çağlar Koçer", "Founder · Product & AI Systems Architect"],
    ["Doğukan Taha Tıraş", "Co-Founder · Frontend & AI Lead"],
    ["Batuhan Evleksiz", "Full-Stack Developer & AI"],
    ["Ayselin Aydoğdu", "AI Engineer"],
    ["Ayşe Sena Bağdat", "AI & Data · Cybersecurity"],
    ["Mehmet Yıldız", "AI Engineer"],
    ["Aynur Oruçoğlu", "AI & Full-Stack Developer"],
  ];
  const accents = [HEX.amber, HEX.teal, HEX.indigo, HEX.coral, HEX.teal, HEX.indigo, HEX.amber];
  for (let i = 0; i < 7; i++) {
    const row = i < 4 ? 0 : 1, col = i < 4 ? i : i - 4;
    const x = 0.6 + col * 2.2, y = 1.5 + row * 1.7;
    card(s, x, y, 2.05, 1.55, HEX.white, "team card " + i);
    const ini = team[i][0].split(" ").map((w) => w[0]).slice(0, 2).join("");
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.18, w: 0.56, h: 0.56, fill: { color: accents[i] }, line: { type: "none" }, objectName: "avatar " + i });
    T(s, ini, { x: x + 0.2, y: y + 0.18, w: 0.56, h: 0.56, fontSize: 14, bold: true, color: HEX.ink, align: "center", valign: "middle" });
    T(s, team[i][0], { x: x + 0.2, y: y + 0.8, w: 1.75, h: 0.3, fontSize: 13, bold: true, color: HEX.ink });
    T(s, team[i][1], { x: x + 0.2, y: y + 1.08, w: 1.75, h: 0.42, fontSize: 10, color: HEX.slate, valign: "top" });
  }
  card(s, 7.25, 3.2, 2.15, 1.55, HEX.ink, "team note");
  T(s, "Seven-person product and AI team in Istanbul.\nack-techs.com", { x: 7.45, y: 3.3, w: 1.8, h: 1.35, fontSize: 12, color: HEX.white, valign: "middle" });
  s.addNotes("Roles are taken from the team's public website (ack-techs.com). Add one line on relevant prior delivery if the form allows.");

  // 14 — Risks
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Risks we have planned for", { placeholder: "title" });
  const rk = [
    ["Payment-provider and company onboarding takes longer than planned", "Phased delivery; pilot credits first; professional support is budgeted."],
    ["STEP is not yet verified in live operation", "Integration and test work is funded; launch only after live provider verification."],
    ["Mentors and companies are slow to join", "Honoraria, active outreach and a small first pilot before scaling."],
    ["Incentive or prize costs may not be eligible", "Eligibility is checked against programme rules before any spending."],
  ];
  for (let i = 0; i < 4; i++) {
    const y = 1.45 + i * 0.9;
    card(s, 0.6, y, 8.8, 0.78, HEX.panel, "risk row " + i);
    T(s, rk[i][0], { x: 0.85, y, w: 4.1, h: 0.78, fontSize: 13, bold: true, color: HEX.white, valign: "middle" });
    T(s, rk[i][1], { x: 5.2, y, w: 4.0, h: 0.78, fontSize: 13, color: HEX.amber, valign: "middle" });
  }
  s.addNotes("Naming risks openly builds trust with a grant committee.");

  // 15 — Close
  s = pres.addSlide({ masterName: "COVER" });
  s.addShape(pres.shapes.OVAL, { x: 6.0, y: -1.1, w: 5.6, h: 5.6, fill: { color: HEX.amber, transparency: 84 }, line: { type: "none" }, objectName: "glow 1" });
  s.addShape(pres.shapes.OVAL, { x: 7.8, y: 2.9, w: 3.4, h: 3.4, fill: { color: HEX.teal, transparency: 82 }, line: { type: "none" }, objectName: "glow 2" });
  s.addText("€31,000 to turn a working community into lasting opportunity.", { placeholder: "title" });
  T(s, "Real experience, proven in public, open to everyone.", { x: 0.7, y: 3.55, w: 5.8, h: 0.6, fontSize: 18, color: HEX.muted, valign: "top" });
  chip(s, "github.com/caglarkc/4-product-one-community", 0.7, 4.5, 3.9, HEX.amber);
  chip(s, "ack-techs.com", 4.75, 4.5, 1.4, HEX.panel, HEX.white);
  s.addNotes("Close with the ask and the single sentence of impact. Contact via ack-techs.com.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("ok");
})();
