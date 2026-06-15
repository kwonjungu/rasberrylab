// Science AI Lab — 학생 화면 메인 (Alpine 컴포넌트)
// 화면(screen): "map"(탐험 지도/스테이지 선택) → "mission"(실험 수행 챗)
// 1 Pi = 1 모둠. 한 번에 한 말풍선, 빠른답변 즉답, 자유질문은 LLM 스트리밍.

// 실험별 테마(아이콘·한 줄 소개) — 지도 위 스테이지 표현용
const MISSION_THEME = {
  "exp-3-magnet-distance":   { icon: "🧲", tag: "자석의 힘을 거리로 측정!" },
  "exp-3-sound-clap":        { icon: "🔊", tag: "박수 소리의 크기를 잡아라" },
  "exp-3-ice-melt-temp":     { icon: "🧊", tag: "얼음이 녹는 온도의 비밀" },
  "exp-4-shadow-light-block":{ icon: "🌑", tag: "그림자는 얼마나 빛을 막을까" },
  "exp-4-vibration-shock":   { icon: "🌋", tag: "흔들림의 세기를 기록하라" },
  "exp-5-insulation-compare":{ icon: "🔥", tag: "어떤 재료가 따뜻함을 지킬까" },
  "exp-5-motion-ultrasonic": { icon: "🚗", tag: "거리와 속도를 추적하라" },
  "exp-5-rc-acceleration":   { icon: "🏎️", tag: "RC카의 가속도에 도전!" },
  "exp-6-auto-light":        { icon: "💡", tag: "어두우면 켜지는 자동 불빛" },
  "exp-6-heartbeat":         { icon: "❤️", tag: "운동하면 심장은 얼마나 빨라질까" },
  "exp-6-color-mixing":      { icon: "🎨", tag: "빛의 색을 섞어보자" },
  "exp-fusion-auto-door":    { icon: "🚪", tag: "스스로 열리는 자동문 시스템" },
  "exp-fusion-self-driving": { icon: "🤖", tag: "장애물을 피하는 자율주행" },
  "exp-fusion-smart-plant":  { icon: "🌱", tag: "빛·온습도로 돌보는 스마트 화분" },
  "exp-6-electric-signal":   { icon: "🚦", tag: "전기로 켜는 신호등·경보기" },
  "exp-4-quake-alarm":       { icon: "🌍", tag: "흔들림을 잡는 지진 경보기" },
  "exp-fusion-servo-gate":   { icon: "🚧", tag: "다가오면 열리는 자동 차단기" },
  "exp-3-incubator":         { icon: "🐣", tag: "따뜻함을 지키는 부화기" },
  "exp-3-animal-detector":   { icon: "🦔", tag: "밤에 누가 지나갔지? 동물 감지기" },
  "exp-5-weather-station":   { icon: "⛅", tag: "우리 반 날씨 관측소" },
  "exp-6-flame-detector":    { icon: "🔥", tag: "촛불 탐정·화재 경보기" },
  "exp-fusion-buzzer-piano": { icon: "🎹", tag: "소리를 만드는 미니 피아노" },
  "exp-6-moon-phase":        { icon: "🌙", tag: "빛으로 보는 달의 위상" },
};

// 학년 → 지도 구역(월드) 메타
const REGION_META = {
  3: { key: "g3", emoji: "🌱", name: "3학년 · 호기심 마을",  klass: "rg-3" },
  4: { key: "g4", emoji: "🔭", name: "4학년 · 탐험 언덕",    klass: "rg-4" },
  5: { key: "g5", emoji: "⚡", name: "5학년 · 실험 계곡",    klass: "rg-5" },
  6: { key: "g6", emoji: "🚀", name: "6학년 · 발견 봉우리",  klass: "rg-6" },
  0: { key: "fx", emoji: "🛰", name: "융합 · 도전 기지",     klass: "rg-fx" },
};
const REGION_ORDER = [3, 4, 5, 6, 0];

