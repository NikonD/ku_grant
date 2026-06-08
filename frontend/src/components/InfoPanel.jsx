// components/InfoPanel.jsx
// Правая колонка — инструкция как пользоваться калькулятором
import { useTranslation } from 'react-i18next';
import './InfoPanel.css';

export default function InfoPanel() {
  const { t } = useTranslation();
  const steps = t('info.steps',  { returnObjects: true });
  const facts = t('info.facts',  { returnObjects: true });

  return (
    <div className="info-panel">

      <div className="info-panel__header">
        <h2 className="info-panel__title">{t('info.title')}</h2>
        <p className="info-panel__desc">{t('info.desc')}</p>
      </div>

      <div className="info-steps">
        {steps.map((s, idx) => (
          <div key={idx} className="info-step">
            <div className="info-step__num">{idx + 1}</div>
            <div className="info-step__body">
              <div className="info-step__title">{s.title}</div>
              <p className="info-step__desc">{s.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="info-facts">
        <p className="info-facts__label">{t('info.stepsHeading')}</p>
        <div className="info-facts__grid">
          {facts.map((text, i) => (
            <div key={i} className="info-fact">
              <span className="info-fact__text">{text}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="info-chat-hint">
        <span className="info-chat-hint__icon">💬</span>
        <div>
          <strong>{t('info.chatHint.title')}</strong>
          <p>{t('info.chatHint.text')}</p>
        </div>
      </div>

    </div>
  );
}
