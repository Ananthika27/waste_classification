// EcoSort AI project deck. Run:  NODE_PATH=node_modules node build_deck.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const SKILL = "/Users/ananthikagajendran/.claude/skills/synced/3964c1c9-5c18-48c2-84f6-8df2a490b75f_b988af4f-9c59-4fc6-b4d3-b73c76e4dfd6/pptx/scripts/apply_theme.js";
const { applyTheme } = require(SKILL);

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(__dirname, "EcoSort_AI_Project_Presentation.pptx");

// ------------------------------------------------------------------ theme
const GREEN = "2B8A3E", BLUE = "1971C2", GREY = "5F676D", RED = "C92A2A", AMBER = "E67700", TEAL = "0B7285";
const INK = "1B2420", DEEP = "10291D", TINT = "F2F5F2", MUTED = "5C6660", LINE = "DDE3DE", GRID = "E3E8E4";
const THEME = {
  name: "EcoSort",
  headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: INK, lt1: "FFFFFF", dk2: DEEP, lt2: TINT, accent1: GREEN, accent2: BLUE, accent3: GREY,
            accent4: RED, accent5: AMBER, accent6: TEAL, hlink: BLUE, folHlink: GREY },
};
const CAT = { bio: GREEN, rec: BLUE, non: GREY, med: RED };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.333 x 7.5 in
pres.title = "EcoSort AI - Real-Time Waste Classification System";
pres.subject = "21CSE454T Computer Vision";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const FOOT = "EcoSort AI  |  21CSE454T Computer Vision  |  SRM Institute of Science and Technology";

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "TITLE", background: { color: DEEP },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.5, w: 7.3, h: 1.05, fontSize: 58,
    bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } }],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.13, h: 0.85, fontSize: 30,
      bold: true, color: C.text2, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: FOOT, options: { x: 0.6, y: 7.04, w: 9, h: 0.28, fontSize: 10, color: MUTED, margin: 0, valign: "middle" } } },
  ],
  slideNumber: { x: 12.1, y: 7.04, w: 0.63, h: 0.28, fontSize: 10, color: MUTED, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSE", background: { color: DEEP },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 0.6, w: 11.9, h: 0.9, fontSize: 38,
      bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: FOOT, options: { x: 0.6, y: 7.04, w: 9, h: 0.28, fontSize: 10, color: "A9B8AE", margin: 0, valign: "middle" } } },
  ],
});

// ------------------------------------------------------------------ helpers
const T = (s, text, o = {}) => s.addText(text, { isTextBox: true, margin: 0, valign: "top", fontSize: 14, color: C.text1, ...o });

function B(s, items, o = {}) {           // bullets; item = "text" or {b:"Bold lead", t:"rest"}
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    const para = { bullet: { indent: 16 }, paraSpaceAfter: o.gap ?? 6 };
    if (typeof it === "string") runs.push({ text: it, options: { ...para, breakLine: !last } });
    else {
      runs.push({ text: it.b, options: { ...para, bold: true } });
      runs.push({ text: " " + it.t, options: { breakLine: !last } });
    }
  });
  const { gap, ...rest } = o;
  T(s, runs, rest);
}

const card = (s, x, y, w, h, name, fill = C.background2) =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill },
    line: { color: LINE, width: 0.75 }, objectName: name });

function disc(s, n, x, y, d, fill = DEEP, size = 16) {
  s.addText(String(n), { x, y, w: d, h: d, shape: pres.shapes.OVAL, fill: { color: fill }, color: "FFFFFF", bold: true,
    fontSize: size, align: "center", valign: "middle", margin: 0, objectName: "Step " + n });
}

function table(s, rows, { x, y, w, colW, fontSize = 13, rowH = 0.42, align = [] }) {
  const cell = (c, ci, base) => typeof c === "string"
    ? { text: c, options: base(ci) } : { text: c.text, options: { ...base(ci), ...c.options } };
  const head = rows[0].map((c, ci) => cell(c, ci, (i) => ({ bold: true, fontSize, color: "FFFFFF", fill: { color: DEEP },
    valign: "middle", align: align[i] || "left" })));
  const body = rows.slice(1).map((r, ri) => r.map((c, ci) => cell(c, ci, (i) => ({ fontSize, color: INK,
    fill: { color: ri % 2 ? TINT : "FFFFFF" }, valign: "middle", align: align[i] || "left" }))));
  s.addTable([head, ...body], { x, y, w, colW, rowH, border: { type: "solid", pt: 0.75, color: LINE },
    margin: [0.05, 0.1, 0.05, 0.1], objectName: "Table" });
}

const chartBase = {
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 12, catAxisLabelColor: MUTED, valAxisLabelColor: MUTED,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  legendFontFace: "+mn-lt", titleFontFace: "+mn-lt", valGridLine: { color: GRID, size: 0.75 },
  catGridLine: { style: "none" }, dataLabelFontSize: 12, dataLabelColor: INK, legendFontSize: 12, legendColor: INK,
  showTitle: true, titleFontSize: 14, titleColor: INK,
};
const chart = (s, type, data, o) => s.addChart(type, data, { ...chartBase, ...o });

function stat(s, x, y, w, h, big, label, cap) {
  card(s, x, y, w, h, "Stat tile");
  T(s, big, { x: x + 0.2, y: y + 0.18, w: w - 0.4, h: 0.85, fontSize: 42, bold: true, color: C.text2, fontFace: "+mj-lt", valign: "middle" });
  T(s, label, { x: x + 0.2, y: y + 1.05, w: w - 0.4, h: 0.32, fontSize: 15, bold: true });
  T(s, cap, { x: x + 0.2, y: y + 1.4, w: w - 0.4, h: h - 1.5, fontSize: 12, color: MUTED });
}
const note = (s, text) => T(s, text, { x: 0.6, y: 6.62, w: 12.1, h: 0.3, fontSize: 11, color: MUTED, italic: true });

let sectionOpen = null;
function content(section, title, notes) {
  if (section !== sectionOpen) { pres.addSection({ title: section }); sectionOpen = section; }
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addNotes(notes);
  return s;
}

// ================================================================== 1. TITLE
pres.addSection({ title: "Introduction" }); sectionOpen = "Introduction";
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  T(s, "21CSE454T  -  COMPUTER VISION", { x: 0.7, y: 0.65, w: 7.3, h: 0.35, fontSize: 14, bold: true, color: "A9D8B5" });
  s.addText("EcoSort AI", { placeholder: "title" });
  T(s, "Real-Time Waste Classification System using Vision-Language Models", { x: 0.7, y: 2.6, w: 7.3, h: 1.0, fontSize: 24, color: "FFFFFF" });
  T(s, "Submitted by", { x: 0.7, y: 3.8, w: 7.3, h: 0.3, fontSize: 14, italic: true, color: "C9D6CD" });
  T(s, [1, 2, 3, 4].map((n, i) => ({ text: `[Student name ${n}]     [Register No.]`, options: { breakLine: i < 3 } })),
    { x: 0.7, y: 4.15, w: 7.3, h: 1.25, fontSize: 15, bold: true, color: "FFFFFF", paraSpaceAfter: 3 });
  T(s, "Under the guidance of", { x: 0.7, y: 5.5, w: 7.3, h: 0.3, fontSize: 14, italic: true, color: "C9D6CD" });
  T(s, [{ text: "[Guide name]", options: { bold: true, fontSize: 15, breakLine: true } },
        { text: "[Designation], Department of Computing Technologies", options: { fontSize: 12 } }],
    { x: 0.7, y: 5.82, w: 7.3, h: 0.6, color: "FFFFFF" });
  T(s, [{ text: "DEPARTMENT OF COMPUTING TECHNOLOGIES, COLLEGE OF ENGINEERING AND TECHNOLOGY", options: { breakLine: true } },
        { text: "SRM INSTITUTE OF SCIENCE AND TECHNOLOGY, KATTANKULATHUR - 603 203  |  NOVEMBER 2026" }],
    { x: 0.7, y: 6.62, w: 7.6, h: 0.5, fontSize: 10.5, bold: true, color: "C9D6CD" });
  const tiles = [["Biodegradable", "food scraps, peels, leaves", CAT.bio], ["Recyclable", "paper, books, bottles, cans", CAT.rec],
                 ["Non-recyclable", "wrappers, cloth, leather, thermocol", CAT.non], ["Medical waste", "tablet strips, syringes, masks", CAT.med]];
  tiles.forEach(([name, ex, col], i) => {
    const x = 8.65 + (i % 2) * 2.2, y = 1.75 + Math.floor(i / 2) * 2.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.05, h: 2.05, rectRadius: 0.1, fill: { color: col }, line: { color: col }, objectName: "Category tile " + name });
    T(s, name, { x: x + 0.18, y: y + 0.2, w: 1.7, h: 0.6, fontSize: 18, bold: true, color: "FFFFFF", fontFace: "+mj-lt" });
    T(s, ex, { x: x + 0.18, y: y + 1.0, w: 1.7, h: 0.9, fontSize: 13, color: "FFFFFF" });
  });
  s.addNotes("Introduce the project: EcoSort AI sorts a waste item shown to a camera into four disposal categories - biodegradable, recyclable, non-recyclable and medical waste - and says 'Unknown' when it is not sure. It runs in real time in a web browser. Fill in team names, register numbers and the guide's name on this slide before presenting.");
}

