import { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../utils/api';
import './ChatBot.css';
import kuLogo from "./ku_logo.png";

export default function ChatBot({ entScore }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Привет! 👋 Я AI-ассистент университета Козыбаева. Помогу выбрать специальность и разобраться с поступлением. Что тебя интересует?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Автоскролл вниз
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    // Добавляем сообщение пользователя
    const userMsg = { role: 'user', content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      // Отправляем на бэкенд (без первого приветственного сообщения)
      const history = newMessages.slice(1, -1); // убираем приветствие и текущее
      const res = await sendChatMessage(text, history, entScore);
      setMessages(prev => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Ошибка соединения с AI. Проверьте, запущен ли бэкенд.'
      }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chatbot-wrapper">
      {/* Окно чата */}
      {open && (
        <div className="chat-window">
          <div className="chat-header">
            <div className="chat-avatar">
              <img
              src={kuLogo} alt="KU logo"
              />
            </div>
            <div>
              <div className="chat-name">AI-Ассистент</div>
              <div className="chat-status">● Онлайн</div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)}>✕</button>
          </div>

          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message message--${msg.role}`}>
                <div className="message-bubble">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="message message--assistant">
                <div className="message-bubble typing">
                  <span/><span/><span/>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-area">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Напишите вопрос..."
              rows={2}
              disabled={loading}
              className="chat-textarea"
            />
            <button onClick={handleSend} disabled={loading || !input.trim()} className="chat-send">
              ➤
            </button>
          </div>
        </div>
      )}

      {/* Кнопка открытия */}
      <button className="chat-toggle" onClick={() => setOpen(!open)}>
        {open ? '✕' : '💬'}
      </button>
    </div>
  );
}