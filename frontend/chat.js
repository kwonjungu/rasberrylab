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

// 한국어 음성 합성 (Web Speech API, 로컬 동작)
SciAI.speak = function (text, enabled) {
  if (!enabled || !("speechSynthesis" in window) || !text) return;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text.replace(/[#*`>_~]/g, ""));
    u.lang = "ko-KR";
    u.rate = 0.95;
    const ko = window.speechSynthesis.getVoices().find((v) => v.lang && v.lang.startsWith("ko"));
    if (ko) u.voice = ko;
    window.speechSynthesis.speak(u);
  } catch (e) {
    /* TTS 미지원이면 조용히 무시 */
  }
};

// 마크다운 → HTML (marked). 실패 시 평문.
SciAI.md = function (text) {
  try {
    return window.marked ? window.marked.parse(text || "") : text;
  } catch (e) {
    return text;
  }
};
