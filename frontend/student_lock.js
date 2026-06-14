// Science AI Lab — 학생 보호 (Phase 6)
// 키오스크에서 학생이 실수로 시스템을 건드리지 않게 차단.
// 교사 모드(window.studentMode=false)에선 일반 동작 복원.
window.studentMode = true;

// F11/F12/개발자도구/새로고침/탭이동/뒤로가기 등 차단
document.addEventListener("keydown", (e) => {
  if (!window.studentMode) return;
  const k = (e.key || "").toLowerCase();
  const block =
    k === "f5" || k === "f11" || k === "f12" ||
    (e.ctrlKey && ["r", "w", "t", "n", "p", "s", "u", "j", "h"].includes(k)) ||
    (e.ctrlKey && e.shiftKey) ||
    (e.altKey && (k === "arrowleft" || k === "arrowright")) ||
    e.metaKey;
  if (block) {
    e.preventDefault();
    e.stopPropagation();
  }
});

// 우클릭 메뉴 차단
document.addEventListener("contextmenu", (e) => {
  if (window.studentMode) e.preventDefault();
});

// 실수 이탈 방지(키오스크 보조)
window.addEventListener("beforeunload", (e) => {
  if (window.studentMode) {
    e.preventDefault();
    e.returnValue = "";
  }
});
