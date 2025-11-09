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
  const [monitoringFrequency, setMonitoringFrequency] = useState("monthly");
  const [sectorPreferences, setSectorPreferences] = useState({
    stocks: { enabled: true, allocation: 50 },
    bonds: { enabled: false, allocation: 30 },
    crypto: { enabled: false, allocation: 5 },
    real_estate: { enabled: false, allocation: 10 },
    commodities: { enabled: false, allocation: 5 },
    forex: { enabled: false, allocation: 0 },
  });
  const [investmentStrategies, setInvestmentStrategies] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  
  // AI suggestions
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSectorToggle = (sector) => {
    setSectorPreferences((prev) => ({
      ...prev,
      [sector]: { ...prev[sector], enabled: !prev[sector].enabled },
    }));
  };

  const handleSectorAllocationChange = (sector, value) => {
    const numValue = parseFloat(value) || 0;
    setSectorPreferences((prev) => ({
      ...prev,
      [sector]: { ...prev[sector], allocation: Math.min(100, Math.max(0, numValue)) },
    }));
  };

  const handleStrategyToggle = (strategyId) => {
    setInvestmentStrategies((prev) =>
      prev.includes(strategyId)
        ? prev.filter((s) => s !== strategyId)
        : [...prev, strategyId]
    );
  };

  const fetchRecommendations = async () => {
    if (!portfolioGoal || !riskTolerance) {
      toast.error("Please fill in portfolio goal and risk tolerance first");
      return;
    }

    setLoadingRecommendations(true);
    try {
      const response = await fetch(`${API}/chat/portfolio-recommendations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          goal: portfolioGoal,
          risk_tolerance: riskTolerance,
          roi_expectations: roiExpectations,
          time_horizon: timeHorizon,
          investment_amount: parseFloat(investmentAmount) || 0,
          monitoring_frequency: monitoringFrequency,
        }),
      });

      const data = await response.json();
      
      if (data.success && data.recommendations) {
        setRecommendations(data.recommendations);
        
        // Apply recommended sector allocations
        const newSectorPrefs = { ...sectorPreferences };
        Object.keys(data.recommendations.sector_allocation).forEach((sector) => {
          if (newSectorPrefs[sector]) {
            newSectorPrefs[sector] = {
              enabled: data.recommendations.sector_allocation[sector] > 0,
              allocation: data.recommendations.sector_allocation[sector],
            };
          }
        });
        setSectorPreferences(newSectorPrefs);
        
        // Apply recommended strategies
        setInvestmentStrategies(data.recommendations.recommended_strategies || []);
        
        toast.success("AI recommendations applied! You can adjust them as needed.");
      }
    } catch (error) {
      console.error("Error fetching recommendations:", error);
      toast.error("Failed to fetch recommendations");
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const sectorInfo = [
    {
      id: "stocks",
      label: "Stocks & Equities",
      emoji: "📈",
      description: "Ownership shares in publicly traded companies",
      details: "Stocks represent ownership stakes in companies, offering growth potential through capital appreciation and dividend income. Historically, stocks have provided the highest long-term returns among major asset classes, averaging 10% annually over the past century. However, they also experience significant short-term volatility.",
      risk: "Medium to High",
      riskFactors: "Market volatility, company-specific risks, economic downturns can cause 30-50% losses, requires diversification",
      roiExpectation: "8-12% annually (long-term average)",
      volatility: "High (can swing 20-40% annually)",
      bestFor: "Long-term investors with 5+ year horizons"
    },
    {
      id: "bonds",
      label: "Bonds & Fixed Income",
      emoji: "💰",
      description: "Debt securities with regular interest payments",
      details: "Bonds are loans to governments or corporations that pay fixed interest (coupon) at regular intervals. They provide predictable income and are less volatile than stocks. Bond prices move inversely with interest rates - when rates rise, bond values fall. Government bonds are safer, corporate bonds offer higher yields but more risk.",
      risk: "Low to Medium",
      riskFactors: "Interest rate risk, inflation can erode returns, credit default risk for corporate bonds, limited growth potential",
      roiExpectation: "3-6% annually",
      volatility: "Low to Medium (5-15% annual swings)",
      bestFor: "Conservative investors, income seekers, portfolio stability"
    },
    {
      id: "crypto",
      label: "Cryptocurrency",
      emoji: "₿",
      description: "Digital assets and blockchain-based currencies",
      details: "Cryptocurrencies like Bitcoin and Ethereum are decentralized digital currencies operating on blockchain technology. They offer potential for massive gains but with extreme volatility. Not backed by governments or physical assets, value is driven by adoption, technology developments, and speculation. Still a relatively new and evolving asset class.",
      risk: "Very High",
      riskFactors: "Extreme volatility (50%+ swings common), regulatory uncertainty, security risks, potential for total loss, liquidity issues",
      roiExpectation: "Highly variable (-50% to +300% annually)",
      volatility: "Extreme (50-100%+ annual swings)",
      bestFor: "Risk-tolerant investors, small portfolio allocation (5-10% max)"
    },
    {
      id: "real_estate",
      label: "Real Estate & REITs",
      emoji: "🏢",
      description: "Property investments and Real Estate Investment Trusts",
      details: "Real estate includes physical properties or REITs (Real Estate Investment Trusts) that own income-generating properties like apartments, offices, or shopping centers. Provides diversification, inflation protection, and regular income through rent. REITs offer liquidity and lower capital requirements than direct property ownership.",
      risk: "Medium",
      riskFactors: "Interest rate sensitivity, market cycles, property-specific risks, liquidity constraints for direct ownership, management complexity",
      roiExpectation: "6-10% annually (appreciation + income)",
      volatility: "Medium (10-25% annual swings for REITs)",
      bestFor: "Diversification seekers, income investors, inflation hedgers"
    },
    {
      id: "commodities",
      label: "Commodities & Precious Metals",
      emoji: "🥇",
      description: "Physical goods like gold, oil, and agricultural products",
      details: "Commodities include precious metals (gold, silver), energy (oil, natural gas), and agricultural products (wheat, corn). Gold is traditionally viewed as a 'safe haven' during economic uncertainty and inflation hedge. Commodities have low correlation with stocks and bonds, providing portfolio diversification. Can be accessed through ETFs, futures, or physical ownership.",
      risk: "Medium to High",
      riskFactors: "Price volatility driven by supply/demand, geopolitical events, no inherent income generation, storage costs for physical assets",
      roiExpectation: "3-8% annually (varies widely by commodity)",
      volatility: "High (20-40% annual swings)",
      bestFor: "Portfolio diversification, inflation protection, experienced investors"
    },
    {
      id: "forex",
      label: "Foreign Exchange (Forex)",
      emoji: "💱",
      description: "Currency trading and exchange rate speculation",
      details: "Forex involves trading currencies against each other (e.g., USD/EUR). It's the world's largest financial market with 24/7 trading. Typically uses high leverage (10:1 to 100:1), magnifying both gains and losses. Requires understanding of macroeconomics, central bank policies, and geopolitical events. Not recommended for most retail investors due to complexity and risk.",
      risk: "Very High",
      riskFactors: "Extreme leverage amplifies losses, requires constant monitoring, complex market dynamics, high transaction costs, 90%+ of retail traders lose money",
      roiExpectation: "Highly variable (most lose money)",
      volatility: "Very High with leverage",
      bestFor: "Professional traders only, not recommended for most investors"
    }
  ];

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

  const riskToleranceOptions = [
    {
      value: "low",
      label: "Low Risk",
      emoji: "🛡️",
      description: "Preserve capital with minimal volatility",
      details: "Focus on capital preservation over growth. Suitable for those nearing retirement or with short investment horizons. Typically involves bonds, dividend stocks, and stable value funds.",
      roiExpectation: "3-8% annually",
      volatility: "Low (5-10% annual swings)",
      drawdownRisk: "Maximum loss typically 10-15% in worst years",
      bestFor: "Conservative investors, near retirees, short-term goals"
    },
    {
      value: "medium",
      label: "Medium Risk",
      emoji: "⚖️",
      description: "Balanced growth and stability",
      details: "Balanced approach mixing stocks (60%) and bonds (40%) for moderate growth with reasonable stability. The most popular choice offering growth potential while cushioning major downturns.",
      roiExpectation: "6-12% annually",
      volatility: "Moderate (10-20% annual swings)",
      drawdownRisk: "Maximum loss typically 20-30% in worst years",
      bestFor: "Most investors with 5+ year horizons, balanced goals"
    },
    {
      value: "high",
      label: "High Risk",
      emoji: "🚀",
      description: "Maximum growth potential",
      details: "Aggressive portfolio heavily weighted toward stocks (80-100%), growth companies, and emerging markets. Accept significant volatility for potential of higher long-term returns. Requires strong conviction to hold through 30%+ drawdowns.",
      roiExpectation: "10-18% annually (long-term average)",
      volatility: "High (20-40% annual swings)",
      drawdownRisk: "Maximum loss can exceed 40-50% in severe bear markets",
      bestFor: "Young investors, long time horizons (10+ years), high risk tolerance"
    }
  ];

  useEffect(() => {
    if (isOpen) {
      loadUserContext();
    }
  }, [isOpen]);

  const totalSteps = 3; // Step 1: Basic info, Step 2: Sectors, Step 3: Strategies

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
        .filter(key => sectorPreferences[key].enabled)
        .map(key => `${key} (${sectorPreferences[key].allocation}%)`)
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
          monitoring_frequency: monitoringFrequency,
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
      // Prepare sector preferences with allocations
      const selectedSectors = Object.keys(sectorPreferences).reduce((acc, key) => {
        if (sectorPreferences[key].enabled) {
          acc[key] = { 
            allowed: true, 
            allocation: sectorPreferences[key].allocation 
          };
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
          time_horizon: timeHorizon,
          monitoring_frequency: monitoringFrequency,
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
                  {riskToleranceOptions.map((option) => (
                    <div key={option.value} className="relative">
                      <button
                        type="button"
                        onClick={() => setRiskTolerance(option.value)}
                        className={`w-full p-4 rounded-lg border-2 transition-all ${
                          riskTolerance === option.value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300'
                        }`}
                      >
                        <div className="flex items-center justify-center gap-2 mb-2">
                          <span className="text-lg">{option.emoji}</span>
                          <div className="font-semibold text-gray-900 text-sm">{option.label.replace(' Risk', '')}</div>
                        </div>
                        <div className="text-xs text-gray-600">{option.description}</div>
                      </button>
                      <TooltipProvider delayDuration={200}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              className="absolute top-2 right-2 p-1 hover:bg-purple-100 rounded-full transition-colors"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <HelpCircle className="w-4 h-4 text-purple-600" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="max-w-sm p-4 bg-gray-900 text-white border-gray-700">
                            <div className="space-y-3">
                              <div>
                                <p className="font-bold text-sm text-purple-400 mb-1">{option.label}</p>
                                <p className="text-xs text-gray-300 leading-relaxed">{option.details}</p>
                              </div>
                              <div className="pt-2 border-t border-gray-700 space-y-2">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-gray-400">Expected ROI:</span>
                                  <span className="text-xs font-semibold text-purple-400">{option.roiExpectation}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-gray-400">Volatility:</span>
                                  <span className="text-xs font-semibold text-white">{option.volatility}</span>
                                </div>
                                <div className="space-y-1">
                                  <p className="text-xs text-gray-400">Drawdown Risk:</p>
                                  <p className="text-xs text-gray-300 italic">{option.drawdownRisk}</p>
                                </div>
                                <div className="pt-1 border-t border-gray-700">
                                  <p className="text-xs text-gray-400"><span className="font-semibold text-white">Best for:</span> {option.bestFor}</p>
                                </div>
                              </div>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  ))}
                </div>
              </div>

              {/* Additional fields on step 1 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Expected Annual Return (%)
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
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Time Horizon
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
                    Monitoring Frequency
                  </label>
                  <select
                    value={monitoringFrequency}
                    onChange={(e) => setMonitoringFrequency(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="daily">Daily - Active monitoring</option>
                    <option value="weekly">Weekly - Regular check-ins</option>
                    <option value="monthly">Monthly - Moderate oversight</option>
                    <option value="quarterly">Quarterly - Periodic reviews</option>
                    <option value="annually">Annually - Long-term hold</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Investment Sectors with AI Recommendations */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Investment Sectors</h3>
                  <p className="text-gray-600">Let AI recommend optimal sector allocation based on your profile</p>
                </div>
                <Button
                  onClick={fetchRecommendations}
                  disabled={loadingRecommendations}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                >
                  {loadingRecommendations ? (
                    <>
                      <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                      Getting AI Recommendations...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Get AI Recommendations
                    </>
                  )}
                </Button>
              </div>

              {recommendations && (
                <div className="p-4 bg-purple-50 border-2 border-purple-200 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Sparkles className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold text-purple-900 mb-1">AI Recommendation</p>
                      <p className="text-sm text-purple-700">{recommendations.reasoning}</p>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Investment Sectors & Allocation (%) *
                </label>
                <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
                  {sectorInfo.map((sector) => (
                    <div
                      key={sector.id}
                      className={`p-3 border-2 rounded-lg transition-all duration-200 ${
                        sectorPreferences[sector.id]?.enabled
                          ? "border-purple-500 bg-purple-50"
                          : "border-gray-200 bg-gray-50"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <button
                          type="button"
                          onClick={() => handleSectorToggle(sector.id)}
                          className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                            sectorPreferences[sector.id]?.enabled ? "bg-purple-100" : "bg-gray-100"
                          }`}
                        >
                          {sectorPreferences[sector.id]?.enabled ? (
                            <div className="w-4 h-4 bg-purple-600 rounded-full"></div>
                          ) : (
                            <div className="w-4 h-4 border-2 border-gray-300 rounded-full"></div>
                          )}
                        </button>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xl">{sector.emoji}</span>
                            <span className="font-semibold text-gray-900">{sector.label}</span>
                          </div>
                          <p className="text-xs text-gray-600">{sector.description}</p>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <Input
                            type="number"
                            value={sectorPreferences[sector.id]?.allocation || 0}
                            onChange={(e) => handleSectorAllocationChange(sector.id, e.target.value)}
                            min="0"
                            max="100"
                            step="1"
                            disabled={!sectorPreferences[sector.id]?.enabled}
                            className="w-20 text-center"
                          />
                          <span className="text-sm font-medium text-gray-600">%</span>
                          <TooltipProvider delayDuration={200}>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => e.stopPropagation()}
                                  className="p-1.5 hover:bg-purple-100 rounded-full transition-colors"
                                >
                                  <HelpCircle className="w-4 h-4 text-purple-600" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="left" className="max-w-sm p-4 bg-gray-900 text-white border-gray-700">
                                <div className="space-y-3">
                                  <div>
                                    <p className="font-bold text-sm text-purple-400 mb-1">{sector.label}</p>
                                    <p className="text-xs text-gray-300 leading-relaxed">{sector.details}</p>
                                  </div>
                                  <div className="pt-2 border-t border-gray-700 space-y-2">
                                    <div className="space-y-1">
                                      <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-400">Risk Level:</span>
                                        <span className="text-xs font-semibold text-white">{sector.risk}</span>
                                      </div>
                                      <p className="text-xs text-gray-400 italic">{sector.riskFactors}</p>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-xs text-gray-400">Expected ROI:</span>
                                      <span className="text-xs font-semibold text-purple-400">{sector.roiExpectation}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-xs text-gray-400">Volatility:</span>
                                      <span className="text-xs font-semibold text-white">{sector.volatility}</span>
                                    </div>
                                    <div className="pt-1 border-t border-gray-700">
                                      <p className="text-xs text-gray-400"><span className="font-semibold text-white">Best for:</span> {sector.bestFor}</p>
                                    </div>
                                  </div>
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-2 p-2 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-xs text-blue-800">
                    💡 Total allocation: {Object.values(sectorPreferences).reduce((sum, s) => sum + (s.enabled ? s.allocation : 0), 0).toFixed(1)}%
                    {Math.abs(Object.values(sectorPreferences).reduce((sum, s) => sum + (s.enabled ? s.allocation : 0), 0) - 100) > 0.1 && 
                      <span className="font-semibold"> (Should total 100%)</span>
                    }
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Investment Strategies */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Investment Strategies</h3>
                <p className="text-gray-600">
                  {recommendations 
                    ? "Based on your profile, we've recommended some strategies. You can adjust these as needed."
                    : "Select investment strategies that align with your goals"}
                </p>
              </div>

              {/* Investment Strategies */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Investment Strategies (Optional)
                </label>
                <div className="space-y-2 max-h-72 overflow-y-auto pr-2">
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
                        <TooltipProvider delayDuration={200}>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => e.stopPropagation()}
                                className="p-1.5 hover:bg-purple-100 rounded-full transition-colors flex-shrink-0"
                              >
                                <HelpCircle className="w-4 h-4 text-purple-600" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="left" className="max-w-sm p-4 bg-gray-900 text-white border-gray-700">
                              <div className="space-y-3">
                                <div>
                                  <p className="font-bold text-sm text-purple-400 mb-1">{strategy.name}</p>
                                  <p className="text-xs text-gray-300 leading-relaxed">{strategy.details}</p>
                                </div>
                                <div className="pt-2 border-t border-gray-700 space-y-2">
                                  <div className="space-y-1">
                                    <div className="flex items-center justify-between">
                                      <span className="text-xs text-gray-400">Risk Level:</span>
                                      <span className="text-xs font-semibold text-white">{strategy.risk}</span>
                                    </div>
                                    <p className="text-xs text-gray-400 italic">{strategy.riskFactors}</p>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs text-gray-400">Expected ROI:</span>
                                    <span className="text-xs font-semibold text-purple-400">{strategy.roiExpectation}</span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs text-gray-400">Time Horizon:</span>
                                    <span className="text-xs font-semibold text-white">{strategy.timeHorizon}</span>
                                  </div>
                                  <div className="pt-1 border-t border-gray-700">
                                    <p className="text-xs text-gray-400"><span className="font-semibold text-white">Best for:</span> {strategy.bestFor}</p>
                                  </div>
                                </div>
                              </div>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                    </div>
                  ))}
                </div>
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
