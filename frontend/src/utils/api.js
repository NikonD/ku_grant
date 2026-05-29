// utils/api.js
// Базовый URL — относительный путь, Vite проксирует на бэкенд :8000
// В Docker подхватывается через VITE_API_URL из docker-compose.yml
const API_URL = import.meta.env.VITE_API_URL || "/api";

// Получить все специальности из БД
export async function getSpecialties() {
  const res = await fetch(`${API_URL}/specialties/`);
  if (!res.ok) throw new Error("Ошибка загрузки специальностей");
  return res.json();
}

// Рассчитать вероятность поступления
// item_comb — строка вида "Математика + Физика" (как в БД)
// quota     — строка вида "general", "rural" и т.д.
export async function calculateProbability(entScore, item_comb, quota) {
  const res = await fetch(`${API_URL}/calculator/assessment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ent_score: entScore,
      item_comb: item_comb, // исправлено: было specialtyId (не существовал)
      quota,
    }),
  });
  if (!res.ok) throw new Error("Ошибка расчёта");
  return res.json();
}

// Отправить сообщение чат-боту (уже подключён правильно)
export async function sendChatMessage(message, history = [], entScore = null) {
  const res = await fetch(`${API_URL}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, ent_score: entScore }),
  });
  if (!res.ok) throw new Error("Ошибка чат-бота");
  return res.json();
}
