// Science AI Lab — 우하단 안내 특화 챗봇 "라비 도우미"
// 범위: (1) 이 앱의 구동/사용 방법  (2) 초등 과학 질문  — 그 외는 정중히 거절.
// 구조:
//   1) 하드코딩 FAQ + 키워드 매칭 → 인터넷/토큰 0 으로 즉답 (오프라인 교실 대비)
//   2) FAQ 미스 시 Ollama 하네스(buildPrompt + /api/helpbot)로 폴백 — 여기선 미구현/미연결이어도
//      "준비 중" 안내로 우아하게 끝남. 추후 Ollama 붙이면 그대로 동작.

(function () {
  // ---------- 1) 하드코딩 지식베이스 ----------
  // 각 항목: 키워드(any 매칭) + 답변. 위에서부터 우선.
  const FAQ = [
    // ===== 앱 사용법 =====
    { k: ["시작", "어떻게 해", "처음", "사용법", "어떻게 시작"],
      a: "🗺️ <b>탐험 지도</b>에서 하고 싶은 미션(실험)을 골라 눌러봐. 미션 설명을 읽고 <b>‘🚀 미션 시작!’</b>을 누르면 라비랑 실험을 시작해! 🤖" },
    { k: ["미션", "실험 골라", "실험 선택", "스테이지"],
      a: "학년별 길을 따라 <b>스테이지</b>가 놓여 있어. 카드를 누르면 미션 목표·준비물이 나와. ⭐ 별이 많을수록 어려운 미션이야!" },
    { k: ["지도", "돌아가", "나가", "뒤로"],
      a: "화면 왼쪽 위 <b>🗺 버튼</b>을 누르면 언제든 탐험 지도로 돌아갈 수 있어." },
    { k: ["다음", "넘어가", "다음 단계"],
      a: "안내를 따라 한 단계를 마치면 <b>‘✅ 다 했어요/다음’</b> 버튼을 눌러 다음 단계로 가면 돼. 위쪽 동그라미로 진행 상황을 볼 수 있어!" },
    { k: ["도와", "도움", "선생님", "모르겠", "막혀"],
      a: "막히면 위쪽 <b>🔔 도움요청</b> 버튼을 눌러! 선생님께 신호가 가. 그리고 나(라비)한테 무엇이든 물어봐도 좋아. 🙂" },
    { k: ["소리", "읽어", "다시 듣기", "음성", "tts"],
      a: "말풍선 아래 <b>🔊 다시 듣기</b>를 누르면 안내를 소리로 들려줘. 화면이 뜰 때 자동으로 읽지는 않아." },
    { k: ["역할", "이름", "모둠", "팀"],
      a: "위쪽 <b>역할 줄</b>(🔬실험왕 등)을 누르면 친구들 별명을 정할 수 있어. 별명은 수업이 끝나면 자동으로 지워져 안전해! 🔒" },
    { k: ["교사", "선생님 모드", "pin", "핀", "비밀번호"],
      a: "🎓 교사 버튼은 선생님용이야. PIN(기본 1234)을 입력하면 진행 상황을 보고 단계를 조절할 수 있어." },
    { k: ["센서", "연결", "esp", "안 돼", "작동", "인터넷"],
      a: "이 앱은 인터넷 없이 교실에서 돌아가도록 만들어졌어. 센서(ESP)나 AI 선생님은 장비가 연결돼야 진짜로 움직여. 없어도 화면과 미션은 그대로 볼 수 있어!" },

    // ===== 과학 개념(초등) =====
    { k: ["자석", "자기", "n극", "s극", "끌어"],
      a: "🧲 자석은 <b>철로 된 물체</b>를 끌어당겨. 같은 극(N-N)은 밀어내고 다른 극(N-S)은 서로 당겨. 멀어질수록 힘이 약해진단다." },
    { k: ["소리", "진동", "데시벨"],
      a: "🔊 소리는 <b>물체의 떨림(진동)</b>이 공기를 타고 퍼지는 거야. 크게 떨릴수록 소리가 커져!" },
    { k: ["온도", "녹", "얼음", "끓"],
      a: "🌡️ 온도는 물체가 <b>얼마나 뜨겁고 차가운지</b>를 나타내. 얼음(0℃)은 열을 받으면 물로 녹아." },
    { k: ["빛", "그림자", "색", "반사"],
      a: "💡 빛은 곧게 나아가다가 물체에 막히면 <b>그림자</b>가 생겨. 빨강·초록·파랑 빛을 섞으면 여러 색을 만들 수 있어!" },
    { k: ["전기", "회로", "전구", "led", "건전지"],
      a: "⚡ 전기는 <b>회로(길)</b>가 이어져야 흘러. 건전지 → 전선 → 전구가 동그랗게 연결되면 불이 켜져!" },
    { k: ["속도", "거리", "빠르", "움직"],
      a: "🚗 <b>속도 = 거리 ÷ 시간</b>이야. 같은 시간에 더 멀리 가면 더 빠른 거지!" },
    { k: ["심장", "맥박", "운동", "심박"],
      a: "❤️ 심장은 온몸에 피를 보내는 펌프야. <b>운동을 하면</b> 산소가 더 필요해서 심장이 빨리 뛴단다." },
    { k: ["식물", "물", "흙", "광합성"],
      a: "🌱 식물은 햇빛·물·공기로 <b>스스로 양분을 만들어(광합성)</b>. 흙이 마르면 물을 줘야 잘 자라!" },
  ];

  // 인사/감사/범위 밖 처리
  const GREET = { k: ["안녕", "하이", "반가", "누구"], a: "안녕! 나는 실험 도우미 <b>라비</b>야 🤖 과학이 궁금하거나, 앱 쓰는 방법이 헷갈리면 뭐든 물어봐!" };
  const THANKS = { k: ["고마", "감사", "땡큐"], a: "천만에! 또 궁금한 게 생기면 언제든 불러줘 😊" };
  const OUT_OF_SCOPE = "음… 나는 <b>과학</b>이랑 <b>이 앱 사용법</b>만 도와줄 수 있어. 그쪽으로 물어봐 줄래? 🔬";

  function norm(s) { return (s || "").toLowerCase().replace(/\s+/g, " ").trim(); }
  function matchFAQ(q) {
    const t = norm(q);
    if (!t) return null;
    for (const item of [GREET, THANKS, ...FAQ]) {
      if (item.k.some((kw) => t.includes(kw))) return item.a;
    }
    return null;
  }

  // ---------- 2) Ollama 하네스 (추후 연결용) ----------
  // 범위를 강제하는 시스템 프롬프트 + 호출부. 백엔드 /api/helpbot 가 생기면 그대로 작동.
  const SYSTEM_PROMPT = [
    "너는 초등학생을 돕는 과학 실험 앱 'Science AI Lab'의 안내 도우미 '라비'다.",
    "다음 두 가지에 대해서만 한국어로 짧고 쉽게(2~3문장) 답한다:",
    "1) 이 앱의 사용/구동 방법, 2) 초등학교 수준의 과학 개념.",
    "그 외 주제(잡담, 폭력, 개인정보, 숙제 대신 풀기 등)는 정중히 거절하고 과학/앱 질문을 유도한다.",
    "초등학생 눈높이로 다정하게, 이모지를 1~2개만 사용한다.",
  ].join(" ");

  function buildPrompt(userText) {
    return `${SYSTEM_PROMPT}\n\n학생 질문: ${userText}\n라비의 답변:`;
  }

  async function askOllama(userText) {
    // 백엔드에 /api/helpbot 엔드포인트가 있으면 사용(스코프 프롬프트를 서버가 적용).
    try {
      const r = await fetch("/api/helpbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userText, system: SYSTEM_PROMPT }),
      });
      if (r.ok) {
        const d = await r.json();
        if (d && d.reply) return d.reply;
      }
    } catch (e) { /* 미연결 */ }
    return null;
  }

  // ---------- 3) Alpine 컴포넌트 ----------
  window.helpBot = function () {
    return {
      open: false,
      input: "",
      busy: false,
      msgs: [
        { who: "bot", html: "안녕! 나는 도우미 <b>라비</b>야 🤖<br>과학이 궁금하거나 앱 사용법이 헷갈리면 물어봐!" },
      ],
      // 추천 질문(탭 1번에 즉답)
      chips: ["어떻게 시작해?", "자석은 왜 붙어?", "도움이 필요해", "다음 단계로 어떻게 가?"],

      toggle() { this.open = !this.open; if (this.open) this.scroll(); },
      pick(c) { this.input = c; this.send(); },

      async send() {
        const q = (this.input || "").trim();
        if (!q || this.busy) return;
        this.msgs.push({ who: "me", html: this.esc(q) });
        this.input = "";
        this.scroll();

        // 1) 하드코딩 즉답(토큰 0)
        const fast = matchFAQ(q);
        if (fast) { this.reply(fast); return; }

        // 2) Ollama 하네스 폴백
        this.busy = true;
        this.msgs.push({ who: "bot", html: "라비가 생각 중… 🤔", temp: true });
        this.scroll();
        const ans = await askOllama(q);
        this.msgs = this.msgs.filter((m) => !m.temp);
        this.busy = false;
        if (ans) this.reply(this.esc(ans));
        else this.reply("아직 <b>AI 선생님(Ollama)</b>이 연결되지 않았어. 지금은 자주 묻는 질문만 답할 수 있어! " + OUT_OF_SCOPE);
      },

      reply(html) { this.msgs.push({ who: "bot", html }); this.scroll(); },
      esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; },
      scroll() { this.$nextTick(() => { const el = this.$refs.body; if (el) el.scrollTop = el.scrollHeight; }); },
    };
  };
})();
