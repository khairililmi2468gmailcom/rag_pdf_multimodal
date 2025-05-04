import React, { useState, useEffect } from "react";
import axios from "axios";

const ChatComponent = () => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
const [currentQuestion, setCurrentQuestion] = useState("");

  useEffect(() => {
    const savedHistory = localStorage.getItem("chatHistory");
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

 const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);

  const q = question;
  setCurrentQuestion(q); // Simpan pertanyaan terakhir yang ditampilkan

  try {
    const response = await axios.post("http://192.168.0.103:7000/ask/", {
      question: q,
    });

    const newAnswer = response.data.answer;
    setAnswer(newAnswer);

    const newHistoryItem = { question: q, answer: newAnswer };
    const updatedHistory = [...history, newHistoryItem];

    setHistory(updatedHistory);
    localStorage.setItem("chatHistory", JSON.stringify(updatedHistory));
  } catch (error) {
    console.error("Error fetching data: ", error);
    setAnswer("Sorry, an error occurred while processing your inquiry.");
  }

  setQuestion(""); // Kosongkan input field
  setLoading(false);
};



  const handleHistoryClick = (item) => {
    setQuestion(item.question);
    setAnswer(item.answer);
  };

  return (
    <div style={styles.container}>
      <div style={styles.chatBox}>
        <h2 style={styles.header}>💬 Chat Assistant Based RAG</h2>

        <div style={styles.messages}>
          {answer && (
              <>
                <div style={styles.userBubble}>
                  <strong>Question:</strong> {currentQuestion}
                </div>
                <div style={styles.aiBubble}>
                  <strong>Answer:</strong> {answer}
                </div>
              </>
            )}

        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question..."
            style={styles.input}
            required
          />
          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? "⏳..." : "Send"}
          </button>
        </form>

        <div style={styles.historyContainer}>
          <h4 style={styles.historyTitle}>Chat History</h4>
          {[...history].reverse().map((item, index) => (
            <div
              key={index}
              style={styles.historyItem}
              onClick={() => handleHistoryClick(item)}
            >
              <div style={styles.historyQ}><strong>Q:</strong> {item.question}</div>
              <div style={styles.historyA}><strong>A:</strong> {item.answer}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    fontFamily: "'Segoe UI', sans-serif",
    backgroundColor: "#f5f7fb",
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    paddingTop: "40px",
  },
  chatBox: {
    width: "100%",
    maxWidth: "600px",
    backgroundColor: "#fff",
    borderRadius: "12px",
    boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
    padding: "30px",
  },
  header: {
    textAlign: "center",
    fontWeight: "600",
    fontSize: "22px",
    marginBottom: "20px",
    color: "#1a1a1a",
  },
  messages: {
    marginBottom: "20px",
    fontSize: "16px",
  },
  userBubble: {
    backgroundColor: "#e0f2fe",
    padding: "12px 16px",
    borderRadius: "8px",
    marginBottom: "10px",
  },
  aiBubble: {
    backgroundColor: "#f0fdf4",
    padding: "12px 16px",
    borderRadius: "8px",
  },
  form: {
    display: "flex",
    gap: "10px",
    marginBottom: "30px",
  },
  input: {
    flexGrow: 1,
    padding: "12px 16px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    fontSize: "16px",
  },
  button: {
    backgroundColor: "#2563eb",
    color: "#fff",
    border: "none",
    padding: "12px 20px",
    fontSize: "16px",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "background 0.3s",
  },
  historyContainer: {
    borderTop: "1px solid #ddd",
    paddingTop: "20px",
  },
  historyTitle: {
    fontSize: "18px",
    marginBottom: "12px",
    color: "#333",
  },
  historyItem: {
    backgroundColor: "#f9fafb",
    border: "1px solid #e2e8f0",
    borderRadius: "8px",
    padding: "12px",
    marginBottom: "12px",
    cursor: "pointer",
    transition: "background 0.2s ease",
  },
  historyItemHover: {
    backgroundColor: "#edf2f7",
  },
  historyQ: {
    fontWeight: "500",
    marginBottom: "4px",
  },
  historyA: {
    color: "#555",
  },
};

export default ChatComponent;
