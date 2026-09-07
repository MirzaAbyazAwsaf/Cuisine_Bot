import { useState, useRef, useEffect } from "react";
import Markdown from "react-markdown";

const SUGGESTIONS = [
  { text: "Best Italian restaurant in Dhaka", icon: "🍕" },
  { text: "Tell me about Star Kabab", icon: "⭐" },
  { text: "Cheap restaurants in Banani", icon: "💰" },
  { text: "Best rated restaurant in Gulshan", icon: "🏆" },
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!loading && inputRef.current) inputRef.current.focus();
  }, [loading]);

  async function send(text) {
    const question = (text ?? input).trim();
    if (!question || loading) return;
    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "bot", answer: data.answer, sources: data.sources }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "bot", answer: { message: `Something went wrong: ${err.message}`, restaurants: [] } }]);
    }
    setLoading(false);
  }

  return (
    <div className="app">
      <header>
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">🍽</span>
            <div>
              <h1>Cuisine Review Bot</h1>
              <p>Ask about restaurants — reviews, ratings, cuisines, and areas in Bangladesh.</p>
            </div>
          </div>
        
        </div>
      </header>

      <div className="chat-area">
        {messages.length === 0 && !loading && (
          <div className="welcome">
            <div className="welcome-icon">💬</div>
            <h2>How can I help you today?</h2>
            <p>Ask me anything about restaurants and I'll find the best answers from real reviews.</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s.text} onClick={() => send(s.text)}>
                  <span className="suggestion-icon">{s.icon}</span>
                  {s.text}
                </button>
              ))}
            </div>
          </div>
        )}

        <main className="chat">
          {messages.map((m, i) => (
            <Message key={i} msg={m} />
          ))}
          {loading && (
            <div className="message-row bot-row">
              <div className="avatar bot-avatar">AI</div>
              <div className="bot-reply">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </main>
      </div>

      <footer>
        <div className="input-wrapper">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask about a restaurant in Bangladesh..."
            disabled={loading}
          />
          <button onClick={() => send()} disabled={loading || !input.trim()}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p className="footer-note">Answers are generated from real customer reviews. Results may vary.</p>
      </footer>
    </div>
  );
}

function Message({ msg }) {
  if (msg.role === "user") {
    return (
      <div className="message-row user-row">
        <div className="user-bubble">
          <p>{msg.content}</p>
        </div>
        <div className="avatar user-avatar">You</div>
      </div>
    );
  }

  const answer = msg.answer || {};
  const restaurants = answer.restaurants || [];

  return (
    <div className="message-row bot-row">
      <div className="avatar bot-avatar">AI</div>
      <div className="bot-reply">
        {answer.message && (
          <div className="bot-content">
            <Markdown>{answer.message}</Markdown>
          </div>
        )}

        {restaurants.length > 0 && (
          <div className="restaurant-list">
            {restaurants.map((r, i) => (
              <RestaurantCard key={i} restaurant={r} />
            ))}
          </div>
        )}

        {msg.sources && msg.sources.length > 0 && (
          <div className="sources-section">
            <span className="sources-label">Sources:</span>
            <span className="sources-names">
              {[...new Set(msg.sources.map((s) => s.restaurant).filter(Boolean))].join(", ")}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function RestaurantCard({ restaurant }) {
  const rating = restaurant.rating;
  return (
    <div className="restaurant-card">
      <div className="card-header">
        <h3>{restaurant.name}</h3>
        {rating != null && rating !== "" && (
          <div className="rating-badge" title={`${rating} / 5`}>
            <span className="star">★</span>
            <span className="rating-value">{Number(rating).toFixed(1)}</span>
          </div>
        )}
      </div>

      <div className="card-fields">
        {restaurant.address && (
          <div className="card-field">
            <span className="field-icon">📍</span>
            <span className="field-label">Address</span>
            <span className="field-value">{restaurant.address}</span>
          </div>
        )}
        {restaurant.price && (
          <div className="card-field">
            <span className="field-icon">💰</span>
            <span className="field-label">Price</span>
            <span className="field-value">{restaurant.price}</span>
          </div>
        )}
      </div>

      {rating != null && rating !== "" && (
        <div className="card-rating">
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              className={star <= Math.round(Number(rating)) ? "star filled" : "star"}
            >
              ★
            </span>
          ))}
        </div>
      )}

      {restaurant.reviews && restaurant.reviews.length > 0 && (
        <div className="card-reviews">
          <h4>Reviews</h4>
          <ul>
            {restaurant.reviews.map((review, i) => (
              <li key={i}>{review}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}