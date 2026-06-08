import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import ru from './locales/ru.json';
import kk from './locales/kk.json';
import en from './locales/en.json';

export const SUPPORTED_LANGS = ['ru', 'kk', 'en'];
export const DEFAULT_LANG = 'ru';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      ru: { translation: ru },
      kk: { translation: kk },
      en: { translation: en },
    },
    fallbackLng: DEFAULT_LANG,
    supportedLngs: SUPPORTED_LANGS,
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'ku_lang',
      caches: ['localStorage'],
    },
  });

// Поддерживаем тег <html lang="..."> в актуальном состоянии
const applyHtmlLang = (lng) => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = lng;
  }
};
applyHtmlLang(i18n.language || DEFAULT_LANG);
i18n.on('languageChanged', applyHtmlLang);

export default i18n;