// ================================================================== 2. EXEC SUMMARY
{
  const s = content("Introduction", "Executive summary",
    "The four numbers on top are the headline results, all measured on photos the model never saw during training. 98.7 percent on 3,308 test images; 96.7 percent on real landfill photographs, which is the hard case; zero ordinary items sent to the medical bin; and about 21 milliseconds per image so it works live. The three blocks below say what we built, how, and the main finding: accuracy on clean dataset photos does not predict real-world accuracy.");
  const w = 2.85, g = (12.13 - 4 * w) / 3;
  [["98.7%", "Test accuracy", "3,308 unseen images, 4 categories"],
   ["96.7%", "Real landfill photos", "RealWaste, 690 unseen images"],
   ["0", "False medical alarms", "among 2,998 non-medical test images"],
   ["21 ms", "Per image", "model time on an Apple-silicon laptop"]]
    .forEach((d, i) => stat(s, 0.6 + i * (w + g), 1.45, w, 1.95, ...d));
  const cols = [
    ["What we built", "A camera-based system that sorts an item into Biodegradable, Recyclable, Non-recyclable or Medical waste, or answers Unknown when it is unsure. It runs in a browser web app with live camera, image upload and a Teach button."],
    ["How it works", "Google's SigLIP 2 vision model turns each image into a 768-number fingerprint. A small trained classifier maps it to the four categories. Training used 21,445 de-duplicated photos from four sources, including real landfill images."],
    ["What we found", "An earlier CNN scored 95.7% on clean photos but only 75.5% (4 categories) on landfill photos. The final model keeps 96.7% on the same images. Testing on real-world photos early is the main lesson."]];
  cols.forEach(([h, t], i) => {
    const x = 0.6 + i * 4.13;
    T(s, h, { x, y: 3.75, w: 3.9, h: 0.4, fontSize: 18, bold: true, color: C.text2, fontFace: "+mj-lt" });
    T(s, t, { x, y: 4.25, w: 3.9, h: 2.4, fontSize: 15 });
  });
}

// ================================================================== 3. PROBLEM + CATEGORIES
{
  const s = content("Introduction", "Problem: waste must be sorted at the source",
    "Explain why this matters. Mixed waste lowers recycling quality and spoils compost. Medical waste such as syringes, tablet strips and masks is a safety risk if it ends up with household waste. Manual sorting is slow and inconsistent. The goal is a camera that names the right bin in real time and admits when it is unsure. On the right are the four categories the system uses - the first three come from the project brief, medical waste was added as the fourth.");
  B(s, [{ b: "Quality:", t: "mixed waste lowers recycling value and contaminates compost." },
        { b: "Safety:", t: "syringes, tablet strips and masks in household waste are a hazard to sanitation workers." },
        { b: "Speed:", t: "manual sorting is slow, inconsistent and tiring." }],
    { x: 0.6, y: 1.5, w: 4.9, h: 3.2, fontSize: 16, gap: 12 });
  card(s, 0.6, 4.85, 4.9, 1.5, "Goal card");
  T(s, [{ text: "Goal", options: { bold: true, breakLine: true, color: C.text2 } },
        { text: "A camera that names the correct bin in real time, and says Unknown when it is not sure." }],
    { x: 0.8, y: 5.0, w: 4.5, h: 1.2, fontSize: 15 });
  const lab = (t, col) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: col } } });
  table(s, [["Category", "Examples"],
    [lab("Biodegradable", CAT.bio), "Food scraps, fruit and vegetable peels, leaves, flowers"],
    [lab("Recyclable", CAT.rec), "Paper, notes, books, cardboard, plastic bottles, metal cans, glass"],
    [lab("Non-recyclable", CAT.non), "Thermocol, chips packets and wrappers, dirty packaging, cloth, leather, shoes"],
    [lab("Medical waste", CAT.med), "Tablet strips, syringes and needles, masks, gloves, medicine bottles, bandages"]],
    { x: 5.9, y: 1.5, w: 6.83, colW: [1.9, 4.93], fontSize: 14, rowH: 0.95 });
}

// ================================================================== 4. OBJECTIVES
{
  const s = content("Introduction", "Objectives and outcomes",
    "Walk through each goal and the measured outcome. The two accuracy goals were set in the project plan at 95 percent and 85 percent; the results are well above them. The medical goal matters most for safety: out of 2,998 ordinary test items none was sent to the medical bin. The Unknown option holds back about one percent of items for manual sorting, and the answers that remain are 99.1 percent correct.");
  table(s, [["Objective", "Goal", "Outcome"],
    ["Accurate 4-category sorting", "95% or more on unseen photos", "98.7% on 3,308 test images (macro-F1 0.988)"],
    ["Work on real-world photos", "85% or more on landfill photos", "96.7% on 690 RealWaste photos never used in training"],
    ["Keep medical waste separate", "No ordinary item sent to the medical bin", "0 false alarms in 2,998 ordinary test items; 97.7% of medical items caught"],
    ["Respond in real time", "Interactive use", "About 21 ms of model time per image"],
    ["Be safe when uncertain", "Defer low-confidence items", "1.0% held as Unknown; the other 99.0% are answered with 99.1% accuracy"],
    ["Adapt to local items", "Learn from user photos", "Teach buttons save labelled photos for the next training run"]],
    { x: 0.6, y: 1.5, w: 12.13, colW: [3.3, 3.6, 5.23], fontSize: 14, rowH: 0.74 });
}

