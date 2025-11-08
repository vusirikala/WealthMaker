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
  const [formData, setFormData] = useState({
    portfolio_type: "",
    date_of_birth: "",
    annual_income: "",
    monthly_investment: "",
    risk_tolerance: "",
    roi_expectations: "",
    financial_goals: "",
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

      // Prepare context data
      const contextData = {
        portfolio_type: formData.portfolio_type,
        date_of_birth: formData.date_of_birth || null,
        annual_income: formData.annual_income ? parseFloat(formData.annual_income) : null,
        monthly_investment: formData.monthly_investment ? parseFloat(formData.monthly_investment) : null,
        risk_tolerance: formData.risk_tolerance,
        roi_expectations: formData.roi_expectations ? parseFloat(formData.roi_expectations) : null,
        liquidity_requirements: liquidity_requirements.length > 0 ? liquidity_requirements : null,
        investment_mode: formData.monthly_investment ? "sip" : "adhoc",
      };

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
        onClick={() => setStep(2)}
        disabled={!formData.portfolio_type}
        className="w-full h-12 text-base font-semibold bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-200"
      >
        Continue
        <ArrowRight className="w-5 h-5 ml-2" />
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 mb-4 shadow-lg">
          <DollarSign className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
          Financial Details
        </h3>
        <p className="text-gray-600">
          Help us understand your investment capacity
        </p>
      </div>

      <div className="space-y-6">
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

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Investment Preferences</h3>
        <p className="text-sm text-gray-600">
          Tell us about your risk appetite and return expectations.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <Label className="text-base mb-3 block">Risk Tolerance</Label>
          <RadioGroup
            value={formData.risk_tolerance}
            onValueChange={(value) => handleInputChange("risk_tolerance", value)}
          >
            <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <RadioGroupItem value="conservative" id="conservative" />
              <Label htmlFor="conservative" className="cursor-pointer flex-1">
                <div className="font-medium">Conservative</div>
                <div className="text-sm text-gray-500">Prefer safety over high returns</div>
              </Label>
            </div>
            <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <RadioGroupItem value="moderate" id="moderate" />
              <Label htmlFor="moderate" className="cursor-pointer flex-1">
                <div className="font-medium">Moderate</div>
                <div className="text-sm text-gray-500">Balanced approach to risk and returns</div>
              </Label>
            </div>
            <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <RadioGroupItem value="aggressive" id="aggressive" />
              <Label htmlFor="aggressive" className="cursor-pointer flex-1">
                <div className="font-medium">Aggressive</div>
                <div className="text-sm text-gray-500">Willing to take risks for higher returns</div>
              </Label>
            </div>
          </RadioGroup>
        </div>

        <div>
          <Label htmlFor="roi_expectations">Target Annual Return (%)</Label>
          <Input
            id="roi_expectations"
            type="number"
            placeholder="e.g., 12"
            value={formData.roi_expectations}
            onChange={(e) => handleInputChange("roi_expectations", e.target.value)}
            className="mt-2"
          />
        </div>
      </div>

      <div className="flex gap-3">
        <Button onClick={() => setStep(2)} variant="outline" className="flex-1">
          Back
        </Button>
        <Button onClick={() => setStep(4)} className="flex-1">
          Continue
        </Button>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Your Financial Goals</h3>
        <p className="text-sm text-gray-600">
          What are you investing for? (One goal per line)
        </p>
      </div>

      <div>
        <Label htmlFor="financial_goals">Goals</Label>
        <Textarea
          id="financial_goals"
          placeholder="Example:
Retirement
Buy a house
Children's education
Emergency fund"
          value={formData.financial_goals}
          onChange={(e) => handleInputChange("financial_goals", e.target.value)}
          className="mt-2 min-h-[150px]"
        />
        <p className="text-xs text-gray-500 mt-1">
          Don't worry, we'll gather more details about each goal in our conversation.
        </p>
      </div>

      <div className="flex gap-3">
        <Button onClick={() => setStep(3)} variant="outline" className="flex-1">
          Back
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="flex-1"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            "Complete Setup"
          )}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-[600px] flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-2xl">Welcome to WealthMaker</CardTitle>
          <CardDescription>
            Step {step} of 4 - Quick setup to get started
          </CardDescription>
          <div className="flex gap-2 mt-4">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`h-2 flex-1 rounded-full ${
                  s <= step ? "bg-cyan-500" : "bg-gray-200"
                }`}
              />
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
          {step === 4 && renderStep4()}
        </CardContent>
      </Card>
    </div>
  );
}
