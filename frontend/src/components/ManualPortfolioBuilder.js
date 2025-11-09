import { useState } from "react";
import { X, Plus, Trash2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ManualPortfolioBuilder({ isOpen, onClose, onSuccess }) {
  const [portfolioName, setPortfolioName] = useState("");
  const [portfolioGoal, setPortfolioGoal] = useState("");
  const [riskTolerance, setRiskTolerance] = useState("medium");
  const [roiExpectations, setRoiExpectations] = useState(10);
  const [sectorPreferences, setSectorPreferences] = useState({
    stocks: true,
    bonds: false,
    crypto: false,
    real_estate: false,
    commodities: false,
    forex: false,
  });
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
              <select
                value={riskTolerance}
                onChange={(e) => setRiskTolerance(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
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
