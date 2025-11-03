import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { TrendingUp, Shield, BarChart3, Newspaper } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LandingPage({ setIsAuthenticated, setUser }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check for session_id in URL fragment
    const hash = window.location.hash;
    if (hash && hash.includes("session_id=")) {
      const sessionId = hash.split("session_id=")[1].split("&")[0];
      handleSessionCallback(sessionId);
    }
  }, []);

  const handleSessionCallback = async (sessionId) => {
    setIsProcessing(true);
    try {
      const response = await fetch(`${API}/auth/session`, {
        method: "POST",
        credentials: "include",
        headers: {
          "X-Session-ID": sessionId,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setIsAuthenticated(true);
        
        // Clean URL and navigate to dashboard
        window.history.replaceState({}, document.title, "/");
        toast.success("Welcome to SmartFolio!");
        
        // Navigate to dashboard
        setTimeout(() => {
          navigate("/dashboard", { replace: true });
        }, 100);
      } else {
        toast.error("Authentication failed. Please try again.");
        setIsProcessing(false);
      }
    } catch (error) {
      console.error("Session processing error:", error);
      toast.error("Something went wrong. Please try again.");
      setIsProcessing(false);
    }
  };

  const handleLogin = () => {
    const redirectUrl = encodeURIComponent(`${window.location.origin}/`);
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;
  };

  if (isProcessing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-emerald-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-slate-600">Setting up your portfolio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-emerald-50" data-testid="landing-page">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <nav className="flex justify-between items-center mb-20">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-8 h-8 text-blue-600" />
            <span className="text-2xl font-bold text-slate-800">SmartFolio</span>
          </div>
          <Button
            onClick={handleLogin}
            data-testid="login-button"
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-full shadow-lg"
          >
            Sign In
          </Button>
        </nav>

        <div className="text-center max-w-4xl mx-auto mb-20">
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-800 mb-6 leading-tight">
            Build Your Perfect
            <span className="block bg-gradient-to-r from-blue-600 to-emerald-500 bg-clip-text text-transparent">
              Investment Portfolio
            </span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-600 mb-10 max-w-2xl mx-auto">
            AI-powered financial advisor that understands your goals and creates personalized investment strategies
          </p>
          <Button
            onClick={handleLogin}
            data-testid="get-started-button"
            size="lg"
            className="bg-blue-600 hover:bg-blue-700 text-white px-10 py-6 text-lg rounded-full shadow-2xl hover:shadow-blue-200"
          >
            Get Started Free
          </Button>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="glass rounded-2xl p-8 hover:shadow-xl" data-testid="feature-chat">
            <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
              <Shield className="w-7 h-7 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-3">AI Financial Advisor</h3>
            <p className="text-slate-600">
              Chat with our AI to understand your risk tolerance, goals, and preferences for personalized recommendations
            </p>
          </div>

          <div className="glass rounded-2xl p-8 hover:shadow-xl" data-testid="feature-portfolio">
            <div className="w-14 h-14 bg-emerald-100 rounded-xl flex items-center justify-center mb-4">
              <BarChart3 className="w-7 h-7 text-emerald-600" />
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-3">Visual Portfolio Analytics</h3>
            <p className="text-slate-600">
              Beautiful charts showing allocation across sectors, asset types, and historical performance
            </p>
          </div>

          <div className="glass rounded-2xl p-8 hover:shadow-xl" data-testid="feature-news">
            <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
              <Newspaper className="w-7 h-7 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-3">Real-Time News</h3>
            <p className="text-slate-600">
              Stay updated with the latest news for all stocks in your portfolio
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}