// ================================================================== 5. ARCHITECTURE
{
  const s = content("Introduction", "System architecture",
    "Follow the path of one image. The browser grabs the centre box from the camera or an uploaded file, compresses it and sends it to a small Python server. The SigLIP 2 image encoder converts it to an embedding, the trained classifier gives probabilities for the four categories, and a confidence threshold decides between a category and Unknown. Below the flow: the display smooths results over frames so the label does not flicker, the app explains its answer with a text description, and the Teach button closes the loop by saving corrected photos for retraining.");
  const steps = [["Camera or upload", "Browser, centre box", "384 px JPEG"], ["Web server", "Python, /api/classify", "one image at a time"],
    ["SigLIP 2 encoder", "Vision transformer", "frozen, 768 numbers"], ["Trained classifier", "Logistic regression", "11 classes"],
    ["Category", "Sum of class probabilities", "4 categories"], ["Decision", "Confidence 0.59 or more", "else Unknown"]];
  const bw = 1.75, gap = (12.13 - 6 * bw) / 5;
  steps.forEach(([a, b, c], i) => {
    const x = 0.6 + i * (bw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.55, w: bw, h: 1.75, rectRadius: 0.08, fill: { color: i === 2 || i === 3 ? DEEP : TINT },
      line: { color: LINE, width: 0.75 }, objectName: "Flow step " + (i + 1) });
    const dark = i === 2 || i === 3;
    T(s, a, { x: x + 0.1, y: 1.65, w: bw - 0.2, h: 0.55, fontSize: 15, bold: true, color: dark ? "FFFFFF" : INK, align: "center", valign: "middle" });
    T(s, b, { x: x + 0.1, y: 2.25, w: bw - 0.2, h: 0.5, fontSize: 12, color: dark ? "DDE8E0" : INK, align: "center" });
    T(s, c, { x: x + 0.1, y: 2.78, w: bw - 0.2, h: 0.45, fontSize: 12, color: dark ? "A9D8B5" : MUTED, align: "center" });
    if (i < 5) s.addShape(pres.shapes.LINE, { x: x + bw + 0.04, y: 2.43, w: gap - 0.08, h: 0, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
  });
  const cards = [["Real-time loop", "Results are smoothed over frames (weight 0.4 for the newest frame) so the label does not flicker. Model time is about 21 ms per image."],
    ["Explanation", "The app also shows what the item looks like in words, e.g. \"an empty plastic water bottle\", using 68 text descriptions grouped by category."],
    ["Teach loop", "If an answer is wrong, one click saves the photo under the correct category. The next training run includes it (80% train, 20% validation)."]];
  cards.forEach(([h, t], i) => {
    const x = 0.6 + i * 4.13;
    card(s, x, 3.75, 3.9, 2.65, "Info card " + h);
    T(s, h, { x: x + 0.2, y: 3.92, w: 3.5, h: 0.4, fontSize: 18, bold: true, color: C.text2, fontFace: "+mj-lt" });
    T(s, t, { x: x + 0.2, y: 4.42, w: 3.5, h: 1.9, fontSize: 14 });
  });
}

// ================================================================== 6. DATA SOURCES
{
  const s = content("Data", "Data sources",
    "Four sources were combined. Garbage Classification from Kaggle supplies most of the images. RealWaste is the important one: photographs taken at a real landfill, so it contains clutter, dirt and odd lighting, unlike studio-style dataset photos. TrashNet turned out to be almost entirely contained in the Kaggle set - only 169 of its 2,527 images are new. No public medical-waste image dataset could be downloaded directly, so medical photos came from freely licensed images on Wikimedia Commons, with author and licence recorded for every file.");
  table(s, [["Source", "Images used", "What it contains", "Licence / terms"],
    ["Garbage Classification (Kaggle, 12 folders)", "15,493", "Web photos: battery, biological, cardboard, clothes, three glass colours, metal, paper, plastic, shoes, trash", "See Kaggle dataset page"],
    ["RealWaste (UCI repository)", "4,752", "Photos taken at a real landfill: nine material classes", "CC BY 4.0"],
    ["TrashNet (Stanford)", "169 new", "Single items on a white board; 2,358 of its 2,527 images are already in Garbage Classification", "See GitHub repository"],
    ["Wikimedia Commons medical photos", "1,031", "Syringes and needles, blister packs, masks, gloves, pill bottles, swabs and bandages, ampoules and vials", "Creative Commons, per file (attribution.csv)"],
    [{ text: "Total", options: { bold: true } }, { text: "21,445", options: { bold: true } }, "Unique images after de-duplication", ""]],
    { x: 0.6, y: 1.5, w: 12.13, colW: [3.2, 1.4, 5.2, 2.33], fontSize: 13, rowH: 0.72, align: ["left", "right", "left", "left"] });
  T(s, "Real-world (landfill) photos are included on purpose, so the model is not tuned only to clean, studio-style pictures.",
    { x: 0.6, y: 6.15, w: 12.13, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
}

// ================================================================== 7. DATA PREPARATION
{
  const s = content("Data", "Data preparation and leakage control",
    "Six steps turn raw downloads into a trustworthy dataset. The important idea is leakage control: if a near-copy of a training photo appears in the test set, the accuracy is inflated. We remove exact duplicates with a file hash, group near-duplicates with a perceptual hash, and make every group stay in a single split. The numbers on each card are real counts from the preparation script. Medical photos are added last with their own split because there are far fewer of them.");
  const cards = [
    ["Collect", "22,794 images from the three photo sources."],
    ["Standardise", "Fix EXIF rotation, convert to RGB, resize the shorter side to 288 px."],
    ["Remove exact duplicates", "MD5 file hash: 2,380 files removed, including 3 hashes with conflicting labels. 20,414 unique images remain."],
    ["Group near-duplicates", "256-bit difference hash, Hamming distance 20 or less: 122 groups covering 742 images; each group stays in one split."],
    ["Split 70 / 15 / 15", "Stratified by category, at group level, seed 42: train 14,339, validation 3,077, test 2,998."],
    ["Add medical photos", "1,150 downloaded; a zero-shot filter drops drawings and documents, leaving 1,031. Split 50 / 20 / 30 per item type."]];
  cards.forEach(([h, t], i) => {
    const x = 0.6 + (i % 3) * 4.13, y = 1.45 + Math.floor(i / 3) * 2.5;
    card(s, x, y, 3.9, 2.3, "Prep card " + (i + 1));
    disc(s, i + 1, x + 0.2, y + 0.2, 0.5);
    T(s, h, { x: x + 0.85, y: y + 0.2, w: 2.85, h: 0.5, fontSize: 16, bold: true, valign: "middle", color: C.text2 });
    T(s, t, { x: x + 0.2, y: y + 0.85, w: 3.5, h: 1.35, fontSize: 14 });
  });
  T(s, "Result: no exact or near-duplicate (by this hash) of a training image appears in the validation or test split.",
    { x: 0.6, y: 6.5, w: 12.13, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
}

// ================================================================== 8. MAPPING
{
  const s = content("Data", "From dataset classes to four categories",
    "The classifier is trained on fine-grained classes such as paper, cardboard and glass, and a fixed rule table converts them to the four categories afterwards. That keeps accuracy high and lets us change the rule without retraining. The rules on the right were agreed for this project: paper, notes and books are recyclable; cloth, leather and shoes are non-recyclable; only food, leaves, peels and plant matter are biodegradable. Be upfront that leather goods and handkerchiefs have no dedicated class of their own - they rely on the shoes and clothes images.");
  const lab = (t, col) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: col } } });
  table(s, [["Category", "Dataset classes merged into it"],
    [lab("Biodegradable", CAT.bio), "biological (Garbage-12); Food Organics and Vegetation (RealWaste)"],
    [lab("Recyclable", CAT.rec), "paper, cardboard, plastic, metal, glass (brown, green and white merged), from all photo sources"],
    [lab("Non-recyclable", CAT.non), "trash / Miscellaneous Trash; clothes / Textile Trash; shoes; battery (hazardous, special collection)"],
    [lab("Medical waste", CAT.med), "Wikimedia photos: syringes and needles, blister packs, masks, gloves, pill bottles, swabs and bandages, ampoules and vials"]],
    { x: 0.6, y: 1.5, w: 7.7, colW: [1.9, 5.8], fontSize: 14, rowH: 1.0 });
  card(s, 8.6, 1.5, 4.13, 4.9, "Rules card");
  T(s, "Sorting rules", { x: 8.8, y: 1.65, w: 3.7, h: 0.4, fontSize: 18, bold: true, color: C.text2, fontFace: "+mj-lt" });
  B(s, ["Paper, notes and books go to Recyclable.", "Cloth, leather and shoes go to Non-recyclable.",
        "Only food, leaves, peels and plant matter are Biodegradable.", "Batteries are flagged Non-recyclable: they need a special collection point."],
    { x: 8.8, y: 2.2, w: 3.75, h: 2.6, fontSize: 14, gap: 8 });
  T(s, "Leather goods and handkerchiefs have no class of their own; they rely on the shoes and clothes images.",
    { x: 8.8, y: 5.0, w: 3.75, h: 1.25, fontSize: 13, italic: true, color: MUTED });
}

// ================================================================== 9. SPLITS
{
  const s = content("Data", "Dataset split and class balance",
    "This is the data behind every result. 14,847 images for training, 3,290 for validation where all tuning decisions were made, and 3,308 for the final test, used once. The classes are imbalanced: medical waste is under five percent of the data. We handle that with class-balanced weights in the classifier and by using macro-F1, which treats every category equally, alongside accuracy.");
  chart(s, pres.charts.BAR, [
    { name: "Biodegradable", labels: ["Train", "Validation", "Test"], values: [1284, 274, 274] },
    { name: "Recyclable", labels: ["Train", "Validation", "Test"], values: [6152, 1267, 1270] },
    { name: "Non-recyclable", labels: ["Train", "Validation", "Test"], values: [6903, 1536, 1454] },
    { name: "Medical", labels: ["Train", "Validation", "Test"], values: [508, 213, 310] }],
    { x: 0.6, y: 1.45, w: 6.2, h: 4.9, barDir: "col", barGrouping: "stacked", chartColors: [GREEN, BLUE, GREY, RED],
      showLegend: true, legendPos: "b", title: "Images per split", valAxisLabelFormatCode: "#,##0", barGapWidthPct: 55 });
  table(s, [["Category", "Train", "Val", "Test", "Share"],
    ["Biodegradable", "1,284", "274", "274", "8.5%"], ["Recyclable", "6,152", "1,267", "1,270", "40.5%"],
    ["Non-recyclable", "6,903", "1,536", "1,454", "46.1%"], ["Medical", "508", "213", "310", "4.8%"],
    [{ text: "Total", options: { bold: true } }, { text: "14,847", options: { bold: true } }, { text: "3,290", options: { bold: true } },
     { text: "3,308", options: { bold: true } }, { text: "21,445", options: { bold: true } }]],
    { x: 7.2, y: 1.55, w: 5.53, colW: [1.75, 0.95, 0.85, 0.9, 1.08], fontSize: 13, rowH: 0.5, align: ["left", "right", "right", "right", "right"] });
  B(s, ["Medical waste is only 4.8% of the data, so the classifier uses class-balanced weights.",
        "Macro-F1 (every category counts equally) is reported next to accuracy.",
        "Validation is used for every tuning decision; the test split is used once."],
    { x: 7.2, y: 4.85, w: 5.53, h: 1.7, fontSize: 14, gap: 6 });
}

// ================================================================== 10. MODEL EVOLUTION
{
  const s = content("Approach", "Four model versions, and why we moved on",
    "This is the story of the project. Version 1 used classical computer vision and reached about 73 percent. Version 2, a fine-tuned MobileNetV2, hit 95.7 percent on clean photos, which looked great, but collapsed on real landfill photos. Version 3, ConvNeXt-Tiny, was started but was too slow and stalled under memory pressure, so it was stopped after two epochs and is not counted as a result. Version 4, SigLIP 2 with a small trained classifier, is the final model. Each step was driven by a measured problem, not a guess.");
  const v = [
    ["V1", "Classical vision + Random Forest / SVM", "Otsu segmentation and 149 hand-crafted features.", "73.1% (6 classes)\n64.7% (10 classes)", "Segmentation breaks on clutter; features too weak."],
    ["V2", "MobileNetV2 CNN, fine-tuned", "ImageNet-pretrained, two-phase fine-tuning.", "95.7% clean photos\n75.5% landfill (4 cat.)", "Collapsed on real-world photos (domain shift)."],
    ["V3", "ConvNeXt-Tiny CNN (attempt)", "Larger CNN, 15-epoch recipe on multi-source data.", "93.0% validation\nafter 2 of 15 epochs", "About 8.5 min per epoch; stalled under memory pressure, stopped."],
    ["V4", "SigLIP 2 + linear classifier", "Frozen vision-language encoder, small trained head.", "98.7% test\n96.7% landfill photos", "Selected: accurate, robust, cheap to retrain."]];
  const w = 2.92, g = (12.13 - 4 * w) / 3;
  v.forEach(([tag, name, what, res, why], i) => {
    const x = 0.6 + i * (w + g), final = i === 3;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w, h: 5.0, rectRadius: 0.08, fill: { color: final ? DEEP : TINT },
      line: { color: final ? DEEP : LINE, width: 0.75 }, objectName: "Version card " + tag });
    const fg = final ? "FFFFFF" : INK, sub = final ? "A9D8B5" : MUTED;
    T(s, tag, { x: x + 0.2, y: 1.6, w: 1, h: 0.55, fontSize: 30, bold: true, color: final ? "A9D8B5" : C.text2, fontFace: "+mj-lt" });
    T(s, name, { x: x + 0.2, y: 2.2, w: w - 0.4, h: 0.75, fontSize: 16, bold: true, color: fg });
    T(s, what, { x: x + 0.2, y: 3.0, w: w - 0.4, h: 0.75, fontSize: 13, color: fg });
    T(s, "Result", { x: x + 0.2, y: 3.8, w: w - 0.4, h: 0.25, fontSize: 11, bold: true, color: sub });
    T(s, res, { x: x + 0.2, y: 4.05, w: w - 0.4, h: 0.65, fontSize: 14, bold: true, color: fg });
    T(s, final ? "Status" : "Why we moved on", { x: x + 0.2, y: 4.85, w: w - 0.4, h: 0.25, fontSize: 11, bold: true, color: sub });
    T(s, why, { x: x + 0.2, y: 5.1, w: w - 0.4, h: 1.2, fontSize: 13, color: fg });
  });
}

