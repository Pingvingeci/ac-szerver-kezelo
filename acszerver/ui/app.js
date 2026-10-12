"use strict";

// Hibák gyűjtése (hibakereséshez)
window.__errs = [];
window.addEventListener("error", (e) => window.__errs.push(String(e.message)));
window.addEventListener("unhandledrejection", (e) => window.__errs.push(String(e.reason)));

/* ================================================================ ikonok */
const ICONS = {
  flag: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>',
  layers: '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
  sliders: '<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/>',
  server: '<rect width="20" height="8" x="2" y="2" rx="2"/><rect width="20" height="8" x="2" y="14" rx="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/>',
  globe: '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
  terminal: '<polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>',
  refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
  stop: '<rect x="5" y="5" width="14" height="14" rx="2"/>',
  play: '<polygon points="6 3 20 12 6 21 6 3"/>',
  route: '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
  car: '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
  activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
  gauge: '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  eye: '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>',
  settings: '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
  plug: '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/>',
  save: '<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/>',
  folder: '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  radar: '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  help: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
  image: '<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>',
  ruler: '<path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/>',
  pin: '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
};
const icon = (name, cls = "") => `<svg class="i ${cls}" viewBox="0 0 24 24">${ICONS[name] || ""}</svg>`;

/* ================================================================ segédek */
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = () => window.pywebview.api;
const RANDOM_SKIN = "Véletlenszerű";

const PAGES = {
  build: ["Összeállítás", "Válaszd ki a pályát és az autókat"],
  rules: ["Szabályok", "Sessionök, időjárás, segédletek és realizmus"],
  server: ["Szerver", "Név, jelszavak, portok és presetek"],
  network: ["Hálózat", "Elérhetőség, port nyitás és meghívó a barátoknak"],
  log: ["Napló", "A szerver élő kimenete"],
};

const WEATHER_NAMES = {
  "1_heavy_fog": "Sűrű köd", "2_light_fog": "Enyhe köd", "3_clear": "Derült", "4_mid_clear": "Gyengén felhős",
  "5_light_clouds": "Enyhén felhős", "6_mid_clouds": "Felhős", "7_heavy_clouds": "Borult",
};

// Aszfalt tapadás: 80–86% drift, 87–95% közepes, 96–100% tapadás
function gripCategory(v) {
  const n = Number(v);
  if (n <= 86) return ["drift", "Drift", "80"];
  if (n <= 95) return ["mid", "Közepes", "90"];
  return ["grip", "Tapadás", "100"];
}

const S = {
  values: {}, defaults: {}, track: null, cars: [],
  tracks: [], allCars: [], trackMap: new Map(), carMap: new Map(), weathers: [],
  status: { running: false, server_ok: false, started_at: null },
  busy: false, page: "build", net: null, linkIp: null, acPath: null, serverPath: null,
  justAdded: new Set(), unseenLog: 0,
};

/* ================================================================ indulás */
window.addEventListener("pywebviewready", boot);

async function boot() {
  hydrateIcons(document);
  buildStaticWidgets();
  bindEvents();
  initUpdates();
  setLoader("Assetto Corsa keresése…");
  let r;
  try {
    r = await api().init();
  } catch (e) {
    setLoader("Hiba történt: " + e);
    return;
  }
  if (r.need_ac) {
    S.defaults = r.defaults;
    S.values = { ...r.defaults };
    renderAll();
    hideLoader();
    const ok = await confirmBox({
      title: "Nem találom az Assetto Corsát",
      text: "Nem sikerült automatikusan megtalálni az Assetto Corsa mappáját.\nKérlek, tallózd be! Általában itt van:\n…\\Steam\\steamapps\\common\\assettocorsa",
      ok: "Tallózás", cancel: "Később",
    });
    if (ok) chooseAc();
    return;
  }
  applyInit(r);
  hideLoader();
  checkNetwork();
}

/* ================================================================ frissítések */
const UPDATE_EVERY_MS = 6 * 3600 * 1000;

async function initUpdates() {
  try {
    const v = await api().app_version();
    S.version = v.version;
    $("#appVersion").textContent = "v" + v.version;
    $("#verInfo").textContent = `v${v.version} · github.com/${v.repo}`;
  } catch (e) { /* régi háttér – nincs frissítés */ return; }
  setTimeout(() => checkUpdate(false), 4000);
  setInterval(() => checkUpdate(false), UPDATE_EVERY_MS);
}

async function checkUpdate(manual) {
  const btn = $("#updCheck");
  if (manual) { btn.disabled = true; btn.innerHTML = '<span class="spin"></span>Keresés…'; }
  try {
    const r = await api().check_update();
    if (r.error) { if (manual) toast("err", r.error); return; }
    if (r.update) showUpdateBar(r.update);
    else if (manual) toast("ok", `A legújabb verziót használod (v${S.version}).`);
  } finally {
    if (manual) { btn.disabled = false; btn.innerHTML = icon("refresh") + "Frissítés keresése"; }
  }
}

function showUpdateBar(u) {
  S.update = u;
  $("#ubVer").textContent = u.version;
  $("#ubCur").textContent = u.current;
  $("#updateBar").classList.add("show");
}

async function installUpdate() {
  if (!S.update) return;
  if (S.status.running) {
    const ok = await confirmBox({
      title: "Frissítés most?",
      text: "A frissítéshez a program bezárul, ezért a szerver leáll, és a játékosok lecsatlakoznak. A telepítés után a program magától újraindul.",
      ok: "Frissítés",
    });
    if (!ok) return;
  }
  const btn = $("#ubInstall");
  btn.disabled = true;
  $("span", btn).textContent = "Letöltés…";
  const r = await api().install_update();
  if (r.error) { toast("err", r.error); btn.disabled = false; $("span", btn).textContent = "Frissítés most"; }
}

function applyInit(r) {
  S.defaults = r.defaults;
  S.values = { ...r.defaults, ...r.values };
  S.acPath = r.ac_path;
  S.serverPath = r.server_path;
  S.status = r.status || S.status;
  setContent(r);
  // Induláskor üres összeállítás: a pályát és az autókat a felhasználó adja hozzá
  S.track = null;
  S.cars = [];
  renderAll();
  if (!r.server_path) {
    confirmBox({
      title: "Hiányzik az AC szerver",
      text: "Nem található az acServer.exe.\n\nTelepítsd a Steamben: Könyvtár → a lenyíló listában jelöld be az „Eszközök” (Tools) kategóriát → „Assetto Corsa Dedicated Server” → Telepítés.\n\nAddig is összeállíthatod a szervert, de indítani csak utána lehet.",
      ok: "Rendben", cancel: null,
    });
  }
}

