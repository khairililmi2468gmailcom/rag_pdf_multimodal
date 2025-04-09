import React, { useState } from "react";
import axios from "axios";

const ChatComponent = () => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post("http://0.0.0.0:8080/ask/", {
        question,
      });
      
      setAnswer(response.data.answer);
    } catch (error) {
      console.error("Error fetching data: ", error);
      setAnswer("Sorry, there was an error while processing your request.");
    }

    setLoading(false);
  };

  return (
    <div style={styles.container}>
      <div style={styles.chatContainer}>
        <div style={styles.chatHeader}>Chat with AI</div>
        <div style={styles.messages}>
          <div style={styles.userMessage}>
            <strong>Your Question: </strong>{question}
          </div>
          <div style={styles.aiMessage}>
            <strong>RAG Answer: </strong>{answer}
          </div>
        </div>
        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question..."
            style={styles.input}
            required
          />
          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? "Loading..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    backgroundColor: "#f0f0f0",
  },
  chatContainer: {
    width: "400px",
    padding: "20px",
    backgroundColor: "white",
    borderRadius: "8px",
    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
    textAlign: "center",
  },
  chatHeader: {
    fontSize: "24px",
    marginBottom: "20px",
    color: "#333",
  },
  messages: {
    textAlign: "left",
    marginBottom: "20px",
    minHeight: "100px",
    fontSize: "16px",
    color: "#555",
  },
  userMessage: {
    backgroundColor: "#e8f4f8",
    padding: "10px",
    borderRadius: "8px",
    marginBottom: "10px",
  },
  aiMessage: {
    backgroundColor: "#e0f7fa",
    padding: "10px",
    borderRadius: "8px",
    marginBottom: "10px",
  },
  form: {
    display: "flex",
    justifyContent: "space-between",
  },
  input: {
    width: "80%",
    padding: "10px",
    borderRadius: "4px",
    border: "1px solid #ddd",
    fontSize: "16px",
  },
  button: {
    padding: "10px 20px",
    backgroundColor: "#007bff",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "16px",
    transition: "background-color 0.3s",
  },
};

export default ChatComponent;