// ================================================================== 11. V1 CLASSICAL
{
  const s = content("Approach", "Version 1: classical computer vision",
    "This was the first approach and it is what the course units cover: grayscale, Gaussian blur, Otsu thresholding, morphology and connected components to find the object, then hand-crafted shape, colour and texture features fed to an SVM or Random Forest. It reached 73 percent on the six-class TrashNet task and 65 percent on ten classes. The picture on the left shows why: on cardboard the object fills the frame, on glass the shadow becomes part of the mask, and on paper and trash the background gradient takes over. If the mask is wrong, every feature is wrong.");
  s.addImage({ path: path.join(ROOT, "results/figures/pipeline/pipeline_all_classes.png"), x: 0.6, y: 1.4, w: 4.95, h: 4.95,
    altText: "Segmentation pipeline stages for six example waste items" });
  T(s, "Segmentation stages for one example per class (original, grayscale, blur, Otsu, morphology, detected object)", { x: 0.6, y: 6.4, w: 4.95, h: 0.5, fontSize: 11, italic: true, color: MUTED });
  B(s, [{ b: "Segmentation:", t: "grayscale, Gaussian blur (5x5), Otsu threshold, opening and closing (5x5 ellipse), largest connected component." },
        { b: "149 features:", t: "4 shape values, 7 Hu moments, 128-bin HSV histogram (8x4x4), 10-bin LBP texture." },
        { b: "Classifiers:", t: "RBF-SVM (C = 10) and Random Forest (300 trees), class-balanced, 80/20 stratified split." }],
    { x: 5.95, y: 1.45, w: 6.78, h: 2.75, fontSize: 14, gap: 7 });
  table(s, [["Dataset", "Classes", "Test images", "Random Forest", "SVM"],
    ["TrashNet", "6", "506", "73.1%", "72.9%"], ["Garbage-10", "10", "1,200", "64.7%", "57.1%"]],
    { x: 5.95, y: 4.3, w: 6.78, colW: [1.7, 1.0, 1.4, 1.5, 1.18], fontSize: 13, rowH: 0.42, align: ["left", "right", "right", "right", "right"] });
  T(s, "Finding: the mask fails when the object fills the frame, casts a shadow or sits on a cluttered background, so every feature built on it is corrupted.",
    { x: 5.95, y: 5.75, w: 6.78, h: 0.95, fontSize: 14, bold: true, color: C.text2 });
}

// ================================================================== 12. V2 MOBILENET
{
  const s = content("Approach", "Version 2: fine-tuned MobileNetV2",
    "Second approach: a pre-trained MobileNetV2 CNN. Phase one trained only the new last layer for three epochs, phase two fine-tuned the whole network for four. Loss falls steadily and held-out accuracy climbs to 95.7 percent. Point out the honest caveat in the footnote: this early version evaluated on the held-out set after every epoch and had no separate validation split, which is fixed in the final pipeline. Note the accuracy axis starts at 80 percent.");
  const ep = ["1", "2", "3", "4", "5", "6", "7"];
  chart(s, pres.charts.LINE, [{ name: "Training loss", labels: ep, values: [1.122, 0.567, 0.459, 0.326, 0.182, 0.128, 0.081] }],
    { x: 0.6, y: 1.45, w: 5.95, h: 3.55, chartColors: [BLUE], title: "Training loss per epoch", showLegend: false, lineSize: 3, lineDataSymbolSize: 8,
      showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 1.4, valAxisMajorUnit: 0.2,
      valAxisLabelFormatCode: "0.0", showCatAxisTitle: true, catAxisTitle: "Epoch", catAxisTitleFontSize: 12, catAxisTitleColor: MUTED });
  chart(s, pres.charts.LINE, [{ name: "Held-out accuracy", labels: ep, values: [85.2, 87.4, 88.7, 93.4, 94.3, 94.8, 95.7] }],
    { x: 6.78, y: 1.45, w: 5.95, h: 3.55, chartColors: [GREEN], title: "Held-out accuracy per epoch (axis starts at 80%)", showLegend: false, lineSize: 3,
      lineDataSymbolSize: 8, showValue: true, dataLabelPosition: "t", dataLabelFormatCode: '0.0"%"', valAxisMinVal: 80, valAxisMaxVal: 100,
      valAxisMajorUnit: 5, valAxisLabelFormatCode: '0"%"', showCatAxisTitle: true, catAxisTitle: "Epoch", catAxisTitleFontSize: 12, catAxisTitleColor: MUTED });
  B(s, [{ b: "Recipe:", t: "ImageNet-pretrained MobileNetV2, 224 px input, batch 32, random flips and rotation (15 degrees)." },
        { b: "Phase 1 (epochs 1-3):", t: "only the new last layer trained, Adam, learning rate 1e-3." },
        { b: "Phase 2 (epochs 4-7):", t: "whole network fine-tuned, Adam, learning rate 1e-4. Data: 4,800 train / 1,200 test images." }],
    { x: 0.6, y: 5.15, w: 12.13, h: 1.4, fontSize: 14, gap: 4 });
  note(s, "This early version had no separate validation split: accuracy is measured on the held-out set after each epoch.");
}