function setContent(r) {
  S.tracks = r.tracks;
  S.allCars = r.cars;
  S.weathers = r.weathers;
  S.trackMap = new Map(r.tracks.map((t) => [t.key, t]));
  S.carMap = new Map(r.cars.map((c) => [c.id, c]));
  if (!S.weathers.includes(S.values["weather.graphics"])) S.values["weather.graphics"] = S.weathers.includes("3_clear") ? "3_clear" : S.weathers[0];
  if (S.track && !S.trackMap.has(S.track)) S.track = null;
  S.cars = S.cars.filter((c) => S.carMap.has(c.id));
}

function setLoader(text) { $("#loaderText").textContent = text; }
function hideLoader() { $("#loader").classList.add("gone"); }

function hydrateIcons(root) {
  $$("i[data-icon]", root).forEach((el) => {
    el.outerHTML = icon(el.dataset.icon, el.className);
  });
}

/* ================================================================ statikus elemek */
function buildStaticWidgets() {
  $$(".seg").forEach((seg) => {
    if (!$(".seg-ind", seg)) seg.insertAdjacentHTML("afterbegin", '<span class="seg-ind"></span>');
  });
}

function renderWeatherChips() {
  $("#weatherChips").innerHTML = S.weathers.map((w) => `<button data-v="${esc(w)}">${esc(WEATHER_NAMES[w] || w)}</button>`).join("");
}

/* ================================================================ események */
function bindEvents() {
  // navigáció
  $$("#nav button").forEach((b) => b.addEventListener("click", () => go(b.dataset.page)));
  window.addEventListener("resize", () => { moveNavPill(); $$(".seg").forEach(updateSeg); });

  // gomb ripple effekt
  document.addEventListener("pointerdown", (e) => {
    const b = e.target.closest(".btn");
    if (!b) return;
    const r = b.getBoundingClientRect();
    const s = Math.max(r.width, r.height);
    const span = document.createElement("span");
    span.className = "ripple";
    span.style.cssText = `width:${s}px;height:${s}px;left:${e.clientX - r.left - s / 2}px;top:${e.clientY - r.top - s / 2}px`;
    b.appendChild(span);
    setTimeout(() => span.remove(), 650);
  });

  // általános data-key mezők
  document.addEventListener("input", (e) => {
    const el = e.target;
    if (!el.dataset || !el.dataset.key) return;
    if (el.type === "checkbox") return;
    const v = el.dataset.key === "weather.hour" ? parseFloat(el.value) : el.value;
    setVal(el.dataset.key, v, el);
  });
  document.addEventListener("change", (e) => {
    const el = e.target;
    if (el.dataset && el.dataset.key && el.type === "checkbox") setVal(el.dataset.key, el.checked, el);
  });
  document.addEventListener("click", (e) => {
    // szegmentált választók és chip választók
    const gripBtn = e.target.closest(".grip-labels > button[data-grip]");
    if (gripBtn) {
      setVal("track.grip", gripBtn.dataset.grip);
      return;
    }
    const segBtn = e.target.closest("[data-key] > button[data-v], #weatherChips > button");
    if (segBtn) {
      const holder = segBtn.parentElement;
      if (holder.dataset.key) setVal(holder.dataset.key, segBtn.dataset.v);
      return;
    }
    // léptetők
    const step = e.target.closest(".stepper > button[data-step]");
    if (step) {
      const input = $("input", step.parentElement);
      const min = Number(input.min ?? -1e9), max = Number(input.max ?? 1e9);
      const cur = Number(input.value) || 0;
      const next = Math.min(max, Math.max(min, cur + Number(step.dataset.step)));
      input.value = next;
      bump(input);
      setVal(input.dataset.key, String(next), input);
    }
  });

  // összeállítás oldal
  $("#trackLane").addEventListener("click", (e) => {
    const a = e.target.closest("[data-act]");
    if (!a) return;
    if (a.dataset.act === "add-track" || a.dataset.act === "change-track") openPicker("track");
    if (a.dataset.act === "remove-track") {
      const card = $(".track-card");
      animateOut(card, () => { S.track = null; renderTrackLane(); updateSummary(); saveSoon(); });
    }
  });
  $("#carGrid").addEventListener("click", (e) => {
    const a = e.target.closest("[data-act]");
    if (!a) return;
    const card = a.closest(".car-card");
    const id = card?.dataset.id;
    if (a.dataset.act === "add-car") openPicker("car");
    else if (a.dataset.act === "remove-car") {
      animateOut(card, () => { S.cars = S.cars.filter((c) => c.id !== id); renderCars(); saveSoon(); });
    } else if (a.dataset.act === "slot-") changeSlots(id, -1, card);
    else if (a.dataset.act === "slot+") changeSlots(id, 1, card);
  });
  $("#carGrid").addEventListener("change", (e) => {
    const card = e.target.closest(".car-card");
    if (!card) return;
    const entry = S.cars.find((c) => c.id === card.dataset.id);
    if (!entry) return;
    if (e.target.matches("select")) {
      entry.skin = e.target.value;
      const wrap = $(".img-wrap", card);
      wrap.classList.remove("loaded", "noimg");
      loadImg(wrap, "car", entry.id, entry.skin === RANDOM_SKIN ? null : entry.skin);
    }
    if (e.target.matches("input.num")) {
      const n = Math.max(1, Math.min(99, parseInt(e.target.value, 10) || 1));
      entry.slots = n;
      e.target.value = n;
      updateSummary();
    }
    saveSoon();
  });

  // frissítések
  $("#updCheck").addEventListener("click", () => checkUpdate(true));
  $("#ubInstall").addEventListener("click", installUpdate);
  $("#ubClose").addEventListener("click", () => $("#updateBar").classList.remove("show"));
  $("#ubNotes").addEventListener("click", () => confirmBox({
    title: `Mi változott? (v${S.update?.version})`,
    text: (S.update?.notes || "Nincs leírás ehhez a verzióhoz.").replace(/\r/g, "").replace(/^#+\s*/gm, "").replace(/\*\*/g, ""),
    ok: "Bezárás", cancel: null,
  }));

  // indítás / leállítás
  $("#btnStart").addEventListener("click", startServer);
  $("#btnJoin").addEventListener("click", async () => {
    const r = await api().join(S.values["server.http_port"], S.values["server.password"] || "");
    if (r.ok) toast("ok", "A Content Manager csatlakozik a szerveredhez…");
    else toast("warn", r.error, 8000);
  });
  $("#btnStop").addEventListener("click", stopServer);
  $("#btnRestart").addEventListener("click", restartServer);

  // szerver oldal
  $("#pwEye").addEventListener("click", () => {
    const i = $("#pwInput");
    i.type = i.type === "password" ? "text" : "password";
  });
  $("#adminNew").addEventListener("click", () => {
    const chars = "abcdefghijkmnpqrstuvwxyz23456789";
    let p = "";
    for (let i = 0; i < 8; i++) p += chars[Math.floor(Math.random() * chars.length)];
    setVal("server.admin_password", p);
    toast("info", "Új admin jelszó generálva.");
  });
  $("#presetSave").addEventListener("click", savePreset);
  $("#presetLoad").addEventListener("click", loadPreset);
  $("#presetReset").addEventListener("click", resetDefaults);
  $("#acChange").addEventListener("click", chooseAc);
  $("#rescan").addEventListener("click", rescan);

  // hálózat oldal
  $("#netCheck").addEventListener("click", checkNetwork);
  $("#fwBtn").addEventListener("click", addFirewall);
  $("#portTest").addEventListener("click", portTest);
  $("#copyLink").addEventListener("click", () => copyText($("#linkField").value, "Link a vágólapra másolva."));
  $("#copyInvite").addEventListener("click", copyInvite);
  $("#ipChoices").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-v]");
    if (!b) return;
    S.linkIp = b.dataset.v;
    renderIpChoices();
  });

  // napló
  $("#logClear").addEventListener("click", () => { $("#log").innerHTML = '<div class="log-empty" id="logEmpty">A napló üres.</div>'; });

  // választó ablak
  $$("#picker [data-close]").forEach((b) => b.addEventListener("click", closePicker));
  $("#picker").addEventListener("mousedown", (e) => { if (e.target.id === "picker") closePicker(); });
  $("#pkSearch").addEventListener("input", () => { P.q = $("#pkSearch").value.trim().toLowerCase(); renderPicker(); });
  $("#pkFilter").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-v]");
    if (!b) return;
    P.filter = b.dataset.v;
    $$("#pkFilter button").forEach((x) => x.classList.toggle("active", x === b));
    updateSeg($("#pkFilter"));
    renderPicker();
  });
  $("#pkGrid").addEventListener("click", (e) => {
    const t = e.target.closest(".tile");
    if (t) toggleTile(t);
  });
  $("#pkGrid").addEventListener("dblclick", (e) => {
    const t = e.target.closest(".tile");
    if (!t || t.classList.contains("added")) return;
    if (!P.sel.has(t.dataset.id)) toggleTile(t);
    confirmPicker();
  });
  $("#pkOk").addEventListener("click", confirmPicker);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if ($("#picker").classList.contains("open")) closePicker();
    }
    if (e.key === "Enter" && $("#picker").classList.contains("open") && P.sel.size) confirmPicker();
  });
}

