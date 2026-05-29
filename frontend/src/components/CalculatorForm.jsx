// components/CalculatorForm.jsx
// Форма калькулятора — подключена к бэкенду через api.js
import { useState, useMemo } from 'react';
import { calculateProbability } from '../utils/api'; // запрос к /api/calculator/assessment
import './CalculatorForm.css';

// Все профильные предметы для выпадающих списков
const ALL_SUBJECTS = [
  'Биология',
  'География',
  'Всемирная история',
  'Основы права',
  'Иностранный язык',
  'Казахский язык',
  'Казахская литература',
  'Русский язык',
  'Русская литература',
  'Математика',
  'Информатика',
  'Физика',
  'Химия',
  'Творческий экзамен',
];

// Допустимые связки предметов → строка item_comb как в БД
// Формат точно совпадает с полем item_comb в таблице specialties
const VALID_PAIRS = [
  { s1: 'Биология',           s2: 'География',           comb: 'Биология + География'           },
  { s1: 'Биология',           s2: 'Химия',                comb: 'Биология + Химия'                },
  { s1: 'Всемирная история',  s2: 'География',            comb: 'Всемирная история + География'  },
  { s1: 'Всемирная история',  s2: 'Основы права',         comb: 'Всемирная история + Основы права'},
  { s1: 'География',          s2: 'Иностранный язык',     comb: 'География + Иностранный язык'   },
  { s1: 'Иностранный язык',   s2: 'Всемирная история',    comb: 'Иностранный язык + Всемирная история'},
  { s1: 'Казахский язык',     s2: 'Казахская литература', comb: 'Казахский язык + Литература'    },
  { s1: 'Русский язык',       s2: 'Русская литература',   comb: 'Русский язык + Литература'      },
  { s1: 'Математика',         s2: 'География',            comb: 'Математика + География'         },
  { s1: 'Математика',         s2: 'Информатика',          comb: 'Математика + Информатика'       },
  { s1: 'Математика',         s2: 'Физика',               comb: 'Математика + Физика'            },
  { s1: 'Химия',              s2: 'Физика',               comb: 'Химия + Физика'                 },
  { s1: 'Творческий экзамен', s2: 'Творческий экзамен',   comb: 'Творческий экзамен'             },
];

// Квоты МОН РК — используются только для отображения описания и % мест
// Значение value передаётся на бэкенд как поле quota
export const QUOTAS = [
  { value: 'общий',            label: 'Общий конкурс',                                        percent: null, note: 'Стандартный конкурс без льгот' },
  { value: 'сельская',         label: 'Сельская молодёжь',                                    percent: 35,   note: '35% всех грантов — самая большая квота' },
  { value: 'rural_move',       label: 'Сельская молодёжь → переселение в приоритетные регионы', percent: 5,  note: 'Переселение в регионы, определённые Правительством РК' },
  { value: 'large_family',     label: 'Дети из многодетных семей (4+ детей)',                  percent: 5,   note: 'Семьи, воспитывающие четырёх и более несовершеннолетних' },
  { value: 'kazakh_diaspora',  label: 'Казахи — не граждане РК',                               percent: 4,   note: 'Лица казахской национальности, не являющиеся гражданами РК' },
  { value: 'conscript',        label: 'После срочной военной службы',                          percent: 2.5, note: 'Граждане РК, выслужившие срок срочной воинской службы' },
  { value: 'disability_self',  label: 'Инвалидность I или II группы / с детства',              percent: 2,   note: 'Граждане с инвалидностью I или II группы' },
  { value: 'disability_family',label: 'Семья, воспитывающая ребёнка-инвалида',                 percent: 2,   note: 'Дети из семей, воспитывающих детей с инвалидностью' },
  { value: 'orphan',           label: 'Дети-сироты / без попечения родителей',                 percent: 1,   note: 'Дети-сироты и дети, оставшиеся без попечения родителей' },
  { value: 'single_parent',    label: 'Дети из неполных семей (статус ≥3 лет)',                percent: 1,   note: 'Дети из неполных семей, имеющих данный статус не менее трёх лет' },
  { value: 'veteran',          label: 'Ветераны боевых действий',                              percent: 0.2, note: 'Ветераны боевых действий на территории других государств' },
];

