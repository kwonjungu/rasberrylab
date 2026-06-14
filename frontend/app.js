// Science AI Lab — 학생 화면 메인 (Alpine 컴포넌트)
// 1 Pi = 1 모둠. 한 번에 한 말풍선, 빠른답변 즉답, 자유질문은 LLM 스트리밍.

function labApp() {
  return {
    // ---- 상태 ----
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

    // Day 3: 안전수칙·역할·도움·막힘
    showSafety: false,
    safety: { intro: "", call: "", rules: [] },
    stuckCount: 0,
    blink: false,
    showRoles: false,
    roleCards: [],
    roleNames: {},

    // Day 4: 교사 모드
    teacherMode: false,
    teacherView: {},
    injectText: "",
    pdfUrl: null,
    _idle: null,

    // Phase 4: 실시간 ESP 센서
    espDevices: [],
    spark: {}, // {espId_sensor: [값...]}
    sensorWs: null,

    // Phase 5: 이어하기
    resumeInfo: null,
    showResume: false,

    // ---- 초기화 ----
    async init() {
      const p = new URLSearchParams(location.search);
      // 부팅 시 미완료 세션 감지 → 이어하기 제안 (launcher가 ?resume=1 부여)
      if (p.get("resume") === "1") {
        const latest = await fetch("/api/checkpoints/latest").then((x) => x.json()).catch(() => ({}));
        if (latest.has_pending) {
          this.resumeInfo = latest;
          this.showResume = true;
        }
      }
      const grade = parseInt(p.get("grade") || "5", 10);
      const exp = p.get("exp") || "exp-5-motion-ultrasonic";
      const team = p.get("team") || "다람쥐";
      const r = await fetch("/api/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_name: team, grade, experiment_id: exp }),
      }).then((x) => x.json());
      this.sessionId = r.session_id;
      this.roleCards = (await fetch("/api/session/roles/cards").then((x) => x.json()).catch(() => ({}))).roles || [];
      this.connectSensorWs();
      await this.loadCurrent();
    },

    // ---- 실시간 센서 WebSocket ----
    connectSensorWs() {
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
      this.teamName = c.team_name || "";
      this.expTitle = c.experiment_title || "";
      this.stepN = c.step_n;
      this.totalSteps = c.total_steps;
      this.instruction = c.instruction || "";
      this.durationSec = c.duration_sec || 0;
      this.quickReplies = c.quick_replies || [];
      this.safetyWarnings = c.safety_warnings || [];
      this.applyGrade();
      this.setBubble(this.instruction, true);
      if (this.durationSec > 0) this.startTimer(this.durationSec);
      // 실험 모드 진입 시 안전수칙 복창(미완료면 게이트)
      if (this.mode === "experiment") await this.checkSafety();
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
      // 'done' 이면 다음 단계로 진행
      if (btn.id === "done" && this.stepN < this.totalSteps) {
        await fetch(`/api/session/${this.sessionId}/step/next`, { method: "POST" });
        setTimeout(() => this.loadCurrent(), 600);
      }
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
      this.roleCards = (await fetch("/api/session/roles/cards").then((x) => x.json()).catch(() => ({}))).roles || [];
      this.connectSensorWs();
      await this.loadCurrent();
      // 이어하기는 안전수칙 간소 재복창(resafety) — checkResume에서 게이트
    },
    startFresh() {
      this.showResume = false;
      location.search = ""; // resume 없이 새 세션
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
      await this.refreshTeacher();
      this.resetIdle();
    },
    async refreshTeacher() {
      this.teacherView = await fetch(`/api/teacher/${this.sessionId}/view`).then((x) => x.json());
    },
    resetIdle() {
      if (this._idle) clearTimeout(this._idle);
      // 30초 무입력 → 자동 학생 모드 복귀
      this._idle = setTimeout(() => (this.teacherMode = false), 30000);
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
