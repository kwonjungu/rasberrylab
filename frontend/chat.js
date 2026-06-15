// Science AI Lab — SSE 스트리밍 + TTS 헬퍼 (인터넷 불필요, 브라우저 내장)
window.SciAI = window.SciAI || {};

// /api/chat 에 POST 하고 SSE 이벤트를 콜백으로 흘려보낸다.
// onEvent(evt) 는 {type:'message'|'token'|'thinking'|'done'|'silent', ...}
SciAI.streamChat = async function (body, onEvent) {
  const resp = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    // SSE는 빈 줄로 이벤트 구분
    let idx;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 2);
      if (chunk.startsWith("data:")) {
        try {
          onEvent(JSON.parse(chunk.slice(5).trim()));
        } catch (e) {
          /* 무시 */
        }
      }
    }
  }
};

// 효과음 엔진 (Web Audio, 합성음 — 오디오 파일 불필요, 완전 오프라인)
// 아이들이 즉각적 피드백을 느끼도록 동작별 짧은 사운드를 재생한다.
SciAI.sfx = (function () {
  let ctx = null, muted = false, lastBlip = 0;
  function ac() {
    if (!ctx) { try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} }
    return ctx;
  }
  // 단음: 주파수/길이/파형/볼륨/지연
  function tone(freq, dur, type = "sine", gain = 0.14, when = 0) {
    const c = ac(); if (!c) return;
    const t = c.currentTime + when;
    const o = c.createOscillator(), g = c.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, t);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(gain, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(c.destination);
    o.start(t); o.stop(t + dur + 0.03);
  }
  const effects = {
    click:     () => tone(440, 0.07, "triangle", 0.10),
    select:    () => { tone(523, 0.06, "triangle", 0.11); tone(784, 0.09, "triangle", 0.09, 0.05); },
    success:   () => { tone(523, 0.10, "sine", 0.14); tone(659, 0.10, "sine", 0.14, 0.08); tone(784, 0.18, "sine", 0.14, 0.16); },
    celebrate: () => { [523, 659, 784, 1047, 1319].forEach((f, i) => tone(f, 0.24, "sine", 0.15, i * 0.09)); },
    step:      () => { tone(587, 0.08, "triangle", 0.11); tone(880, 0.10, "triangle", 0.11, 0.07); },
    connect:   () => { tone(440, 0.09, "sine", 0.13); tone(660, 0.09, "sine", 0.13, 0.09); tone(990, 0.16, "sine", 0.15, 0.18); }, // 띠↗ 연결 성공
    blip:      () => tone(1175, 0.035, "sine", 0.05),  // 신호 1건(아주 작게)
    help:      () => { tone(740, 0.12, "square", 0.09); tone(740, 0.12, "square", 0.09, 0.17); },
    warn:      () => { tone(415, 0.13, "square", 0.09); tone(415, 0.13, "square", 0.09, 0.17); },
    error:     () => { tone(311, 0.18, "sawtooth", 0.09); tone(233, 0.22, "sawtooth", 0.09, 0.12); },
  };
  return {
    play(name) {
      if (muted) return;
      const f = effects[name]; if (!f) return;
      try { const c = ac(); if (c && c.state === "suspended") c.resume(); f(); } catch (e) {}
    },
    blipThrottled() { const n = Date.now(); if (n - lastBlip < 900) return; lastBlip = n; this.play("blip"); },
    setMuted(m) { muted = !!m; },
    isMuted() { return muted; },
  };
})();

// TTS 제거됨 — 기존 호출 호환을 위해 no-op 유지 (소리 안 남)
SciAI.speak = function () { /* TTS removed */ };

// 마크다운 → HTML (marked). 실패 시 평문.
SciAI.md = function (text) {
  try {
    return window.marked ? window.marked.parse(text || "") : text;
  } catch (e) {
    return text;
  }
};
