import { useState } from "react";
import { X, Plus, Trash2, AlertCircle, HelpCircle } from "lucide-react";
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

export default function ManualPortfolioBuilder({ isOpen, onClose, onSuccess }) {
  const [portfolioName, setPortfolioName] = useState("");
  const [portfolioGoal, setPortfolioGoal] = useState("");
  const [riskTolerance, setRiskTolerance] = useState("medium");
  const [roiExpectations, setRoiExpectations] = useState(10);
  const [timeHorizon, setTimeHorizon] = useState("5-10");
  const [investmentAmount, setInvestmentAmount] = useState("");
  const [monitoringFrequency, setMonitoringFrequency] = useState("monthly");
  const [sectorPreferences, setSectorPreferences] = useState({
    stocks: true,
    bonds: false,
    crypto: false,
    real_estate: false,
    commodities: false,
    forex: false,
  });
  const [investmentStrategies, setInvestmentStrategies] = useState([]);
  const [allocations, setAllocations] = useState([{ 
    ticker: "", 
    allocation_percentage: "",
    sector: "",
    asset_type: "stock"
  }]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

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

  const addAllocation = () => {
    setAllocations([...allocations, { 
      ticker: "", 
      allocation_percentage: "",
      sector: "",
      asset_type: "stock"
    }]);
  };

  const removeAllocation = (index) => {
    const newAllocations = allocations.filter((_, i) => i !== index);
    setAllocations(newAllocations);
  };

  const fetchStockInfo = async (ticker) => {
    if (!ticker || ticker.length < 1) return null;
    
    try {
      const response = await fetch(`${API}/data/asset/${ticker.toUpperCase()}`, {
        credentials: "include",
      });
      
      if (response.ok) {
        const data = await response.json();
        return {
          sector: data.fundamentals?.sector || "Unknown",
          asset_type: data.assetType || "stock"
        };
      }
    } catch (error) {
      console.error("Error fetching stock info:", error);
    }
    return null;
  };

  const updateAllocation = async (index, field, value) => {
    const newAllocations = [...allocations];
    newAllocations[index][field] = value;
    
    // If ticker is updated and it's valid, fetch stock info
    if (field === 'ticker' && value && value.length >= 1) {
      const stockInfo = await fetchStockInfo(value);
      if (stockInfo) {
        newAllocations[index].sector = stockInfo.sector;
        newAllocations[index].asset_type = stockInfo.asset_type;
      }
    }
    
    setAllocations(newAllocations);
  };

  const getTotalAllocation = () => {
    return allocations.reduce((sum, alloc) => {
      const pct = parseFloat(alloc.allocation_percentage) || 0;
      return sum + pct;
    }, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!portfolioName.trim()) {
      toast.error("Please enter a portfolio name");
      return;
    }

    const validAllocations = allocations.filter(
      a => a.ticker.trim() && parseFloat(a.allocation_percentage) > 0
    );

    if (validAllocations.length === 0) {
      toast.error("Please add at least one stock");
      return;
    }

    const totalAllocation = getTotalAllocation();
    if (Math.abs(totalAllocation - 100) > 0.1) {
      toast.error(`Total allocation must equal 100%. Current total: ${totalAllocation.toFixed(1)}%`);
      return;
    }

    setIsSubmitting(true);

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
          type: "manual",
          risk_tolerance: riskTolerance,
          roi_expectations: roiExpectations,
          sector_preferences: Object.keys(selectedSectors).length > 0 ? selectedSectors : null,
          investment_strategy: investmentStrategies.length > 0 ? investmentStrategies : null,
          allocations: validAllocations.map(a => ({
            ticker: a.ticker.toUpperCase(),
            allocation_percentage: parseFloat(a.allocation_percentage),
            asset_type: "stock",
            sector: "Unknown" // Will be updated when fetching stock data
          }))
        }),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success("Portfolio created successfully!");
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
      setIsSubmitting(false);
    }
  };

  const totalAllocation = getTotalAllocation();
  const isValid = Math.abs(totalAllocation - 100) < 0.1;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full my-8">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Create Manual Portfolio</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Portfolio Details */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Portfolio Name *
            </label>
            <Input
              value={portfolioName}
              onChange={(e) => setPortfolioName(e.target.value)}
              placeholder="e.g., Retirement Fund, Growth Portfolio"
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Goal (Optional)
            </label>
            <Textarea
              value={portfolioGoal}
              onChange={(e) => setPortfolioGoal(e.target.value)}
              placeholder="Describe the purpose of this portfolio..."
              className="w-full resize-none"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Risk Tolerance
              </label>
              <div className="space-y-2">
                {riskToleranceOptions.map((option) => (
                  <div
                    key={option.value}
                    onClick={() => setRiskTolerance(option.value)}
                    className={`p-3 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md ${
                      riskTolerance === option.value
                        ? "border-cyan-500 bg-cyan-50"
                        : "border-gray-200 hover:border-cyan-300"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-xl mt-0.5">{option.emoji}</span>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900 text-sm">{option.label}</div>
                        <div className="text-xs text-gray-600">{option.description}</div>
                      </div>
                      <TooltipProvider delayDuration={200}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              onClick={(e) => e.stopPropagation()}
                              className="p-1 hover:bg-cyan-100 rounded-full transition-colors flex-shrink-0"
                            >
                              <HelpCircle className="w-4 h-4 text-cyan-600" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="right" className="max-w-sm p-4 bg-gray-900 text-white border-gray-700">
                            <div className="space-y-3">
                              <div>
                                <p className="font-bold text-sm text-cyan-400 mb-1">{option.label}</p>
                                <p className="text-xs text-gray-300 leading-relaxed">{option.details}</p>
                              </div>
                              <div className="pt-2 border-t border-gray-700 space-y-2">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-gray-400">Expected ROI:</span>
                                  <span className="text-xs font-semibold text-cyan-400">{option.roiExpectation}</span>
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
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Expected ROI (%)
              </label>
              <Input
                type="number"
                value={roiExpectations}
                onChange={(e) => setRoiExpectations(parseFloat(e.target.value))}
                min="0"
                max="100"
                step="0.1"
                className="w-full"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Time Horizon
              </label>
              <select
                value={timeHorizon}
                onChange={(e) => setTimeHorizon(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              >
                <option value="0-3">Short term (0-3 years)</option>
                <option value="3-5">Medium term (3-5 years)</option>
                <option value="5-10">Long term (5-10 years)</option>
                <option value="10+">Very long term (10+ years)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Monitoring Frequency
              </label>
              <select
                value={monitoringFrequency}
                onChange={(e) => setMonitoringFrequency(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              >
                <option value="daily">Daily - Active monitoring</option>
                <option value="weekly">Weekly - Regular check-ins</option>
                <option value="monthly">Monthly - Moderate oversight</option>
                <option value="quarterly">Quarterly - Periodic reviews</option>
                <option value="annually">Annually - Long-term hold</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Initial Investment Amount ($)
            </label>
            <Input
              type="number"
              value={investmentAmount}
              onChange={(e) => setInvestmentAmount(e.target.value)}
              placeholder="Optional - You can invest later"
              min="0"
              step="100"
              className="w-full"
            />
          </div>

          {/* Sector Preferences */}
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
                      ? "bg-cyan-100 text-cyan-700 border-2 border-cyan-500"
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
            <div className="space-y-2 max-h-72 overflow-y-auto pr-2">
              {strategies.map((strategy) => (
                <div
                  key={strategy.id}
                  onClick={() => handleStrategyToggle(strategy.id)}
                  className={`p-3 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md ${
                    investmentStrategies.includes(strategy.id)
                      ? "border-emerald-500 bg-emerald-50"
                      : "border-gray-200 hover:border-emerald-300"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center mt-0.5 flex-shrink-0 ${
                      investmentStrategies.includes(strategy.id) ? "bg-emerald-100" : "bg-gray-100"
                    }`}>
                      {investmentStrategies.includes(strategy.id) ? (
                        <div className="w-4 h-4 bg-emerald-600 rounded-full"></div>
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
                            className="p-1.5 hover:bg-emerald-100 rounded-full transition-colors flex-shrink-0"
                          >
                            <HelpCircle className="w-4 h-4 text-emerald-600" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent side="left" className="max-w-sm p-4 bg-gray-900 text-white border-gray-700">
                          <div className="space-y-3">
                            <div>
                              <p className="font-bold text-sm text-emerald-400 mb-1">{strategy.name}</p>
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
                                <span className="text-xs font-semibold text-emerald-400">{strategy.roiExpectation}</span>
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

          {/* Stock Allocations */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-semibold text-gray-700">
                Stock Allocations *
              </label>
              <Button
                type="button"
                onClick={addAllocation}
                size="sm"
                variant="outline"
                className="text-xs"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Stock
              </Button>
            </div>

            <div className="space-y-3 max-h-64 overflow-y-auto">
              {allocations.map((alloc, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex gap-3 items-center">
                    <Input
                      value={alloc.ticker}
                      onChange={(e) => updateAllocation(index, 'ticker', e.target.value.toUpperCase())}
                      placeholder="Ticker (e.g., AAPL)"
                      className="flex-1"
                    />
                    <div className="relative flex-1">
                      <Input
                        type="number"
                        value={alloc.allocation_percentage}
                        onChange={(e) => updateAllocation(index, 'allocation_percentage', e.target.value)}
                        placeholder="Allocation %"
                        min="0"
                        max="100"
                        step="0.1"
                        className="w-full pr-8"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">
                        %
                      </span>
                    </div>
                    {allocations.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeAllocation(index)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                  {alloc.ticker && alloc.sector && (
                    <div className="flex items-center gap-2 text-xs text-gray-600 ml-1">
                      <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                        {alloc.asset_type}
                      </span>
                      <span>{alloc.sector}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Total Allocation Display */}
            <div className={`mt-4 p-3 rounded-lg flex items-center justify-between ${
              isValid ? 'bg-green-50 border border-green-200' : 'bg-amber-50 border border-amber-200'
            }`}>
              <div className="flex items-center gap-2">
                <AlertCircle className={`w-4 h-4 ${isValid ? 'text-green-600' : 'text-amber-600'}`} />
                <span className={`text-sm font-semibold ${isValid ? 'text-green-900' : 'text-amber-900'}`}>
                  Total Allocation:
                </span>
              </div>
              <span className={`text-lg font-bold ${isValid ? 'text-green-600' : 'text-amber-600'}`}>
                {totalAllocation.toFixed(1)}%
              </span>
            </div>
            {!isValid && (
              <p className="text-xs text-amber-600 mt-2">
                Total must equal 100% to create portfolio
              </p>
            )}
          </div>
        </form>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 flex justify-end gap-3">
          <Button
            type="button"
            onClick={onClose}
            variant="outline"
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !isValid || !portfolioName.trim()}
            className="bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white"
          >
            {isSubmitting ? "Creating..." : "Create Portfolio"}
          </Button>
        </div>
      </div>
    </div>
  );
}
