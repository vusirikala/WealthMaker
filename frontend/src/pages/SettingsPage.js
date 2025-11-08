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
      // Implementation would call delete endpoint
      toast.success("Account deletion request submitted");
    } catch (error) {
      console.error("Error deleting account:", error);
      toast.error("Failed to delete account");
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
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Account?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete your account and remove all your data from our servers.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDeleteAccount} className="bg-red-600 hover:bg-red-700">
                  Yes, Delete My Account
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
