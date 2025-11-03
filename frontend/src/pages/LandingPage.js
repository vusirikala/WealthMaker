import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { TrendingUp, Shield, BarChart3, Newspaper, Sparkles, CheckCircle2, ArrowRight } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LandingPage({ setIsAuthenticated, setUser }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const hash = window.location.hash;
    if (hash && hash.includes("session_id=")) {
      const sessionId = hash.split("session_id=")[1].split("&")[0];
      handleSessionCallback(sessionId);
    }

    // Listen for messages from popup window
    const handleMessage = (event) => {
      // Verify origin for security
      if (event.origin !== window.location.origin) return;
      
      if (event.data.type === 'AUTH_SUCCESS' && event.data.sessionId) {
        handleSessionCallback(event.data.sessionId);
      }
    };

    window.addEventListener('message', handleMessage);
    
    return () => {
      window.removeEventListener('message', handleMessage);
    };
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
        
        window.history.replaceState({}, document.title, "/");
        toast.success("Welcome to SmartFolio!");
        
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
    // Create a special callback page URL
    const callbackUrl = encodeURIComponent(`${window.location.origin}/auth-callback`);
    const authUrl = `https://auth.emergentagent.com/?redirect=${callbackUrl}`;
    
    // Open popup window
    const width = 500;
    const height = 600;
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    
    const popup = window.open(
      authUrl,
      'Google Sign In',
      `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );

    // Check if popup was blocked
    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
      toast.error('Popup blocked. Please allow popups for this site.');
      return;
    }

    // Monitor popup
    const checkPopup = setInterval(() => {
      if (!popup || popup.closed) {
        clearInterval(checkPopup);
      }
    }, 1000);
  };

  if (isProcessing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-6 spinner"></div>
          <p className="text-lg font-medium text-gray-900">Setting up your portfolio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50" data-testid="landing-page">
      <div className="container mx-auto px-4 py-6">
        {/* Nav */}
        <nav className="flex justify-between items-center mb-16 fade-in">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-xl flex items-center justify-center shadow-sm">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-gray-900">SmartFolio</span>
          </div>
          <Button
            onClick={handleLogin}
            data-testid="login-button"
            variant="outline"
            className="border-gray-300 text-gray-700 hover:bg-gray-50 px-6 py-2 rounded-lg font-medium smooth-transition"
          >
            Sign In
          </Button>
        </nav>

        {/* Hero */}
        <div className="max-w-4xl mx-auto text-center mb-20">
          <div className="badge mb-6 fade-in-1">
            <Sparkles className="w-4 h-4 mr-2 text-cyan-600" />
            AI-Powered Financial Intelligence
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight fade-in-2">
            Build Your Perfect
            <span className="block gradient-text mt-2">Investment Portfolio</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed fade-in-3">
            Harness the power of AI to create personalized investment strategies tailored to your goals and risk tolerance.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center fade-in-4">
            <Button
              onClick={handleLogin}
              data-testid="get-started-button"
              size="lg"
              className="bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white px-10 py-6 text-lg rounded-xl font-semibold shadow-lg shadow-cyan-500/25 group"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 smooth-transition" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="border-gray-300 text-gray-700 hover:bg-gray-50 px-10 py-6 text-lg rounded-xl font-semibold"
            >
              Watch Demo
            </Button>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-20">
          <div className="clean-card p-8 card-hover fade-in-1" data-testid="feature-chat">
            <div className="icon-wrapper mb-6">
              <Shield className="w-6 h-6 text-cyan-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">AI Financial Advisor</h3>
            <p className="text-gray-600 leading-relaxed">
              Chat with our intelligent AI to understand your risk profile and receive personalized investment recommendations.
            </p>
          </div>

          <div className="clean-card p-8 card-hover fade-in-2" data-testid="feature-portfolio">
            <div className="icon-wrapper mb-6">
              <BarChart3 className="w-6 h-6 text-emerald-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">Visual Analytics</h3>
            <p className="text-gray-600 leading-relaxed">
              Beautiful visualizations of portfolio allocation, sector distribution, and historical performance.
            </p>
          </div>

          <div className="clean-card p-8 card-hover fade-in-3" data-testid="feature-news">
            <div className="icon-wrapper mb-6">
              <Newspaper className="w-6 h-6 text-cyan-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">Real-Time Market News</h3>
            <p className="text-gray-600 leading-relaxed">
              Stay informed with the latest news and insights for every stock in your portfolio.
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="max-w-4xl mx-auto">
          <div className="clean-card p-12">
            <div className="grid md:grid-cols-3 gap-12">
              <div className="text-center fade-in-1">
                <div className="stat-number mb-2">98%</div>
                <div className="text-gray-600 text-sm font-medium uppercase tracking-wide">Accuracy Rate</div>
              </div>
              <div className="text-center fade-in-2">
                <div className="stat-number mb-2">24/7</div>
                <div className="text-gray-600 text-sm font-medium uppercase tracking-wide">AI Support</div>
              </div>
              <div className="text-center fade-in-3">
                <div className="stat-number mb-2">Real-time</div>
                <div className="text-gray-600 text-sm font-medium uppercase tracking-wide">Market Data</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}