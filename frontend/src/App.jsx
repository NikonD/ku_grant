import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import CalculatorForm   from './components/CalculatorForm';
import ResultPanel      from './components/ResultPanel';
import InfoPanel        from './components/InfoPanel';
import ChatBot          from './components/ChatBot';
import LanguageSwitcher from './components/LanguageSwitcher';
import './App.css';

export default function App() {
  const { t, i18n } = useTranslation();
  const [result, setResult]         = useState(null);
  const [entScore, setEntScore]     = useState(null);
  const [quotaCode, setQuotaCode]   = useState('общий');
  const [excluded, setExcluded]     = useState(0);

  function handleResult(data, score, qCode, excludedByThreshold = 0) {
    setResult(data);
    setEntScore(score);
    setQuotaCode(qCode);
    setExcluded(excludedByThreshold);
  }

  useEffect(() => {
    document.title = t('header.title');
    const desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute('content', t('header.description'));
  }, [t, i18n.language]);

  // При смене языка инвалидируем устаревший результат, чтобы названия
  // специальностей в нём не остались на старом языке (нужен новый запрос).
  useEffect(() => {
    setResult(null);
  }, [i18n.language]);

  const quotaLabel = t(`quotas.${quotaCode}.label`);

  return (
    <div className="app">
      <header className="site-header">
        <nav className="navbar navbar-expand-lg navbar-light">
          <div className="lp-navbar-brand-arizona mb-2 mb-md-0">
            <a href="https://ku.edu.kz">
              <img
                src="./ku.png"
                className="img-fluid ku-icon"
                alt={t('header.logoAlt')}
              />
            </a>
          </div>
          <LanguageSwitcher />
        </nav>
      </header>

      <main className="layout">
        <div className="layout__left">
          <CalculatorForm onResult={handleResult} />
        </div>

        <div className="layout__right">
          {result
            ? <ResultPanel result={result} entScore={entScore} quotaLabel={quotaLabel} excludedByThreshold={excluded} />
            : <InfoPanel />
          }
        </div>
      </main>

      <ChatBot entScore={entScore} />
    </div>
  );
}
