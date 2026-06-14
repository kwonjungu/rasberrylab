// Science AI Lab — 이전 대화 사이드 패널 헬퍼
// 한 번에 한 말풍선만 보여주므로, 지난 대화는 [⬅] 패널에서 확인.
window.SciAI = window.SciAI || {};

SciAI.roleIcon = function (role) {
  return role === "user" ? "🙋" : "🤖";
};
