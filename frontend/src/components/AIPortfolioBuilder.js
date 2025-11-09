import { useState, useEffect } from "react";
import { X, ArrowRight, ArrowLeft, Sparkles, CheckCircle, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AIPortfolioBuilder({ isOpen, onClose, onSuccess }) {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [userContext, setUserContext] = useState(null);
  
  // Form data
  const [portfolioName, setPortfolioName] = useState("");
  const [portfolioGoal, setPortfolioGoal] = useState("");
  const [riskTolerance, setRiskTolerance] = useState("medium");
  const [investmentAmount, setInvestmentAmount] = useState("");
  const [timeHorizon, setTimeHorizon] = useState("5-10");
  const [roiExpectations, setRoiExpectations] = useState(10);
  const [sectorPreferences, setSectorPreferences] = useState({
    stocks: true,
    bonds: false,
    crypto: false,
    real_estate: false,
    commodities: false,
    forex: false,
  });
  const [investmentStrategies, setInvestmentStrategies] = useState([]);
  
  // AI suggestions
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSectorToggle = (sector) => {
    setSectorPreferences((prev) => ({
      ...prev,
      [sector]: !prev[sector],
    }));
  };

  const handleStrategyToggle = (strategyId) => {
    setInvestmentStrategies((prev) =>
      prev.includes(strategyId)
        ? prev.filter((s) => s !== strategyId)
        : [...prev, strategyId]
    );
  };

  const strategies = [
    {
      id: "value_investing",
      name: "Value Investing",
      description: "Buy undervalued stocks for long-term growth",
      details: "This strategy involves identifying stocks trading below their intrinsic value based on fundamental analysis of financial statements, P/E ratios, and book values. Popularized by Benjamin Graham and Warren Buffett, it requires patience and conviction to hold through market volatility until the market recognizes the stock's true value.",
      risk: "Low to Medium",
      riskFactors: "Market may take years to recognize value, value traps exist, requires deep analysis skills",
      roiExpectation: "8-15% annually",
      timeHorizon: "Long-term (3-10 years)",
      bestFor: "Patient investors with analytical skills"
    },
    {
      id: "growth_investing",
      name: "Growth Investing",
      description: "Invest in high-growth potential companies",
      details: "Focus on companies with above-average earnings growth, strong competitive advantages, and expanding market opportunities. These stocks often trade at premium valuations but offer significant upside potential. Think of tech companies, emerging market leaders, and innovative businesses disrupting traditional industries.",
      risk: "Medium to High",
      riskFactors: "Higher volatility, sensitivity to interest rates, growth may not materialize, premium valuations can deflate quickly",
      roiExpectation: "15-30% annually",
      timeHorizon: "Medium to Long-term (3-7 years)",
      bestFor: "Risk-tolerant investors seeking capital appreciation"
    },
    {
      id: "income_investing",
      name: "Income/Dividend Investing",
      description: "Focus on dividend-paying stocks and bonds",
      details: "Build a portfolio of established companies with consistent dividend payments and bonds providing regular interest income. This creates a steady cash flow stream that can be reinvested or used as passive income. Ideal for retirees or those seeking regular income alongside capital preservation.",
      risk: "Low to Medium",
      riskFactors: "Dividend cuts during downturns, interest rate sensitivity, lower growth potential, inflation can erode income value",
      roiExpectation: "5-10% annually + 2-6% dividend yield",
      timeHorizon: "Long-term (5+ years)",
      bestFor: "Conservative investors seeking regular income"
    },
    {
      id: "index_funds",
      name: "Index Fund Investing",
      description: "Passive investing through market index funds",
      details: "Gain broad market exposure by investing in funds that replicate major indices like S&P 500, NASDAQ, or total market indexes. This 'set it and forget it' approach offers instant diversification, low fees (typically 0.03-0.20%), and historically consistent returns. Recommended by experts like John Bogle and Warren Buffett for most investors.",
      risk: "Low to Medium",
      riskFactors: "Market risk affects entire portfolio, no downside protection, cannot outperform market, sector concentration in indices",
      roiExpectation: "8-12% annually (historical market average)",
      timeHorizon: "Long-term (5+ years)",
      bestFor: "Beginner to intermediate investors seeking simplicity"
    },
    {
      id: "dollar_cost_averaging",
      name: "Dollar-Cost Averaging (DCA)",
      description: "Invest fixed amounts regularly over time",
      details: "Commit to investing a fixed dollar amount at regular intervals (weekly, monthly, quarterly) regardless of market conditions. This eliminates the stress of market timing, reduces the impact of volatility by averaging purchase prices, and enforces disciplined saving. When prices are low, you buy more shares; when high, fewer shares.",
      risk: "Low",
      riskFactors: "May underperform lump sum investing in rising markets, requires discipline to maintain, doesn't prevent losses in bear markets",
      roiExpectation: "Matches underlying asset returns (typically 8-12% for stock indices)",
      timeHorizon: "Long-term (5+ years)",
      bestFor: "All investors, especially those with regular income to invest"
    },
    {
      id: "momentum_investing",
      name: "Momentum Investing",
      description: "Follow market trends and price momentum",
      details: "Capitalize on market trends by buying assets that have recently risen in price, expecting the momentum to continue. Uses technical indicators like moving averages, RSI, and MACD to identify entry and exit points. Popular in both bull markets and for swing trading. Requires active monitoring, quick decisions, and strict stop-loss discipline.",
      risk: "High",
      riskFactors: "Trend reversals can be sudden and severe, requires constant monitoring, higher transaction costs, emotional stress, whipsaws in volatile markets",
      roiExpectation: "20-50% annually (highly volatile, inconsistent)",
      timeHorizon: "Short to Medium-term (6 months - 3 years)",
      bestFor: "Experienced traders with time for active management and high risk tolerance"
    },
  ];

  useEffect(() => {
    if (isOpen) {
      loadUserContext();
    }
  }, [isOpen]);

  const loadUserContext = async () => {
    try {
      const response = await fetch(`${API}/context`, {
        credentials: "include",
      });
      if (response.ok) {
        const context = await response.json();
        setUserContext(context);
      }
    } catch (error) {
      console.error("Error loading context:", error);
    }
  };

  const handleGeneratePortfolio = async () => {
    setIsGenerating(true);

    try {
      // Prepare sector preferences
      const selectedSectors = Object.keys(sectorPreferences)
        .filter(key => sectorPreferences[key])
        .join(", ");

      // Send request to AI to generate portfolio suggestion
      const response = await fetch(`${API}/chat/generate-portfolio`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          portfolio_name: portfolioName,
          goal: portfolioGoal,
          risk_tolerance: riskTolerance,
          investment_amount: parseFloat(investmentAmount) || 0,
          time_horizon: timeHorizon,
          roi_expectations: roiExpectations,
          sector_preferences: selectedSectors,
          investment_strategies: investmentStrategies,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAiSuggestion(data.portfolio_suggestion);
        setStep(3); // Move to review step
      } else {
        toast.error("Failed to generate portfolio");
      }
    } catch (error) {
      console.error("Error generating portfolio:", error);
      toast.error("Failed to generate portfolio");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAcceptPortfolio = async () => {
    setIsLoading(true);

    try {
      // Prepare sector preferences
      const selectedSectors = Object.keys(sectorPreferences).reduce((acc, key) => {
        if (sectorPreferences[key]) {
          acc[key] = { allowed: true };
        }
        return acc;
      }, {});

      const response = await fetch(`${API}/portfolios-v2/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          name: portfolioName,
          goal: portfolioGoal,
          type: "ai",
          risk_tolerance: riskTolerance,
          roi_expectations: roiExpectations,
          sector_preferences: Object.keys(selectedSectors).length > 0 ? selectedSectors : null,
          investment_strategy: investmentStrategies.length > 0 ? investmentStrategies : null,
          allocations: aiSuggestion.allocations || [],
        }),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success("AI Portfolio created successfully!");
        onSuccess(data.portfolio);
        onClose();
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || "Failed to create portfolio");
      }
    } catch (error) {
      console.error("Error creating portfolio:", error);
      toast.error("Failed to create portfolio");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full my-8">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between bg-gradient-to-r from-purple-50 to-pink-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">AI Portfolio Builder</h2>
              <p className="text-sm text-gray-600">Step {step} of 3</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-gray-200">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300"
            style={{ width: `${(step / 3) * 100}%` }}
          ></div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Step 1: Portfolio Details */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Portfolio Details</h3>
                <p className="text-gray-600">Let's start with the basics</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Portfolio Name *
                </label>
                <Input
                  value={portfolioName}
                  onChange={(e) => setPortfolioName(e.target.value)}
                  placeholder="e.g., Retirement Fund, College Savings"
                  className="w-full"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  What's your goal for this portfolio? *
                </label>
                <Textarea
                  value={portfolioGoal}
                  onChange={(e) => setPortfolioGoal(e.target.value)}
                  placeholder="Describe what you want to achieve with this portfolio..."
                  className="w-full resize-none"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Risk Tolerance *
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {['low', 'medium', 'high'].map((risk) => (
                    <button
                      key={risk}
                      onClick={() => setRiskTolerance(risk)}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        riskTolerance === risk
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-purple-300'
                      }`}
                    >
                      <div className="font-semibold text-gray-900 capitalize">{risk}</div>
                      <div className="text-xs text-gray-600 mt-1">
                        {risk === 'low' && 'Preserve capital'}
                        {risk === 'medium' && 'Balanced growth'}
                        {risk === 'high' && 'Maximum returns'}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Investment Preferences */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Investment Preferences</h3>
                <p className="text-gray-600">Help our AI understand your investment strategy</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Initial Investment Amount ($)
                  </label>
                  <Input
                    type="number"
                    value={investmentAmount}
                    onChange={(e) => setInvestmentAmount(e.target.value)}
                    placeholder="Optional"
                    min="0"
                    step="100"
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">You can invest later too</p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Time Horizon (Years)
                  </label>
                  <select
                    value={timeHorizon}
                    onChange={(e) => setTimeHorizon(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="0-3">Short term (0-3 years)</option>
                    <option value="3-5">Medium term (3-5 years)</option>
                    <option value="5-10">Long term (5-10 years)</option>
                    <option value="10+">Very long term (10+ years)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Expected Annual ROI (%)
                </label>
                <Input
                  type="number"
                  value={roiExpectations}
                  onChange={(e) => setRoiExpectations(parseFloat(e.target.value))}
                  min="0"
                  max="100"
                  step="0.5"
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Investment Sectors (Optional)
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {[
                    { id: "stocks", label: "Stocks", emoji: "📈" },
                    { id: "bonds", label: "Bonds", emoji: "💰" },
                    { id: "crypto", label: "Crypto", emoji: "₿" },
                    { id: "real_estate", label: "Real Estate", emoji: "🏢" },
                    { id: "commodities", label: "Commodities", emoji: "🥇" },
                    { id: "forex", label: "Forex", emoji: "💱" },
                  ].map((sector) => (
                    <button
                      key={sector.id}
                      type="button"
                      onClick={() => handleSectorToggle(sector.id)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                        sectorPreferences[sector.id]
                          ? "bg-purple-100 text-purple-700 border-2 border-purple-500"
                          : "bg-gray-50 text-gray-600 border-2 border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      <span>{sector.emoji}</span>
                      <span>{sector.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Investment Strategies */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Investment Strategies (Optional)
                </label>
                <TooltipProvider>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {strategies.map((strategy) => (
                      <div
                        key={strategy.id}
                        onClick={() => handleStrategyToggle(strategy.id)}
                        className={`p-3 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md ${
                          investmentStrategies.includes(strategy.id)
                            ? "border-purple-500 bg-purple-50"
                            : "border-gray-200 hover:border-purple-300"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center mt-0.5 flex-shrink-0 ${
                            investmentStrategies.includes(strategy.id) ? "bg-purple-100" : "bg-gray-100"
                          }`}>
                            {investmentStrategies.includes(strategy.id) ? (
                              <div className="w-4 h-4 bg-purple-600 rounded-full"></div>
                            ) : (
                              <div className="w-4 h-4 border-2 border-gray-300 rounded-full"></div>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-gray-900 text-sm">{strategy.name}</div>
                            <div className="text-xs text-gray-600 mt-0.5">{strategy.description}</div>
                          </div>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => e.stopPropagation()}
                                className="p-1 hover:bg-gray-200 rounded-full transition-colors flex-shrink-0"
                              >
                                <HelpCircle className="w-4 h-4 text-gray-500" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-sm p-4 bg-gray-900 text-white">
                              <div className="space-y-2">
                                <p className="font-semibold text-sm">{strategy.name}</p>
                                <p className="text-xs text-gray-300">{strategy.details}</p>
                                <div className="pt-2 border-t border-gray-700 space-y-1">
                                  <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Risk Level:</span>
                                    <span className="font-medium">{strategy.risk}</span>
                                  </div>
                                  <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Expected ROI:</span>
                                    <span className="font-medium">{strategy.roiExpectation}</span>
                                  </div>
                                  <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Time Horizon:</span>
                                    <span className="font-medium">{strategy.timeHorizon}</span>
                                  </div>
                                </div>
                              </div>
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      </div>
                    ))}
                  </div>
                </TooltipProvider>
              </div>
            </div>
          )}

          {/* Step 3: AI Suggestion Review */}
          {step === 3 && (
            <div className="space-y-6">
              {isGenerating ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Generating Your Portfolio...</h3>
                  <p className="text-gray-600">Our AI is analyzing market data and creating a personalized portfolio for you</p>
                </div>
              ) : aiSuggestion ? (
                <>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">AI-Generated Portfolio</h3>
                    <p className="text-gray-600">Review the suggested allocation below</p>
                  </div>

                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border-2 border-purple-200">
                    <div className="flex items-center gap-2 mb-4">
                      <CheckCircle className="w-5 h-5 text-purple-600" />
                      <h4 className="font-bold text-gray-900">Recommended Allocation</h4>
                    </div>

                    {aiSuggestion.reasoning && (
                      <p className="text-sm text-gray-700 mb-4">
                        {aiSuggestion.reasoning}
                      </p>
                    )}

                    <div className="space-y-3">
                      {aiSuggestion.allocations?.map((alloc, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-white rounded-lg border border-purple-200">
                          <div>
                            <div className="font-bold text-gray-900">{alloc.ticker}</div>
                            <div className="text-xs text-gray-600">{alloc.sector}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-purple-600">{alloc.allocation_percentage}%</div>
                            <div className="text-xs text-gray-600">{alloc.asset_type}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-900">
                      💡 <strong>Tip:</strong> You can adjust allocations later by clicking on individual stocks in the portfolio view or chatting with our AI assistant.
                    </p>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-600">Something went wrong. Please try again.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 flex justify-between">
          <Button
            onClick={() => {
              if (step > 1) {
                setStep(step - 1);
              } else {
                onClose();
              }
            }}
            variant="outline"
            disabled={isGenerating || isLoading}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {step === 1 ? 'Cancel' : 'Back'}
          </Button>

          {step < 3 ? (
            <Button
              onClick={() => {
                if (step === 1) {
                  if (!portfolioName.trim() || !portfolioGoal.trim()) {
                    toast.error("Please fill in required fields");
                    return;
                  }
                  setStep(2);
                } else if (step === 2) {
                  handleGeneratePortfolio();
                }
              }}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
              disabled={isGenerating}
            >
              {step === 2 && isGenerating ? "Generating..." : "Next"}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={handleAcceptPortfolio}
              disabled={isLoading || !aiSuggestion}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
            >
              {isLoading ? "Creating..." : "Create Portfolio"}
              <CheckCircle className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