/* ================================================================ oldalak */
function go(page) {
  if (!PAGES[page]) return;
  S.page = page;
  $$("#nav button").forEach((b) => b.classList.toggle("active", b.dataset.page === page));
  $$(".page").forEach((p) => p.classList.toggle("active", p.id === "page-" + page));
  const [title, sub] = PAGES[page];
  const h = $("#pageTitle");
  h.textContent = title;
  $("#pageSub").textContent = sub;
  h.classList.remove("title-anim");
  void h.offsetWidth;
  h.classList.add("title-anim");
  moveNavPill();
  if (page === "log") {
    S.unseenLog = 0;
    updateLogBadge();
    const log = $("#log");
    log.scrollTop = log.scrollHeight;
  }
  requestAnimationFrame(() => $$(".page.active .seg").forEach(updateSeg));
}

function moveNavPill() {
  const active = $("#nav button.active");
  if (active) $("#navPill").style.transform = `translateY(${active.offsetTop}px)`;
}

/* ================================================================ értékek */
let saveTimer = null;
function setVal(key, value, src) {
  S.values[key] = value;
  syncKey(key, src);
  if (key === "server.http_port") updateLink();
  saveSoon();
}

function saveSoon() {
  saveTimer && clearTimeout(saveTimer);
  saveTimer = setTimeout(() => api().save_last(preset()), 700);
}

function syncKey(key, src) {
  const v = S.values[key];
  $$(`[data-key="${CSS.escape(key)}"]`).forEach((el) => {
    if (el.classList.contains("seg") || el.classList.contains("chip-select") || el.classList.contains("opt-grid")) {
      $$(":scope > button[data-v]", el).forEach((b) => b.classList.toggle("active", b.dataset.v === String(v)));
      if (el.classList.contains("seg")) updateSeg(el);
      return;
    }
    if (el === src) { if (el.type === "range") updateRange(el); return; }
    if (el.type === "checkbox") el.checked = !!v;
    else el.value = v ?? "";
    if (el.type === "range") updateRange(el);
  });
  if (key === "weather.hour") renderSky();
  if (key === "track.grip") {
    const [cls, label, anchor] = gripCategory(v);
    const badge = $("#gripBadge");
    badge.className = "grip-badge " + cls;
    badge.textContent = label;
    $$(".grip-labels > button").forEach((b) => b.classList.toggle("active", b.dataset.grip === anchor));
  }
  if (key === "pit.mandatory") $("#pitBlock").classList.toggle("disabled-block", !v);
}

function renderValues() {
  renderWeatherChips();
  Object.keys(S.values).forEach((k) => syncKey(k));
  renderSky();
}

function updateSeg(seg) {
  const ind = $(".seg-ind", seg);
  const active = $(":scope > button.active", seg);
  if (!ind) return;
  if (!active) { ind.style.width = "0px"; return; }
  ind.style.left = active.offsetLeft + "px";
  ind.style.width = active.offsetWidth + "px";
}

function updateRange(el) {
  const p = ((Number(el.value) - Number(el.min)) / (Number(el.max) - Number(el.min))) * 100;
  el.style.setProperty("--p", p + "%");
  const out = el.parentElement.querySelector("output");
  if (out) out.textContent = el.value + (el.dataset.suffix || "");
}