// ================================================================== 13. DOMAIN SHIFT
{
  const s = content("Approach", "The reality check: clean photos versus real landfill photos",
    "This slide explains why we changed approach. The same MobileNetV2 scored 95.7 percent on clean dataset photos but only 45.1 percent on the ten-class task for real landfill photos. Collapsing to four categories makes the task easier, so for a fair comparison we also scored it that way on exactly the same 690 images: 75.5 percent. The bars on the right show recall per class on landfill photos - trash was caught only 4 percent of the time and cardboard 27 percent. The lesson: accuracy on a clean test set does not tell you how a model will behave in the real world.");
  chart(s, pres.charts.BAR, [{ name: "Accuracy", labels: ["Own test set (10 classes)", "RealWaste (10 classes)", "RealWaste (4 categories)"], values: [95.7, 45.1, 75.5] }],
    { x: 0.6, y: 1.45, w: 5.6, h: 4.2, barDir: "col", chartColors: [GREEN, RED, AMBER], title: "MobileNetV2 accuracy", showLegend: false, showValue: true,
      dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20, valAxisLabelFormatCode: '0"%"', barGapWidthPct: 60 });
  chart(s, pres.charts.BAR, [{ name: "Recall", labels: ["metal", "paper", "biological", "glass", "plastic", "clothes", "cardboard", "trash"],
      values: [65.0, 62.8, 55.2, 44.8, 43.3, 41.2, 26.6, 4.0] }],
    { x: 6.45, y: 1.45, w: 6.28, h: 4.2, barDir: "bar", chartColors: [BLUE], title: "Recall per class on landfill photos", showLegend: false, showValue: true,
      dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20, valAxisLabelFormatCode: '0"%"', barGapWidthPct: 45 });
  T(s, "Why: the CNN saw centred objects on plain backgrounds. Landfill photos have clutter, dirt, mixed materials and unusual lighting. Accuracy on a clean test set did not predict real-world accuracy.",
    { x: 0.6, y: 5.85, w: 12.13, h: 0.7, fontSize: 15, bold: true, color: C.text2 });
  note(s, "Same 690 RealWaste test images for both bar charts. The 10-class and 4-category tasks differ in difficulty, so compare only bars with the same label.");
}

