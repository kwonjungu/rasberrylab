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
  "exp-fusion-smart-plant":  { icon: "🌱", tag: "스마트 화분 자동 돌봄" },
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
    ttsOn: true,
    sensor: null, // {label, value, unit}
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

    // 이어하기
    resumeInfo: null,
    showResume: false,

    // ---- 초기화 ----
    async init() {
      const p = new URLSearchParams(location.search);
      this.teamName = p.get("team") || "";
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
      SciAI.speak(this.briefLine || `${exp.title}. 미션을 시작할까요?`, false);
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
            const key = `${ev.esp_id}_${ev.sensor}`;
            const arr = this.spark[key] || [];
            arr.push(ev.value);
            if (arr.length > 30) arr.shift();
            this.spark[key] = arr;
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
    espIcon(status) {
      return status === "alive" ? "🤖" : status === "dead" ? "😵" : "😴";
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
      // 저학년: TTS 자동재생 ON, 고학년: OFF (age_adapter 규칙)
      this.ttsOn = this.gradeTier === "lower";
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
    async callHelp() {
      const r = await fetch(`/api/session/${this.sessionId}/help`, { method: "POST" }).then((x) => x.json());
      this.history.push({ role: "user", text: "🤚 도와줘" });
      this.setBubble(r.message || "선생님께 알렸어요! 🔔", true);
      // GPIO가 없으면 화면 깜빡임으로 대체
      if (r.signal && r.signal.fallback === "screen_blink") {
        this.blink = true;
        setTimeout(() => (this.blink = false), 1500);
      }
    },

    // ---- 말풍선 ----
    setBubble(text, speak) {
      this.bubble = text || "";
      this.bubbleHtml = SciAI.md(this.bubble);
      if (text) this.history.push({ role: "assistant", text });
      if (speak) SciAI.speak(text, this.ttsOn);
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
      if (btn.id === "begin") {
        await fetch(`/api/session/${this.sessionId}/step/next`, { method: "POST" });
        await this.loadCurrent();
        return;
      }
      if (btn.id === "help") {
        await this.callHelp();
        return;
      }
      this.history.push({ role: "user", text: btn.label });
      // 막힘 신호: stuck/repeat 연속 2회 이상이면 도움 권유
      if (btn.id === "stuck" || btn.id === "repeat") {
        this.stuckCount++;
      } else {
        this.stuckCount = 0;
      }
      await this.send({ input_type: "quick_reply", payload: { button_id: btn.id } });
      if (this.stuckCount >= 2) {
        setTimeout(() => this.setBubble("선생님을 부를까? 🤚 도와줘 버튼을 눌러봐.", true), 800);
        this.stuckCount = 0;
      }
      // 'done' 이면 다음 단계로 진행 — 마지막 단계면 미션 클리어 축하
      if (btn.id === "done") {
        if (this.stepN < this.totalSteps) {
          await fetch(`/api/session/${this.sessionId}/step/next`, { method: "POST" });
          setTimeout(() => this.loadCurrent(), 600);
        } else if (this.totalSteps > 0) {
          setTimeout(() => this.celebrateClear(), 500);
        }
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
      SciAI.speak(this.celebrate.line, true);
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
          if (streaming) {
            this.history.push({ role: "assistant", text: this.bubble });
            SciAI.speak(this.bubble, this.ttsOn);
          }
        }
      });
    },

    repeatTts() {
      SciAI.speak(this.bubble, true);
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