function renderSky() {
  const h = Number(S.values["weather.hour"] ?? 14);
  const t = (h - 8) / 10;
  const edge = Math.abs(t - 0.5) * 2;
  const e2 = Math.pow(edge, 1.6);
  const top = `hsl(${212 - 180 * e2}, ${70 + 15 * e2}%, ${48 - 10 * e2}%)`;
  const bottom = `hsl(${205 - 175 * e2}, ${85}%, ${74 - 12 * e2}%)`;
  const sky = $("#sky");
  sky.style.setProperty("--sky1", top);
  sky.style.setProperty("--sky2", bottom);
  const sun = $("#sun");
  sun.style.left = 8 + t * 84 + "%";
  sun.style.top = 82 - Math.sin(Math.PI * t) * 58 + "%";
  const hh = Math.floor(h), mm = Math.round((h - hh) * 60);
  $("#skyTime").textContent = `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}

function bump(el) {
  el.classList.remove("bump");
  void el.offsetWidth;
  el.classList.add("bump");
}

function preset() {
  return { values: S.values, track: S.track, cars: S.cars.map((c) => ({ id: c.id, slots: c.slots, skin: c.skin })) };
}

/* ================================================================ összeállítás */
function renderAll() {
  renderValues();
  renderTrackLane();
  renderCars();
  renderStatus();
  renderPaths();
  moveNavPill();
  $("#pageSub").textContent = PAGES[S.page][1];
}

function addCard(kind, title, sub, extra = "") {
  return `<button class="add-card ${extra}" data-act="add-${kind}"><span class="plus">${icon("plus")}</span><b>${title}</b><small>${sub}</small></button>`;
}

function imgWrap(extraCls = "") {
  return `<div class="img-wrap ${extraCls}"><img alt="">${icon("image", "noimg-icon")}</div>`;
}

function renderTrackLane() {
  const el = $("#trackLane");
  const t = S.trackMap.get(S.track);
  $("#trackChip").textContent = t ? "1 / 1" : "0 / 1";
  $("#trackChip").classList.toggle("ok", !!t);
  if (!t) {
    el.innerHTML = addCard("track", "Pálya hozzáadása", `${S.tracks.length} telepített pálya és layout közül választhatsz`, "wide empty-pulse enter");
  } else {
    const len = formatLength(t.length);
    el.innerHTML = `
      <div class="track-card enter">
        ${imgWrap()}
        <div class="tc-body">
          <span class="badge ${t.mod ? "mod" : ""}">${t.mod ? "Mod" : "Gyári"}</span>
          <h3>${esc(t.name)}</h3>
          <span class="muted">${esc(t.id)}${t.layout ? " · " + esc(t.layout) : ""}</span>
          <div class="chips">
            <span class="chip">${icon("users")}${t.pitboxes ?? "?"} pit box</span>
            ${len ? `<span class="chip">${icon("ruler")}${len}</span>` : ""}
            ${t.country ? `<span class="chip">${icon("pin")}${esc(t.country)}</span>` : ""}
          </div>
          <div class="tc-actions">
            <button class="btn sm" data-act="change-track">${icon("refresh")}Csere</button>
            <button class="btn sm ghost danger-text" data-act="remove-track">${icon("x")}Eltávolítás</button>
          </div>
        </div>
      </div>`;
    loadImg($(".img-wrap", el), "track", t.key);
  }
  updateSummary();
}

function renderCars() {
  const grid = $("#carGrid");
  const html = S.cars.map((entry) => {
    const c = S.carMap.get(entry.id);
    const isNew = S.justAdded.has(entry.id);
    const skins = [RANDOM_SKIN, ...c.skins];
    return `
      <div class="car-card ${isNew ? "enter" : ""}" data-id="${esc(c.id)}">
        <button class="card-x" data-act="remove-car" title="Eltávolítás">${icon("x")}</button>
        <div style="position:relative">${imgWrap()}<div class="overlay">${c.brand ? `<span class="badge">${esc(c.brand)}</span>` : ""}${c.mod ? '<span class="badge mod">Mod</span>' : ""}</div></div>
        <div class="cc-body">
          <h4 title="${esc(c.name)}">${esc(c.name)}</h4>
          <div class="cc-row">
            <span class="muted">Helyek</span>
            <div class="stepper"><button data-act="slot-">−</button><input class="num" type="number" min="1" max="99" value="${entry.slots}"><button data-act="slot+">+</button></div>
          </div>
          <select class="select" title="Skin">${skins.map((s) => `<option value="${esc(s)}" ${s === entry.skin ? "selected" : ""}>${esc(s === RANDOM_SKIN ? "🎲 Véletlenszerű skin" : s)}</option>`).join("")}</select>
        </div>
      </div>`;
  });
  html.push(addCard("car", S.cars.length ? "Újabb autó" : "Autó hozzáadása", `${S.allCars.length} telepített autó`, S.cars.length ? "" : "empty-pulse"));
  grid.innerHTML = html.join("");
  $$(".car-card", grid).forEach((card) => {
    const entry = S.cars.find((c) => c.id === card.dataset.id);
    loadImg($(".img-wrap", card), "car", entry.id, entry.skin === RANDOM_SKIN ? null : entry.skin);
  });
  S.justAdded.clear();
  updateSummary();
}

function changeSlots(id, delta, card) {
  const entry = S.cars.find((c) => c.id === id);
  if (!entry) return;
  entry.slots = Math.max(1, Math.min(99, entry.slots + delta));
  const input = $("input.num", card);
  input.value = entry.slots;
  bump(input);
  updateSummary();
  saveSoon();
}

function animateOut(el, done) {
  if (!el) return done();
  el.classList.add("leave");
  setTimeout(done, 280);
}

function totalSlots() { return S.cars.reduce((a, c) => a + (Number(c.slots) || 0), 0); }

function updateSummary() {
  const t = S.trackMap.get(S.track);
  const total = totalSlots();
  const pit = t?.pitboxes ?? null;
  const over = pit != null && total > pit;
  $("#capText").textContent = pit ? `${total} / ${pit}` : `${total}`;
  $("#capFill").style.width = (pit ? Math.min(100, (total / pit) * 100) : total ? 100 : 0) + "%";
  $("#capacity").classList.toggle("over", over);

  $("#statusMini").innerHTML = t
    ? `${esc(t.name)}<br>${S.cars.length} autótípus · ${total} hely`
    : "Nincs pálya kiválasztva";

  const mods = [];
  if (t?.mod) mods.push("pálya: " + t.name);
  S.cars.forEach((e) => { const c = S.carMap.get(e.id); if (c?.mod) mods.push("autó: " + c.name); });
  const banner = $("#modBanner");
  if (mods.length) {
    banner.innerHTML = `${icon("alert")}<div><b>Modolt tartalom van kiválasztva.</b> Ezeket a barátaidnak is telepíteniük kell, különben nem tudnak csatlakozni:<br><span class="muted">${mods.map(esc).join(" · ")}</span></div>`;
    banner.classList.remove("hidden");
  } else banner.classList.add("hidden");
}

function formatLength(raw) {
  const m = String(raw || "").replace(",", ".").match(/[\d.]+/);
  if (!m) return "";
  const n = parseFloat(m[0]);
  if (!isFinite(n) || n <= 0) return "";
  return n > 100 ? (n / 1000).toFixed(2) + " km" : n + " km";
}

/* ---------------- képek ---------------- */
const thumbCache = new Map();
function thumbUrl(kind, id, skin) {
  const key = `${kind}|${id}|${skin || ""}`;
  if (!thumbCache.has(key)) thumbCache.set(key, api().thumb(kind, id, skin || null).catch(() => null));
  return thumbCache.get(key);
}
async function loadImg(wrap, kind, id, skin) {
  if (!wrap) return;
  const token = `${kind}|${id}|${skin || ""}`;
  wrap.dataset.token = token;
  const url = await thumbUrl(kind, id, skin);
  if (wrap.dataset.token !== token) return;
  const img = $("img", wrap);
  if (!url) { wrap.classList.add("noimg"); return; }
  img.onload = () => wrap.classList.add("loaded");
  img.src = url;
}

/* ================================================================ választó ablak */
const P = { kind: null, sel: new Set(), filter: "all", q: "", observer: null, newIds: new Set() };

/* Megnyitáskor újraolvassuk a pályákat / autókat, hogy a közben feltett modok is látszódjanak */
async function refreshContentFor(kind) {
  const before = new Set(kind === "track" ? S.tracks.map((t) => t.key) : S.allCars.map((c) => c.id));
  let r;
  try { r = await api().rescan(); } catch (e) { return; }
  if (!r || r.error) return;
  const hadTrack = S.track, hadCars = S.cars.length;
  setContent(r);
  const now = kind === "track" ? S.tracks.map((t) => t.key) : S.allCars.map((c) => c.id);
  const added = now.filter((id) => !before.has(id));
  added.forEach((id) => P.newIds.add(id));
  if (S.track !== hadTrack) renderTrackLane();
  if (S.cars.length !== hadCars) renderCars();
  if (P.kind === kind && $("#picker").classList.contains("open") && (added.length || now.length !== before.size)) renderPicker();
  if (added.length) toast("info", `${added.length} új ${kind === "track" ? "pálya" : "autó"} található.`);
}

function openPicker(kind) {
  refreshContentFor(kind);
  P.kind = kind;
  P.sel = new Set();
  P.filter = "all";
  P.q = "";
  $("#pkSearch").value = "";
  $$("#pkFilter button").forEach((b) => b.classList.toggle("active", b.dataset.v === "all"));
  $("#pkTitle").textContent = kind === "track" ? "Pálya kiválasztása" : "Autók hozzáadása";
  $("#pkHint").textContent = kind === "track" ? "Kattints egy pályára, vagy kattints duplán a gyors kiválasztáshoz." : "Több autót is kijelölhetsz egyszerre.";
  $("#picker").classList.add("open");
  renderPicker();
  setTimeout(() => { updateSeg($("#pkFilter")); $("#pkSearch").focus(); }, 60);
}

function closePicker() {
  $("#picker").classList.remove("open");
  if (P.observer) P.observer.disconnect();
}

function renderPicker() {
  const isTrack = P.kind === "track";
  const items = (isTrack ? S.tracks : S.allCars).filter((it) => {
    if (P.filter === "stock" && it.mod) return false;
    if (P.filter === "mod" && !it.mod) return false;
    if (!P.q) return true;
    const hay = isTrack ? `${it.name} ${it.id} ${it.layout} ${it.country}` : `${it.name} ${it.id} ${it.brand}`;
    return hay.toLowerCase().includes(P.q);
  });
  const added = new Set(S.cars.map((c) => c.id));
  const grid = $("#pkGrid");
  if (!items.length) {
    grid.innerHTML = `<div class="empty-state">${icon("search")}<p style="margin-top:10px">Nincs találat.</p></div>`;
  } else {
    grid.innerHTML = items.map((it, i) => {
      const id = isTrack ? it.key : it.id;
      const isAdded = !isTrack && added.has(id);
      const isCurrent = isTrack && S.track === id;
      const sub = isTrack ? `${it.pitboxes ?? "?"} box${it.layout ? " · " + esc(it.layout) : ""}` : `${esc(it.brand || "–")} · ${it.skins.length} skin`;
      const delay = Math.min(i, 24) * 18;
      return `<div class="tile ${P.sel.has(id) ? "sel" : ""} ${isAdded ? "added" : ""}" data-id="${esc(id)}" style="animation-delay:${delay}ms">
        ${imgWrap()}
        ${it.mod ? '<span class="badge mod">Mod</span>' : ""}
        ${isAdded ? '<span class="badge added-tag">Hozzáadva</span>' : ""}
        ${isCurrent ? '<span class="badge added-tag">Jelenlegi</span>' : ""}
        ${!isAdded && !isCurrent && P.newIds.has(id) ? '<span class="badge new-tag">Új</span>' : ""}
        <span class="check">${icon("check")}</span>
        <div class="tb"><b title="${esc(it.name)}">${esc(it.name)}</b><small>${sub}</small></div>
      </div>`;
    }).join("");
  }
  if (P.observer) P.observer.disconnect();
  P.observer = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      const tile = en.target;
      P.observer.unobserve(tile);
      loadImg($(".img-wrap", tile), P.kind, tile.dataset.id, null);
    });
  }, { root: grid, rootMargin: "200px" });
  $$(".tile", grid).forEach((t) => P.observer.observe(t));
  updatePickerFoot();
}

function toggleTile(tile) {
  if (tile.classList.contains("added")) return;
  const id = tile.dataset.id;
  if (P.kind === "track") {
    P.sel = new Set([id]);
    $$("#pkGrid .tile.sel").forEach((t) => t.classList.remove("sel"));
    tile.classList.add("sel");
  } else {
    if (P.sel.has(id)) P.sel.delete(id); else P.sel.add(id);
    tile.classList.toggle("sel", P.sel.has(id));
  }
  updatePickerFoot();
}

function updatePickerFoot() {
  const n = P.sel.size;
  const ok = $("#pkOk");
  ok.disabled = n === 0;
  ok.textContent = P.kind === "track" ? "Kiválasztás" : n > 1 ? `Hozzáadás (${n})` : "Hozzáadás";
}

function confirmPicker() {
  if (!P.sel.size) return;
  setTimeout(saveSoon, 0);
  if (P.kind === "track") {
    S.track = [...P.sel][0];
    closePicker();
    renderTrackLane();
    const t = S.trackMap.get(S.track);
    toast("ok", `Pálya kiválasztva: ${t.name}`);
    if (t.pitboxes && totalSlots() > t.pitboxes) toast("warn", `Ezen a pályán csak ${t.pitboxes} pit box van. Csökkentsd a helyek számát.`);
  } else {
    const ids = [...P.sel];
    const pit = S.trackMap.get(S.track)?.pitboxes;
    ids.forEach((id, i) => {
      const free = pit ? pit - totalSlots() : 4;
      const share = pit ? Math.floor(free / (ids.length - i)) : 4;
      S.cars.push({ id, slots: Math.max(1, Math.min(4, share)), skin: RANDOM_SKIN });
      S.justAdded.add(id);
    });
    closePicker();
    renderCars();
    toast("ok", ids.length > 1 ? `${ids.length} autó hozzáadva.` : `Autó hozzáadva: ${S.carMap.get(ids[0]).name}`);
  }
}

/* ================================================================ szerver */
function renderStatus() {
  const st = S.status;
  document.body.classList.toggle("running", !!st.running);
  document.body.classList.toggle("busy", !!S.busy);
  $("#statusText").textContent = S.busy ? S.busy : st.running ? "Fut" : "Leállítva";
  const start = $("#btnStart");
  start.disabled = st.running || !!S.busy || !st.server_ok;
  $("#btnStop").disabled = !st.running || !!S.busy;
  $("#btnRestart").disabled = !st.running || !!S.busy;
  const lbl = $(".lbl", start);
  const spin = $(".spin", start);
  if (S.busy === "Indítás…") {
    lbl.textContent = "Indítás…";
    if (!spin) start.insertAdjacentHTML("afterbegin", '<span class="spin"></span>');
  } else {
    lbl.textContent = st.running ? "Fut" : "Szerver indítása";
    spin && spin.remove();
  }
}

setInterval(() => {
  const st = S.status;
  if (st.running && st.started_at) {
    const s = Math.max(0, Math.floor(Date.now() / 1000 - st.started_at));
    $("#uptime").textContent = [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60].map((x) => String(x).padStart(2, "0")).join(":");
  } else $("#uptime").textContent = "--:--:--";
}, 1000);

async function startServer() {
  if (S.busy || S.status.running) return;
  S.busy = "Indítás…";
  renderStatus();
  let r;
  try {
    r = await api().start(preset());
  } catch (e) {
    r = { ok: false, error: String(e) };
  }
  S.busy = false;
  if (r.ok) {
    S.status = r.status;
    toast("ok", "A szerver elindult! 🏁");
  } else {
    if (r.page) go(r.page);
    const b = $("#btnStart");
    b.classList.remove("shake");
    void b.offsetWidth;
    b.classList.add("shake");
    toast("err", r.error || "Nem sikerült elindítani a szervert.", 7000);
  }
  renderStatus();
}

async function stopServer() {
  if (S.busy || !S.status.running) return;
  S.busy = "Leállítás…";
  renderStatus();
  try {
    S.status = await api().stop();
  } finally {
    S.busy = false;
    renderStatus();
  }
  toast("info", "A szerver leállt.");
}

async function restartServer() {
  await stopServer();
  await startServer();
}

/* backend események */
window.onBackend = (event, data) => {
  if (event === "log") appendLog(data);
  else if (event === "status") {
    const was = S.status.running;
    S.status = data;
    renderStatus();
    if (was && !data.running && !S.busy) toast("warn", "A szerver leállt. A részleteket a Napló oldalon látod.", 6000);
  } else if (event === "toast") toast(data.kind, data.text);
  else if (event === "reach") showReach(data.state, true, data.nat, data.upnp);
  else if (event === "update_progress") {
    $("#ubProg").style.width = data + "%";
    $("#ubInstall span").textContent = data >= 100 ? "Telepítés…" : `Letöltés… ${data}%`;
  } else if (event === "update_failed") {
    toast("err", data, 8000);
    $("#ubInstall").disabled = false;
    $("#ubInstall span").textContent = "Frissítés most";
    $("#ubProg").style.width = "0";
  }
  else if (event === "confirm_close") {
    confirmBox({
      title: "Bezárod a programot?",
      text: "A szerver jelenleg fut. Ha bezárod a programot, a szerver is leáll, és a játékosok lecsatlakoznak.",
      ok: "Leállítás és bezárás",
    }).then((ok) => ok && api().quit());
  }
};

/* ================================================================ napló */
function appendLog(lines) {
  const log = $("#log");
  const empty = $("#logEmpty");
  empty && empty.remove();
  const nearBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 60;
  const frag = document.createDocumentFragment();
  lines.forEach((line) => {
    const d = document.createElement("div");
    const low = line.toLowerCase();
    if (line.startsWith("[Kezelő]")) d.className = "app";
    else if (low.includes("error") || low.includes("hiba") || low.includes("failed") || low.includes("figyelem")) d.className = "err";
    else if (low.includes("server started") || low.includes("lobby registration successful")) d.className = "ok";
    else if (low.startsWith("sending") || low.startsWith("pos:") || low.startsWith("car:")) d.className = "dim";
    d.textContent = line;
    frag.appendChild(d);
  });
  log.appendChild(frag);
  while (log.childElementCount > 3000) log.firstElementChild.remove();
  if ($("#autoScroll").checked && (nearBottom || S.page !== "log")) log.scrollTop = log.scrollHeight;
  if (S.page !== "log") {
    S.unseenLog += lines.length;
    updateLogBadge();
  }
}

function updateLogBadge() {
  const b = $("#logBadge");
  b.textContent = S.unseenLog > 99 ? "99+" : S.unseenLog;
  b.classList.toggle("show", S.unseenLog > 0);
}

/* ================================================================ hálózat */
async function checkNetwork() {
  const btn = $("#netCheck");
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>Ellenőrzés…';
  $("#verdict").className = "verdict";
  $("#verdict").innerHTML = `${icon("globe")}<div><b>Hálózat ellenőrzése…</b><span class="muted">Router, publikus IP és UPnP keresése.</span></div>`;
  try {
    S.net = await api().network();
    renderNetwork();
  } catch (e) {
    toast("err", "A hálózat ellenőrzése nem sikerült.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = icon("refresh") + "Hálózat ellenőrzése";
  }
}

function renderNetwork() {
  const n = S.net;
  if (!n) return;
  $("#netLocal").innerHTML = n.local.map((l) => `${esc(l.ip)} ${l.desc ? `<small class="muted">(${esc(l.desc)})</small>` : ""}`).join("<br>") || "–";
  $("#netPublic").innerHTML = n.public ? esc(n.public) : '<span class="danger-text">nem sikerült lekérdezni</span>';
  $("#netUpnp").innerHTML = n.upnp.ok
    ? `<span style="color:var(--green)">✔ Elérhető</span><br><small class="muted">${esc(n.upnp.text)}</small>`
    : `<span style="color:var(--warn)">✖ Nem elérhető</span><br><small class="muted">${esc(n.upnp.text)}</small>`;
  const titles = { ok: "Minden rendben", warn: "Dupla NAT észlelve", bad: "CGNAT: kívülről nem elérhető", unknown: "Nem egyértelmű" };
  const icons = { ok: "check", warn: "alert", bad: "alert", unknown: "help" };
  const v = $("#verdict");
  v.className = "verdict " + n.nat.level;
  v.innerHTML = `${icon(icons[n.nat.level])}<div><b>${titles[n.nat.level]}</b><span class="muted">${esc(n.nat.text)}</span></div>`;
  v.style.animation = "none";
  void v.offsetWidth;
  v.style.animation = "";
  if (!S.linkIp || ![n.public, ...n.local.map((l) => l.ip)].includes(S.linkIp)) S.linkIp = n.public || n.local[0]?.ip;
  renderIpChoices();
}

function renderIpChoices() {
  const n = S.net;
  if (!n) return;
  const opts = [];
  if (n.public) opts.push([n.public, "Internet"]);
  n.local.forEach((l) => opts.push([l.ip, l.desc || "helyi"]));
  $("#ipChoices").innerHTML = opts.map(([ip, d]) => `<button data-v="${esc(ip)}" class="${ip === S.linkIp ? "active" : ""}">${esc(d)}: ${esc(ip)}</button>`).join("");
  updateLink();
}

function joinLink(ip) {
  return `https://acstuff.club/s/q:race/online/join?ip=${ip}&httpPort=${Number(S.values["server.http_port"]) || 8081}`;
}

