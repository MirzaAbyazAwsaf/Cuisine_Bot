import { useState, useRef, useEffect } from "react";

const SUGGESTIONS = [
  "Best Italian restaurant in Dhaka",
  "Tell me about Star Kabab",
  "Cheap restaurants in Banani",
  "Best rated restaurant in Gulshan",
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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
      setMessages((m) => [...m, { role: "bot", content: data.answer, sources: data.sources }]);
    } catch (err) {
      setMessages((m) => [{ ...m, role: "bot", content: `Error: ${err.message}` }]);
    }
    setLoading(false);
  }

  return (
    <div className="app">
      <header>
        <h1>Cuisine Review Bot</h1>
        <p>Ask about any restaurant — reviews, ratings, cuisines, and areas.</p>
      </header>

      {messages.length === 0 && !loading && (
        <div className="suggestions">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <main className="chat">
        {messages.map((m, i) => (
          <Message key={i} msg={m} />
        ))}
        {loading && <div className="bubble bot">Thinking...</div>}
        <div ref={bottomRef} />
      </main>

      <footer>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask about a restaurant in Bangladesh..."
          disabled={loading}
        />
        <button onClick={() => send()} disabled={loading}>
          Send
        </button>
      </footer>
    </div>
  );
}

function Message({ msg }) {
  if (msg.role === "user") {
    return <div className="bubble user">{msg.content}</div>;
  }
  return (
    <div className="bubble bot">
      <p style={{ whiteSpace: "pre-wrap" }}>{msg.content}</p>
      {msg.sources && msg.sources.length > 0 && (
        <details>
          <summary>Sources</summary>
          <ul>
            {msg.sources.map((s, i) => (
              <li key={i}>
                <strong>{s.restaurant}</strong> — {s.snippet}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}