// ================================================================== 14. WHY SIGLIP2
{
  const s = content("Approach", "Why we chose SigLIP 2",
    "The table is the evidence from our own runs; the tiles are the reasons. Classical features and the fine-tuned CNN were rejected because of the measured real-world drop. ConvNeXt was not pursued because each epoch took around eight and a half minutes and the run stalled. SigLIP 2 is a vision-language model from Google trained on very large collections of web images with text, which is why its features transfer to unfamiliar photo styles. We keep it frozen and train only a small classifier on top, so adapting to new photos is cheap. Its text encoder also lets us describe items in words.");
  table(s, [["Candidate", "Evidence from our runs", "Verdict"],
    ["Classical features + Random Forest", "64.7% on 10 classes; segmentation fails on clutter", "Rejected"],
    ["MobileNetV2, fine-tuned", "95.7% on clean photos but 75.5% (4 categories) on landfill photos", "Rejected: poor transfer"],
    ["ConvNeXt-Tiny, fine-tuned", "93.0% validation after 2 epochs; about 8.5 min per epoch; run stalled", "Not pursued: cost"],
    [{ text: "SigLIP 2 + linear classifier", options: { bold: true } }, "98.7% test, 96.7% on landfill photos, about 21 ms per image", { text: "Selected", options: { bold: true, color: GREEN } }]],
    { x: 0.6, y: 1.45, w: 12.13, colW: [3.4, 6.5, 2.23], fontSize: 14, rowH: 0.56 });
  const why = [["Robust features", "Pre-trained on very large collections of web images with text, so features transfer to unfamiliar photo styles."],
    ["Cheap to adapt", "The encoder stays frozen; only a small classifier is trained, so adding new photos is practical."],
    ["Understands words", "The text encoder lets us describe items in words, used for the app's explanations."],
    ["Fast enough", "About 21 ms per image on a laptop GPU, so the camera view stays live."]];
  const w = 2.92, g = (12.13 - 4 * w) / 3;
  why.forEach(([h, t], i) => {
    const x = 0.6 + i * (w + g);
    card(s, x, 4.45, w, 2.15, "Reason " + (i + 1));
    T(s, h, { x: x + 0.18, y: 4.58, w: w - 0.36, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
    T(s, t, { x: x + 0.18, y: 5.03, w: w - 0.36, h: 1.5, fontSize: 13 });
  });
}

// ================================================================== 15. FINAL ARCHITECTURE
{
  const s = content("Approach", "Final model: SigLIP 2 with a trained classifier",
    "The image is resized to 224 by 224 and passed through the frozen SigLIP 2 vision transformer, which produces a 768-number embedding. A logistic-regression classifier trained on eleven fine-grained classes turns that into class probabilities, and we add up the probabilities that belong to each of the four categories. Mapping classes to categories after training is deliberate: it keeps accuracy high and lets us change the rule table without retraining. The text branch encodes 68 short descriptions to give the app its 'looks like' explanation; it was also evaluated on its own as a no-training baseline at 83.3 percent.");
  const bx = [["Image", "224 x 224 RGB"], ["SigLIP 2 encoder", "ViT-B/16, frozen"], ["Embedding", "768 numbers, unit length"],
    ["Linear classifier", "11 classes, C = 20, balanced"], ["Category scores", "sum of class probabilities"]];
  const bw = 2.1, gap = (12.13 - 5 * bw) / 4;
  bx.forEach(([a, b], i) => {
    const x = 0.6 + i * (bw + gap), dark = i === 1 || i === 3;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: bw, h: 1.35, rectRadius: 0.08, fill: { color: dark ? DEEP : TINT }, line: { color: LINE, width: 0.75 }, objectName: "Model block " + (i + 1) });
    T(s, a, { x: x + 0.1, y: 1.62, w: bw - 0.2, h: 0.5, fontSize: 16, bold: true, color: dark ? "FFFFFF" : INK, align: "center", valign: "middle" });
    T(s, b, { x: x + 0.1, y: 2.15, w: bw - 0.2, h: 0.6, fontSize: 12, color: dark ? "DDE8E0" : MUTED, align: "center" });
    if (i < 4) s.addShape(pres.shapes.LINE, { x: x + bw + 0.04, y: 2.17, w: gap - 0.08, h: 0, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
  });
  card(s, 0.6, 3.15, 12.13, 1.2, "Text branch");
  T(s, [{ text: "Text branch.  ", options: { bold: true, color: C.text2 } },
        { text: "68 short descriptions (14 biodegradable, 16 recyclable, 19 non-recyclable, 19 medical) x 5 sentence templates are encoded once by the text encoder. The closest descriptions to an image give the app's \"looks like: ...\" explanation. Used alone as a no-training baseline: 83.3% test accuracy." }],
    { x: 0.85, y: 3.3, w: 11.6, h: 0.95, fontSize: 14, valign: "middle" });
  const info = [["Why sum probabilities?", "The classifier learns fine-grained classes (paper, cardboard, glass...), which keeps it accurate. The 4-category rule is applied afterwards, so it can change without retraining."],
    ["Why frozen?", "The encoder is already strong. Training only the small classifier avoids over-fitting to our smaller dataset and keeps retraining fast."],
    ["Model size", "SigLIP 2 base (patch 16, 224 px): about 375 million parameters in total (1.5 GB file), image and text towers together."]];
  info.forEach(([h, t], i) => {
    const x = 0.6 + i * 4.13;
    T(s, h, { x, y: 4.6, w: 3.9, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
    T(s, t, { x, y: 5.05, w: 3.9, h: 1.55, fontSize: 14 });
  });
}

// ================================================================== 16. TRAINING PROTOCOL
{
  const s = content("Approach", "Training protocol and hyperparameters",
    "Left: every setting used for the final model. The key discipline is that all choices - the regularisation strength C, whether to blend in the zero-shot scores, and the Unknown threshold - were made on the validation split, and the test split was used once at the end. Right: validation accuracy as C increases. It is still improving slightly at the largest value we tried, 20, but the gain from 10 to 20 is only about 0.1 points, so it is flattening. We also tested blending the text-based scores with the trained classifier; the best blend gained at most 0.002 macro-F1 on validation, which is noise, so we kept the simpler model.");
  table(s, [["Setting", "Value"],
    ["Backbone", "google/siglip2-base-patch16-224 (frozen)"], ["Input", "224 x 224 RGB, normalised to -1 to 1"],
    ["Classifier", "Logistic regression, L2, class-balanced"], ["Regularisation C", "20 (chosen from 0.5 to 20 on validation)"],
    ["Targets", "11 fine-grained classes mapped to 4 categories"], ["Unknown threshold", "0.59 (99% accuracy on accepted validation items)"],
    ["Selection metric", "Validation macro-F1"], ["Random seed", "42"], ["Data", "14,847 train / 3,290 validation / 3,308 test"]],
    { x: 0.6, y: 1.45, w: 6.6, colW: [2.1, 4.5], fontSize: 13, rowH: 0.45 });
  chart(s, pres.charts.LINE, [
    { name: "Validation accuracy", labels: ["0.5", "1", "2", "5", "10", "20"], values: [97.66, 97.99, 98.27, 98.57, 98.63, 98.75] },
    { name: "Validation macro-F1", labels: ["0.5", "1", "2", "5", "10", "20"], values: [97.27, 97.53, 97.98, 98.34, 98.46, 98.48] }],
    { x: 7.45, y: 1.45, w: 5.28, h: 3.9, chartColors: [GREEN, BLUE], title: "Validation score vs C (axis starts at 97%)", showLegend: true, legendPos: "b",
      lineSize: 3, lineDataSymbolSize: 8, valAxisMinVal: 97, valAxisMaxVal: 99, valAxisMajorUnit: 0.5, valAxisLabelFormatCode: '0.0"%"',
      showCatAxisTitle: true, catAxisTitle: "Regularisation strength C", catAxisTitleFontSize: 12, catAxisTitleColor: MUTED });
  T(s, "Still rising at the largest C tried, but only +0.12 points from C = 10 to 20. Blending the text scores in gained at most 0.002 macro-F1, so the simpler classifier-only model was kept.",
    { x: 7.45, y: 5.45, w: 5.28, h: 1.1, fontSize: 13, color: MUTED });
}

// ================================================================== 17. TRAIN VAL TEST
{
  const s = content("Results", "Training, validation and test accuracy",
    "These are the three numbers people ask for. Training accuracy 99.6 percent, validation 98.75, test 98.73. The gap between training and test is under one point, so the classifier is not memorising. Validation and test are almost identical, which shows that tuning on validation did not leak into the test set. The remaining errors are concentrated in non-recyclable versus recyclable - about half of the test errors - which the confusion matrix shows.");
  const w = 3.9;
  [["99.60%", "Training", "14,847 images"], ["98.75%", "Validation", "3,290 images, used for tuning"], ["98.73%", "Test", "3,308 images, used once"]]
    .forEach((d, i) => stat(s, 0.6 + i * (w + 0.215), 1.45, w, 1.95, ...d));
  table(s, [["Split", "Images", "Accuracy", "Macro-F1", "Mean confidence"],
    ["Training", "14,847", "99.60%", "0.9966", "98.4%"], ["Validation", "3,290", "98.75%", "0.9848", "97.9%"], ["Test", "3,308", "98.73%", "0.9875", "98.0%"]],
    { x: 0.6, y: 3.75, w: 7.2, colW: [1.7, 1.3, 1.4, 1.35, 1.45], fontSize: 14, rowH: 0.5, align: ["left", "right", "right", "right", "right"] });
  B(s, ["Training to test gap is only 0.87 points: the classifier is not memorising.",
        "Validation and test agree (98.75% vs 98.73%): tuning did not leak into the test set.",
        "About half of the 42 test errors are non-recyclable items predicted as recyclable."],
    { x: 8.2, y: 3.75, w: 4.53, h: 2.8, fontSize: 14, gap: 8 });
}

// ================================================================== 18. PER CATEGORY
{
  const s = content("Results", "Test results by category",
    "Precision asks: when the model says this category, how often is it right? Recall asks: of the items that really are this category, how many does it find? All four categories are between 97.7 and 100 percent. Medical waste has precision of exactly 1.000 - nothing else ever lands in the medical bin - and recall of 97.7 percent, meaning 7 of 310 medical items were missed. Note the chart axis starts at 90 percent so the small differences are visible.");
  const cats = ["Biodegradable", "Recyclable", "Non-recyclable", "Medical"];
  chart(s, pres.charts.BAR, [
    { name: "Precision", labels: cats, values: [98.5, 97.8, 99.3, 100] },
    { name: "Recall", labels: cats, values: [98.9, 99.5, 98.2, 97.7] },
    { name: "F1-score", labels: cats, values: [98.7, 98.7, 98.8, 98.9] }],
    { x: 0.6, y: 1.45, w: 7.0, h: 4.9, barDir: "col", chartColors: [BLUE, GREEN, AMBER], title: "Test precision, recall and F1 (axis starts at 90%)",
      showLegend: true, legendPos: "b", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 11,
      valAxisMinVal: 90, valAxisMaxVal: 101, valAxisMajorUnit: 2, valAxisLabelFormatCode: '0"%"', barGapWidthPct: 40 });
  table(s, [["Category", "Prec.", "Recall", "F1", "Images"],
    ["Biodegradable", "0.985", "0.989", "0.987", "274"], ["Recyclable", "0.978", "0.995", "0.987", "1,270"],
    ["Non-recyclable", "0.993", "0.982", "0.988", "1,454"], ["Medical", "1.000", "0.977", "0.989", "310"],
    [{ text: "Macro average", options: { bold: true } }, { text: "0.989", options: { bold: true } }, { text: "0.986", options: { bold: true } }, { text: "0.988", options: { bold: true } }, { text: "3,308", options: { bold: true } }]],
    { x: 7.9, y: 1.55, w: 4.83, colW: [1.6, 0.75, 0.8, 0.7, 0.98], fontSize: 12.5, rowH: 0.5, align: ["left", "right", "right", "right", "right"] });
  T(s, "Medical waste: precision 1.000 means nothing else is ever sent to the medical bin.", { x: 7.9, y: 4.85, w: 4.83, h: 0.75, fontSize: 14, bold: true, color: C.text2 });
  T(s, "Weighted average: precision, recall and F1 are all 0.987.", { x: 7.9, y: 5.7, w: 4.83, h: 0.5, fontSize: 13, color: MUTED });
}

// ================================================================== 19. CONFUSION MATRIX
{
  const s = content("Results", "Confusion matrix on the test split",
    "Rows are the true category, columns what the model predicted, so the diagonal is correct answers. 42 of 3,308 images were wrong, 1.27 percent. The largest error cell is 22 non-recyclable items predicted as recyclable, 1.5 percent of that class. We have not yet looked at those 22 images one by one, so we should not claim why. Medical waste is never confused with biodegradable and nothing else is predicted as medical: the medical column has 303 correct and zero wrong. Seven medical items were missed, five predicted recyclable and two non-recyclable.");
  const names = ["Biodegradable", "Recyclable", "Non-recyclable", "Medical"];
  const cm = [[271, 1, 2, 0], [0, 1264, 6, 0], [4, 22, 1428, 0], [0, 5, 2, 303]];
  const rec = ["98.9%", "99.5%", "98.2%", "97.7%"], prec = ["98.5%", "97.8%", "99.3%", "100%"];
  const shade = (i, j, v) => i === j ? "D3EBD8" : v >= 10 ? "F5B7B7" : v > 0 ? "FBE3E3" : "FFFFFF";
  const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: DEEP }, align: "center", valign: "middle", fontSize: 13 } });
  const rows = [[hdr("True \\ Predicted"), ...names.map(hdr), hdr("Recall")]];
  cm.forEach((r, i) => rows.push([{ text: names[i], options: { bold: true, fill: { color: TINT }, fontSize: 13, valign: "middle" } },
    ...r.map((v, j) => ({ text: v.toLocaleString("en-US"), options: { align: "center", valign: "middle", fontSize: 16, bold: i === j, fill: { color: shade(i, j, v) }, color: INK } })),
    { text: rec[i], options: { align: "center", bold: true, valign: "middle", fontSize: 13, fill: { color: TINT } } }]));
  rows.push([{ text: "Precision", options: { bold: true, fill: { color: TINT }, fontSize: 13, valign: "middle" } },
    ...prec.map((p) => ({ text: p, options: { align: "center", bold: true, valign: "middle", fontSize: 13, fill: { color: TINT } } })),
    { text: "98.7%", options: { align: "center", bold: true, valign: "middle", fontSize: 13, fill: { color: "D3EBD8" } } }]);
  s.addTable(rows, { x: 0.6, y: 1.5, w: 7.7, colW: [1.9, 1.3, 1.1, 1.3, 1.1, 1.0], rowH: [0.6, 0.8, 0.8, 0.8, 0.8, 0.6],
    border: { type: "solid", pt: 0.75, color: LINE }, margin: [0.05, 0.1, 0.05, 0.1], objectName: "Confusion matrix" });
  T(s, "Counts of test images. Green: correct. Pink: errors (darker = 10 or more).", { x: 0.6, y: 6.0, w: 7.7, h: 0.4, fontSize: 11, italic: true, color: MUTED });
  B(s, [{ b: "42 errors", t: "in 3,308 images (1.27%)." },
        { b: "Largest error:", t: "22 non-recyclable items predicted recyclable (1.5% of that class). We have not yet reviewed these images individually." },
        { b: "Medical:", t: "the column has 303 correct and 0 wrong. 7 medical items were missed (5 predicted recyclable, 2 non-recyclable)." },
        { b: "Biodegradable", t: "is almost never confused with recyclable (1 of 274)." }],
    { x: 8.6, y: 1.5, w: 4.13, h: 5.0, fontSize: 14, gap: 9 });
}

