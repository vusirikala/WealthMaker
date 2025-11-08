import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function OnboardingForm({ onComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    portfolio_type: "",
    age: "",
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
        age: formData.age ? parseInt(formData.age) : null,
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
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Let's Get Started</h3>
        <p className="text-sm text-gray-600 mb-6">
          Tell us a bit about yourself so we can create a personalized investment strategy.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <Label className="text-base mb-3 block">Who is this portfolio for?</Label>
          <RadioGroup
            value={formData.portfolio_type}
            onValueChange={(value) => handleInputChange("portfolio_type", value)}
          >
            <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <RadioGroupItem value="personal" id="personal" />
              <Label htmlFor="personal" className="cursor-pointer flex-1">
                <div className="font-medium">Personal</div>
                <div className="text-sm text-gray-500">Building wealth for myself or family</div>
              </Label>
            </div>
            <div className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <RadioGroupItem value="institutional" id="institutional" />
              <Label htmlFor="institutional" className="cursor-pointer flex-1">
                <div className="font-medium">Institutional</div>
                <div className="text-sm text-gray-500">Managing funds for an organization</div>
              </Label>
            </div>
          </RadioGroup>
        </div>

        {formData.portfolio_type === "personal" && (
          <div>
            <Label htmlFor="age">Your Age</Label>
            <Input
              id="age"
              type="number"
              placeholder="e.g., 35"
              value={formData.age}
              onChange={(e) => handleInputChange("age", e.target.value)}
              className="mt-2"
            />
          </div>
        )}
      </div>

      <Button
        onClick={() => setStep(2)}
        disabled={!formData.portfolio_type}
        className="w-full"
      >
        Continue
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Financial Details</h3>
        <p className="text-sm text-gray-600">
          This helps us understand your investment capacity.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="annual_income">Annual Income ($)</Label>
          <Input
            id="annual_income"
            type="number"
            placeholder="e.g., 120000"
            value={formData.annual_income}
            onChange={(e) => handleInputChange("annual_income", e.target.value)}
            className="mt-2"
          />
        </div>

        <div>
          <Label htmlFor="monthly_investment">Monthly Investment Amount ($)</Label>
          <Input
            id="monthly_investment"
            type="number"
            placeholder="e.g., 5000"
            value={formData.monthly_investment}
            onChange={(e) => handleInputChange("monthly_investment", e.target.value)}
            className="mt-2"
          />
          <p className="text-xs text-gray-500 mt-1">How much can you invest each month?</p>
        </div>
      </div>

      <div className="flex gap-3">
        <Button onClick={() => setStep(1)} variant="outline" className="flex-1">
          Back
        </Button>
        <Button onClick={() => setStep(3)} className="flex-1">
          Continue
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
