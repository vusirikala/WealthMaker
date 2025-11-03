import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Bot, User, Sparkles, CheckCircle2, XCircle, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ChatTab() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [pendingSuggestions, setPendingSuggestions] = useState({});
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadChatHistory = async () => {
    try {
      const response = await fetch(`${API}/chat/messages`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (error) {
      console.error("Failed to load chat history:", error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");
    setIsLoading(true);

    // Add user message optimistically
    const tempUserMsg = {
      role: "user",
      message: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await fetch(`${API}/chat/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ message: userMessage }),
      });

      if (response.ok) {
        const data = await response.json();
        const aiMessage = {
          role: "assistant",
          message: data.message,
          timestamp: new Date().toISOString(),
          portfolio_suggestion: data.portfolio_suggestion,
          suggestion_id: data.suggestion_id,
        };
        setMessages((prev) => [...prev, aiMessage]);

        if (data.portfolio_suggestion && data.suggestion_id) {
          // Store the suggestion
          setPendingSuggestions(prev => ({
            ...prev,
            [data.suggestion_id]: data.portfolio_suggestion
          }));
        }
      } else {
        toast.error("Failed to send message");
      }
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptPortfolio = async (suggestionId, portfolioData) => {
    try {
      const response = await fetch(`${API}/portfolio/accept`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ 
          suggestion_id: suggestionId,
          portfolio_data: portfolioData
        }),
      });

      if (response.ok) {
        toast.success("Portfolio updated successfully!", {
          icon: <CheckCircle2 className="w-5 h-5" />,
        });
        
        // Remove from pending suggestions
        setPendingSuggestions(prev => {
          const newSuggestions = { ...prev };
          delete newSuggestions[suggestionId];
          return newSuggestions;
        });

        // Add a confirmation message
        const confirmMsg = {
          role: "assistant",
          message: "Great! I've updated your portfolio. You can view it in the Portfolio tab.",
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, confirmMsg]);
        
        // Refresh portfolio data (trigger event)
        window.dispatchEvent(new Event('portfolioUpdated'));
      } else {
        toast.error("Failed to update portfolio");
      }
    } catch (error) {
      console.error("Error accepting portfolio:", error);
      toast.error("Something went wrong");
    }
  };

  const handleRejectPortfolio = (suggestionId) => {
    setPendingSuggestions(prev => {
      const newSuggestions = { ...prev };
      delete newSuggestions[suggestionId];
      return newSuggestions;
    });

    const rejectMsg = {
      role: "assistant",
      message: "No problem! Feel free to tell me more about what you're looking for, and I can suggest a different portfolio allocation.",
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, rejectMsg]);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isLoadingHistory) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="w-16 h-16 spinner"></div>
      </div>
    );
  }

  return (
    <div className="clean-card rounded-2xl overflow-hidden shadow-sm" data-testid="chat-interface">
      {/* Messages Area */}
      <div className="h-[600px] overflow-y-auto p-6 space-y-6" data-testid="chat-messages">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-32 stagger-item">
            <div className="relative inline-block mb-6">
              <Bot className="w-20 h-20 mx-auto text-purple-400" style={{ filter: 'drop-shadow(0 0 20px rgba(168, 85, 247, 0.8))' }} />
              <div className="absolute inset-0 bg-purple-400 blur-2xl opacity-50 animate-pulse"></div>
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">
              <span className="gradient-text">Welcome to Your AI Financial Advisor!</span>
            </h3>
            <p className="text-base text-gray-300 max-w-md mx-auto">
              Tell me about your investment preferences, risk tolerance, and financial goals.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              data-testid={`message-${msg.role}`}
              className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"} smooth-transition hover:scale-[1.02]`}
            >
              {msg.role === "assistant" && (
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center flex-shrink-0 neon-glow">
                  <Bot className="w-6 h-6 text-white" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-3xl px-6 py-4 smooth-transition ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-teal-600 to-cyan-600 text-white neon-glow"
                    : "glass-card text-white border border-purple-500/30"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="prose prose-sm max-w-none text-sm text-gray-100">
                    <ReactMarkdown>
                      {msg.message}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.message}</p>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-pink-600 to-rose-600 flex items-center justify-center flex-shrink-0 neon-glow">
                  <User className="w-6 h-6 text-white" />
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex gap-4 justify-start">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center flex-shrink-0 pulse-glow">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div className="glass-card rounded-3xl px-6 py-4 border border-purple-500/30">
              <div className="flex gap-2">
                <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce"></div>
                <div className="w-3 h-3 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                <div className="w-3 h-3 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-purple-500/20 p-4 glass-card">
        <div className="flex gap-3">
          <Textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your investment strategy..."
            data-testid="chat-input"
            className="resize-none rounded-2xl border-2 border-purple-500/30 bg-transparent text-white placeholder:text-gray-500 focus:border-purple-500 smooth-transition"
            rows={2}
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            data-testid="send-button"
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-2xl px-8 neon-glow hover-lift"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}