// Правая колонка — список специальностей после расчёта
import './ResultPanel.css';

function getBadge(prob) {
  if (prob >= 75) return { color: 'green',  label: 'Отлично' };
  if (prob >= 50) return { color: 'blue',   label: 'Хорошо'  };
  if (prob >= 30) return { color: 'orange', label: 'Средне'  };
  return               { color: 'red',    label: 'Низко'   };
}

export default function ResultPanel({ result, entScore, quotaLabel }) {
  const total          = result.length;
  const highChance     = result.filter(r => r.probability >= 50).length;
  const best           = result[0];
  const fallbackCount  = result.filter(r => r.isFallback).length;
  const allFallback    = fallbackCount > 0 && fallbackCount === total;

  return (
    <div className="result-panel">

      {/* Шапка */}
      <div className="rp-header">
        <h2 className="rp-title">Результаты расчёта</h2>
        <div className="rp-chips">
          <span className="rp-chip">Балл: <strong>{entScore}</strong></span>
          <span className="rp-chip">{quotaLabel}</span>
          <span className="rp-chip">Найдено: <strong>{total}</strong></span>
          <span className="rp-chip rp-chip--green">Шанс ≥50%: <strong>{highChance}</strong></span>
        </div>
      </div>

      {/* Предупреждение, если по выбранной квоте нет точной статистики */}
      {allFallback && (
        <div></div>
        // <div className="rp-notice rp-notice--warn">
        //   ⚠ По выбранной квоте университет не публикует отдельную статистику.
        //   Расчёт сделан по общему конкурсу 2025,
        //   проверьте условия квоты на <a href="https://ku.edu.kz" target="_blank" rel="noreferrer">сайте университета&nbsp;</a>.
        // </div>
      )}
      {!allFallback && fallbackCount > 0 && (
        <div className="rp-notice rp-notice--info">
          Звёздочкой (<span className="rp-fallback-mark">∗</span>) отмечены программы,
          по которым на эту квоту в 2025&nbsp;г. не было заявок —
          расчёт сделан по общему конкурсу.
        </div>
      )}

      {/* Лучший вариант */}
      {best && (
        <div className={`rp-best rp-best--${getBadge(best.probability).color}`}>
          <span className="rp-best__label">⭐ Лучший вариант</span>
          <div className="rp-best__info">
            <span className="rp-best__code">{best.code}</span>
            <span className="rp-best__name">{best.name}</span>
          </div>
          <span className="rp-best__prob">{best.probability}%</span>
        </div>
      )}

      {/* Легенда */}
      <div className="rp-legend">
        <span className="rp-legend__item"><span className="rp-dot rp-dot--green"/>≥75%</span>
        <span className="rp-legend__item"><span className="rp-dot rp-dot--blue"/>50–74%</span>
        <span className="rp-legend__item"><span className="rp-dot rp-dot--orange"/>30–49%</span>
        <span className="rp-legend__item"><span className="rp-dot rp-dot--red"/>{'<'}30%</span>
      </div>

      {/* Список специальностей */}
      <div className="rp-list">
        {result.map((spec, i) => {
          const badge = getBadge(spec.probability);
          return (
            <div key={spec.code} className={`rp-row rp-row--${badge.color}`}>
              <span className="rp-row__num">{i + 1}</span>
              <div className="rp-row__info">
                <span className="rp-row__code">{spec.code}</span>
                <span className="rp-row__name">
                  {spec.name}
                  {spec.isFallback && (
                    <span
                      className="rp-fallback-mark"
                      title="Для этой программы нет данных по выбранной квоте — расчёт сделан по общему конкурсу"
                    >∗</span>
                  )}
                </span>
                <div className="rp-row__bar-wrap">
                  <div className="rp-row__bar-bg">
                    <div
                      className={`rp-row__bar-fill rp-row__bar-fill--${badge.color}`}
                      style={{ width: `${spec.probability}%` }}
                    />
                  </div>
                  <span className="rp-row__base">порог ~{spec.baseScore} б.</span>
                </div>
              </div>
              <div className="rp-row__right">
                <span className={`rp-badge rp-badge--${badge.color}`}>{badge.label}</span>
                <span className="rp-row__prob">{spec.probability}%</span>
              </div>
            </div>
          );
        })}
      </div>

      <p className="rp-footer">
        💡 Вероятность рассчитана на основе исторических проходных баллов и квот МОН РК.
        Уточняйте данные в приёмной комиссии университета.
      </p>
    </div>
  );
}