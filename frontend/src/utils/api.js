// utils/api.js
// Базовый URL — относительный путь, Vite проксирует на бэкенд :8000
// В Docker подхватывается через VITE_API_URL из docker-compose.yml
import i18n from '../i18n';

const API_URL = import.meta.env.VITE_API_URL || '/api';

function lang() {
  return (i18n.language || 'ru').slice(0, 2);
}

// Получить все специальности из БД (на текущем языке)
export async function getSpecialties() {
  const res = await fetch(`${API_URL}/specialties/?lang=${lang()}`);
  if (!res.ok) throw new Error('Ошибка загрузки специальностей');
  return res.json();
}

// Рассчитать вероятность поступления
// item_comb — каноническая (RU) строка вида "Математика + Физика"
// quotas    — массив кодов квот ["общий", "сельская", ...]; берётся лучший шанс
export async function calculateProbability(entScore, item_comb, quotas) {
  const list = Array.isArray(quotas) ? quotas : [quotas].filter(Boolean);
  const res = await fetch(`${API_URL}/calculator/assessment?lang=${lang()}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ent_score: entScore,
      item_comb,
      quotas: list,
      quota: list[0],   // для обратной совместимости со старым бэкендом
      lang: lang(),
    }),
  });
  if (!res.ok) throw new Error('Ошибка расчёта');
  return res.json();
}

// Отправить сообщение чат-боту
export async function sendChatMessage(message, history = [], entScore = null) {
  const res = await fetch(`${API_URL}/chat/?lang=${lang()}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, ent_score: entScore, lang: lang() }),
  });
  if (!res.ok) throw new Error('Ошибка чат-бота');
  return res.json();
}