function updateLink() {
  $("#linkField").value = S.linkIp ? joinLink(S.linkIp) : "";
}

async function copyText(text, msg) {
  if (!text) { toast("warn", "Még nincs cím. Futtasd a hálózat ellenőrzését."); return; }
  const ok = await api().copy(text);
  toast(ok ? "ok" : "err", ok ? msg : "Nem sikerült a vágólapra másolni.");
}

function copyInvite() {
  if (!S.linkIp) { toast("warn", "Még nincs cím. Futtasd a hálózat ellenőrzését."); return; }
  const t = S.trackMap.get(S.track);
  const v = S.values;
  const lines = [
    `🏁 Gyere AC-zni! Szerver: ${v["server.name"]}`,
    t ? `Pálya: ${t.name}` : "",
    S.cars.length ? "Autók: " + S.cars.map((c) => S.carMap.get(c.id).name).join(", ") : "",
    `Csatlakozás Content Managerrel: ${joinLink(S.linkIp)}`,
    `Cím: ${S.linkIp}  (TCP/UDP ${v["server.tcp_port"]}, HTTP ${v["server.http_port"]})`,
    v["server.password"] ? `Jelszó: ${v["server.password"]}` : "",
  ];
  const mods = S.cars.map((c) => S.carMap.get(c.id)).filter((c) => c.mod).map((c) => c.name);
  if (t?.mod) mods.push(t.name);
  if (mods.length) lines.push("Telepítendő modok: " + mods.join(", "));
  copyText(lines.filter(Boolean).join("\n"), "Meghívó szöveg a vágólapra másolva.");
}

