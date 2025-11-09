import { useState, useEffect } from "react";
import { DollarSign, TrendingUp, TrendingDown, Edit, MessageSquare, Trash2, Download, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import EditAllocationModal from "./EditAllocationModal";
import EditPortfolioInfoModal from "./EditPortfolioInfoModal";
import DeletePortfolioModal from "./DeletePortfolioModal";
import ExportPortfolioModal from "./ExportPortfolioModal";
import StockDetailModal from "./StockDetailModal";
import PortfolioPerformanceChart from "./PortfolioPerformanceChart";
import RiskMetricsDashboard from "./RiskMetricsDashboard";
import CorrelationHeatmap from "./CorrelationHeatmap";
import PortfolioDistributions from "./PortfolioDistributions";
import DividendTracker from "./DividendTracker";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];

export default function PortfolioView({ portfolioId, onChatToggle }) {
  const [portfolio, setPortfolio] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showInvestModal, setShowInvestModal] = useState(false);
  const [investAmount, setInvestAmount] = useState("");
  const [isInvesting, setIsInvesting] = useState(false);
  const [showEditAllocationModal, setShowEditAllocationModal] = useState(false);
  const [showEditInfoModal, setShowEditInfoModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showStockDetail, setShowStockDetail] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [selectedHolding, setSelectedHolding] = useState(null);

  useEffect(() => {
    if (portfolioId) {
      loadPortfolio();
    }
  }, [portfolioId]);

  const loadPortfolio = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API}/portfolios-v2/${portfolioId}`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setPortfolio(data.portfolio);
      } else {
        toast.error("Failed to load portfolio");
      }
    } catch (error) {
      console.error("Error loading portfolio:", error);
      toast.error("Failed to load portfolio");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePortfolioDeleted = () => {
    // Reload the page to refresh portfolio list
    window.location.reload();
  };

  const handleInvest = async () => {
    const amount = parseFloat(investAmount);
    
    if (isNaN(amount) || amount <= 0) {
      toast.error("Please enter a valid investment amount");
      return;
    }

    setIsInvesting(true);

    try {
      const response = await fetch(`${API}/portfolios-v2/${portfolioId}/invest`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ amount }),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        setShowInvestModal(false);
        setInvestAmount("");
        loadPortfolio(); // Reload to show updated holdings
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || "Failed to invest");
      }
    } catch (error) {
      console.error("Error investing:", error);
      toast.error("Failed to invest");
    } finally {
      setIsInvesting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Select a portfolio to view details</p>
        </div>
      </div>
    );
  }

  const hasHoldings = portfolio.holdings && portfolio.holdings.length > 0;
  const hasAllocations = portfolio.allocations && portfolio.allocations.length > 0;

  // Prepare chart data for ticker allocation
  const chartData = hasHoldings
    ? portfolio.holdings.map((h, idx) => ({
        name: h.ticker,
        value: h.current_value,
        color: COLORS[idx % COLORS.length]
      }))
    : hasAllocations
    ? portfolio.allocations.map((a, idx) => ({
        name: a.ticker,
        value: a.allocation_percentage,
        color: COLORS[idx % COLORS.length]
      }))
    : [];

  // Prepare asset type allocation data
  const assetTypeData = hasAllocations ? (() => {
    const typeMap = {};
    portfolio.allocations.forEach(alloc => {
      const type = alloc.asset_type || 'Unknown';
      if (!typeMap[type]) {
        typeMap[type] = 0;
      }
      typeMap[type] += alloc.allocation_percentage;
    });
    return Object.entries(typeMap).map(([name, value], idx) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: parseFloat(value.toFixed(2)),
      color: COLORS[idx % COLORS.length]
    }));
  })() : [];

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">{portfolio.name}</h1>
              {portfolio.type === 'ai' && (
                <span className="text-xs bg-purple-100 text-purple-700 px-3 py-1 rounded-full font-semibold">
                  AI Portfolio
                </span>
              )}
            </div>
            {portfolio.goal && (
              <p className="text-gray-600">{portfolio.goal}</p>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setShowInvestModal(true)}
              className="bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white"
            >
              <DollarSign className="w-4 h-4 mr-2" />
              Invest
            </Button>
            <Button
              onClick={onChatToggle}
              variant="outline"
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              Chat
            </Button>
            
            {/* More Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem onClick={() => setShowEditInfoModal(true)}>
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Portfolio Info
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowEditAllocationModal(true)}>
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Allocations
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowExportModal(true)}>
                  <Download className="w-4 h-4 mr-2" />
                  Export Portfolio
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => setShowDeleteModal(true)}
                  className="text-red-600 focus:text-red-600"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Portfolio
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Portfolio Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-xl p-4">
            <div className="text-sm text-gray-600 mb-1">Total Invested</div>
            <div className="text-2xl font-bold text-gray-900">
              ${portfolio.total_invested?.toLocaleString() || '0'}
            </div>
          </div>
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl p-4">
            <div className="text-sm text-gray-600 mb-1">Current Value</div>
            <div className="text-2xl font-bold text-gray-900">
              ${portfolio.current_value?.toLocaleString() || '0'}
            </div>
          </div>
          <div className={`rounded-xl p-4 ${
            portfolio.total_return >= 0
              ? 'bg-gradient-to-br from-green-50 to-emerald-50'
              : 'bg-gradient-to-br from-red-50 to-pink-50'
          }`}>
            <div className="text-sm text-gray-600 mb-1">Total Return</div>
            <div className={`text-2xl font-bold flex items-center gap-2 ${
              portfolio.total_return >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {portfolio.total_return >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
              ${Math.abs(portfolio.total_return || 0).toLocaleString()}
            </div>
          </div>
          <div className={`rounded-xl p-4 ${
            portfolio.total_return_percentage >= 0
              ? 'bg-gradient-to-br from-green-50 to-emerald-50'
              : 'bg-gradient-to-br from-red-50 to-pink-50'
          }`}>
            <div className="text-sm text-gray-600 mb-1">Return %</div>
            <div className={`text-2xl font-bold ${
              portfolio.total_return_percentage >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {portfolio.total_return_percentage >= 0 ? '+' : ''}
              {portfolio.total_return_percentage?.toFixed(2) || '0'}%
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Performance Chart - Full Width */}
        {hasAllocations && (
          <div className="mb-6">
            <PortfolioPerformanceChart portfolioId={portfolioId} />
          </div>
        )}

        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Ticker Allocation Chart */}
          {chartData.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                {hasHoldings ? 'Current Holdings' : 'Ticker Allocation'}
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => 
                      hasHoldings 
                        ? `${name}: $${value.toFixed(0)}`
                        : `${name}: ${value.toFixed(1)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Asset Type Allocation Chart */}
          {assetTypeData.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Asset Type Allocation
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={assetTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {assetTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Holdings/Allocations Table - Full Width */}
        <div className="mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {hasHoldings ? 'Holdings' : 'Allocations'}
            </h3>
            <div className="space-y-3">
              {hasHoldings ? (
                portfolio.holdings.map((holding, idx) => (
                  <div 
                    key={idx} 
                    onClick={() => {
                      setSelectedStock(holding.ticker);
                      setSelectedHolding(holding);
                      setShowStockDetail(true);
                    }}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                  >
                    <div>
                      <div className="font-bold text-gray-900">{holding.ticker}</div>
                      <div className="text-xs text-gray-600">
                        {holding.shares.toFixed(4)} shares @ ${holding.purchase_price.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-600 flex items-center gap-2 mt-1">
                        {holding.asset_type && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">
                            {holding.asset_type}
                          </span>
                        )}
                        {holding.sector && (
                          <span className="text-gray-500">
                            {holding.sector}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900">
                        ${holding.current_value.toFixed(2)}
                      </div>
                      <div className={`text-xs ${
                        holding.current_value >= holding.cost_basis ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {holding.current_value >= holding.cost_basis ? '+' : ''}
                        {((holding.current_value - holding.cost_basis) / holding.cost_basis * 100).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                ))
              ) : hasAllocations ? (
                portfolio.allocations.map((alloc, idx) => (
                  <div 
                    key={idx} 
                    onClick={() => {
                      setSelectedStock(alloc.ticker);
                      setSelectedHolding(null);
                      setShowStockDetail(true);
                    }}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors group"
                  >
                    <div>
                      <div className="font-bold text-gray-900">{alloc.ticker}</div>
                      <div className="text-xs text-gray-600 flex items-center gap-2 mt-1">
                        {alloc.asset_type && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">
                            {alloc.asset_type}
                          </span>
                        )}
                        {alloc.sector && (
                          <span className="text-gray-500">
                            {alloc.sector}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right flex items-center gap-2">
                      <div className="font-bold gradient-text">
                        {alloc.allocation_percentage}%
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-8">No allocations set</p>
              )}
            </div>
          </div>
        </div>

        {/* Risk Metrics Dashboard - Full Width */}
        {hasAllocations && (
          <div className="mb-6">
            <RiskMetricsDashboard portfolioId={portfolioId} />
          </div>
        )}

        {/* Correlation Heatmap - Full Width */}
        {hasAllocations && (
          <div className="mb-6">
            <CorrelationHeatmap portfolioId={portfolioId} />
          </div>
        )}

        {/* Portfolio Distributions - 2 columns */}
        {hasAllocations && (
          <div className="mb-6">
            <PortfolioDistributions portfolioId={portfolioId} />
          </div>
        )}

        {/* Dividend Tracker - Full Width */}
        {hasAllocations && (
          <div className="mb-6">
            <DividendTracker portfolioId={portfolioId} />
          </div>
        )}
      </div>

      {/* Investment Modal */}
      {showInvestModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Invest in {portfolio.name}</h3>
            <p className="text-sm text-gray-600 mb-4">
              Enter the amount you want to invest. The system will automatically calculate shares based on current prices and your allocation percentages.
            </p>
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Investment Amount ($)
              </label>
              <Input
                type="number"
                value={investAmount}
                onChange={(e) => setInvestAmount(e.target.value)}
                placeholder="Enter amount"
                min="0"
                step="0.01"
                className="w-full text-lg"
                autoFocus
              />
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => setShowInvestModal(false)}
                variant="outline"
                className="flex-1"
                disabled={isInvesting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleInvest}
                disabled={isInvesting || !investAmount}
                className="flex-1 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white"
              >
                {isInvesting ? "Investing..." : "Invest"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Allocation Modal */}
      <EditAllocationModal
        isOpen={showEditAllocationModal}
        onClose={() => setShowEditAllocationModal(false)}
        portfolio={portfolio}
        onSuccess={loadPortfolio}
      />

      {/* Edit Portfolio Info Modal */}
      <EditPortfolioInfoModal
        isOpen={showEditInfoModal}
        onClose={() => setShowEditInfoModal(false)}
        portfolio={portfolio}
        onSuccess={loadPortfolio}
      />

      {/* Delete Portfolio Modal */}
      <DeletePortfolioModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        portfolio={portfolio}
        onSuccess={handlePortfolioDeleted}
      />

      {/* Export Portfolio Modal */}
      <ExportPortfolioModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        portfolio={portfolio}
      />

      {/* Stock Detail Modal */}
      <StockDetailModal
        symbol={selectedStock}
        holding={selectedHolding}
        isOpen={showStockDetail}
        onClose={() => {
          setShowStockDetail(false);
          setSelectedStock(null);
          setSelectedHolding(null);
        }}
      />
    </div>
  );
}
