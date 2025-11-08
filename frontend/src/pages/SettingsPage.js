import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Bell, Shield, Trash2, Download, Upload } from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.VITE_BACKEND_URL;

export default function SettingsPage() {
  const [notificationSettings, setNotificationSettings] = useState({
    portfolioUpdates: true,
    marketAlerts: true,
    newsDigest: false,
    goalReminders: true,
  });

  const handleNotificationChange = (key) => {
    setNotificationSettings((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
    toast.success("Notification settings updated");
  };

  const handleExportData = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/context`, {
        credentials: "include",
      });
      
      if (response.ok) {
        const data = await response.json();
        const dataStr = JSON.stringify(data, null, 2);
        const dataBlob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `wealthmaker-profile-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
        toast.success("Profile data exported successfully");
      }
    } catch (error) {
      console.error("Error exporting data:", error);
      toast.error("Failed to export data");
    }
  };

  const handleDeleteAccount = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/account`, {
        method: "DELETE",
        credentials: "include",
      });
      
      if (response.ok) {
        toast.success("Account deleted successfully");
        // Redirect to landing page after short delay
        setTimeout(() => {
          window.location.href = "/";
        }, 1500);
      } else {
        throw new Error("Failed to delete account");
      }
    } catch (error) {
      console.error("Error deleting account:", error);
      toast.error("Failed to delete account. Please try again.");
    }
  };

  const handleClearPortfolio = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/portfolios`, {
        method: "DELETE",
        credentials: "include",
      });
      
      if (response.ok) {
        toast.success("Portfolio data cleared");
      }
    } catch (error) {
      console.error("Error clearing portfolio:", error);
      toast.error("Failed to clear portfolio");
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account preferences and privacy</p>
      </div>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-cyan-500" />
            <CardTitle>Notifications</CardTitle>
          </div>
          <CardDescription>Choose what updates you want to receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="portfolio-updates" className="font-medium">Portfolio Updates</Label>
              <p className="text-sm text-gray-500">Get notified about portfolio changes</p>
            </div>
            <Switch
              id="portfolio-updates"
              checked={notificationSettings.portfolioUpdates}
              onCheckedChange={() => handleNotificationChange("portfolioUpdates")}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="market-alerts" className="font-medium">Market Alerts</Label>
              <p className="text-sm text-gray-500">Alerts for significant market movements</p>
            </div>
            <Switch
              id="market-alerts"
              checked={notificationSettings.marketAlerts}
              onCheckedChange={() => handleNotificationChange("marketAlerts")}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="news-digest" className="font-medium">Daily News Digest</Label>
              <p className="text-sm text-gray-500">Daily summary of relevant news</p>
            </div>
            <Switch
              id="news-digest"
              checked={notificationSettings.newsDigest}
              onCheckedChange={() => handleNotificationChange("newsDigest")}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="goal-reminders" className="font-medium">Goal Reminders</Label>
              <p className="text-sm text-gray-500">Reminders about your financial goals</p>
            </div>
            <Switch
              id="goal-reminders"
              checked={notificationSettings.goalReminders}
              onCheckedChange={() => handleNotificationChange("goalReminders")}
            />
          </div>
        </CardContent>
      </Card>

      {/* Privacy & Data */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-500" />
            <CardTitle>Privacy & Data</CardTitle>
          </div>
          <CardDescription>Manage your data and privacy settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            onClick={handleExportData}
            variant="outline"
            className="w-full justify-start"
          >
            <Download className="w-4 h-4 mr-2" />
            Export My Data
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" className="w-full justify-start text-orange-600 hover:text-orange-700">
                <Trash2 className="w-4 h-4 mr-2" />
                Clear Portfolio Data
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clear Portfolio Data?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will remove all your portfolio allocations and suggestions. Your profile information will be preserved. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleClearPortfolio} className="bg-orange-600 hover:bg-orange-700">
                  Clear Portfolio
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-red-200">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-red-500" />
            <CardTitle className="text-red-600">Danger Zone</CardTitle>
          </div>
          <CardDescription>Irreversible actions</CardDescription>
        </CardHeader>
        <CardContent>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" className="w-full">
                Delete Account
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="max-w-md">
              <AlertDialogHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                    <Trash2 className="w-6 h-6 text-red-600" />
                  </div>
                  <AlertDialogTitle className="text-xl">Delete Account?</AlertDialogTitle>
                </div>
                <AlertDialogDescription className="space-y-4 pt-2">
                  <p className="text-base font-semibold text-red-600">
                    ⚠️ This action is irreversible and cannot be undone.
                  </p>
                  <p className="text-sm text-gray-700">
                    Deleting your account will permanently remove:
                  </p>
                  <ul className="text-sm text-gray-600 space-y-2 pl-5">
                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">•</span>
                      <span>Your profile and personal information</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">•</span>
                      <span>All portfolio data and recommendations</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">•</span>
                      <span>Chat history and financial goals</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">•</span>
                      <span>All saved preferences and settings</span>
                    </li>
                  </ul>
                  <p className="text-sm text-gray-700 font-medium pt-2">
                    Are you absolutely sure you want to proceed?
                  </p>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter className="gap-2 sm:gap-2">
                <AlertDialogCancel className="flex-1">Cancel</AlertDialogCancel>
                <AlertDialogAction 
                  onClick={handleDeleteAccount} 
                  className="flex-1 bg-red-600 hover:bg-red-700 focus:ring-red-600"
                >
                  Yes, Delete Everything
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>

      {/* App Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">App Information</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-gray-600 space-y-1">
          <p>WealthMaker Version 1.0.0</p>
          <p>© 2025 WealthMaker. All rights reserved.</p>
          <div className="flex gap-4 mt-3">
            <a href="#" className="text-cyan-600 hover:underline">Terms of Service</a>
            <a href="#" className="text-cyan-600 hover:underline">Privacy Policy</a>
            <a href="#" className="text-cyan-600 hover:underline">Help Center</a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
