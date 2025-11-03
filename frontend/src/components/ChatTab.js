import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Bot, User } from "lucide-react";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ChatTab() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
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
        };
        setMessages((prev) => [...prev, aiMessage]);

        if (data.portfolio_updated) {
          toast.success("Portfolio updated based on your preferences!");
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

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isLoadingHistory) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-slate-600">Loading chat...</div>
      </div>
    );
  }

  return (
    <div className="glass rounded-2xl overflow-hidden shadow-xl" data-testid="chat-interface">
      {/* Messages Area */}
      <div className="h-[600px] overflow-y-auto p-6 space-y-4" data-testid="chat-messages">
        {messages.length === 0 ? (
          <div className="text-center text-slate-500 mt-20">
            <Bot className="w-16 h-16 mx-auto mb-4 text-blue-600" />
            <h3 className="text-xl font-semibold text-slate-800 mb-2">
              Welcome to Your Financial Advisor!
            </h3>
            <p className="text-sm">
              Tell me about your investment preferences, risk tolerance, and goals.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              data-testid={`message-${msg.role}`}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-slate-800 shadow-md"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="prose prose-sm max-w-none text-sm">
                    <ReactMarkdown>
                      {msg.message}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-slate-600" />
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
              <Bot className="w-5 h-5 text-blue-600" />
            </div>
            <div className="bg-white rounded-2xl px-4 py-3 shadow-md">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-200 p-4 bg-white/50">
        <div className="flex gap-2">
          <Textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Tell me about your investment goals..."
            data-testid="chat-input"
            className="resize-none rounded-xl border-slate-300 focus:border-blue-500"
            rows={2}
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            data-testid="send-button"
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-6"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}