import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { Loader2, Building2, User, DollarSign, Target, TrendingUp, Calendar, ArrowRight, ArrowLeft, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

export default function OnboardingForm({ onComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [totalSteps, setTotalSteps] = useState(5);
  const [formData, setFormData] = useState({
    portfolio_type: "",
    // Personal fields
    date_of_birth: "",
    annual_income: "",
    net_worth: "",
    home_ownership: "", // own, rent, other
    house_price: "",
    mortgage_amount: "",
    mortgage_monthly: "",
    // Institutional fields
    institution_name: "",
    institution_sector: "",
    annual_revenue: "",
    annual_profit: "",
    number_of_employees: "",
    // Common fields
    monthly_investment: "",
    risk_tolerance: "",
    roi_expectations: "",
    financial_goals: [],
  });

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.VITE_BACKEND_URL;
      
      // Parse financial goals
      const goalsText = formData.financial_goals.trim();
      let liquidity_requirements = [];
      if (goalsText) {
        const goalLines = goalsText.split('\n').filter(line => line.trim());
        liquidity_requirements = goalLines.map(goal => ({
          goal_id: `goal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          goal_name: goal.trim(),
          goal_type: "other",
          priority: "medium",
        }));
      }

      // Prepare context data based on portfolio type
      const contextData = {
        portfolio_type: formData.portfolio_type,
        risk_tolerance: formData.risk_tolerance,
        roi_expectations: formData.roi_expectations ? parseFloat(formData.roi_expectations) : null,
        monthly_investment: formData.monthly_investment ? parseFloat(formData.monthly_investment) : null,
        investment_mode: formData.monthly_investment ? "sip" : "adhoc",
        liquidity_requirements: formData.financial_goals.length > 0 ? formData.financial_goals : null,
      };

      // Add personal-specific fields
      if (formData.portfolio_type === "personal") {
        contextData.date_of_birth = formData.date_of_birth || null;
        contextData.annual_income = formData.annual_income ? parseFloat(formData.annual_income) : null;
        contextData.net_worth = formData.net_worth ? parseFloat(formData.net_worth) : null;
        contextData.home_ownership = formData.home_ownership || null;
        if (formData.home_ownership === "own") {
          contextData.house_price = formData.house_price ? parseFloat(formData.house_price) : null;
          contextData.mortgage_amount = formData.mortgage_amount ? parseFloat(formData.mortgage_amount) : null;
          contextData.mortgage_monthly = formData.mortgage_monthly ? parseFloat(formData.mortgage_monthly) : null;
        }
      }

      // Add institutional-specific fields
      if (formData.portfolio_type === "institutional") {
        contextData.institution_name = formData.institution_name || null;
        contextData.institution_sector = formData.institution_sector || null;
        contextData.annual_revenue = formData.annual_revenue ? parseFloat(formData.annual_revenue) : null;
        contextData.annual_profit = formData.annual_profit ? parseFloat(formData.annual_profit) : null;
        contextData.number_of_employees = formData.number_of_employees ? parseInt(formData.number_of_employees) : null;
      }

      // Remove null values
      Object.keys(contextData).forEach(key => {
        if (contextData[key] === null || contextData[key] === "") {
          delete contextData[key];
        }
      });

      const response = await fetch(`${backendUrl}/api/context`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(contextData),
      });

      if (!response.ok) throw new Error("Failed to save profile");

      toast.success("Profile saved! Let's refine your portfolio together.");
      onComplete();
    } catch (error) {
      console.error("Error saving profile:", error);
      toast.error("Failed to save profile. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 mb-4 shadow-lg">
          <User className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
          Welcome to WealthMaker
        </h3>
        <p className="text-gray-600">
          Let's create your personalized investment strategy
        </p>
      </div>

      <div className="space-y-4">
        <Label className="text-base font-semibold text-gray-700 mb-3 block">
          Who is this portfolio for?
        </Label>
        <RadioGroup
          value={formData.portfolio_type}
          onValueChange={(value) => handleInputChange("portfolio_type", value)}
          className="grid grid-cols-1 gap-4"
        >
          <div
            className={`relative p-6 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-lg ${
              formData.portfolio_type === "personal"
                ? "border-cyan-500 bg-cyan-50 shadow-md"
                : "border-gray-200 hover:border-cyan-300"
            }`}
          >
            <RadioGroupItem value="personal" id="personal" className="sr-only" />
            <Label htmlFor="personal" className="cursor-pointer flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${
                formData.portfolio_type === "personal" 
                  ? "bg-gradient-to-br from-cyan-500 to-emerald-500 text-white" 
                  : "bg-gray-100 text-gray-400"
              }`}>
                <User className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-gray-900 mb-1 text-lg">Personal Portfolio</div>
                <div className="text-sm text-gray-600">
                  Building wealth for yourself or your family's future
                </div>
              </div>
              {formData.portfolio_type === "personal" && (
                <CheckCircle2 className="w-6 h-6 text-cyan-600 absolute top-4 right-4" />
              )}
            </Label>
          </div>

          <div
            className={`relative p-6 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-lg ${
              formData.portfolio_type === "institutional"
                ? "border-cyan-500 bg-cyan-50 shadow-md"
                : "border-gray-200 hover:border-cyan-300"
            }`}
          >
            <RadioGroupItem value="institutional" id="institutional" className="sr-only" />
            <Label htmlFor="institutional" className="cursor-pointer flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${
                formData.portfolio_type === "institutional" 
                  ? "bg-gradient-to-br from-cyan-500 to-emerald-500 text-white" 
                  : "bg-gray-100 text-gray-400"
              }`}>
                <Building2 className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-gray-900 mb-1 text-lg">Institutional Portfolio</div>
                <div className="text-sm text-gray-600">
                  Managing investments for an organization or fund
                </div>
              </div>
              {formData.portfolio_type === "institutional" && (
                <CheckCircle2 className="w-6 h-6 text-cyan-600 absolute top-4 right-4" />
              )}
            </Label>
          </div>
        </RadioGroup>

        {formData.portfolio_type === "personal" && (
          <div className="mt-6 p-4 bg-gradient-to-r from-cyan-50 to-emerald-50 rounded-xl border border-cyan-200">
            <Label htmlFor="date_of_birth" className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-cyan-600" />
              Date of Birth
            </Label>
            <Input
              id="date_of_birth"
              type="date"
              value={formData.date_of_birth}
              onChange={(e) => handleInputChange("date_of_birth", e.target.value)}
              className="mt-2 border-cyan-200 focus:border-cyan-500 focus:ring-cyan-500"
            />
            <p className="text-xs text-gray-600 mt-2">This helps us understand your investment timeline</p>
          </div>
        )}
      </div>

      <Button
        onClick={() => {
          setStep(2);
          // Update total steps based on portfolio type
          setTotalSteps(5);
        }}
        disabled={!formData.portfolio_type}
        className="w-full h-12 text-base font-semibold bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-200"
      >
        Continue
        <ArrowRight className="w-5 h-5 ml-2" />
      </Button>
    </div>
  );

  // Step 2: Conditional rendering based on portfolio type
  const renderStep2 = () => {
    return formData.portfolio_type === "personal" ? renderPersonalStep2() : renderInstitutionalStep2();
  };

  // Step 2a: Personal Details (only for personal portfolios)
  const renderPersonalStep2 = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 mb-4 shadow-lg">
          <User className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
          Personal Information
        </h3>
        <p className="text-gray-600">
          Tell us about your financial situation
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="net_worth" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-600" />
            Approximate Net Worth
          </Label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-medium">$</span>
            <Input
              id="net_worth"
              type="number"
              placeholder="500,000"
              value={formData.net_worth}
              onChange={(e) => handleInputChange("net_worth", e.target.value)}
              className="pl-8 h-12 border-gray-300 focus:border-cyan-500 focus:ring-cyan-500"
            />
          </div>
          <p className="text-xs text-gray-500">Total assets minus debts</p>
        </div>

        <div>
          <Label className="text-sm font-semibold text-gray-700 mb-3 block">
            Home Ownership
          </Label>
          <RadioGroup
            value={formData.home_ownership}
            onValueChange={(value) => handleInputChange("home_ownership", value)}
            className="grid grid-cols-1 gap-3"
          >
            <div
              className={`relative p-4 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md ${
                formData.home_ownership === "own"
                  ? "border-cyan-500 bg-cyan-50"
                  : "border-gray-200 hover:border-cyan-300"
              }`}
            >
              <RadioGroupItem value="own" id="own" className="sr-only" />
              <Label htmlFor="own" className="cursor-pointer flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-2xl ${
                  formData.home_ownership === "own" ? "bg-cyan-100" : "bg-gray-100"
                }`}>
                  🏠
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">Own a Home</div>
                  <div className="text-sm text-gray-600">I own my primary residence</div>
                </div>
                {formData.home_ownership === "own" && (
                  <CheckCircle2 className="w-5 h-5 text-cyan-600" />
                )}
              </Label>
            </div>

            <div
              className={`relative p-4 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md ${
                formData.home_ownership === "rent"
                  ? "border-cyan-500 bg-cyan-50"
                  : "border-gray-200 hover:border-cyan-300"
              }`}
            >
              <RadioGroupItem value="rent" id="rent" className="sr-only" />
              <Label htmlFor="rent" className="cursor-pointer flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-2xl ${
                  formData.home_ownership === "rent" ? "bg-cyan-100" : "bg-gray-100"
                }`}>
                  🏢
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">Rent</div>
                  <div className="text-sm text-gray-600">I rent my primary residence</div>
                </div>
                {formData.home_ownership === "rent" && (
                  <CheckCircle2 className="w-5 h-5 text-cyan-600" />
                )}
              </Label>
            </div>

            <div
              className={`relative p-4 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md ${
                formData.home_ownership === "other"
                  ? "border-cyan-500 bg-cyan-50"
                  : "border-gray-200 hover:border-cyan-300"
              }`}
            >
              <RadioGroupItem value="other" id="other-home" className="sr-only" />
              <Label htmlFor="other-home" className="cursor-pointer flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-2xl ${
                  formData.home_ownership === "other" ? "bg-cyan-100" : "bg-gray-100"
                }`}>
                  🏘️
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">Other</div>
                  <div className="text-sm text-gray-600">Living with family or other arrangement</div>
                </div>
                {formData.home_ownership === "other" && (
                  <CheckCircle2 className="w-5 h-5 text-cyan-600" />
                )}
              </Label>
            </div>
          </RadioGroup>
        </div>

        {formData.home_ownership === "own" && (
          <div className="space-y-4 p-4 bg-gradient-to-r from-cyan-50 to-emerald-50 rounded-xl border border-cyan-200">
            <p className="text-sm font-semibold text-gray-700">Home Details</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="house_price" className="text-sm text-gray-700">
                  Estimated Home Value
                </Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <Input
                    id="house_price"
                    type="number"
                    placeholder="400,000"
                    value={formData.house_price}
                    onChange={(e) => handleInputChange("house_price", e.target.value)}
                    className="pl-8 h-10"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="mortgage_amount" className="text-sm text-gray-700">
                  Outstanding Mortgage
                </Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <Input
                    id="mortgage_amount"
                    type="number"
                    placeholder="300,000"
                    value={formData.mortgage_amount}
                    onChange={(e) => handleInputChange("mortgage_amount", e.target.value)}
                    className="pl-8 h-10"
                  />
                </div>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="mortgage_monthly" className="text-sm text-gray-700">
                  Monthly Mortgage Payment
                </Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <Input
                    id="mortgage_monthly"
                    type="number"
                    placeholder="2,500"
                    value={formData.mortgage_monthly}
                    onChange={(e) => handleInputChange("mortgage_monthly", e.target.value)}
                    className="pl-8 h-10"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <Button 
          onClick={() => setStep(1)} 
          variant="outline" 
          className="flex-1 h-12 border-2 hover:bg-gray-50"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        <Button 
          onClick={() => setStep(3)} 
          className="flex-1 h-12 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-200"
        >
          Continue
          <ArrowRight className="w-5 h-5 ml-2" />
        </Button>
      </div>
    </div>
  );

  // Step 2b: Institutional Details (only for institutional portfolios)
  const renderInstitutionalStep2 = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 mb-4 shadow-lg">
          <Building2 className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
          Organization Details
        </h3>
        <p className="text-gray-600">
          Tell us about your institution
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="institution_name" className="text-sm font-semibold text-gray-700">
            Institution Name
          </Label>
          <Input
            id="institution_name"
            type="text"
            placeholder="e.g., Acme Investment Fund"
            value={formData.institution_name}
            onChange={(e) => handleInputChange("institution_name", e.target.value)}
            className="h-12 border-gray-300 focus:border-cyan-500 focus:ring-cyan-500"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="institution_sector" className="text-sm font-semibold text-gray-700">
            Primary Sector/Industry
          </Label>
          <Input
            id="institution_sector"
            type="text"
            placeholder="e.g., Technology, Healthcare, Finance"
            value={formData.institution_sector}
            onChange={(e) => handleInputChange("institution_sector", e.target.value)}
            className="h-12 border-gray-300 focus:border-cyan-500 focus:ring-cyan-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="annual_revenue" className="text-sm font-semibold text-gray-700">
              Annual Revenue
            </Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-medium">$</span>
              <Input
                id="annual_revenue"
                type="number"
                placeholder="10,000,000"
                value={formData.annual_revenue}
                onChange={(e) => handleInputChange("annual_revenue", e.target.value)}
                className="pl-8 h-12 border-gray-300 focus:border-cyan-500 focus:ring-cyan-500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="annual_profit" className="text-sm font-semibold text-gray-700">
              Annual Profit
            </Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-medium">$</span>
              <Input
                id="annual_profit"
                type="number"
                placeholder="2,000,000"
                value={formData.annual_profit}
                onChange={(e) => handleInputChange("annual_profit", e.target.value)}
                className="pl-8 h-12 border-gray-300 focus:border-cyan-500 focus:ring-cyan-500"
              />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="number_of_employees" className="text-sm font-semibold text-gray-700">
            Number of Employees
          </Label>
          <Input
            id="number_of_employees"
            type="number"
            placeholder="e.g., 50"
            value={formData.number_of_employees}
            onChange={(e) => handleInputChange("number_of_employees", e.target.value)}
            className="h-12 border-gray-300 focus:border-cyan-500 focus:ring-cyan-500"
          />
        </div>
      </div>

      <div className="flex gap-3">
        <Button 
          onClick={() => setStep(1)} 
          variant="outline" 
          className="flex-1 h-12 border-2 hover:bg-gray-50"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        <Button 
          onClick={() => setStep(3)} 
          className="flex-1 h-12 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-200"
        >
          Continue
          <ArrowRight className="w-5 h-5 ml-2" />
        </Button>
      </div>
    </div>
  );

  // Step 3: Financial/Investment Details (common for both)
  const renderStep3 = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 mb-4 shadow-lg">
          <DollarSign className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
          Investment Capacity
        </h3>
        <p className="text-gray-600">
          How much are you planning to invest?
        </p>
      </div>

      <div className="space-y-6">
        {formData.portfolio_type === "personal" && (
          <div className="space-y-2">
            <Label htmlFor="annual_income" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-600" />
              Annual Income
            </Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-medium">$</span>
              <Input
                id="annual_income"
                type="number"
                placeholder="120,000"
                value={formData.annual_income}
                onChange={(e) => handleInputChange("annual_income", e.target.value)}
                className="pl-8 h-12 border-gray-300 focus:border-cyan-500 focus:ring-cyan-500"
              />
            </div>
            <p className="text-xs text-gray-500">Your approximate yearly income</p>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="monthly_investment" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-emerald-600" />
            Monthly Investment Amount
          </Label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-medium">$</span>
            <Input
              id="monthly_investment"
              type="number"
              placeholder="5,000"
              value={formData.monthly_investment}
              onChange={(e) => handleInputChange("monthly_investment", e.target.value)}
              className="pl-8 h-12 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
          </div>
          <p className="text-xs text-gray-500">How much you plan to invest each month</p>
        </div>
      </div>

      <div className="flex gap-3">
        <Button 
          onClick={() => setStep(2)} 
          variant="outline" 
          className="flex-1 h-12 border-2 hover:bg-gray-50"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        <Button 
          onClick={() => setStep(4)} 
          className="flex-1 h-12 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-200"
        >
          Continue
          <ArrowRight className="w-5 h-5 ml-2" />
        </Button>
      </div>
    </div>
  );

  // Step 4: Investment Preferences
  const renderStep4 = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 mb-4 shadow-lg">
          <Target className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
          Investment Preferences
        </h3>
        <p className="text-gray-600">
          Define your risk appetite and return expectations
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <Label className="text-base font-semibold text-gray-700 mb-4 block">
            Risk Tolerance
          </Label>
          <RadioGroup
            value={formData.risk_tolerance}
            onValueChange={(value) => handleInputChange("risk_tolerance", value)}
            className="grid grid-cols-1 gap-3"
          >
            <div
              className={`relative p-4 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md ${
                formData.risk_tolerance === "conservative"
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-blue-300"
              }`}
            >
              <RadioGroupItem value="conservative" id="conservative" className="sr-only" />
              <Label htmlFor="conservative" className="cursor-pointer flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-2xl ${
                  formData.risk_tolerance === "conservative" ? "bg-blue-100" : "bg-gray-100"
                }`}>
                  🛡️
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">Conservative</div>
                  <div className="text-sm text-gray-600">Prefer safety over high returns</div>
                </div>
                {formData.risk_tolerance === "conservative" && (
                  <CheckCircle2 className="w-5 h-5 text-blue-600" />
                )}
              </Label>
            </div>

            <div
              className={`relative p-4 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md ${
                formData.risk_tolerance === "moderate"
                  ? "border-cyan-500 bg-cyan-50"
                  : "border-gray-200 hover:border-cyan-300"
              }`}
            >
              <RadioGroupItem value="moderate" id="moderate" className="sr-only" />
              <Label htmlFor="moderate" className="cursor-pointer flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-2xl ${
                  formData.risk_tolerance === "moderate" ? "bg-cyan-100" : "bg-gray-100"
                }`}>
                  ⚖️
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">Moderate</div>
                  <div className="text-sm text-gray-600">Balanced approach to risk and returns</div>
                </div>
                {formData.risk_tolerance === "moderate" && (
                  <CheckCircle2 className="w-5 h-5 text-cyan-600" />
                )}
              </Label>
            </div>

            <div
              className={`relative p-4 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md ${
                formData.risk_tolerance === "aggressive"
                  ? "border-emerald-500 bg-emerald-50"
                  : "border-gray-200 hover:border-emerald-300"
              }`}
            >
              <RadioGroupItem value="aggressive" id="aggressive" className="sr-only" />
              <Label htmlFor="aggressive" className="cursor-pointer flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-2xl ${
                  formData.risk_tolerance === "aggressive" ? "bg-emerald-100" : "bg-gray-100"
                }`}>
                  🚀
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">Aggressive</div>
                  <div className="text-sm text-gray-600">Willing to take risks for higher returns</div>
                </div>
                {formData.risk_tolerance === "aggressive" && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                )}
              </Label>
            </div>
          </RadioGroup>
        </div>

        <div className="space-y-2">
          <Label htmlFor="roi_expectations" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            Target Annual Return
          </Label>
          <div className="relative">
            <Input
              id="roi_expectations"
              type="number"
              placeholder="12"
              value={formData.roi_expectations}
              onChange={(e) => handleInputChange("roi_expectations", e.target.value)}
              className="h-12 pr-12 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 font-medium">%</span>
          </div>
          <p className="text-xs text-gray-500">Expected annual return on your investment</p>
        </div>
      </div>

      <div className="flex gap-3">
        <Button 
          onClick={() => setStep(2)} 
          variant="outline" 
          className="flex-1 h-12 border-2 hover:bg-gray-50"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        <Button 
          onClick={() => setStep(4)} 
          className="flex-1 h-12 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-200"
        >
          Continue
          <ArrowRight className="w-5 h-5 ml-2" />
        </Button>
      </div>
    </div>
  );

  const renderStep5 = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 mb-4 shadow-lg">
          <Target className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
          Your Financial Goals
        </h3>
        <p className="text-gray-600">
          What are you investing for?
        </p>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-gradient-to-r from-cyan-50 to-emerald-50 rounded-xl border border-cyan-200">
          <Label htmlFor="financial_goals" className="text-sm font-semibold text-gray-700 mb-2 block">
            List Your Goals (One per line)
          </Label>
          <Textarea
            id="financial_goals"
            placeholder="Examples:
• Retirement at age 60
• Buy a house in 5 years
• Children's college education
• Build emergency fund
• Start a business"
            value={formData.financial_goals}
            onChange={(e) => handleInputChange("financial_goals", e.target.value)}
            className="mt-2 min-h-[180px] border-cyan-200 focus:border-cyan-500 focus:ring-cyan-500 resize-none"
          />
          <div className="mt-3 p-3 bg-white rounded-lg border border-cyan-200">
            <p className="text-xs text-gray-600 flex items-start gap-2">
              <span className="text-cyan-600 mt-0.5">💡</span>
              <span>Don't worry about details now. We'll refine each goal through our conversation.</span>
            </p>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <Button 
          onClick={() => setStep(3)} 
          variant="outline" 
          className="flex-1 h-12 border-2 hover:bg-gray-50"
          disabled={loading}
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="flex-1 h-12 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Setting up...
            </>
          ) : (
            <>
              Complete Setup
              <CheckCircle2 className="w-5 h-5 ml-2" />
            </>
          )}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-cyan-50 via-white to-emerald-50">
      <Card className="w-full max-w-3xl shadow-2xl border-0 overflow-hidden">
        <div className="h-2 bg-gradient-to-r from-cyan-500 via-emerald-500 to-cyan-500" />
        <CardHeader className="pb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <CardTitle className="text-3xl font-bold bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
                WealthMaker
              </CardTitle>
              <CardDescription className="text-base mt-1">
                Step {step} of 4
              </CardDescription>
            </div>
            <div className="px-4 py-2 bg-gradient-to-r from-cyan-100 to-emerald-100 rounded-full">
              <span className="text-sm font-semibold text-cyan-700">{Math.round((step / 4) * 100)}% Complete</span>
            </div>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`h-2 flex-1 rounded-full transition-all duration-500 ${
                  s < step 
                    ? "bg-gradient-to-r from-cyan-500 to-emerald-500" 
                    : s === step 
                    ? "bg-gradient-to-r from-cyan-400 to-emerald-400 animate-pulse" 
                    : "bg-gray-200"
                }`}
              />
            ))}
          </div>
        </CardHeader>
        <CardContent className="pb-8">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
          {step === 4 && renderStep4()}
          {step === 5 && renderStep5()}
        </CardContent>
      </Card>
    </div>
  );
}
