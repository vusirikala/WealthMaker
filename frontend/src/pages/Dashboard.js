import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LogOut, MessageSquare, PieChart, Newspaper, TrendingUp, Sparkles, User, Settings } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import ChatTab from "@/components/ChatTab";
import PortfolioTab from "@/components/PortfolioTab";
import NewsTab from "@/components/NewsTab";
import OnboardingForm from "@/components/OnboardingForm";
import ProfilePage from "./ProfilePage";
import SettingsPage from "./SettingsPage";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard({ user, setIsAuthenticated }) {
  const [currentView, setCurrentView] = useState("dashboard"); // dashboard, profile, settings
  const [activeTab, setActiveTab] = useState("chat");
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [checkingContext, setCheckingContext] = useState(true);
  const [userContext, setUserContext] = useState(null);

  // Check if user needs onboarding
  useEffect(() => {
    checkUserContext();
  }, []);

  const checkUserContext = async () => {
    try {
      const response = await fetch(`${API}/context`, {
        credentials: "include",
      });
      
      if (response.ok) {
        const context = await response.json();
        setUserContext(context);
        
        // Show onboarding if critical fields are missing
        const needsOnboarding = !context.portfolio_type || 
                                !context.risk_tolerance || 
                                (!context.monthly_investment && !context.annual_investment);
        
        setShowOnboarding(needsOnboarding);
      }
    } catch (error) {
      console.error("Error checking context:", error);
    } finally {
      setCheckingContext(false);
    }
  };

  const handleOnboardingComplete = async () => {
    setShowOnboarding(false);
    // Refresh context without re-checking if onboarding is needed
    try {
      const response = await fetch(`${API}/context`, {
        credentials: "include",
      });
      
      if (response.ok) {
        const context = await response.json();
        setUserContext(context);
      }
    } catch (error) {
      console.error("Error refreshing context:", error);
    }
    toast.success("Great! Now let's chat to refine your portfolio.");
  };

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

  // Show loading while checking context
  if (checkingContext) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-xl flex items-center justify-center animate-pulse">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <p className="text-gray-600">Loading your portfolio...</p>
        </div>
      </div>
    );
  }

  // Show onboarding if needed
  if (showOnboarding) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-white to-emerald-50">
        <OnboardingForm onComplete={handleOnboardingComplete} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50" data-testid="dashboard">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-xl flex items-center justify-center shadow-sm">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-gray-900">WealthMaker</span>
            </div>

            <div className="flex items-center gap-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="gap-2">
                    <Avatar className="w-8 h-8 border-2 border-cyan-500">
                      <AvatarImage src={user?.picture} alt={user?.name} />
                      <AvatarFallback className="bg-gradient-to-br from-cyan-500 to-emerald-500 text-white text-sm font-semibold">
                        {user?.name?.[0] || "U"}
                      </AvatarFallback>
                    </Avatar>
                    <div className="hidden sm:block text-left">
                      <p className="text-sm font-semibold text-gray-900">{user?.name}</p>
                      <p className="text-xs text-gray-500">{user?.email}</p>
                    </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => setCurrentView("dashboard")}>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Dashboard
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setCurrentView("profile")}>
                    <User className="mr-2 h-4 w-4" />
                    Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setCurrentView("settings")}>
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {currentView === "profile" && <ProfilePage />}
        {currentView === "settings" && <SettingsPage />}
        {currentView === "dashboard" && (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="bg-white border border-gray-200 w-full sm:w-auto grid grid-cols-3 mb-8 p-1 rounded-xl shadow-sm">
              <TabsTrigger
                value="chat"
                data-testid="tab-chat"
                className="rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-500 data-[state=active]:to-emerald-500 data-[state=active]:text-white data-[state=active]:shadow-md smooth-transition font-semibold text-gray-600"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Chat</span>
              </TabsTrigger>
              <TabsTrigger
                value="portfolio"
                data-testid="tab-portfolio"
                className="rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-500 data-[state=active]:to-emerald-500 data-[state=active]:text-white data-[state=active]:shadow-md smooth-transition font-semibold text-gray-600"
              >
                <PieChart className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Portfolio</span>
              </TabsTrigger>
              <TabsTrigger
                value="news"
                data-testid="tab-news"
                className="rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-500 data-[state=active]:to-emerald-500 data-[state=active]:text-white data-[state=active]:shadow-md smooth-transition font-semibold text-gray-600"
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
        )}
      </main>
    </div>
  );
}