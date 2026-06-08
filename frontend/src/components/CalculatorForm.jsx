// components/CalculatorForm.jsx
// Форма калькулятора — подключена к бэкенду через api.js
import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { calculateProbability } from '../utils/api';
import './CalculatorForm.css';

// Канонические (русские) имена предметов. Используются как ключи
// перевода (subjects.*) и как часть item_comb для бэкенда.
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

// Допустимые связки предметов → строка item_comb как в БД (RU, каноническая).
const VALID_PAIRS = [
  { s1: 'Биология',           s2: 'География',            comb: 'Биология + География'           },
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

// Код квоты → процент. Лейблы и заметки берутся из i18n (quotas.{code}.label / .note).
export const QUOTAS = [
  { value: 'общий',             percent: null },
  { value: 'сельская',          percent: 35   },
  { value: 'rural_move',        percent: 5    },
  { value: 'large_family',      percent: 5    },
  { value: 'kazakh_diaspora',   percent: 4    },
  { value: 'disability_self',   percent: 2    },
  { value: 'disability_family', percent: 2    },
  { value: 'orphan',            percent: 1    },
  { value: 'single_parent',     percent: 1    },
  { value: 'veteran',           percent: 0.2  },
];

export default function CalculatorForm({ onResult }) {
  const { t } = useTranslation();

  const [entScore, setEntScore] = useState('');
  const [sub1,     setSub1]     = useState('');
  const [sub2,     setSub2]     = useState('');
  const [quota,    setQuota]    = useState('общий');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  const availableSub2 = useMemo(() => {
    if (!sub1) return [];
    return VALID_PAIRS
      .filter(p => p.s1 === sub1 || p.s2 === sub1)
      .map(p => p.s1 === sub1 ? p.s2 : p.s1)
      .filter((v, i, arr) => arr.indexOf(v) === i);
  }, [sub1]);

  function handleSub1Change(val) {
    setSub1(val);
    setSub2('');
  }

  function getPairComb(s1, s2) {
    const pair = VALID_PAIRS.find(
      p => (p.s1 === s1 && p.s2 === s2) || (p.s1 === s2 && p.s2 === s1)
    );
    return pair?.comb ?? null;
  }

  const pairComb = sub1 && sub2 ? getPairComb(sub1, sub2) : null;
  const selectedQuota = QUOTAS.find(q => q.value === quota);

  // отображаемая связка — берём перевод комбинации из i18n.subjects
  function displayPair(comb) {
    if (!comb) return '';
    if (comb === 'Творческий экзамен') return t('subjects.Творческий экзамен');
    // комбинации лежат в формате "A + B"; "Литература" — особая (нет в subjects).
    return comb.split(' + ').map(part => {
      if (part === 'Литература' && sub1 === 'Казахская литература') return t('subjects.Казахская литература');
      if (part === 'Литература' && sub1 === 'Русская литература')  return t('subjects.Русская литература');
      if (part === 'Литература') return t('subjects.Казахская литература');
      return t(`subjects.${part}`, { defaultValue: part });
    }).join(' + ');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    const score = parseInt(entScore);
    if (!entScore || isNaN(score) || score < 0 || score > 140) {
      setError(t('calculator.errors.score'));
      return;
    }
    if (!sub1)     { setError(t('calculator.errors.sub1')); return; }
    if (!sub2)     { setError(t('calculator.errors.sub2')); return; }
    if (!pairComb) { setError(t('calculator.errors.pair')); return; }

    setLoading(true);
    try {
      const data = await calculateProbability(score, pairComb, quota);

      const adapted = data.assessments
        .map(item => ({
          ...item,
          probability: Math.round(item.chance),
          baseScore:   item.min_score,
          isFallback:  item.is_fallback === true,
        }))
        .sort((a, b) => b.probability - a.probability);

      onResult(adapted, score, quota, data.excluded_by_threshold || 0);
    } catch (err) {
      setError(t('calculator.errors.server', { message: err.message }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="calc-card">
      <div className="calc-top">
        <div>
          <h2 className="calc-title">{t('calculator.title')}</h2>
          <p className="calc-sub">{t('calculator.subtitle')}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="calc-form">

        <div className="field">
          <label className="field__label">{t('calculator.entScore')}</label>
          <input
            type="number" min="0" max="140"
            placeholder={t('calculator.entScorePlaceholder')}
            value={entScore}
            onChange={e => setEntScore(e.target.value)}
          />
        </div>

        <div className="field">
          <label className="field__label">{t('calculator.subject1')}</label>
          <select value={sub1} onChange={e => handleSub1Change(e.target.value)}>
            <option value="">{t('calculator.pickSubject')}</option>
            {ALL_SUBJECTS.map(s => (
              <option key={s} value={s}>{t(`subjects.${s}`, { defaultValue: s })}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className={`field__label ${!sub1 ? 'field__label--muted' : ''}`}>
            {t('calculator.subject2')}
          </label>
          <select
            value={sub2}
            onChange={e => setSub2(e.target.value)}
            disabled={!sub1}
          >
            <option value="">
              {sub1 ? t('calculator.pickSubject2') : t('calculator.pickFirstFirst')}
            </option>
            {availableSub2.map(s => (
              <option key={s} value={s}>{t(`subjects.${s}`, { defaultValue: s })}</option>
            ))}
          </select>
          {sub1 && availableSub2.length > 0 && (
            <span className="field__note">
              {t('calculator.available', {
                count:   availableSub2.length,
                subject: t(`subjects.${sub1}`, { defaultValue: sub1 }),
              })}
            </span>
          )}
          {pairComb && (
            <span className="field__pair-badge">
              {t('calculator.pair', { comb: displayPair(pairComb) })}
            </span>
          )}
        </div>

        <div className="field">
          <label className="label">{t('calculator.quota')}</label>
          <select value={quota} onChange={e => setQuota(e.target.value)}>
            {QUOTAS.map(q => (
              <option key={q.value} value={q.value}>{t(`quotas.${q.value}.label`)}</option>
            ))}
          </select>
          <span className="field__note field__note--blue">
            ℹ️ {t(`quotas.${quota}.note`)}
          </span>
          {selectedQuota?.percent != null && (
            <span className="field__percent">
              {t('calculator.quotaPercent', { percent: selectedQuota.percent })}
            </span>
          )}
        </div>

        {error && (
          <div className="form-error">⚠️ {error}</div>
        )}

        <button type="submit" className="btn-calc" disabled={loading}>
          {loading ? t('calculator.loading') : t('calculator.submit')}
        </button>

      </form>
    </div>
  );
}
