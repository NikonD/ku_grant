// components/InfoPanel.jsx
// Правая колонка — инструкция как пользоваться калькулятором
import './InfoPanel.css';

const STEPS = [
  {
    num: '1',
    title: 'Введите балл ЕНТ',
    desc: 'Укажите итоговый балл, который вы получили на Едином Национальном Тестировании. Максимум — 140 баллов.',
  },
  {
    num: '2',
    title: 'Выберите предметы',
    desc: 'Сначала выберите первый профильный предмет, затем — второй. Система автоматически подберёт доступные комбинации.',
  },
  {
    num: '3',
    title: 'Укажите квоту',
    desc: 'Выберите категорию, по которой вы имеете право участвовать. Квота влияет на проходной порог.',
  },
  {
    num: '4',
    title: 'Получите результат',
    desc: 'Нажмите кнопку — справа появится список всех специальностей с вероятностью поступления на грант для каждой.',
  },
];

const FACTS = [
  { text: '57 специальностей в трёх группах обучения' },
  { text: 'Расчёт по sigmoid-модели и историческим данным' },
  { text: 'Учитываются все 11 официальных квот МОН РК' },
  { text: 'AI-чат поможет выбрать специальность' },
];

export default function InfoPanel() {
  return (
    <div className="info-panel">

      <div className="info-panel__header">
        <h2 className="info-panel__title">Как пользоваться калькулятором</h2>
        <p className="info-panel__desc">
          Заполните форму слева — и вы увидите все специальности СКУ им. Козыбаева,
          на которые подходят ваши профильные предметы, с вероятностью поступления на грант.
        </p>
      </div>

      {/* Шаги */}
      <div className="info-steps">
        {STEPS.map(s => (
          <div key={s.num} className="info-step">
            <div className="info-step__num">{s.num}</div>
            <div className="info-step__body">
              <div className="info-step__title">
                <span className="info-step__icon">{s.icon}</span>
                {s.title}
              </div>
              <p className="info-step__desc">{s.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Факты */}
      <div className="info-facts">
        <p className="info-facts__label">О калькуляторе</p>
        <div className="info-facts__grid">
          {FACTS.map((f, i) => (
            <div key={i} className="info-fact">
              <span className="info-fact__icon">{f.icon}</span>
              <span className="info-fact__text">{f.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Подсказка про чат-бот */}
      <div className="info-chat-hint">
        <span className="info-chat-hint__icon">💬</span>
        <div>
          <strong>Нужна помощь с выбором?</strong>
          <p>Нажмите на кнопку чата в правом нижнем углу — AI-ассистент поможет разобраться со специальностями и ответит на вопросы о поступлении.</p>
        </div>
      </div>

    </div>
  );
}