async function addFirewall() {
  const ok = await confirmBox({
    title: "Tűzfal szabály hozzáadása",
    text: "A Windows tűzfalon engedélyezem a szerver portjait és az acServer.exe-t.\n\nEhhez rendszergazdai jog kell: a következő ablakban (UAC) kattints az „Igen” gombra.",
    ok: "Mehet",
  });
  if (!ok) return;
  const btn = $("#fwBtn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>Folyamatban…';
  try {
    const v = S.values;
    const r = await api().firewall(v["server.tcp_port"], v["server.udp_port"], v["server.http_port"]);
    toast(r.ok ? "ok" : "warn", r.ok ? "Tűzfal szabályok hozzáadva." : "Nem sikerült hozzáadni a tűzfal szabályokat (lehet, hogy a „Nem”-et választottad).");
  } finally {
    btn.disabled = false;
    btn.innerHTML = icon("shield") + "Tűzfal szabály";
  }
}

async function portTest() {
  if (!S.status.running) {
    toast("info", "A teszthez előbb indítsd el a szervert.");
    return;
  }
  const btn = $("#portTest");
  btn.disabled = true;
  btn.innerHTML = '<span class="radar"></span>Tesztelés… (~10 mp)';
  $("#testResult").innerHTML = "";
  try {
    const r = await api().port_test(S.values["server.http_port"]);
    if (r.result === "not_running") toast("info", "A teszthez előbb indítsd el a szervert.");
    else showReach(r.result, false);
  } finally {
    btn.disabled = false;
    btn.innerHTML = icon("radar") + "Elérhetőség teszt";
  }
}

/* A kézi és az indítás utáni automatikus elérhetőség teszt eredménye */
function showReach(state, auto, nat, upnpState) {
  const box = $("#testResult");
  const tcp = S.values["server.tcp_port"], http = S.values["server.http_port"];
  const local = S.net?.gateway_ip || "a géped helyi IP-je";
  const level = (nat || S.net?.nat || {}).level;
  if (state === "testing") {
    box.innerHTML = `<div class="result info" style="display:flex;gap:10px;align-items:center"><span class="radar"></span>Automatikus elérhetőség teszt folyamatban…</div>`;
  } else if (state === "open") {
    box.innerHTML = `<div class="result ok"><b>✔ ELÉRHETŐ!</b> A szerver kívülről is látszik, a barátaid tudnak csatlakozni.</div>`;
    toast("ok", "A szerver kívülről is elérhető – a barátaid csatlakozhatnak! 🏁", 6000);
  } else if (state === "closed") {
    const cause = upnpState === "off"
      ? "<b>Ok: az automatikus port nyitás ki van kapcsolva</b> (Szerver oldal → Automatikus hálózatbeállítás).<br>"
      : upnpState === "failed"
        ? "<b>Ok: a router nem engedte a port nyitást (UPnP).</b> Kapcsold be a routeren az UPnP-t, vagy állíts be port forwardingot kézzel.<br>"
        : level === "warn"
      ? "<b>Ok: dupla NAT.</b> A szolgáltatói modemen egyszer be kell állítani a port forwardingot a routered felé (vagy bridge módot), ezt a program nem tudja megtenni helyetted.<br>"
      : level === "bad"
        ? "<b>Ok: CGNAT.</b> A szolgáltatód nem ad nyilvános IP-t, ezért csak VPN-nel (Radmin VPN / ZeroTier / Tailscale) lehet játszani.<br>"
        : "";
    box.innerHTML = `<div class="result bad"><b>✖ Kívülről NEM érhető el.</b><br>${cause}
      1) Ha az UPnP nem működött, állíts be port forwardingot a routeren: TCP+UDP ${esc(tcp)}, TCP ${esc(http)} → ${esc(local)}.<br>
      2) Dupla NAT esetén a szolgáltatói modemen is kell port forwarding (vagy bridge mód).<br>
      3) Ha semmi nem segít (pl. CGNAT): Radmin VPN / ZeroTier / Tailscale.</div>`;
    if (auto) toast("warn", "A szerver fut, de interneten keresztül nem érhető el. A részleteket a Hálózat oldalon látod.", 9000);
  } else if (state === "no_ip") {
    box.innerHTML = `<div class="result info">Nem sikerült lekérdezni a publikus IP-t. Van internetkapcsolat?</div>`;
  } else {
    box.innerHTML = `<div class="result info">A tesztelő szolgáltatás nem válaszolt. Próbáld újra kicsit később.</div>`;
  }
}

/* ================================================================ presetek, mappa */
async function savePreset() {
  const r = await api().save_preset(preset());
  if (r.ok) toast("ok", "Preset elmentve.");
  else if (r.error) toast("err", r.error);
}

async function loadPreset() {
  const r = await api().load_preset();
  if (r.cancelled) return;
  if (r.error) { toast("err", r.error); return; }
  const p = r.preset;
  S.values = { ...S.defaults, ...S.values, ...(p.values || {}) };
  S.track = S.trackMap.has(p.track) ? p.track : null;
  S.cars = (p.cars || []).filter((c) => S.carMap.has(c.id)).map((c) => ({ id: c.id, slots: Math.max(1, parseInt(c.slots, 10) || 1), skin: c.skin || RANDOM_SKIN }));
  S.cars.forEach((c) => S.justAdded.add(c.id));
  renderAll();
  setVal("server.name", S.values["server.name"]);
  if (r.missing.length) {
    confirmBox({
      title: "Hiányzó tartalom",
      text: "A preset betöltve, de ezek nincsenek telepítve ezen a gépen, ezért kimaradtak:\n\n• " + r.missing.join("\n• "),
      ok: "Rendben", cancel: null,
    });
  } else toast("ok", "Preset betöltve.");
}

async function resetDefaults() {
  const ok = await confirmBox({ title: "Alapértékek visszaállítása", text: "Visszaállítod az összes beállítást az alapértékekre? A pálya és az autók maradnak.", ok: "Visszaállítás" });
  if (!ok) return;
  const admin = S.values["server.admin_password"];
  S.values = { ...S.defaults, "server.admin_password": admin };
  renderValues();
  setVal("server.name", S.values["server.name"]);
  toast("info", "Alapértékek visszaállítva.");
}

async function chooseAc() {
  const r = await api().choose_ac_folder();
  if (r.cancelled) return;
  if (r.error) { toast("err", r.error); return; }
  const keepTrack = S.track, keepCars = S.cars;
  applyInit(r);
  S.track = r.tracks.some((t) => t.key === keepTrack) ? keepTrack : null;
  S.cars = keepCars.filter((c) => S.carMap.has(c.id));
  renderAll();
  toast("ok", "Assetto Corsa mappa beállítva.");
  checkNetwork();
}

async function rescan() {
  const btn = $("#rescan");
  btn.disabled = true;
  const r = await api().rescan();
  btn.disabled = false;
  if (r.error) { toast("err", r.error); return; }
  thumbCache.clear();
  setContent(r);
  renderAll();
  toast("ok", `Beolvasva: ${r.tracks.length} pálya/layout, ${r.cars.length} autó.`);
}

function renderPaths() {
  $("#acPath").textContent = S.acPath || "nincs kiválasztva";
  const sp = $("#srvPath");
  sp.textContent = S.serverPath || "NINCS TELEPÍTVE – Steam → Eszközök → Assetto Corsa Dedicated Server";
  sp.classList.toggle("danger-text", !S.serverPath);
}

/* ================================================================ értesítések, megerősítés */
function toast(kind, text, ms = 3800) {
  const icons = { ok: "check", warn: "alert", err: "alert", info: "info" };
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.innerHTML = `${icon(icons[kind] || "info")}<div>${esc(text)}</div><span class="bar" style="animation-duration:${ms}ms"></span>`;
  $("#toasts").appendChild(el);
  const remove = () => { el.classList.add("out"); setTimeout(() => el.remove(), 350); };
  const timer = setTimeout(remove, ms);
  el.addEventListener("click", () => { clearTimeout(timer); remove(); });
  while ($("#toasts").childElementCount > 4) $("#toasts").firstElementChild.remove();
}

function confirmBox({ title, text, ok = "OK", cancel = "Mégse" }) {
  return new Promise((resolve) => {
    const m = $("#confirm");
    $("#cfTitle").textContent = title;
    $("#cfBody").textContent = text;
    const okBtn = $("#cfOk"), cancelBtn = $("#cfCancel");
    okBtn.textContent = ok;
    cancelBtn.classList.toggle("hidden", cancel === null);
    if (cancel) cancelBtn.textContent = cancel;
    const close = (val) => {
      m.classList.remove("open");
      okBtn.onclick = cancelBtn.onclick = null;
      resolve(val);
    };
    okBtn.onclick = () => close(true);
    cancelBtn.onclick = () => close(false);
    m.classList.add("open");
  });
}
