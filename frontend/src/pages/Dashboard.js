import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LogOut, MessageSquare, PieChart, Newspaper, TrendingUp } from "lucide-react";
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-emerald-50" data-testid="dashboard">
      {/* Header */}
      <header className="glass border-b border-slate-200/50 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-blue-600" />
              <span className="text-2xl font-bold text-slate-800">SmartFolio</span>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={user?.picture} alt={user?.name} />
                  <AvatarFallback>{user?.name?.[0] || "U"}</AvatarFallback>
                </Avatar>
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-800">{user?.name}</p>
                  <p className="text-xs text-slate-500">{user?.email}</p>
                </div>
              </div>
              <Button
                onClick={handleLogout}
                variant="outline"
                size="sm"
                data-testid="logout-button"
                className="rounded-full border-slate-300 hover:bg-slate-100"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="glass w-full sm:w-auto grid grid-cols-3 mb-8 p-1 rounded-xl">
            <TabsTrigger
              value="chat"
              data-testid="tab-chat"
              className="rounded-lg data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Chat</span>
            </TabsTrigger>
            <TabsTrigger
              value="portfolio"
              data-testid="tab-portfolio"
              className="rounded-lg data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <PieChart className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Portfolio</span>
            </TabsTrigger>
            <TabsTrigger
              value="news"
              data-testid="tab-news"
              className="rounded-lg data-[state=active]:bg-blue-600 data-[state=active]:text-white"
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