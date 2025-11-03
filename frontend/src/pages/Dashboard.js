import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LogOut, MessageSquare, PieChart, Newspaper, TrendingUp, Sparkles } from "lucide-react";
import ChatTab from "@/components/ChatTab";
import PortfolioTab from "@/components/PortfolioTab";
import NewsTab from "@/components/NewsTab";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard({ user, setIsAuthenticated }) {
  const [activeTab, setActiveTab] = useState("chat");

  const handleLogout = async () => {
    try {
      await fetch(`${API}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      setIsAuthenticated(false);
      toast.success("Logged out successfully");
    } catch (error) {
      console.error("Logout error:", error);
      toast.error("Failed to logout");
    }
  };

  return (
    <div className="min-h-screen animated-bg relative overflow-hidden" data-testid="dashboard">
      {/* Animated background particles */}
      <div className="particle-bg">
        {[...Array(15)].map((_, i) => (
          <div
            key={i}
            className="particle"
            style={{
              width: Math.random() * 4 + 2 + 'px',
              height: Math.random() * 4 + 2 + 'px',
              left: Math.random() * 100 + '%',
              background: `rgba(${i % 3 === 0 ? '168, 85, 247' : i % 3 === 1 ? '20, 184, 166' : '251, 113, 133'}, 0.4)`,
              animation: `particle-float ${Math.random() * 15 + 15}s linear infinite`,
              animationDelay: `${Math.random() * 5}s`
            }}
          />
        ))}
      </div>

      {/* Header */}
      <header className="glass-card border-b border-purple-500/20 sticky top-0 z-50 backdrop-blur-xl">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 group">
              <div className="relative">
                <TrendingUp className="w-8 h-8 text-purple-400" style={{ filter: 'drop-shadow(0 0 8px rgba(168, 85, 247, 0.8))' }} />
                <div className="absolute inset-0 bg-purple-400 blur-lg opacity-50 group-hover:opacity-100 transition-opacity"></div>
              </div>
              <span className="text-2xl font-bold gradient-text">SmartFolio</span>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-3 glass-card px-4 py-2 rounded-full border border-purple-500/30">
                <Avatar className="w-8 h-8 border-2 border-purple-500">
                  <AvatarImage src={user?.picture} alt={user?.name} />
                  <AvatarFallback className="bg-gradient-to-br from-purple-600 to-pink-600 text-white">
                    {user?.name?.[0] || "U"}
                  </AvatarFallback>
                </Avatar>
                <div className="text-right">
                  <p className="text-sm font-semibold text-white">{user?.name}</p>
                  <p className="text-xs text-gray-400">{user?.email}</p>
                </div>
              </div>
              <Button
                onClick={handleLogout}
                variant="outline"
                size="sm"
                data-testid="logout-button"
                className="rounded-full border-2 border-purple-500/50 text-purple-300 hover:bg-purple-500/20 hover:border-purple-400 smooth-transition"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 relative z-10">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="glass-card w-full sm:w-auto grid grid-cols-3 mb-8 p-1.5 rounded-2xl border border-purple-500/30 neon-glow">
            <TabsTrigger
              value="chat"
              data-testid="tab-chat"
              className="rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-600 data-[state=active]:to-pink-600 data-[state=active]:text-white smooth-transition font-semibold"
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Chat</span>
            </TabsTrigger>
            <TabsTrigger
              value="portfolio"
              data-testid="tab-portfolio"
              className="rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-teal-600 data-[state=active]:to-cyan-600 data-[state=active]:text-white smooth-transition font-semibold"
            >
              <PieChart className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Portfolio</span>
            </TabsTrigger>
            <TabsTrigger
              value="news"
              data-testid="tab-news"
              className="rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-pink-600 data-[state=active]:to-rose-600 data-[state=active]:text-white smooth-transition font-semibold"
            >
              <Newspaper className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">News</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="mt-0">
            <ChatTab />
          </TabsContent>

          <TabsContent value="portfolio" className="mt-0">
            <PortfolioTab />
          </TabsContent>

          <TabsContent value="news" className="mt-0">
            <NewsTab />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}