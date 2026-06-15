// Science AI Lab — 스토리/세계관 레이어
// 게임 몰입을 위한 내러티브: 마스코트 '라비', 탐험 등급, 미션별 도입/클리어 대사.
// (안전·정답 등 교육 핵심은 백엔드 스크립트가 담당. 여기는 '분위기'만.)
window.SciStory = {
  mascot: { name: "라비", img: "/assets/mascot/labi.svg", cheer: "/assets/mascot/labi-cheer.svg" },

  // 첫 진입 인트로(지도 위 오버레이)
  intro: {
    title: "🔬 과학 탐험대에 온 걸 환영해!",
    lines: [
      "안녕! 나는 실험실 도우미 로봇 <b>라비</b>야. 🤖",
      "이곳 <b>과학 탐험 지도</b>에는 학년마다 신기한 미션들이 숨어 있어.",
      "센서로 직접 측정하고, 나랑 이야기하며 비밀을 풀어보자!",
      "준비됐으면 스테이지를 골라 모험을 시작해 줘! 🚀",
    ],
    cta: "탐험 시작!",
  },

  // 탐험 등급(난이도/클리어 분위기 표현용)
  ranks: [
    { min: 1, name: "새싹 탐험가", icon: "🌱" },
    { min: 2, name: "꼬마 과학자", icon: "🔍" },
    { min: 3, name: "주니어 연구원", icon: "🧪" },
    { min: 4, name: "수석 연구원", icon: "🥽" },
    { min: 5, name: "탐험 마스터", icon: "🏆" },
  ],
  rankFor(diff) {
    let r = this.ranks[0];
    for (const x of this.ranks) if ((diff || 1) >= x.min) r = x;
    return r;
  },

  // 미션별 도입 대사(브리핑) — 없으면 fallback
  brief(expId, title) {
    const m = this._brief[expId];
    return m || `좋아! 이번 미션은 「${title}」이야. 우리가 직접 알아내 보자! 🔬`;
  },
  // 미션 클리어 축하 대사
  clear(expId) {
    const m = this._clear[expId];
    return m || "미션 성공! 멋진 탐험가야. 데이터로 비밀을 밝혀냈어! 🎉";
  },

  _brief: {
    "exp-3-magnet-distance": "자석은 멀어지면 힘이 약해질까? 거리마다 직접 재서 확인해 보자! 🧲",
    "exp-3-sound-clap": "박수 소리는 얼마나 클까? 조용할 때와 비교해 측정해 보자! 👏",
    "exp-3-ice-melt-temp": "얼음이 녹는 동안 온도는 어떻게 변할까? 지켜보자! 🧊",
    "exp-4-shadow-light-block": "그림자는 빛을 얼마나 막을까? 직접 가려서 측정! 🌑",
    "exp-4-vibration-shock": "흔들림이 셀수록 센서는 크게 반응할까? 흔들어 보자! 🌋",
    "exp-5-insulation-compare": "어떤 재료가 따뜻함을 더 잘 지킬까? 보온 대결! 🔥",
    "exp-5-motion-ultrasonic": "거리와 시간을 알면 속도를 구할 수 있어. 추적해 보자! 🚗",
    "exp-5-rc-acceleration": "RC카는 얼마나 빨리 빨라질까? 가속도에 도전! 🏎️",
    "exp-6-auto-light": "어두워지면 불이 켜지게 만들 수 있을까? 회로에 도전! 💡",
    "exp-6-heartbeat": "운동하면 심장은 얼마나 빨라질까? 직접 재 보자! ❤️",
    "exp-6-color-mixing": "빛의 색을 섞으면 무슨 색이 될까? 실험! 🎨",
    "exp-fusion-auto-door": "사람이 오면 스스로 열리는 문! 시스템을 완성하자! 🚪",
    "exp-fusion-self-driving": "장애물을 피하는 똑똑한 자동차를 만들어 보자! 🤖",
    "exp-fusion-smart-plant": "흙이 마르면 자동으로 물 주기! 스마트 화분 완성! 🌱",
  },
  _clear: {
    "exp-3-magnet-distance": "성공! 자석은 멀어질수록 약해진다는 걸 데이터로 증명했어! 🧲🏅",
    "exp-5-motion-ultrasonic": "성공! 거리÷시간으로 속도를 구한 진짜 과학자야! 🚗🏅",
    "exp-6-heartbeat": "성공! 운동하면 심장이 빨라진다는 걸 직접 확인했어! ❤️🏅",
    "exp-fusion-smart-plant": "성공! 스스로 식물을 돌보는 시스템을 완성했어! 🌱🏅",
  },
};
