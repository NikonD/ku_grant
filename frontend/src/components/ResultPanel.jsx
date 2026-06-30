// Правая колонка — список специальностей после расчёта
import { useTranslation } from 'react-i18next';
import './ResultPanel.css';

function getBadge(prob, t) {
  if (prob >= 75) return { color: 'green',  label: t('result.badges.excellent') };
  if (prob >= 50) return { color: 'blue',   label: t('result.badges.good')      };
  if (prob >= 30) return { color: 'orange', label: t('result.badges.average')   };
  return                 { color: 'red',    label: t('result.badges.low')       };
}

export default function ResultPanel({ result, entScore, quotaLabel, excludedByThreshold = 0, multiQuota = false }) {
  const { t } = useTranslation();

  const total          = result.length;
  const highChance     = result.filter(r => r.probability >= 50).length;
  const best           = result[0];
  const fallbackCount  = result.filter(r => r.isFallback).length;
  const allFallback    = fallbackCount > 0 && fallbackCount === total;

  return (
    <div className="result-panel">

      <div className="rp-header">
        <h2 className="rp-title">{t('result.title')}</h2>
        <div className="rp-chips">
          <span className="rp-chip">{t('result.score')}: <strong>{entScore}</strong></span>
          <span className="rp-chip">{quotaLabel}</span>
          <span className="rp-chip">{t('result.found')}: <strong>{total}</strong></span>
          <span className="rp-chip rp-chip--green">{t('result.highChance')}: <strong>{highChance}</strong></span>
        </div>
      </div>

      {allFallback && <div />}
      {!allFallback && fallbackCount > 0 && (
        <div className="rp-notice rp-notice--info">
          {t('result.fallbackNotice')}
        </div>
      )}
      {excludedByThreshold > 0 && (
        <div className="rp-notice rp-notice--warn">
          ⚠ {t('result.thresholdNotice', { count: excludedByThreshold })}
        </div>
      )}

      {best && (
        <div className={`rp-best rp-best--${getBadge(best.probability, t).color}`}>
          <span className="rp-best__label">{t('result.best')}</span>
          <div className="rp-best__info">
            <span className="rp-best__code">{best.code}</span>
            <span className="rp-best__name">{best.name}</span>
          </div>
          <span className="rp-best__prob">{best.probability}%</span>
        </div>
      )}

      <div className="rp-legend">
        <span className="rp-legend__item"><span className="rp-dot rp-dot--green"/>≥75%</span>
        <span className="rp-legend__item"><span className="rp-dot rp-dot--blue"/>50–74%</span>
        <span className="rp-legend__item"><span className="rp-dot rp-dot--orange"/>30–49%</span>
        <span className="rp-legend__item"><span className="rp-dot rp-dot--red"/>{'<'}30%</span>
      </div>

      <div className="rp-list">
        {result.map((spec, i) => {
          const badge = getBadge(spec.probability, t);
          return (
            <div key={spec.code || spec.id} className={`rp-row rp-row--${badge.color}`}>
              <span className="rp-row__num">{i + 1}</span>
              <div className="rp-row__info">
                <span className="rp-row__code">{spec.code}</span>
                <span className="rp-row__name">
                  {spec.name}
                  {spec.isFallback && (
                    <span className="rp-fallback-mark" title={t('result.fallbackNotice')}>∗</span>
                  )}
                  {multiQuota && spec.bestQuota && (
                    <span className="rp-bestquota" title={t('result.bestQuota')}>
                      {t(`quotas.${spec.bestQuota}.label`)}
                    </span>
                  )}
                </span>
                <div className="rp-row__bar-wrap">
                  <div className="rp-row__bar-bg">
                    <div
                      className={`rp-row__bar-fill rp-row__bar-fill--${badge.color}`}
                      style={{ width: `${spec.probability}%` }}
                    />
                  </div>
                  <span className="rp-row__base">{t('result.threshold', { score: spec.baseScore })}</span>
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
        {t('result.footer')}
      </p>
    </div>
  );
}
