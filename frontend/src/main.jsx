// src/main.jsx — точка входа React приложения
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './i18n';            // инициализация react-i18next до рендера
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