function labApp() {
  return {
    // ---- 화면 ----
    screen: "map", // map | mission

    // ---- 스토리/몰입 ----
    story: window.SciStory,
    showStory: false,
    briefLine: "",
    stepImage: null,
    currentExp: null,
    celebrate: { show: false, rank: { icon: "🌱", name: "새싹 탐험가" }, line: "" },

    // ---- 지도 상태 ----
    experiments: [],
    gradeFilter: "all", // all | 3 | 4 | 5 | 6 | 0
    briefing: null,     // 미션 브리핑에 띄울 실험 객체
    kit: {},            // sensor_id → {kit_no, label, photo} (실제 키트 사진 매핑)

    // ---- 세션 상태 ----
    sessionId: null,
    mode: "greeting",
    grade: null,
    gradeTier: "upper", // lower(3~4) | upper(5~6)
    teamName: "",
    expTitle: "",
    stepN: 0,
    totalSteps: 0,
    instruction: "",
    durationSec: 0,
    quickReplies: [],
    safetyWarnings: [],

    bubble: "", // 현재 AI 말풍선
    bubbleHtml: "",
    thinking: false,
    inputText: "",
    history: [], // {role, text}
    showHistory: false,
    sensor: null, // (구) 단일 센서 위젯 — 미사용
    timer: { total: 0, left: 0, handle: null },

    // 안전수칙·역할·도움·막힘
    showSafety: false,
    safety: { intro: "", call: "", rules: [] },
    stuckCount: 0,
    blink: false,
    showRoles: false,
    roleCards: [],
    roleNames: {},

    // 교사 모드
    teacherMode: false,
    teacherView: {},
    injectText: "",
    pdfUrl: null,
    _idle: null,

    // 실시간 ESP 센서
    espDevices: [],
    spark: {}, // {espId_sensor: [값...]}
    sensorWs: null,

    // ---- 실시간 신호/데이터 ----
    sensorLive: {},      // "esp_sensor" → {esp, sensor, value, unit, ts}
    sensorPulse: {},     // "esp_sensor" → bool (도착 펄스)
    nowTick: Date.now(), // 1초 틱 (신선도 재계산용)
    dataLog: [],         // {t, esp, sensor, value, unit} — micro:bit식 기록
    showData: false,     // 데이터 패널 토글
    firstSignal: false,  // 첫 신호 도착 여부 (성공 연출용)
    signalToast: "",     // 일시 안내 배너
    sfxMuted: false,

    // 이어하기
    resumeInfo: null,
    showResume: false,

    // ---- 초기화 ----
    async init() {
      const p = new URLSearchParams(location.search);
      this.teamName = p.get("team") || "";
      this.demoMode = p.get("demo") === "1";
      // 부팅 시 미완료 세션 감지 → 이어하기 제안 (launcher가 ?resume=1 부여)
      if (p.get("resume") === "1") {
        const latest = await fetch("/api/checkpoints/latest").then((x) => x.json()).catch(() => ({}));
        if (latest.has_pending) {
          this.resumeInfo = latest;
          this.showResume = true;
        }
      }
      await this.loadMap();
      // URL에 exp가 명시되면 곧바로 그 미션으로 진입(런처/QR 호환)
      const directExp = p.get("exp");
      if (directExp && !this.showResume) {
        const e = this.experiments.find((x) => x.id === directExp);
        if (e) { await this.startMission(e); return; }
      }
      // 첫 방문이면 라비의 스토리 인트로 1회 노출
      if (!this.showResume && !localStorage.getItem("sci_intro_seen")) {
        this.showStory = true;
      }
    },

    closeStory() {
      this.showStory = false;
      try { localStorage.setItem("sci_intro_seen", "1"); } catch (e) {}
    },

    // ================= 탐험 지도 =================
    async loadMap() {
      // 실제 센서 키트 사진 매핑(준비물 가이드용)
      this.kit = await fetch("/assets/kit/kit_map.json").then((x) => x.json()).catch(() => ({}));
      const r = await fetch("/api/data/experiments").then((x) => x.json()).catch(() => ({}));
      const items = r.experiments || [];
      // 학년 → 난이도 순으로 정렬해 길 위에 자연스럽게 배치
      items.sort((a, b) => (a.grade - b.grade) || (a.difficulty - b.difficulty));
      this.experiments = items;
    },
    theme(exp) {
      return MISSION_THEME[exp.id] || { icon: "🔬", tag: exp.title };
    },
    // 필터 적용된 구역 목록(렌더용): [{meta, stages:[{exp, n, side}]}]
    get regions() {
      const out = [];
      for (const g of REGION_ORDER) {
        if (this.gradeFilter !== "all" && String(g) !== String(this.gradeFilter)) continue;
        const list = this.experiments.filter((e) => e.grade === g);
        if (!list.length) continue;
        out.push({
          meta: REGION_META[g],
          stages: list.map((exp, i) => ({ exp, n: i + 1, side: i % 2 === 0 ? "left" : "right" })),
        });
      }
      return out;
    },
    stars(n) { return "⭐".repeat(Math.max(1, Math.min(5, n || 1))); },
    safetyBadge(level) {
      return ({
        low:    { txt: "안전 ✅", klass: "sf-low" },
        medium: { txt: "주의 ⚠️", klass: "sf-mid" },
        high:   { txt: "조심 🔥", klass: "sf-high" },
      })[level] || { txt: "안전 ✅", klass: "sf-low" };
    },

    // ---- 미션 브리핑 ----
    openBriefing(exp) {
      this.briefing = exp;
      this.briefLine = this.story ? this.story.brief(exp.id, exp.title) : "";
      this.sfx("select");
    },
    closeBriefing() { this.briefing = null; },

    // ================= 미션 시작/세션 =================
    async startMission(exp) {
      const team = this.teamName || "다람쥐";
      const r = await fetch("/api/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_name: team, grade: exp.grade || 5, experiment_id: exp.id }),
      }).then((x) => x.json());
      this.sessionId = r.session_id;
      this.currentExp = exp;
      this.briefing = null;
      this.celebrate.show = false;
      this.screen = "mission";
      this.history = [];
      this.roleCards = (await fetch("/api/session/roles/cards").then((x) => x.json()).catch(() => ({}))).roles || [];
      this.connectSensorWs();
      await this.loadCurrent();
    },
    backToMap() {
      this.clearTimer();
      this.celebrate.show = false;
      this.stepImage = null;
      this.screen = "map";
      this.bubble = "";
      this.bubbleHtml = "";
    },

    // ---- 실시간 센서 WebSocket ----
    connectSensorWs() {
      // 신선도(신호 들어오는 중/끊김) 1초마다 재계산
      if (!this._tick) this._tick = setInterval(() => { this.nowTick = Date.now(); }, 1000);
      if (this.demoMode) this.startDemoFeed();   // ?demo=1: 가짜 신호 주입
      if (this.sensorWs && this.sensorWs.readyState <= 1) return; // 이미 연결됨
      try {
        const proto = location.protocol === "https:" ? "wss" : "ws";
        const ws = new WebSocket(`${proto}://${location.host}/ws/sensors`);
        this.sensorWs = ws;
        ws.onmessage = (e) => {
          const ev = JSON.parse(e.data);
          if (ev.type === "snapshot") this.espDevices = ev.devices || [];
          else if (ev.type === "esp_status") this.refreshEsp();
          else if (ev.type === "data") {
            this.refreshEsp();
            this.onSensorData(ev);
          } else if (ev.type === "message" && ev.source === "rule") {
            this.setBubble(ev.content, true); // 라이브 룰 피드백을 챗에 자동 표시
          }
        };
        ws.onclose = () => setTimeout(() => this.connectSensorWs(), 3000); // 자동 재연결
      } catch (e) {
        /* WS 미지원이면 폴링 생략 */
      }
    },
    async refreshEsp() {
      this.espDevices = (await fetch("/api/sensors/active").then((x) => x.json()).catch(() => ({}))).devices || [];
    },
    // 센서 1건 처리(실시간 값·펄스·기록·효과음) — WS와 데모 공용
    onSensorData(ev) {
      const key = `${ev.esp_id}_${ev.sensor}`;
      const arr = this.spark[key] || [];
      arr.push(ev.value);
      if (arr.length > 30) arr.shift();
      this.spark[key] = arr;
      this.sensorLive = { ...this.sensorLive, [key]: { esp: ev.esp_id, sensor: ev.sensor, value: ev.value, unit: ev.unit || "", ts: Date.now() } };
      this.sensorPulse = { ...this.sensorPulse, [key]: true };
      setTimeout(() => { this.sensorPulse = { ...this.sensorPulse, [key]: false }; }, 480);
      this.dataLog.push({ t: Date.now(), esp: ev.esp_id, sensor: ev.sensor, value: ev.value, unit: ev.unit || "" });
      if (this.dataLog.length > 3000) this.dataLog.shift();
      if (!this.firstSignal) { this.firstSignal = true; this.sfx("connect"); this.flashSignal("센서 연결 성공! 신호가 들어와요 🎉"); }
      else this.sfx("blip");
    },
    // 데모 신호 주입 (?demo=1) — 실제 센서 없이 대시보드/데이터/효과음 테스트
    startDemoFeed() {
      if (this._demo) return;
      const sensors = [
        { esp: "demo-01", sensor: "temperature", unit: "°C", base: 22, amp: 6 },
        { esp: "demo-02", sensor: "photoresistor", unit: "lux", base: 300, amp: 180 },
      ];
      let k = 0;
      this._demo = setInterval(() => {
        k++;
        for (const s of sensors) {
          const v = Math.round((s.base + Math.sin(k / 3 + s.base) * s.amp) * 10) / 10;
          this.onSensorData({ esp_id: s.esp, sensor: s.sensor, value: v, unit: s.unit });
        }
      }, 1200);
    },
    espIcon(status) {
      return status === "alive" ? "🤖" : status === "dead" ? "😵" : "😴";
    },

    // ===== 효과음 =====
    sfx(name) {
      const s = window.SciAI && SciAI.sfx; if (!s) return;
      if (name === "blip") s.blipThrottled(); else s.play(name);
    },
    toggleMute() {
      this.sfxMuted = !this.sfxMuted;
      if (window.SciAI && SciAI.sfx) SciAI.sfx.setMuted(this.sfxMuted);
      if (!this.sfxMuted) this.sfx("click");
    },

    // ===== 실시간 신호 대시보드 =====
    get liveSensors() {
      return Object.values(this.sensorLive)
        .sort((a, b) => (a.esp + a.sensor).localeCompare(b.esp + b.sensor));
    },
    get liveCount() {
      return Object.values(this.sensorLive).filter((it) => this.nowTick - it.ts < 4000).length;
    },
    // 신호 신선도: 4초내=수신중 / 12초내=느림 / 그외=끊김 (nowTick 의존 → 1초마다 갱신)
    sig(it) {
      const age = this.nowTick - it.ts;
      if (age < 4000) return { cls: "live", dot: "on", label: "📡 신호 들어오는 중" };
      if (age < 12000) return { cls: "slow", dot: "slow", label: "신호가 느려요…" };
      return { cls: "stale", dot: "off", label: "신호 끊김 ⚠" };
    },
    fmtVal(v) {
      return (typeof v === "number" && !Number.isInteger(v)) ? v.toFixed(1) : v;
    },
    // 노드 파이프라인 표시용
    get pipeSensorName() {
      const l = this.liveSensors[0];
      if (l) return this.sensorLabel(l.sensor);
      const d = this.espDevices[0];
      return (d && (d.sensor_type)) ? this.sensorLabel(d.sensor_type) : "센서 대기";
    },
    get pipeEspName() {
      const l = this.liveSensors[0];
      return (l && l.esp) || (this.espDevices[0] && this.espDevices[0].id) || "연결 대기";
    },
    get anyPulse() {
      return Object.values(this.sensorPulse).some(Boolean);
    },
    sensorLabel(id) {
      return (this.kit[id] && this.kit[id].label) || id;
    },
    flashSignal(msg) {
      this.signalToast = msg;
      clearTimeout(this._sigT);
      this._sigT = setTimeout(() => { this.signalToast = ""; }, 2600);
    },

    // ===== 데이터(마이크로비트 스타일) =====
    toggleData() { this.sfx("click"); this.showData = !this.showData; },
    clearLog() { this.sfx("warn"); this.dataLog = []; },
    downloadCsv() {
      this.sfx("success");
      if (!this.dataLog.length) return;
      const head = ["시간", "ESP", "센서", "값", "단위"];
      const esc = (c) => `"${String(c).replace(/"/g, '""')}"`;
      const lines = [head.map(esc).join(",")];
      for (const d of this.dataLog) {
        lines.push([new Date(d.t).toLocaleString("ko-KR"), d.esp, d.sensor, d.value, d.unit || ""].map(esc).join(","));
      }
      const csv = "﻿" + lines.join("\r\n"); // BOM → 엑셀 한글 깨짐 방지
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const stamp = new Date().toISOString().slice(0, 16).replace(/[:T]/g, "-");
      a.href = url;
      a.download = `${this.teamName || "실험"}_${(this.expTitle || "데이터").replace(/\s+/g, "")}_${stamp}.csv`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    },
    get dataPreview() {
      return this.dataLog.slice(-40).reverse();
    },
    sparkPoints(esp, sensor) {
      const arr = this.spark[`${esp}_${sensor}`] || [];
      if (arr.length < 2) return "";
      const max = Math.max(...arr), min = Math.min(...arr), rng = max - min || 1;
      return arr.map((v, i) => `${(i / (arr.length - 1)) * 100},${30 - ((v - min) / rng) * 28}`).join(" ");
    },

    applyGrade() {
      this.gradeTier = this.grade && this.grade <= 4 ? "lower" : "upper";
      document.body.dataset.gradeTier = this.gradeTier;
    },

    async loadCurrent() {
      const c = await fetch(`/api/session/${this.sessionId}/current`).then((x) => x.json());
      if (c.error) return;
      this.mode = c.mode;
      this.grade = c.grade;
      this.teamName = c.team_name || this.teamName || "";
      this.expTitle = c.experiment_title || "";
      this.stepN = c.step_n;
      this.totalSteps = c.total_steps;
      this.instruction = c.instruction || "";
      this.durationSec = c.duration_sec || 0;
      this.quickReplies = c.quick_replies || [];
      this.safetyWarnings = c.safety_warnings || [];
      this.stepImage = c.image_path || null;
      this.applyGrade();
      // 화면이 나올 때 미션/안내문을 자동으로 읽어주지 않음(요청).
      // 듣고 싶으면 말풍선의 "🔊 다시 듣기" 버튼 사용.
      this.setBubble(this.instruction, false);
      if (this.durationSec > 0) this.startTimer(this.durationSec);
      // 실험 모드 진입 시 안전수칙 복창(미완료면 게이트)
      if (this.mode === "experiment") await this.checkSafety();
    },

    // ---- 진행률(미션 HUD) ----
    get progressPct() {
      return this.totalSteps ? Math.round((this.stepN / this.totalSteps) * 100) : 0;
    },

    // ---- 안전수칙 복창 ----
    async checkSafety() {
      const d = await fetch(`/api/session/${this.sessionId}/safety`).then((x) => x.json());
      if (d.error) return;
      this.safety = d;
      this.showSafety = !d.done;
    },
    async confirmSafety() {
      await fetch(`/api/session/${this.sessionId}/safety/done`, { method: "POST" });
      this.showSafety = false;
    },

    // ---- 역할 선택 ----
    async saveRoles() {
      await fetch("/api/session/roles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: this.sessionId, role_assignments: this.roleNames }),
      });
      this.showRoles = false;
    },

    // ---- 도움요청 → GPIO 부저·LED ----
    // 🤚 도와줘 → AI(라비)와 직접 대화. 지금 단계 맥락으로 즉시 도움 요청.
    async askAiHelp() {
      this.sfx("help");
      this.history.push({ role: "user", text: "🤚 도와줘" });
      const q = `지금 "${this.expTitle || '이 미션'}"의 ${this.stepN}단계에서 막혔어. `
              + `${this.instruction ? "단계 안내는 '" + this.instruction + "' 야. " : ""}`
              + `어떻게 하면 되는지 쉽고 친절하게 알려줘. 궁금한 걸 더 물어볼 수도 있어.`;
      await this.send({ input_type: "text", payload: { text: q } });
      try { this.$nextTick(() => { const el = document.getElementById("chatInput"); if (el) el.focus(); }); } catch (e) {}
    },
    // (선택) 실제 교사 호출 — 부저/LED. 현재 도움 버튼은 AI 대화로 동작.
    async callTeacher() {
      this.sfx("help");
      const r = await fetch(`/api/session/${this.sessionId}/help`, { method: "POST" }).then((x) => x.json()).catch(() => ({}));
      this.history.push({ role: "user", text: "🔔 선생님 호출" });
      this.setBubble(r.message || "선생님께 알렸어요! 🔔");
      if (r.signal && r.signal.fallback === "screen_blink") {
        this.blink = true;
        setTimeout(() => (this.blink = false), 1500);
      }
    },

    // ---- 말풍선 ----
    setBubble(text /*, speak (TTS 제거됨) */) {
      this.bubble = text || "";
      this.bubbleHtml = SciAI.md(this.bubble);
      if (text) this.history.push({ role: "assistant", text });
    },

    // ---- 타이머 ----
    startTimer(sec) {
      this.clearTimer();
      this.timer.total = sec;
      this.timer.left = sec;
      this.timer.handle = setInterval(() => {
        this.timer.left--;
        if (this.timer.left <= 0) this.clearTimer();
      }, 1000);
    },
    clearTimer() {
      if (this.timer.handle) clearInterval(this.timer.handle);
      this.timer.handle = null;
    },
    get timerPct() {
      return this.timer.total ? Math.max(0, (this.timer.left / this.timer.total) * 100) : 0;
    },

    // ---- 빠른답변 버튼 ----
    async onQuick(btn) {
      this.sfx("click");
      if (btn.id === "begin") {
        this.sfx("step");
        await fetch(`/api/session/${this.sessionId}/step/next`, { method: "POST" });
        await this.loadCurrent();
        return;
      }
      if (btn.id === "help") {
        await this.askAiHelp();
        return;
      }
      this.history.push({ role: "user", text: btn.label });
      // '다 했어요' → AI 확인 후 통과(핵심 단계만 게이트)
      if (btn.id === "done") { await this.tryAdvance(); return; }
      // 막힘 신호: stuck/repeat 연속 2회 이상이면 도움 권유
      if (btn.id === "stuck" || btn.id === "repeat") {
        this.stuckCount++;
      } else {
        this.stuckCount = 0;
      }
      await this.send({ input_type: "quick_reply", payload: { button_id: btn.id } });
      if (this.stuckCount >= 2) {
        setTimeout(() => this.setBubble("막히면 🤚 도와줘를 눌러줘. 내가 바로 도와줄게! 🤖"), 800);
        this.stuckCount = 0;
      }
    },

    // AI 단계 확인 → 통과해야 다음 단계. 핵심(데이터수집) 단계만 게이트, 나머지는 자동 통과.
    async tryAdvance() {
      if (this.totalSteps <= 0) return;
      this.verifying = true;
      this.setBubble("🤖 라비가 데이터를 확인하고 있어요...");
      let v = { pass: true };
      try {
        v = await fetch(`/api/session/${this.sessionId}/step/verify`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answer: (this.inputText || "").trim() }),
        }).then((x) => x.json());
      } catch (e) { v = { pass: true }; }
      this.verifying = false;
      if (v && v.error) v = { pass: true };

      if (v.pass) {
        this.sfx("success");
        if (v.gated && v.feedback) this.setBubble("✅ " + v.feedback);
        if (this.stepN < this.totalSteps) {
          this.sfx("step");
          this.inputText = "";
          await fetch(`/api/session/${this.sessionId}/step/next`, { method: "POST" });
          setTimeout(() => this.loadCurrent(), 700);
        } else {
          setTimeout(() => this.celebrateClear(), 600);
        }
      } else {
        this.sfx("warn");
        this.setBubble("🤔 " + (v.feedback || "조금 더 해볼까? 측정을 다시 확인해줘.")
          + "  준비되면 다시 ✅ 를 누르거나, 무엇을 관찰했는지 아래에 적어줘!");
      }
    },

    // ---- 미션 클리어 축하 연출 ----
    celebrateClear() {
      const exp = this.currentExp;
      const diff = exp ? exp.difficulty : 1;
      this.clearTimer();
      this.celebrate = {
        show: true,
        rank: this.story ? this.story.rankFor(diff) : { icon: "🏆", name: "탐험가" },
        line: this.story && exp ? this.story.clear(exp.id) : "미션 성공! 🎉",
      };
      this.sfx("celebrate");
    },

    // ---- 자유 텍스트 전송 ----
    async sendText() {
      const t = this.inputText.trim();
      if (!t) return;
      this.history.push({ role: "user", text: t });
      this.inputText = "";
      await this.send({ input_type: "text", payload: { text: t } });
    },

    // ---- 공통 전송 + SSE 처리 ----
    async send(extra) {
      const body = { session_id: this.sessionId, ...extra };
      let streaming = false;
      await SciAI.streamChat(body, (evt) => {
        if (evt.type === "thinking") {
          this.thinking = true;
          this.bubble = "";
          this.bubbleHtml = "";
        } else if (evt.type === "token") {
          this.thinking = false;
          streaming = true;
          this.bubble += evt.content;
          this.bubbleHtml = SciAI.md(this.bubble);
        } else if (evt.type === "message") {
          this.thinking = false;
          this.setBubble(evt.content, true); // 스크립트/룰 즉답 + TTS
        } else if (evt.type === "silent") {
          this.thinking = false; // 조용히 무응답
        } else if (evt.type === "done") {
          this.thinking = false;
          if (streaming) this.history.push({ role: "assistant", text: this.bubble });
        }
      });
    },


    // ---- 이어하기 ----
    async doResume() {
      const sid = this.resumeInfo.session_id;
      await fetch(`/api/checkpoints/resume/${sid}`, { method: "POST" });
      this.sessionId = sid;
      this.showResume = false;
      this.screen = "mission";
      this.roleCards = (await fetch("/api/session/roles/cards").then((x) => x.json()).catch(() => ({}))).roles || [];
      this.connectSensorWs();
      await this.loadCurrent();
      // 이어하기는 안전수칙 간소 재복창(resafety) — checkResume에서 게이트
    },
    startFresh() {
      this.showResume = false; // 지도에 머무름
    },

    // ---- 교사 모드 (PIN, 30초 자동 복귀) ----
    async openTeacher() {
      const pin = prompt("교사 PIN을 입력하세요");
      if (pin === null) return;
      const r = await fetch("/api/teacher/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin }),
      }).then((x) => x.json());
      if (!r.ok) {
        alert(r.message || "PIN이 달라요.");
        return;
      }
      this.teacherMode = true;
      window.studentMode = false; // 교사: 브라우저 기능 복원
      await this.refreshTeacher();
      this.resetIdle();
    },
    async refreshTeacher() {
      this.teacherView = await fetch(`/api/teacher/${this.sessionId}/view`).then((x) => x.json());
    },
    resetIdle() {
      if (this._idle) clearTimeout(this._idle);
      // 30초 무입력 → 자동 학생 모드 복귀(보호 재활성)
      this._idle = setTimeout(() => {
        this.teacherMode = false;
        window.studentMode = true;
      }, 30000);
    },
    async teacherNext() {
      await fetch(`/api/session/${this.sessionId}/step/next`, { method: "POST" });
      await this.refreshTeacher();
      this.resetIdle();
    },
    async teacherControl(action) {
      await fetch("/api/teacher/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: this.sessionId, action }),
      });
      await this.refreshTeacher();
      this.resetIdle();
    },
    async teacherInject() {
      if (!this.injectText.trim()) return;
      await fetch("/api/teacher/inject", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: this.sessionId, content: this.injectText }),
      });
      this.setBubble(this.injectText, true);
      this.injectText = "";
      this.resetIdle();
    },
    async endSession() {
      const r = await fetch(`/api/session/${this.sessionId}/end`, { method: "POST" }).then((x) => x.json());
      this.pdfUrl = r.pdf;
      this.resetIdle();
    },
  };
}
window.labApp = labApp;