// ================================================================== 20. BY SOURCE
{
  const s = content("Results", "Results by data source",
    "The model is strongest on the web photos in Garbage-12 and the medical photos, and a little lower on real landfill photos, which are the hardest. On the right is the fairest comparison in the project: the same 690 landfill photos, the same four categories, the earlier CNN at 75.5 percent against the final model at 96.7. One caveat: the final model was also trained on landfill photographs that the earlier CNN never saw, so the gain reflects both the stronger model and the extra in-domain data; we did not separate the two. A second caution on TrashNet: only 26 test images are left after removing duplicates, so 73 percent there rests on 19 of 26 correct and is a very uncertain number.");
  chart(s, pres.charts.BAR, [{ name: "Test accuracy", labels: ["Garbage-12 (n=2,282)", "Medical photos (n=310)", "RealWaste (n=690)", "TrashNet (n=26)"], values: [99.8, 97.7, 96.7, 73.1] }],
    { x: 0.6, y: 1.45, w: 7.0, h: 4.75, barDir: "col", chartColors: [GREEN], title: "Test accuracy by data source", showLegend: false, showValue: true,
      dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20, valAxisLabelFormatCode: '0"%"', barGapWidthPct: 55 });
  chart(s, pres.charts.BAR, [{ name: "Accuracy", labels: ["Earlier CNN (MobileNetV2)", "EcoSort AI (SigLIP 2)"], values: [75.5, 96.7] }],
    { x: 7.9, y: 1.45, w: 4.83, h: 3.4, barDir: "col", chartColors: [GREY, GREEN], title: "Same 690 landfill photos, 4 categories", showLegend: false, showValue: true,
      dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20, valAxisLabelFormatCode: '0"%"', barGapWidthPct: 60 });
  T(s, "+21.2 points on real landfill photos, on identical images and the identical 4-category task.", { x: 7.9, y: 4.95, w: 4.83, h: 0.7, fontSize: 14, bold: true, color: C.text2 });
  T(s, "TrashNet has only 26 test images after removing duplicates (19 correct): treat that bar as very uncertain.", { x: 7.9, y: 5.7, w: 4.83, h: 0.75, fontSize: 12, italic: true, color: MUTED });
  note(s, "Caveat: the final model was also trained on landfill photos (3,328 images), so the gain combines backbone and data effects; they were not separated.");
}

