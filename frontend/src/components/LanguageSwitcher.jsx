import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGS } from '../i18n';
import './LanguageSwitcher.css';

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const current = (i18n.language || 'ru').slice(0, 2);

  return (
    <div className="lang-switcher" role="group" aria-label={t('languageSwitcher.ariaLabel')}>
      {SUPPORTED_LANGS.map(code => (
        <button
          key={code}
          type="button"
          className={`lang-switcher__btn ${current === code ? 'lang-switcher__btn--active' : ''}`}
          onClick={() => i18n.changeLanguage(code)}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
