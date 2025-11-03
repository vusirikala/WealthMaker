import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { TrendingUp, Shield, BarChart3, Newspaper, Sparkles, Zap, ArrowRight } from "lucide-react";
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
    console.log("Processing session ID:", sessionId.substring(0, 10) + "...");
    setIsProcessing(true);
    try {
      const response = await fetch(`${API}/auth/session`, {
        method: "POST",
        credentials: "include",
        headers: {
          "X-Session-ID": sessionId,
        },
      });

      console.log("Session response status:", response.status);

      if (response.ok) {
        const data = await response.json();
        console.log("Session data received:", data.user.email);
        setUser(data.user);
        setIsAuthenticated(true);
        
        // Clean URL and navigate to dashboard
        window.history.replaceState({}, document.title, "/");
        toast.success("Welcome to SmartFolio!");
        
        // Navigate to dashboard
        console.log("Navigating to dashboard...");
        setTimeout(() => {
          navigate("/dashboard", { replace: true });
        }, 100);
      } else {
        const errorText = await response.text();
        console.error("Authentication failed:", response.status, errorText);
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
      <div className="min-h-screen flex items-center justify-center animated-bg">
        <div className="text-center">
          <div className="w-20 h-20 mx-auto mb-6 spinner"></div>
          <p className="text-xl font-medium gradient-text">Setting up your portfolio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen animated-bg relative overflow-hidden" data-testid="landing-page">
      {/* Animated particles background */}
      <div className="particle-bg">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="particle"
            style={{
              width: Math.random() * 5 + 2 + 'px',
              height: Math.random() * 5 + 2 + 'px',
              left: Math.random() * 100 + '%',
              background: `rgba(${i % 3 === 0 ? '6, 182, 212' : i % 3 === 1 ? '16, 185, 129' : '12, 74, 110'}, 0.6)`,
              animation: `particle-float ${Math.random() * 10 + 10}s linear infinite`,
              animationDelay: `${Math.random() * 5}s`
            }}
          />
        ))}
      </div>

      <div className="container mx-auto px-4 py-8 relative z-10">
        {/* Nav */}
        <nav className="flex justify-between items-center mb-20 stagger-item">
          <div className="flex items-center gap-3 group">
            <div className="relative">
              <TrendingUp className="w-10 h-10 text-cyan-400" style={{ filter: 'drop-shadow(0 0 10px rgba(6, 182, 212, 0.8))' }} />
              <div className="absolute inset-0 bg-cyan-400 blur-xl opacity-50 group-hover:opacity-100 transition-opacity"></div>
            </div>
            <span className="text-3xl font-bold gradient-text">SmartFolio</span>
          </div>
          <Button
            onClick={handleLogin}
            data-testid="login-button"
            className="bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white px-8 py-3 rounded-full shadow-lg neon-glow font-semibold"
          >
            Sign In
          </Button>
        </nav>

        {/* Hero */}
        <div className="text-center max-w-5xl mx-auto mb-24 stagger-item">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/30 mb-8 pulse-glow">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span className="text-sm font-medium text-cyan-300">AI-Powered Financial Intelligence</span>
          </div>
          
          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-black mb-8 leading-tight">
            <span className="block text-white mb-2">Build Your</span>
            <span className="block gradient-text text-transparent bg-clip-text">Perfect Portfolio</span>
          </h1>
          
          <p className="text-xl sm:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
            Harness the power of AI to create personalized investment strategies that match your goals, risk tolerance, and dreams.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button
              onClick={handleLogin}
              data-testid="get-started-button"
              size="lg"
              className="bg-gradient-to-r from-purple-600 via-pink-600 to-teal-600 hover:from-purple-700 hover:via-pink-700 hover:to-teal-700 text-white px-12 py-7 text-xl rounded-full font-bold neon-glow hover-lift group"
            >
              Get Started Free
              <ArrowRight className="w-6 h-6 ml-2 group-hover:translate-x-2 transition-transform" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="border-2 border-purple-500/50 text-purple-300 hover:bg-purple-500/10 px-10 py-7 text-xl rounded-full font-semibold backdrop-blur-sm"
            >
              Watch Demo
            </Button>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="glass-card rounded-3xl p-8 hover-lift stagger-item" data-testid="feature-chat">
            <div className="relative mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-600 to-purple-800 rounded-2xl flex items-center justify-center neon-glow">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <Zap className="absolute -top-2 -right-2 w-6 h-6 text-teal-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">AI Financial Advisor</h3>
            <p className="text-gray-300 leading-relaxed">
              Engage with our intelligent AI to understand your risk profile, financial goals, and receive tailored investment recommendations.
            </p>
          </div>

          <div className="glass-card rounded-3xl p-8 hover-lift stagger-item" data-testid="feature-portfolio">
            <div className="relative mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-teal-600 to-teal-800 rounded-2xl flex items-center justify-center neon-glow">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
              <Sparkles className="absolute -top-2 -right-2 w-6 h-6 text-coral-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Visual Analytics</h3>
            <p className="text-gray-300 leading-relaxed">
              Stunning visualizations of your portfolio allocation, sector distribution, and historical performance with real-time updates.
            </p>
          </div>

          <div className="glass-card rounded-3xl p-8 hover-lift stagger-item" data-testid="feature-news">
            <div className="relative mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-pink-600 to-pink-800 rounded-2xl flex items-center justify-center neon-glow">
                <Newspaper className="w-8 h-8 text-white" />
              </div>
              <TrendingUp className="absolute -top-2 -right-2 w-6 h-6 text-purple-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Real-Time Market News</h3>
            <p className="text-gray-300 leading-relaxed">
              Stay ahead with the latest news and insights for every stock in your portfolio, delivered in real-time.
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto mt-24 stagger-item">
          <div className="text-center">
            <div className="text-5xl font-black gradient-text mb-2">98%</div>
            <div className="text-gray-400 text-sm uppercase tracking-wider">Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-5xl font-black gradient-text mb-2">24/7</div>
            <div className="text-gray-400 text-sm uppercase tracking-wider">AI Support</div>
          </div>
          <div className="text-center">
            <div className="text-5xl font-black gradient-text mb-2">Real-time</div>
            <div className="text-gray-400 text-sm uppercase tracking-wider">Market Data</div>
          </div>
        </div>
      </div>
    </div>
  );
}