// ================================================================== 21. MEDICAL
{
  const s = content("Results", "Medical waste detection",
    "Medical waste is the safety-critical category. Of 310 medical test photos, 303 were identified, 97.7 percent, and none of the 2,998 ordinary items was wrongly sent to the medical bin. Syringes, needles and gloves were 100 percent; blister packs were lowest at 84.6 percent but there are only 13 test photos of them, so that figure is shaky. The caveats are important: all the medical photos come from Wikimedia Commons, which are cleaner than real hospital waste, and a few are mislabelled. The Teach button is how to close this gap with your own photos.");
  chart(s, pres.charts.BAR, [{ name: "Recall", labels: ["Blister packs (n=13)", "Pill bottles (n=16)", "Masks (n=22)", "Ampoules, vials (n=50)", "Swabs, bandages (n=73)", "Gloves (n=26)", "Syringes, needles (n=110)"],
      values: [84.6, 93.8, 95.5, 96.0, 98.6, 100, 100] }],
    { x: 0.6, y: 1.45, w: 7.1, h: 4.95, barDir: "bar", chartColors: [RED], title: "Recall per medical item type (test photos)", showLegend: false, showValue: true,
      dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', valAxisMinVal: 0, valAxisMaxVal: 110, valAxisMajorUnit: 20, valAxisLabelFormatCode: '0"%"', barGapWidthPct: 45 });
  const w = 2.3;
  [["97.7%", "Recall", "303 of 310 medical test photos"], ["0", "False alarms", "of 2,998 ordinary test items"]].forEach((d, i) => {
    const x = 8.0 + i * (w + 0.13);
    card(s, x, 1.5, w, 1.65, "Medical stat " + (i + 1));
    T(s, d[0], { x: x + 0.15, y: 1.58, w: w - 0.3, h: 0.7, fontSize: 36, bold: true, color: C.text2, fontFace: "+mj-lt", valign: "middle" });
    T(s, d[1], { x: x + 0.15, y: 2.28, w: w - 0.3, h: 0.3, fontSize: 14, bold: true });
    T(s, d[2], { x: x + 0.15, y: 2.58, w: w - 0.3, h: 0.5, fontSize: 11, color: MUTED });
  });
  T(s, "Caveats", { x: 8.0, y: 3.4, w: 4.73, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  B(s, ["All photos come from Wikimedia Commons: cleaner than real hospital waste.",
        "1,150 downloaded, 1,031 kept after removing drawings and documents; a few labels are noisy.",
        "Blister packs: only 13 test photos, so 84.6% is a shaky estimate.",
        "Next step: collect photos of real items with the Teach button."],
    { x: 8.0, y: 3.8, w: 4.73, h: 2.7, fontSize: 13, gap: 5 });
}

// ================================================================== 22. UNKNOWN
{
  const s = content("Results", "Confidence and the Unknown option",
    "A sorting system should know when it does not know. The model gives a confidence for every answer. If the top confidence is below 0.59 the app says Unknown and asks for manual sorting. We chose 0.59 on the validation split as the lowest threshold at which the answers we keep are at least 99 percent correct. On the test split that holds back 32 images, one percent, and the rest are answered with 99.1 percent accuracy, up from 98.7 without the option.");
  const w = 3.9;
  [["0.59", "Confidence threshold", "chosen on validation"], ["32 of 3,308", "Held as Unknown", "1.0% of test images"], ["99.1%", "Accuracy when answered", "98.7% without the Unknown option"]]
    .forEach((d, i) => stat(s, 0.6 + i * (w + 0.215), 1.45, w, 1.95, ...d));
  T(s, "How the threshold is chosen", { x: 0.6, y: 3.75, w: 6.0, h: 0.4, fontSize: 18, bold: true, color: C.text2, fontFace: "+mj-lt" });
  B(s, ["Try every threshold from 0.30 to 0.95 on the validation split.", "Pick the lowest one where the answers kept are at least 99% correct.",
        "Apply it unchanged to the test split."], { x: 0.6, y: 4.25, w: 6.0, h: 2.2, fontSize: 15, gap: 8 });
  T(s, "In the app", { x: 7.0, y: 3.75, w: 5.7, h: 0.4, fontSize: 18, bold: true, color: C.text2, fontFace: "+mj-lt" });
  B(s, ["Below 0.59 the result card turns amber and reads \"Unknown - check manually\".", "The slider-free design keeps the decision consistent for every user.",
        "Best guess is still shown, so a person can decide quickly."], { x: 7.0, y: 4.25, w: 5.7, h: 2.2, fontSize: 15, gap: 8 });
}

// ================================================================== 23. VERSION COMPARISON
{
  const s = content("Results", "Model version comparison",
    "Everything in one table. Read it with care: the rows use different class sets and different test sets, so only compare rows that share a test set. The fair comparison is the two RealWaste rows: 45.1 percent for ten classes with the earlier CNN, 75.5 percent when collapsed to four categories, and 96.7 percent for the final model. Version 3 is shown for completeness, but it was stopped early and has no test result.");
  const fin = (t) => ({ text: t, options: { bold: true, color: GREEN } });
  table(s, [["Version", "Model", "Task and data", "Test images", "Result", "Note"],
    ["V1", "Random Forest, 149 features", "TrashNet, 6 classes", "506", "73.1%", "Needs plain backgrounds"],
    ["V1", "Random Forest / SVM", "Garbage-10, 10 classes", "1,200", "64.7% / 57.1%", "Weak features"],
    ["V2", "MobileNetV2, fine-tuned", "Garbage-10, 10 classes", "1,200", "95.7%", "Clean photos only"],
    ["V2", "MobileNetV2, fine-tuned", "RealWaste, 10 classes", "690", "45.1%", "4 categories: 75.5%"],
    ["V3", "ConvNeXt-Tiny", "Multi-source, 10 classes", "none", "93.0% validation", "Stopped at epoch 2 of 15"],
    [fin("V4"), fin("SigLIP 2 + linear head"), "Multi-source, 4 categories", "3,308", fin("98.7% (F1 0.988)"), fin("Final model")],
    [fin("V4"), fin("SigLIP 2 + linear head"), "RealWaste, 4 categories", "690", fin("96.7%"), "Same images as V2 row"]],
    { x: 0.6, y: 1.45, w: 12.13, colW: [0.9, 2.9, 2.6, 1.3, 2.0, 2.43], fontSize: 13, rowH: 0.56, align: ["left", "left", "left", "right", "left", "left"] });
  note(s, "Rows use different class sets and test sets: compare only rows that share a test set (RealWaste: 45.1% / 75.5% for V2, 96.7% for V4).");
}

// ================================================================== 24. APPLICATION + STACK
{
  const s = content("System", "Real-time application and engineering",
    "The web app opens in any browser and asks for camera permission itself. It has a live camera mode with a centre box, an upload mode for single or multiple images, a session log, and the Teach buttons. The server is a small Python program with three endpoints. On the right is the exact software stack and hardware so the results can be reproduced: fixed random seed, every image's split recorded in a manifest file, 38 automated tests, and all code under version control.");
  T(s, "Web application", { x: 0.6, y: 1.45, w: 6.0, h: 0.4, fontSize: 18, bold: true, color: C.text2, fontFace: "+mj-lt" });
  B(s, [{ b: "Live camera:", t: "hold an item in the centre box; colour-coded result, confidence bars and \"looks like\" text." },
        { b: "Upload:", t: "drop one or many photos and get a category for each." },
        { b: "Teach:", t: "one click saves a corrected photo for the next training run." },
        { b: "Session log:", t: "running count per category with thumbnails." },
        { b: "API:", t: "GET /api/info, POST /api/classify, POST /api/teach (Python standard library server)." }],
    { x: 0.6, y: 1.95, w: 6.0, h: 4.5, fontSize: 14, gap: 8 });
  table(s, [["Component", "Version"],
    ["Python", "3.10.13"], ["PyTorch (Apple MPS GPU)", "2.14.1"], ["Transformers (SigLIP 2)", "5.20.2"], ["scikit-learn", "1.7.2"],
    ["OpenCV", "5.0.0"], ["NumPy / pandas", "2.2.6 / 2.3.3"], ["Hardware", "Apple-silicon Mac, 16 GB RAM"],
    ["Reproducibility", "Seed 42; split manifest; 38 tests; git"]],
    { x: 7.0, y: 1.5, w: 5.73, colW: [2.9, 2.83], fontSize: 13, rowH: 0.52 });
}

// ================================================================== 25. LIMITS + FUTURE
{
  const s = content("System", "Limitations and future work",
    "Be candid with the audience. The biggest gap is that we have not yet measured accuracy on live webcam frames - the results here are on photo datasets. The app also handles one item at a time, the medical data are web photos, and a few items such as leather goods and handkerchiefs rely on neighbouring classes. The right column is the plan: a locked real-world test set from our own camera first, then multi-item detection and tracking, then real medical-waste photos collected with the right approvals.");
  T(s, "Limitations", { x: 0.6, y: 1.45, w: 5.9, h: 0.4, fontSize: 20, bold: true, color: C.text2, fontFace: "+mj-lt" });
  B(s, ["Accuracy on live webcam frames has not been measured yet; results are on photo datasets.",
        "One item at a time: the camera classifies the centre box only.",
        "Medical data are web photos, cleaner than real hospital waste.",
        "Leather goods and handkerchiefs have no class of their own; they rely on the shoes and clothes images.",
        "Some items are ambiguous by appearance alone (paper vs tissue, cloth vs plant fibre)."],
    { x: 0.6, y: 1.95, w: 5.9, h: 4.6, fontSize: 14, gap: 8 });
  T(s, "Future work", { x: 6.85, y: 1.45, w: 5.9, h: 0.4, fontSize: 20, bold: true, color: C.text2, fontFace: "+mj-lt" });
  B(s, ["Collect 200 to 300 photos from our own camera as a locked real-world test set.",
        "Add an object detector and tracker so several items in one frame are sorted and counted.",
        "Gather real medical-waste photos with institutional approval; retrain with the Teach photos.",
        "Review the 42 test errors one by one and add targeted training data.",
        "Export the model for edge devices (ONNX / Core ML) and connect it to a bin-sorting mechanism."],
    { x: 6.85, y: 1.95, w: 5.88, h: 4.6, fontSize: 14, gap: 8 });
}

// ================================================================== 26. CONCLUSION
{
  pres.addSection({ title: "Conclusion" }); sectionOpen = "Conclusion";
  const s = pres.addSlide({ masterName: "CLOSE", sectionTitle: "Conclusion" });
  s.addText("Conclusion", { placeholder: "title" });
  const pts = ["A 4-category waste sorter (biodegradable, recyclable, non-recyclable, medical) that runs in real time in a web browser.",
    "98.7% accuracy on 3,308 unseen images and 96.7% on real landfill photos, up from 75.5% with the earlier CNN on the same images.",
    "Medical waste: 97.7% of items caught and no ordinary item sent to the medical bin (0 of 2,998).",
    "Main lesson: test on real-world photos early. Clean-photo accuracy hid a drop of about 50 points."];
  pts.forEach((t, i) => {
    const y = 1.85 + i * 1.05;
    disc(s, i + 1, 0.8, y + 0.05, 0.55, GREEN, 18);
    T(s, t, { x: 1.0 + 0.55, y, w: 11.0, h: 0.9, fontSize: 18, color: "FFFFFF", valign: "middle" });
  });
  T(s, "Thank you  -  Questions?", { x: 0.8, y: 6.1, w: 11.7, h: 0.6, fontSize: 28, bold: true, color: "A9D8B5", fontFace: "+mj-lt" });
  s.addNotes("Close with the four takeaways: what we built, the headline accuracy on unseen and real-world photos, the medical-waste safety result, and the main lesson - benchmark on real-world data early. Then invite questions. Likely questions: why SigLIP 2 (slide 14), how medical waste was handled without a public dataset (slide 21), what is not done yet (slide 25).");
}

// ================================================================== 27. REFERENCES
{
  const s = content("Conclusion", "References",
    "Reference list for models, datasets and libraries used in the project. Check each citation against the original source before submitting the final report.");
  const refs = [
    "[1] Tschannen, M. et al. (2025). SigLIP 2: Multilingual Vision-Language Encoders with Improved Semantic Understanding, Localization, and Dense Features. arXiv.",
    "[2] Zhai, X., Mustafa, B., Kolesnikov, A., Beyer, L. (2023). Sigmoid Loss for Language Image Pre-Training. ICCV.",
    "[3] Sandler, M. et al. (2018). MobileNetV2: Inverted Residuals and Linear Bottlenecks. CVPR.",
    "[4] Liu, Z. et al. (2022). A ConvNet for the 2020s. CVPR.",
    "[5] Single, S., Iranmanesh, S., Raad, R. (2023). RealWaste: A Novel Real-Life Data Set for Landfill Waste Classification Using Deep Learning. Information, 14(12). UCI Machine Learning Repository.",
    "[6] Yang, M., Thung, G. (2016). Classification of Trash for Recyclability Status. Stanford CS229 project report (TrashNet).",
    "[7] Otsu, N. (1979). A Threshold Selection Method from Gray-Level Histograms. IEEE Trans. Systems, Man and Cybernetics, 9(1).",
    "[8] Garbage Classification (12 classes), Kaggle; medical photos from Wikimedia Commons (author and licence per file in attribution.csv).",
    "[9] Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. JMLR 12.   [10] Paszke, A. et al. (2019). PyTorch. NeurIPS."];
  T(s, refs.map((r, i) => ({ text: r, options: { breakLine: i < refs.length - 1, paraSpaceAfter: 7 } })),
    { x: 0.6, y: 1.5, w: 12.13, h: 5.2, fontSize: 14 });
}

// ------------------------------------------------------------------ write
(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("Wrote", OUT);
})();
