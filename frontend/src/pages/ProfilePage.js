import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Loader2, Save, User, DollarSign, Target, Calendar } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.VITE_BACKEND_URL;

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({});
  const [editedProfile, setEditedProfile] = useState({});

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/context`, {
        credentials: "include",
      });
      
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setEditedProfile(data);
      }
    } catch (error) {
      console.error("Error fetching profile:", error);
      toast.error("Failed to load profile");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/context`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(editedProfile),
      });

      if (!response.ok) throw new Error("Failed to save profile");

      setProfile(editedProfile);
      toast.success("Profile updated successfully!");
    } catch (error) {
      console.error("Error saving profile:", error);
      toast.error("Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    setEditedProfile((prev) => ({ ...prev, [field]: value }));
  };

  const calculateAge = (dob) => {
    if (!dob) return "N/A";
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  const isPersonal = editedProfile.portfolio_type === "personal";

  return (
    <div className="max-w-5xl mx-auto space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
          <p className="text-gray-600 mt-1">Manage your personal and financial information</p>
        </div>
        <Button onClick={handleSave} disabled={saving} className="bg-gradient-to-r from-cyan-500 to-emerald-500">
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="w-5 h-5 text-cyan-500" />
            <CardTitle>Basic Information</CardTitle>
          </div>
          <CardDescription>Your personal details and portfolio type</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Portfolio Type</Label>
            <RadioGroup
              value={editedProfile.portfolio_type || ""}
              onValueChange={(value) => handleChange("portfolio_type", value)}
              className="mt-2"
            >
              <div className="flex items-center space-x-2 p-3 border rounded-lg">
                <RadioGroupItem value="personal" id="profile-personal" />
                <Label htmlFor="profile-personal">Personal</Label>
              </div>
              <div className="flex items-center space-x-2 p-3 border rounded-lg">
                <RadioGroupItem value="institutional" id="profile-institutional" />
                <Label htmlFor="profile-institutional">Institutional</Label>
              </div>
            </RadioGroup>
          </div>

          {isPersonal ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="date_of_birth">Date of Birth</Label>
                  <Input
                    id="date_of_birth"
                    type="date"
                    value={editedProfile.date_of_birth?.split('T')[0] || ""}
                    onChange={(e) => handleChange("date_of_birth", e.target.value)}
                    className="mt-2"
                  />
                  {editedProfile.date_of_birth && (
                    <p className="text-sm text-gray-500 mt-1">
                      Current Age: {calculateAge(editedProfile.date_of_birth)} years
                    </p>
                  )}
                </div>
                <div>
                  <Label htmlFor="retirement_age">Target Retirement Age</Label>
                  <Input
                    id="retirement_age"
                    type="number"
                    value={editedProfile.retirement_age || ""}
                    onChange={(e) => handleChange("retirement_age", parseInt(e.target.value))}
                    className="mt-2"
                    placeholder="e.g., 65"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="retirement_plans">Retirement Plans</Label>
                <Textarea
                  id="retirement_plans"
                  value={editedProfile.retirement_plans || ""}
                  onChange={(e) => handleChange("retirement_plans", e.target.value)}
                  className="mt-2"
                  placeholder="Describe your retirement goals and plans..."
                  rows={3}
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <Label htmlFor="institution_name">Institution Name</Label>
                <Input
                  id="institution_name"
                  value={editedProfile.institution_name || ""}
                  onChange={(e) => handleChange("institution_name", e.target.value)}
                  className="mt-2"
                  placeholder="e.g., ABC Investment Fund"
                />
              </div>
              <div>
                <Label htmlFor="institution_sector">Sector</Label>
                <Input
                  id="institution_sector"
                  value={editedProfile.institution_sector || ""}
                  onChange={(e) => handleChange("institution_sector", e.target.value)}
                  className="mt-2"
                  placeholder="e.g., Technology, Healthcare"
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Financial Information */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-500" />
            <CardTitle>Financial Information</CardTitle>
          </div>
          <CardDescription>Your income, investments, and net worth</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="annual_income">Annual Income ($)</Label>
              <Input
                id="annual_income"
                type="number"
                value={editedProfile.annual_income || ""}
                onChange={(e) => handleChange("annual_income", parseFloat(e.target.value))}
                className="mt-2"
                placeholder="e.g., 120000"
              />
            </div>
            <div>
              <Label htmlFor="net_worth">Net Worth ($)</Label>
              <Input
                id="net_worth"
                type="number"
                value={editedProfile.net_worth || ""}
                onChange={(e) => handleChange("net_worth", parseFloat(e.target.value))}
                className="mt-2"
                placeholder="e.g., 500000"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="monthly_investment">Monthly Investment ($)</Label>
              <Input
                id="monthly_investment"
                type="number"
                value={editedProfile.monthly_investment || ""}
                onChange={(e) => handleChange("monthly_investment", parseFloat(e.target.value))}
                className="mt-2"
                placeholder="e.g., 5000"
              />
            </div>
            <div>
              <Label htmlFor="annual_investment">Annual Investment ($)</Label>
              <Input
                id="annual_investment"
                type="number"
                value={editedProfile.annual_investment || ""}
                onChange={(e) => handleChange("annual_investment", parseFloat(e.target.value))}
                className="mt-2"
                placeholder="e.g., 60000"
              />
            </div>
          </div>

          <div>
            <Label>Investment Mode</Label>
            <RadioGroup
              value={editedProfile.investment_mode || ""}
              onValueChange={(value) => handleChange("investment_mode", value)}
              className="mt-2"
            >
              <div className="flex flex-wrap gap-3">
                <div className="flex items-center space-x-2 p-3 border rounded-lg">
                  <RadioGroupItem value="sip" id="mode-sip" />
                  <Label htmlFor="mode-sip">SIP (Monthly)</Label>
                </div>
                <div className="flex items-center space-x-2 p-3 border rounded-lg">
                  <RadioGroupItem value="adhoc" id="mode-adhoc" />
                  <Label htmlFor="mode-adhoc">Ad-hoc (Lump Sum)</Label>
                </div>
                <div className="flex items-center space-x-2 p-3 border rounded-lg">
                  <RadioGroupItem value="both" id="mode-both" />
                  <Label htmlFor="mode-both">Both</Label>
                </div>
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>

      {/* Investment Preferences */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-500" />
            <CardTitle>Investment Preferences</CardTitle>
          </div>
          <CardDescription>Your risk tolerance and investment strategy</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Risk Tolerance</Label>
            <RadioGroup
              value={editedProfile.risk_tolerance || ""}
              onValueChange={(value) => handleChange("risk_tolerance", value)}
              className="mt-2"
            >
              <div className="flex items-center space-x-2 p-3 border rounded-lg">
                <RadioGroupItem value="conservative" id="risk-conservative" />
                <Label htmlFor="risk-conservative">
                  <div className="font-medium">Conservative</div>
                  <div className="text-sm text-gray-500">Prefer safety over high returns</div>
                </Label>
              </div>
              <div className="flex items-center space-x-2 p-3 border rounded-lg">
                <RadioGroupItem value="moderate" id="risk-moderate" />
                <Label htmlFor="risk-moderate">
                  <div className="font-medium">Moderate</div>
                  <div className="text-sm text-gray-500">Balanced approach</div>
                </Label>
              </div>
              <div className="flex items-center space-x-2 p-3 border rounded-lg">
                <RadioGroupItem value="aggressive" id="risk-aggressive" />
                <Label htmlFor="risk-aggressive">
                  <div className="font-medium">Aggressive</div>
                  <div className="text-sm text-gray-500">Willing to take risks</div>
                </Label>
              </div>
              <div className="flex items-center space-x-2 p-3 border rounded-lg">
                <RadioGroupItem value="very_aggressive" id="risk-very-aggressive" />
                <Label htmlFor="risk-very-aggressive">
                  <div className="font-medium">Very Aggressive</div>
                  <div className="text-sm text-gray-500">Maximum risk for maximum returns</div>
                </Label>
              </div>
            </RadioGroup>
          </div>

          <div>
            <Label htmlFor="risk_details">Risk Tolerance Details</Label>
            <Textarea
              id="risk_details"
              value={editedProfile.risk_details || ""}
              onChange={(e) => handleChange("risk_details", e.target.value)}
              className="mt-2"
              placeholder="Describe your comfort level with market fluctuations..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="roi_expectations">Target Annual Return (%)</Label>
              <Input
                id="roi_expectations"
                type="number"
                step="0.1"
                value={editedProfile.roi_expectations || ""}
                onChange={(e) => handleChange("roi_expectations", parseFloat(e.target.value))}
                className="mt-2"
                placeholder="e.g., 12.5"
              />
            </div>
            <div>
              <Label htmlFor="investment_style">Investment Style</Label>
              <RadioGroup
                value={editedProfile.investment_style || ""}
                onValueChange={(value) => handleChange("investment_style", value)}
                className="mt-2"
              >
                <div className="flex flex-wrap gap-3">
                  <div className="flex items-center space-x-2 p-2 border rounded-lg">
                    <RadioGroupItem value="active" id="style-active" />
                    <Label htmlFor="style-active" className="text-sm">Active</Label>
                  </div>
                  <div className="flex items-center space-x-2 p-2 border rounded-lg">
                    <RadioGroupItem value="passive" id="style-passive" />
                    <Label htmlFor="style-passive" className="text-sm">Passive</Label>
                  </div>
                  <div className="flex items-center space-x-2 p-2 border rounded-lg">
                    <RadioGroupItem value="hybrid" id="style-hybrid" />
                    <Label htmlFor="style-hybrid" className="text-sm">Hybrid</Label>
                  </div>
                </div>
              </RadioGroup>
            </div>
          </div>

          <div>
            <Label htmlFor="diversification_preference">Diversification Preference</Label>
            <RadioGroup
              value={editedProfile.diversification_preference || ""}
              onValueChange={(value) => handleChange("diversification_preference", value)}
              className="mt-2"
            >
              <div className="flex flex-wrap gap-3">
                <div className="flex items-center space-x-2 p-2 border rounded-lg">
                  <RadioGroupItem value="highly_diversified" id="div-high" />
                  <Label htmlFor="div-high" className="text-sm">Highly Diversified</Label>
                </div>
                <div className="flex items-center space-x-2 p-2 border rounded-lg">
                  <RadioGroupItem value="moderately_diversified" id="div-moderate" />
                  <Label htmlFor="div-moderate" className="text-sm">Moderately Diversified</Label>
                </div>
                <div className="flex items-center space-x-2 p-2 border rounded-lg">
                  <RadioGroupItem value="concentrated" id="div-concentrated" />
                  <Label htmlFor="div-concentrated" className="text-sm">Concentrated</Label>
                </div>
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
