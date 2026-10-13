// Yatırımcı sunumu üretici. Gerekenler: npm i pptxgenjs react react-dom react-icons sharp; PPTX_SKILL_DIR = pptx skill klasörü (apply_theme.js için)
// Çalıştır: PPTX_SKILL_DIR=... node build-deck.js
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require(process.env.PPTX_SKILL_DIR + "/scripts/apply_theme.js");

const THEME = {
  name: "4PC Pitch",
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
pres.title = "4-Product One Community — Yatırımcı Sunumu";
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

(async () => {
  // 1 — Kapak
  let s = pres.addSlide({ masterName: "COVER" });
  s.addShape(pres.shapes.OVAL, { x: 6.3, y: -0.9, w: 5.2, h: 5.2, fill: { color: HEX.indigo, transparency: 82 }, line: { type: "none" }, objectName: "glow 1" });
  s.addShape(pres.shapes.OVAL, { x: 7.4, y: 2.6, w: 3.6, h: 3.6, fill: { color: HEX.amber, transparency: 80 }, line: { type: "none" }, objectName: "glow 2" });
  T(s, "4-PRODUCT ONE COMMUNITY", { x: 0.7, y: 0.75, w: 6, h: 0.3, fontSize: 12, bold: true, color: HEX.amber, charSpacing: 4 });
  s.addText("Diplomadan önce deneyim. Mezuniyetten önce kanıt.", { placeholder: "title" });
  T(s, "Öğrenciyi daha okurken sektörün içine alan, açık kaynaklı kariyer ekosistemi.", { x: 0.7, y: 3.55, w: 5.8, h: 0.8, fontSize: 18, color: HEX.muted, valign: "top" });
  chip(s, "YATIRIMCI SUNUMU · 2026", 0.7, 4.6, 2.3, HEX.amber);
  chip(s, "Apache-2.0 · Açık kaynak", 3.15, 4.6, 2.1, HEX.panel, HEX.white);
  s.addNotes("Açılış: 'Her yıl binlerce genç diplomayla mezun oluyor ama kimse onlara ilk deneyimi vermiyor. Biz o deneyimi okurken veriyoruz.' Kısa tut, hikâyeyi 2. slaytta başlat.");

  // 2 — Sorun
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("İlk iş kapısı kapanıyor", { placeholder: "title" });
  T(s, [
    { text: "Deneyimsiz diye işe alınmıyorlar.", options: { breakLine: true, color: HEX.white } },
    { text: "İşe alınmadıkları için deneyimsiz kalıyorlar.", options: { color: HEX.amber } },
  ], { x: 0.6, y: 1.5, w: 4.4, h: 2.4, fontSize: 24, bold: true, fontFace: "Cambria", valign: "top", paraSpaceAfter: 10 });
  T(s, "Yapay zekâ giriş seviyesi işleri hızla otomatikleştiriyor. Yeni mezunlar için bu kısır döngü her yıl daha da sıkılaşıyor.", { x: 0.6, y: 3.8, w: 4.4, h: 1.1, fontSize: 14, color: HEX.muted, valign: "top" });
  const prob = [
    ["FaUserGraduate", "Yeni mezun", "Diploması var, kanıtlanabilir işi yok.", HEX.coral],
    ["FaUniversity", "Üniversite", "Teori güçlü; gerçek sistem ve müşteri baskısı dışarıda.", HEX.indigo],
    ["FaBuilding", "Şirket", "Adayın gerçekte ne ürettiğini göremiyor.", HEX.teal],
  ];
  for (let i = 0; i < prob.length; i++) {
    const y = 1.5 + i * 1.18;
    card(s, 5.4, y, 4.0, 1.04, HEX.panel, "problem card " + i);
    await iconBadge(s, prob[i][0], 5.6, y + 0.2, 0.64, prob[i][3], HEX.ink, "problem " + i);
    T(s, prob[i][1], { x: 6.45, y: y + 0.14, w: 2.8, h: 0.3, fontSize: 15, bold: true, color: HEX.white });
    T(s, prob[i][2], { x: 6.45, y: y + 0.45, w: 2.8, h: 0.5, fontSize: 12, color: HEX.muted, valign: "top" });
  }
  s.addNotes("Sorun üç tarafta da aynı: yetenek var, kanıt yolu yok. Rakam kullanacaksan güvenilir kaynak (TÜİK/OECD) ekle; uydurma istatistik kullanma.");

  // 3 — Neden şimdi
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("Neden şimdi?", { placeholder: "title" });
  const now = [
    ["FaRobot", "AI giriş işlerini üstleniyor", "Rutin kod, taslak ve analiz dakikalara indi; 'stajyer işi' tanımı değişiyor.", HEX.coral],
    ["FaSearch", "Şirketler kanıt arıyor", "Özgeçmiş cümlesi yerine yapılmış işe, teslimata ve referansa bakılıyor.", HEX.indigo],
    ["FaLaptopCode", "Öğrenciler dijitalde üretebiliyor", "Uzaktan, takım halinde ve araçlarla çalışmak yeni kuşak için doğal.", HEX.teal],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 3.0;
    card(s, x, 1.6, 2.8, 3.2, HEX.white, "now card " + i);
    await iconBadge(s, now[i][0], x + 0.3, 1.9, 0.8, now[i][3], HEX.white, "now " + i);
    T(s, now[i][1], { x: x + 0.3, y: 2.9, w: 2.2, h: 0.7, fontSize: 17, bold: true, color: HEX.ink, valign: "top" });
    T(s, now[i][2], { x: x + 0.3, y: 3.65, w: 2.2, h: 1.0, fontSize: 13, color: HEX.slate, valign: "top" });
  }
  s.addNotes("Üç dalga aynı anda geliyor: AI, kanıt odaklı işe alım, uzaktan çalışma. Boşluk tam burada.");

  // 4 — Çözüm
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Çözüm: sektörün içinde okumak", { placeholder: "title" });
  T(s, "Öğrenci gerçek projede, gerçek müşteriyle, gerçek mentorla çalışır. Herkes kazanır.", { x: 0.6, y: 1.3, w: 8.6, h: 0.5, fontSize: 16, color: HEX.muted, valign: "top" });
  const who = [
    ["FaUserGraduate", "Öğrenci", "Mezun olmadan iş geçmişi, ilk kazanç, portföy", HEX.amber],
    ["FaChalkboardTeacher", "Deneyimli profesyonel", "Mentorlukla gelir ve yeni nesil yetiştirme", HEX.teal],
    ["FaBuilding", "Şirket", "Özgeçmişte değil, yapılan işte aday görmek", HEX.indigo],
    ["FaUniversity", "Üniversite", "Müfredata dokunmadan sektör köprüsü", HEX.coral],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * 4.4, y = 2.05 + Math.floor(i / 2) * 1.5;
    card(s, x, y, 4.2, 1.35, HEX.panel, "who card " + i);
    await iconBadge(s, who[i][0], x + 0.25, y + 0.33, 0.7, who[i][3], HEX.ink, "who " + i);
    T(s, who[i][1], { x: x + 1.15, y: y + 0.22, w: 2.9, h: 0.35, fontSize: 16, bold: true, color: HEX.white });
    T(s, who[i][2], { x: x + 1.15, y: y + 0.6, w: 2.9, h: 0.65, fontSize: 13, color: HEX.muted, valign: "top" });
  }
  s.addNotes("Dört tarafın her biri için net bir 'ne kazanıyorum' var. Bu, ekosistemin döngüsünü mümkün kılıyor.");

  // 5 — Dört ürün
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("Dört ürün, tek yolculuk", { placeholder: "title" });
  const prods = [
    ["FIRST", "Birlikte üret", "Proje ve açık kaynak topluluğu: ekip kur, katkı ver.", "ÇALIŞIYOR", HEX.teal, "FaUsers"],
    ["STEP", "Ücretli iş al", "Doğrulanmış öğrenciler için iş pazarı ve ödeme güvencesi.", "CANLIYA HAZIRLIK", HEX.amber, "FaBriefcase"],
    ["INTO", "Mentordan öğren", "Ücretli/gönüllü mentorluk ve acil destek.", "KAPSAM NETLEŞTİ", HEX.indigo, "FaLightbulb"],
    ["PATH", "Problem çöz, görün", "Şirket problemleri üzerinde yarışmalar.", "FİKİR AŞAMASI", HEX.muted, "FaFlagCheckered"],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 2.2;
    card(s, x, 1.55, 2.05, 3.35, HEX.white, "product card " + prods[i][0]);
    await iconBadge(s, prods[i][5], x + 0.25, 1.8, 0.62, prods[i][4], HEX.ink, prods[i][0]);
    T(s, prods[i][0], { x: x + 0.25, y: 2.55, w: 1.6, h: 0.4, fontSize: 22, bold: true, fontFace: "Cambria", color: HEX.ink });
    T(s, prods[i][1], { x: x + 0.25, y: 2.95, w: 1.6, h: 0.3, fontSize: 13, bold: true, color: HEX.slate });
    T(s, prods[i][2], { x: x + 0.25, y: 3.3, w: 1.6, h: 1.0, fontSize: 12, color: HEX.slate, valign: "top" });
    chip(s, prods[i][3], x + 0.25, 4.45, 1.55, prods[i][4]);
  }
  s.addNotes("Öğrencinin 4 yıllık yolculuğu olarak anlat: önce üretir (FIRST), sonra kazanır (STEP), mentordan hızlanır (INTO), kendini yarışmada gösterir (PATH).");

  // 6 — Kanıt
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Fikir değil: çalışan bir temel", { placeholder: "title" });
  const stats = [["4", "ürün, tek ekosistem"], ["1", "ortak kullanıcı yolculuğu"], ["3", "işletim sisteminde takip istemcisi"], ["Apache-2.0", "açık kaynak lisans"]];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 2.2;
    T(s, stats[i][0], { x, y: 1.55, w: 2.0, h: 0.8, fontSize: i === 3 ? 22 : 40, bold: true, fontFace: "Cambria", color: HEX.amber, valign: "middle" });
    T(s, stats[i][1], { x, y: 2.35, w: 2.0, h: 0.5, fontSize: 12, color: HEX.muted, valign: "top" });
  }
  card(s, 0.6, 3.05, 8.8, 1.95, HEX.panel, "built panel");
  T(s, "FIRST'te bugün uygulanmış:", { x: 0.9, y: 3.2, w: 4, h: 0.3, fontSize: 14, bold: true, color: HEX.white });
  const feats = ["Google ve GitHub ile giriş", "GitHub repo bağlantısı", "Proje ilanı, başvuru ve davet", "Ekipler ve görev keşfi", "Topluluk akışı ve kişi keşfi", "Özel repodan seçili dosya vitrini"];
  for (let i = 0; i < feats.length; i++) {
    const x = 0.9 + (i % 2) * 4.2, y = 3.6 + Math.floor(i / 2) * 0.42;
    s.addImage({ data: await icon("FaCheckCircle", HEX.teal), x, y: y + 0.04, w: 0.22, h: 0.22, objectName: "check " + i });
    T(s, feats[i], { x: x + 0.35, y, w: 3.6, h: 0.3, fontSize: 13, color: HEX.white, valign: "middle" });
  }
  s.addNotes("Bu slayt güvenilirlik slaytı. STEP'in kaynak olarak geliştirildiğini, canlı ödeme ve test doğrulamasının sıradaki kilometre taşı olduğunu açıkça söyle.");

  // 7 — Flywheel
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("Her iş bir sonrakini besler", { placeholder: "title" });
  const nodes = [
    ["FIRST", "Katkı görünür olur", 1.0, 1.75, HEX.teal],
    ["STEP", "Görünürlük ücretli işe dönüşür", 4.0, 1.75, HEX.amber],
    ["INTO", "Mentor, işi ve projeyi hızlandırır", 4.0, 3.45, HEX.indigo],
    ["PATH", "Şirket problemi, yeteneği ortaya çıkarır", 1.0, 3.45, HEX.coral],
  ];
  nodes.forEach((n) => {
    card(s, n[2], n[3], 2.6, 1.3, HEX.white, "node " + n[0]);
    s.addShape(pres.shapes.OVAL, { x: n[2] + 0.2, y: n[3] + 0.2, w: 0.36, h: 0.36, fill: { color: n[4] }, line: { type: "none" }, objectName: "dot " + n[0] });
    T(s, n[0], { x: n[2] + 0.7, y: n[3] + 0.18, w: 1.7, h: 0.4, fontSize: 18, bold: true, fontFace: "Cambria", color: HEX.ink, valign: "middle" });
    T(s, n[1], { x: n[2] + 0.2, y: n[3] + 0.7, w: 2.25, h: 0.5, fontSize: 12, color: HEX.slate, valign: "top" });
  });
  const arrow = (x1, y1, x2, y2) => s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line: { color: HEX.slate, width: 2, endArrowType: "triangle" }, objectName: "flow arrow" });
  arrow(3.65, 2.4, 3.95, 2.4);
  arrow(5.3, 3.1, 5.3, 3.4);
  arrow(3.95, 4.1, 3.65, 4.1);
  arrow(2.3, 3.4, 2.3, 3.1);
  card(s, 7.1, 1.75, 2.3, 3.0, HEX.ink, "flywheel result");
  T(s, "Sonuç", { x: 7.3, y: 1.95, w: 1.9, h: 0.3, fontSize: 12, bold: true, color: HEX.amber });
  T(s, "Tek profilde birikmiş, doğrulanmış iş geçmişi. Şirketlerin ödeme yapmaya razı olduğu veri.", { x: 7.3, y: 2.35, w: 1.95, h: 2.2, fontSize: 15, bold: true, color: HEX.white, valign: "top" });
  s.addNotes("Ürünlerin tek tek değil, birlikte değerli olduğunu vurgula: her tamamlanan iş profili güçlendirir, güçlenen profil yeni iş getirir.");

  // 8 — Gelir modeli
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Değer nasıl gelire dönüşür", { placeholder: "title" });
  const rev = [
    ["FaPercent", "İş komisyonu", "STEP'te freelancer iş bedelinden %10 platform payı.", "KARARLAŞTIRILDI", HEX.amber],
    ["FaCoins", "Kredi satışı", "İlan açma, başvuru ve öne çıkarma kredi ile; krediler satın alınabilir.", "KARARLAŞTIRILDI", HEX.amber],
    ["FaHandsHelping", "Mentorluk işlemleri", "Ücretli mentorluk eşleşmelerinden işlem payı.", "PLANLANAN", HEX.indigo],
    ["FaHandshake", "Kurumsal ortaklık", "Şirketler için aday keşfi, problem sunma ve PATH etkinlikleri.", "PLANLANAN", HEX.indigo],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * 4.4, y = 1.5 + Math.floor(i / 2) * 1.75;
    card(s, x, y, 4.2, 1.6, HEX.panel, "rev card " + i);
    await iconBadge(s, rev[i][0], x + 0.25, y + 0.25, 0.62, rev[i][4], HEX.ink, "rev " + i);
    T(s, rev[i][1], { x: x + 1.1, y: y + 0.2, w: 2.9, h: 0.35, fontSize: 16, bold: true, color: HEX.white });
    T(s, rev[i][2], { x: x + 1.1, y: y + 0.58, w: 2.9, h: 0.6, fontSize: 12, color: HEX.muted, valign: "top" });
    chip(s, rev[i][3], x + 1.1, y + 1.22, 1.5, rev[i][4]);
  }
  s.addNotes("Gelir ilk günden net: işlem komisyonu ve kredi. Kredi fiyatları ve komisyon oranının nihai değerleri yönetimden yapılandırılır; bunu doğru söyle.");

  // 9 — Fark
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("Boşluk tam burada", { placeholder: "title" });
  const yes = { text: "●", options: { color: HEX.teal, bold: true, align: "center" } };
  const part = { text: "◐", options: { color: HEX.amber, bold: true, align: "center" } };
  const no = { text: "–", options: { color: HEX.muted, align: "center" } };
  const hd = (t) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: HEX.ink }, align: "center", fontSize: 12 } });
  const lbl = (t) => ({ text: t, options: { color: HEX.ink, fontSize: 13 } });
  s.addTable([
    [{ text: "", options: { fill: { color: HEX.ink } } }, hd("Klasik freelance"), hd("Eğitim platformları"), hd("4-Product One")],
    [lbl("Öğrenciye özel ve doğrulanmış"), no, part, yes],
    [lbl("Gerçek müşteri ve gerçek ödeme"), yes, no, yes],
    [lbl("Mentor desteği"), no, part, yes],
    [lbl("Kanıtlanabilir portföy ve iş geçmişi"), part, no, yes],
    [lbl("Topluluk ve ekip kurma"), no, part, yes],
    [lbl("Açık kaynak ve şeffaf"), no, no, yes],
  ], { x: 0.6, y: 1.5, w: 8.8, colW: [3.4, 1.8, 1.8, 1.8], rowH: 0.45, fontSize: 14, fontFace: "Calibri", border: { type: "solid", color: "D9DCEB", pt: 0.75 }, fill: { color: HEX.white }, valign: "middle", objectName: "comparison table" });
  T(s, "● tam karşılıyor   ◐ kısmen   – karşılamıyor.  Kategori düzeyinde genel değerlendirmedir.", { x: 0.6, y: 4.85, w: 8.8, h: 0.3, fontSize: 10, color: HEX.slate });
  s.addNotes("Marka adı vermeden kategori karşılaştırması yaptık. Toplantıda Upwork, Bionluk, Kaggle, Patika gibi somut rakipleri sözlü olarak konumlandırabilirsin.");

  // 10 — Hendek
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Kopyalanması zor olan: doğrulanmış iş geçmişi", { placeholder: "title" });
  const moat = [
    ["FaDatabase", "Veri hendeği", "Her tamamlanan iş, kimsenin sahip olmadığı doğrulanmış yetenek verisi üretir."],
    ["FaNetworkWired", "Ağ etkisi", "Öğrenci, mentor ve şirket çoğaldıkça her taraf için değer artar."],
    ["FaCodeBranch", "Açık kaynak güveni", "Şeffaf kod ve kararlar; topluluk katkısı ve denetlenebilirlik."],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 3.0;
    card(s, x, 1.7, 2.8, 3.0, HEX.panel, "moat card " + i);
    await iconBadge(s, moat[i][0], x + 0.3, 1.95, 0.75, HEX.amber, HEX.ink, "moat " + i);
    T(s, moat[i][1], { x: x + 0.3, y: 2.9, w: 2.2, h: 0.4, fontSize: 18, bold: true, color: HEX.white });
    T(s, moat[i][2], { x: x + 0.3, y: 3.4, w: 2.25, h: 1.2, fontSize: 13, color: HEX.muted, valign: "top" });
  }
  s.addNotes("Ürün kopyalanır; ama biriken, doğrulanmış iş geçmişi ve iki taraflı ağ zamanla kopyalanamaz hale gelir.");

  // 11 — Yol haritası
  s = pres.addSlide({ masterName: "LIGHT" });
  s.addText("Büyüme aşamasındayız: ağ kuruluyor", { placeholder: "title" });
  const road = [
    ["ŞİMDİ", "FIRST yayında\nSTEP canlıya hazırlık\nAçık kaynak topluluk", HEX.teal],
    ["SIRADAKİ", "Pilot üniversiteler\nİlk ücretli işler\nSTEP güvenlik ve ödeme doğrulaması", HEX.amber],
    ["ÖLÇEKLEME", "INTO mentorluk\nKurumsal ortaklar\nKullanıcı ve iş hacmi büyümesi", HEX.indigo],
    ["VİZYON", "PATH yarışmaları\nUlusal ölçek\nÇok sektörlü ekosistem", HEX.coral],
  ];
  s.addShape(pres.shapes.LINE, { x: 0.8, y: 2.0, w: 8.4, h: 0, line: { color: HEX.slate, width: 2 }, objectName: "timeline line" });
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 2.2;
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: 1.84, w: 0.32, h: 0.32, fill: { color: road[i][2] }, line: { color: HEX.pale, width: 3 }, objectName: "milestone " + i });
    T(s, road[i][0], { x: x + 0.2, y: 2.35, w: 1.9, h: 0.3, fontSize: 14, bold: true, color: HEX.ink });
    T(s, road[i][1], { x: x + 0.2, y: 2.75, w: 1.95, h: 1.6, fontSize: 13, color: HEX.slate, valign: "top", paraSpaceAfter: 6 });
  }
  card(s, 0.6, 4.4, 8.8, 0.6, HEX.ink, "roadmap banner");
  T(s, "Her adım bir sonrakinin kullanıcı, veri ve güven girdisidir.", { x: 0.9, y: 4.4, w: 8.2, h: 0.6, fontSize: 14, bold: true, color: HEX.amber, valign: "middle" });
  s.addNotes("Büyümeyi dürüst anlat: ürün temeli hazır, şimdi kullanıcı ve iş hacmi büyütme aşamasındayız. Hedef sayıları bu slayta eklemek için kendi planını gir.");

  // 12 — Yatırımla ne açılır
  s = pres.addSlide({ masterName: "DARK" });
  s.addText("Yatırım neyi açar?", { placeholder: "title" });
  const uses = [
    ["FaShieldAlt", "Güven altyapısı", "Bağımsız güvenlik denetimi, canlı ödeme sağlayıcı doğrulaması, öğrenci doğrulama."],
    ["FaUniversity", "Pilot ve büyüme", "Üniversite pilotları, topluluk yönetimi ve kullanıcı edinimi."],
    ["FaHandshake", "Şirket ve mentor ağı", "Kurumsal ortaklar, mentor kazanımı ve INTO'nun hayata geçmesi."],
    ["FaRocket", "Yeni ürün hatları", "PATH yarışma altyapısı, erişilebilirlik ve çok dillilik."],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * 4.4, y = 1.5 + Math.floor(i / 2) * 1.75;
    card(s, x, y, 4.2, 1.6, HEX.panel, "use card " + i);
    await iconBadge(s, uses[i][0], x + 0.25, y + 0.25, 0.62, HEX.amber, HEX.ink, "use " + i);
    T(s, uses[i][1], { x: x + 1.1, y: y + 0.2, w: 2.9, h: 0.35, fontSize: 16, bold: true, color: HEX.white });
    T(s, uses[i][2], { x: x + 1.1, y: y + 0.6, w: 2.9, h: 0.9, fontSize: 12, color: HEX.muted, valign: "top" });
  }
  s.addNotes("Burada yatırım tutarını ve her kalemin yüzdesini kendi bütçene göre ekle. Tutar ve dağılım koşulları görüşmede netleşir.");

  // 13 — Kapanış
  s = pres.addSlide({ masterName: "COVER" });
  s.addShape(pres.shapes.OVAL, { x: 6.0, y: -1.1, w: 5.6, h: 5.6, fill: { color: HEX.amber, transparency: 84 }, line: { type: "none" }, objectName: "glow 1" });
  s.addShape(pres.shapes.OVAL, { x: 7.8, y: 2.9, w: 3.4, h: 3.4, fill: { color: HEX.teal, transparency: 82 }, line: { type: "none" }, objectName: "glow 2" });
  s.addText("Bir nesli işsizlikle değil, deneyimle başlatalım.", { placeholder: "title" });
  T(s, "Birlikte kuralım: öğrenciyi, mentoru ve şirketi aynı ekosistemde buluşturan altyapıyı.", { x: 0.7, y: 3.55, w: 5.8, h: 0.8, fontSize: 18, color: HEX.muted, valign: "top" });
  chip(s, "github.com/caglarkc/4-product-one-community", 0.7, 4.6, 4.1, HEX.amber);
  s.addNotes("Kapanış: net bir çağrı yap. Bir sonraki adımı söyle: pilot, görüşme ya da due diligence.");

  await pres.writeFile({ fileName: "4-product-one-community-yatirimci-sunumu.pptx" });
  await applyTheme("4-product-one-community-yatirimci-sunumu.pptx", THEME);
  console.log("ok");
})();
