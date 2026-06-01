import { useState, useEffect, useRef } from 'react';
import CalculatorForm from './components/CalculatorForm';
import ResultPanel    from './components/ResultPanel';
import InfoPanel      from './components/InfoPanel';
import ChatBot        from './components/ChatBot';
import './App.css';



const HOT_CAREERS = [
  {
    title: 'IT-разработчик',
    salary: 'от 300 000 ₸',
    spec: 'Информационные технологии',
    trend: '+42% спрос за год',
  },
  {
    title: 'Врач общей практики',
    salary: 'от 280 000 ₸',
    spec: 'Общая медицина',
    trend: 'Всегда востребован',
  },
  {
    title: 'Инженер-электроэнергетик',
    salary: 'от 250 000 ₸',
    spec: 'Электротехника и энергетика',
    trend: '+28% спрос за год',
  },
  {
    title: 'Финансовый аналитик',
    salary: 'от 220 000 ₸',
    spec: 'Финансы / Аудит',
    trend: 'Стабильный рост',
  },
  {
    title: 'Агроинженер',
    salary: 'от 200 000 ₸',
    spec: 'Растениеводство / Животноводство',
    trend: 'Приоритет гос. программ',
  },
];
 
// КОМПОНЕНТ: Бегущая строка с карточками
function CareerTicker() {
  const [current,   setCurrent]   = useState(0);
  const [animating, setAnimating] = useState(false);
  const timerRef = useRef(null);

  function step(dir) {
    setAnimating(true);
    setTimeout(() => {
      setCurrent(c => (c + dir + HOT_CAREERS.length) % HOT_CAREERS.length);
      setAnimating(false);
    }, 280);
  }

  function startTimer() {
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => step(1), 5000);
  }

  useEffect(() => {
    startTimer();
    return () => clearInterval(timerRef.current);
  }, []);

  function handleArrow(dir) {
    step(dir);
    startTimer();
  }

  const c = HOT_CAREERS[current];

  return (
    <div className="ticker">
      <span className="ticker__label"> Популярные профессий Кзахстана</span>
      <div className={`ticker__card ${animating ? 'ticker__card--out' : 'ticker__card--in'}`}>
        <span className="ticker__emoji">{c.emoji}</span>
        <div className="ticker__info">
          <span className="ticker__title">{c.title}</span>
          <span className="ticker__sub">{c.spec}</span>
        </div>
        <div className="ticker__right">
          <span className="ticker__salary">{c.salary}</span>
          <span className="ticker__trend">{c.trend}</span>
        </div>
      </div>
      <div className="ticker__dots">
        {HOT_CAREERS.map((_, i) => (
          <button
            key={i}
            className={`ticker__dot ${i === current ? 'ticker__dot--active' : ''}`}
            onClick={() => { setCurrent(i); startTimer(); }}
          />
        ))}
      </div>
      <button className="ticker__arrow ticker__arrow--l" onClick={() => handleArrow(-1)}>‹</button>
      <button className="ticker__arrow ticker__arrow--r" onClick={() => handleArrow(1)}>›</button>
    </div>
  );
}
 


export default function App() {
  const [result, setResult]         = useState(null);
  const [entScore, setEntScore]     = useState(null);
  const [quotaLabel, setQuotaLabel] = useState('');

 function handleResult(data, score, qLabel) {
    setResult(data);
    setEntScore(score);
    setQuotaLabel(qLabel);
  }

  return (
    <div className="app">
      {/* Шапка */}
      <header className="site-header">
        <nav className="navbar navbar-expand-lg navbar-light">
          <div className="lp-navbar-brand-arizona mb-2 mb-md-0">
            <a href="https://ku.edu.kz">
              <img 
                src="./ku.png"
                className="img-fluid ku-icon"
                alt="Kozybayev University"
              />
            </a> 
           </div> 

            
        </nav>
      </header>

      <CareerTicker />

      {/* Основной контент */}
      <main className="layout">
        <div className="layout__left">
          <CalculatorForm onResult={handleResult} />
        </div>
 
        {/* Правая колонка — инфо ИЛИ результат */}
        <div className="layout__right">
          {result
            ? <ResultPanel result={result} entScore={entScore} quotaLabel={quotaLabel} />
            : <InfoPanel />
          }
        </div>
      </main>

      {/* Чат-бот (фиксированный в правом углу) */}
      <ChatBot entScore={entScore} />
    </div>
  );
}