export default function CalculatorForm({ onResult }) {
  const [entScore, setEntScore] = useState('');
  const [sub1,     setSub1]     = useState('');
  const [sub2,     setSub2]     = useState('');
  const [quota,    setQuota]    = useState('общий');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false); // состояние загрузки при запросе

  // Доступные вторые предметы зависят от первого выбора
  const availableSub2 = useMemo(() => {
    if (!sub1) return [];
    return VALID_PAIRS
      .filter(p => p.s1 === sub1 || p.s2 === sub1)
      .map(p => p.s1 === sub1 ? p.s2 : p.s1)
      .filter((v, i, arr) => arr.indexOf(v) === i);
  }, [sub1]);

  // Сбрасываем второй предмет при смене первого
  function handleSub1Change(val) {
    setSub1(val);
    setSub2('');
  }

  // Найти строку item_comb по двум выбранным предметам
  function getPairComb(s1, s2) {
    const pair = VALID_PAIRS.find(
      p => (p.s1 === s1 && p.s2 === s2) || (p.s1 === s2 && p.s2 === s1)
    );
    return pair?.comb ?? null;
  }

  const selectedQuota = QUOTAS.find(q => q.value === quota);
  const pairComb = sub1 && sub2 ? getPairComb(sub1, sub2) : null; // строка для бэкенда

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    // Валидация на фронте перед запросом
    const score = parseInt(entScore);
    if (!entScore || isNaN(score) || score < 0 || score > 140) {
      setError('Введите корректный балл ЕНТ от 0 до 140');
      return;
    }
    if (!sub1) { setError('Выберите первый профильный предмет'); return; }
    if (!sub2) { setError('Выберите второй профильный предмет'); return; }
    if (!pairComb) { setError('Выбранная комбинация предметов недопустима'); return; }

    setLoading(true);
    try {
      // Запрос к POST /api/calculator/assessment
      // Бэкенд возвращает { assessments: [{id, name, min_score, chance}, ...] }
      const data = await calculateProbability(score, pairComb, quota);

      // Адаптируем поля бэкенда к тому что ожидает ResultPanel:
      // бэк даёт chance (0-100), ResultPanel ждёт probability
      // бэк даёт min_score, ResultPanel ждёт baseScore
      const adapted = data.assessments
        .map(item => ({
          ...item,
          probability: Math.round(item.chance), // chance → probability
          baseScore:   item.min_score,          // min_score → baseScore
        }))
        .sort((a, b) => b.probability - a.probability);

      // Передаём результат наверх в App.jsx
      onResult(adapted, score, selectedQuota?.label || 'Общий конкурс');
    } catch (err) {
      setError('Ошибка сервера: ' + err.message + '. Проверьте, запущен ли бэкенд.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="calc-card">

      <div className="calc-top">
        <div>
          <h2 className="calc-title">Калькулятор гранта</h2>
          <p className="calc-sub">СКУ им. М. Козыбаева</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="calc-form">

        {/* Балл ЕНТ */}
        <div className="field">
          <label className="field__label">Балл ЕНТ</label>
          <input
            type="number" min="0" max="140"
            placeholder="Например: 95"
            value={entScore}
            onChange={e => setEntScore(e.target.value)}
          />
        </div>

        {/* Первый предмет */}
        <div className="field">
          <label className="field__label">Первый профильный предмет</label>
          <select value={sub1} onChange={e => handleSub1Change(e.target.value)}>
            <option value="">— Выберите предмет —</option>
            {ALL_SUBJECTS.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Второй предмет — активен только после выбора первого */}
        <div className="field">
          <label className={`field__label ${!sub1 ? 'field__label--muted' : ''}`}>
            Второй профильный предмет
          </label>
          <select
            value={sub2}
            onChange={e => setSub2(e.target.value)}
            disabled={!sub1}
          >
            <option value="">
              {sub1 ? '— Выберите второй предмет —' : 'Сначала выберите первый'}
            </option>
            {availableSub2.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          {sub1 && availableSub2.length > 0 && (
            <span className="field__note">
              Доступно {availableSub2.length} вариантов для предмета «{sub1}»
            </span>
          )}
          {/* Показываем строку item_comb которая уйдёт на бэкенд */}
          {pairComb && (
            <span className="field__pair-badge">
              Связка: {pairComb}
            </span>
          )}
        </div>

        {/* Квота */}
        <div className="field">
          <label className="label">Квота поступления</label>
          <select value={quota} onChange={e => setQuota(e.target.value)}>
            {QUOTAS.map(q => (
              <option key={q.value} value={q.value}>{q.label}</option>
            ))}
          </select>
          {selectedQuota?.note && (
            <span className="field__note field__note--blue">
              ℹ️ {selectedQuota.note}
            </span>
          )}
          {selectedQuota?.percent && (
            <span className="field__percent">
              {selectedQuota.percent}% грантов по этой квоте
            </span>
          )}
        </div>

        {/* Ошибка */}
        {error && (
          <div className="form-error">⚠️ {error}</div>
        )}

        {/* Кнопка — показывает спиннер во время запроса */}
        <button type="submit" className="btn-calc" disabled={loading}>
          {loading ? 'Загрузка...' : 'Рассчитать вероятность'}
        </button>

      </form>
    </div>
  );
}
