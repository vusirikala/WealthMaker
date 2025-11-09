import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Bot, User, Sparkles, CheckCircle2, XCircle, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ChatTab({ portfolioId = null }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [pendingSuggestions, setPendingSuggestions] = useState({});
  const [portfolioContext, setPortfolioContext] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Clear messages when portfolio changes to avoid showing old messages
    setMessages([]);
    setIsLoadingHistory(true);
    
    // Load chat history for this specific portfolio
    loadChatHistory();
    
    // Load portfolio context if portfolioId is provided
    if (portfolioId) {
      loadPortfolioContext();
    } else {
      setPortfolioContext(null);
    }
  }, [portfolioId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadPortfolioContext = async () => {
    if (!portfolioId) return;
    
    try {
      const response = await fetch(`${API}/portfolios-v2/${portfolioId}`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setPortfolioContext(data.portfolio);
      }
    } catch (error) {
      console.error("Error loading portfolio context:", error);
    }
  };

  const loadChatHistory = async () => {
    try {
      // Add portfolio_id as query parameter if available
      const url = portfolioId 
        ? `${API}/chat/messages?portfolio_id=${portfolioId}`
        : `${API}/chat/messages`;
      
      console.log(`Loading chat history for portfolio: ${portfolioId || 'global'}`);
      
      const response = await fetch(url, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        console.log(`Loaded ${data.length} messages for portfolio: ${portfolioId || 'global'}`);
        setMessages(data);
        
        // If no messages, try to initialize chat with AI greeting
        if (data.length === 0) {
          try {
            const initResponse = await fetch(`${API}/chat/init`, {
              credentials: "include",
            });
            if (initResponse.ok) {
              const initData = await initResponse.json();
              if (initData.message) {
                // Add the initial AI message to the chat
                const aiMessage = {
                  role: "assistant",
                  message: initData.message,
                  timestamp: initData.timestamp || new Date().toISOString(),
                };
                setMessages([aiMessage]);
              }
            }
          } catch (initError) {
            console.error("Failed to initialize chat:", initError);
          }
        }
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
      // Include portfolio_id if available
      const requestBody = { 
        message: userMessage,
        portfolio_id: portfolioId || null
      };
      
      // Also include portfolio context for AI awareness
      if (portfolioContext) {
        requestBody.portfolio_context = {
          portfolio_id: portfolioContext.portfolio_id,
          name: portfolioContext.name,
          goal: portfolioContext.goal,
          allocations: portfolioContext.allocations,
          total_invested: portfolioContext.total_invested
        };
      }

      const response = await fetch(`${API}/chat/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(requestBody),
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
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (e) {
          // If JSON parsing fails, use empty object
          console.error("Could not parse error response as JSON:", e);
        }
        console.error("Failed to send message:", response.status, errorData);
        toast.error(`Failed to send message: ${errorData.detail || response.statusText}`);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error(`Something went wrong: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptPortfolio = async (suggestionId, portfolioData) => {
    console.log("Accepting portfolio with data:", portfolioData);
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
        console.log("Portfolio accepted successfully");
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
        console.log("Dispatching portfolioUpdated event");
        window.dispatchEvent(new Event('portfolioUpdated'));
      } else {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (e) {
          console.error("Could not parse error response as JSON:", e);
        }
        console.error("Failed to accept portfolio:", errorData);
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
    <div className="h-full flex flex-col" data-testid="chat-interface">
      {/* Portfolio Context Header */}
      {portfolioContext && (
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white border-b border-purple-700 px-4 py-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-sm font-bold">
                  {portfolioContext.name}
                </div>
                {portfolioContext.goal && (
                  <div className="text-xs text-white/80 truncate max-w-[300px]">
                    {portfolioContext.goal}
                  </div>
                )}
              </div>
            </div>
            <div className="text-xs bg-white/20 px-2 py-1 rounded-full">
              Portfolio Chat
            </div>
          </div>
        </div>
      )}
      
      {/* Debug Info - Remove after testing */}
      {portfolioId && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 text-xs text-blue-700">
          🔍 Debug: Portfolio ID: {portfolioId} | Messages: {messages.length}
        </div>
      )}
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50" data-testid="chat-messages">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-20 fade-in px-4">
            <div className="w-14 h-14 mx-auto mb-4 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-xl flex items-center justify-center">
              <Bot className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              {portfolioContext ? `Chat about ${portfolioContext.name}` : 'Welcome to Your AI Advisor!'}
            </h3>
            <p className="text-sm text-gray-600 max-w-sm mx-auto">
              {portfolioContext 
                ? `Ask me anything about your ${portfolioContext.name} portfolio or request adjustments.`
                : 'Ask me about your investment preferences, risk tolerance, and financial goals.'}
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx}>
              <div
                data-testid={`message-${msg.role}`}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"} smooth-transition`}
              >
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center flex-shrink-0 shadow-sm">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-xl px-4 py-3 smooth-transition ${
                    msg.role === "user"
                      ? "bg-gradient-to-r from-cyan-600 to-emerald-600 text-white shadow-md"
                      : "bg-white text-gray-900 shadow-sm border border-gray-200"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div className="prose prose-sm max-w-none text-sm text-gray-900">
                      <ReactMarkdown>
                        {msg.message}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.message}</p>
                  )}
                </div>
                {msg.role === "user" && (
                  <div className="w-10 h-10 rounded-xl bg-gray-700 flex items-center justify-center flex-shrink-0 shadow-sm">
                    <User className="w-6 h-6 text-white" />
                  </div>
                )}
              </div>

              {/* Portfolio Suggestion Card */}
              {msg.role === "assistant" && msg.portfolio_suggestion && msg.suggestion_id && pendingSuggestions[msg.suggestion_id] && (
                <div className="ml-14 mt-4 clean-card p-6 max-w-[80%] border-2 border-cyan-200 bg-gradient-to-br from-cyan-50 to-emerald-50">
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp className="w-5 h-5 text-cyan-600" />
                    <h4 className="font-bold text-gray-900">Portfolio Recommendation</h4>
                  </div>
                  
                  <div className="space-y-3 mb-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Risk Tolerance:</span>
                      <span className="font-semibold text-gray-900 capitalize">{msg.portfolio_suggestion.risk_tolerance}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">ROI Target:</span>
                      <span className="font-semibold text-gray-900">{msg.portfolio_suggestion.roi_expectations}%</span>
                    </div>
                    
                    <div className="divider my-3"></div>
                    
                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-2">Allocations:</p>
                      <div className="space-y-2">
                        {msg.portfolio_suggestion.allocations?.map((alloc, i) => (
                          <div key={i} className="flex justify-between items-center text-sm bg-white rounded-lg p-2 border border-gray-200">
                            <div>
                              <span className="font-bold text-gray-900">{alloc.ticker}</span>
                              <span className="text-gray-500 ml-2">({alloc.asset_type})</span>
                            </div>
                            <span className="font-semibold gradient-text">{alloc.allocation}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleAcceptPortfolio(msg.suggestion_id, msg.portfolio_suggestion)}
                      className="flex-1 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white rounded-lg font-semibold shadow-md"
                      data-testid="accept-portfolio-btn"
                    >
                      <CheckCircle2 className="w-4 h-4 mr-2" />
                      Accept Portfolio
                    </Button>
                    <Button
                      onClick={() => handleRejectPortfolio(msg.suggestion_id)}
                      variant="outline"
                      className="flex-1 border-gray-300 text-gray-700 hover:bg-gray-100 rounded-lg font-semibold"
                      data-testid="reject-portfolio-btn"
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex gap-4 justify-start">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center flex-shrink-0">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div className="bg-white rounded-2xl px-6 py-4 border border-gray-200 shadow-sm">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                <div className="w-2 h-2 bg-cyan-600 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-white flex-shrink-0">
        <div className="flex gap-2">
          <Textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your portfolio or investment goals..."
            data-testid="chat-input"
            className="resize-none rounded-lg border-2 border-gray-200 bg-white text-gray-900 placeholder:text-gray-400 focus:border-cyan-500 smooth-transition text-sm"
            rows={2}
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            data-testid="send-button"
            className="bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white rounded-lg px-4 shadow-md flex-shrink-0"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}