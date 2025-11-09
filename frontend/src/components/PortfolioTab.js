import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line, Area, AreaChart, CartesianGrid } from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Zap, Calendar } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import StockDetailModal from "./StockDetailModal";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];

// Generate realistic portfolio data
const generatePortfolioData = (days) => {
  const data = [];
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  
  let baseValue = 10000;
  
  for (let i = 0; i <= days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    
    // Simulate market volatility with trend
    const trend = 0.0003; // Slight upward trend
    const volatility = (Math.random() - 0.5) * 100;
    baseValue = baseValue * (1 + trend) + volatility;
    
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(baseValue * 100) / 100,
      displayDate: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    });
  }
  
  return data;
};

const TIME_RANGES = [
  { label: '1W', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
  { label: 'ALL', days: 730 }, // 2 years
];

export default function PortfolioTab() {
  const [portfolio, setPortfolio] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRange, setSelectedRange] = useState('6M');
  const [performanceData, setPerformanceData] = useState([]);
  const [fullData] = useState(generatePortfolioData(730)); // Generate 2 years of data
  const [selectedStock, setSelectedStock] = useState(null);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [showStockDetail, setShowStockDetail] = useState(false);

  useEffect(() => {
    loadPortfolio();
    
    // Listen for portfolio updates from chat
    const handlePortfolioUpdate = () => {
      loadPortfolio();
    };
    
    window.addEventListener('portfolioUpdated', handlePortfolioUpdate);
    
    return () => {
      window.removeEventListener('portfolioUpdated', handlePortfolioUpdate);
    };
  }, []);

  useEffect(() => {
    // Filter data based on selected range
    const range = TIME_RANGES.find(r => r.label === selectedRange);
    if (range && fullData.length > 0) {
      const filteredData = fullData.slice(-range.days);
      setPerformanceData(filteredData);
    }
  }, [selectedRange, fullData]);

  const loadPortfolio = async () => {
    try {
      // Try loading "My Portfolio" first (new endpoint)
      const myPortfolioResponse = await fetch(`${API}/portfolios/my-portfolio?t=${Date.now()}`, {
        credentials: "include",
        cache: "no-store"
      });
      
      if (myPortfolioResponse.ok) {
        const myPortfolioData = await myPortfolioResponse.json();
        if (myPortfolioData.portfolio) {
          console.log("My Portfolio loaded:", myPortfolioData);
          
          // Filter out holdings with 0 quantity
          const activeHoldings = myPortfolioData.portfolio.holdings?.filter(h => h.quantity > 0) || [];
          
          // Transform to match expected format
          const transformedPortfolio = {
            risk_tolerance: myPortfolioData.portfolio.risk_tolerance || "medium",
            roi_expectations: myPortfolioData.portfolio.roi_expectations || 10,
            allocations: activeHoldings.map(h => ({
              ticker: h.symbol,
              asset_type: h.asset_type || "stock",
              allocation: h.allocation_percentage || 0,
              sector: h.sector || "Unknown",
              // Store full holding data for modal
              holdingData: h
            })),
            fullHoldings: activeHoldings // Store full holdings for reference
          };
          setPortfolio(transformedPortfolio);
          setIsLoading(false);
          return;
        }
      }
      
      // Fall back to AI-generated portfolio
      const response = await fetch(`${API}/portfolio?t=${Date.now()}`, {
        credentials: "include",
        cache: "no-store"
      });
      if (response.ok) {
        const data = await response.json();
        console.log("AI Portfolio loaded:", data);
        setPortfolio(data);
      }
    } catch (error) {
      console.error("Failed to load portfolio:", error);
      toast.error("Failed to load portfolio");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="w-16 h-16 spinner"></div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="clean-card rounded-2xl p-8 text-center">
        <p className="text-gray-600">No portfolio data available</p>
      </div>
    );
  }

  // Prepare data for charts
  const sectorData = {};
  const assetTypeData = {};
  
  portfolio.allocations?.forEach((alloc) => {
    if (sectorData[alloc.sector]) {
      sectorData[alloc.sector] += alloc.allocation;
    } else {
      sectorData[alloc.sector] = alloc.allocation;
    }
    
    if (assetTypeData[alloc.asset_type]) {
      assetTypeData[alloc.asset_type] += alloc.allocation;
    } else {
      assetTypeData[alloc.asset_type] = alloc.allocation;
    }
  });

  const sectorChartData = Object.entries(sectorData).map(([name, value]) => ({
    name,
    value: parseFloat(value.toFixed(2)),
  }));

  const assetTypeChartData = Object.entries(assetTypeData).map(([name, value]) => ({
    name,
    value: parseFloat(value.toFixed(2)),
  }));

  const startValue = performanceData[0]?.value || 10000;
  const endValue = performanceData[performanceData.length - 1]?.value || 10000;
  const totalReturn = ((endValue - startValue) / startValue * 100).toFixed(2);
  const isPositive = parseFloat(totalReturn) >= 0;

  // Custom tooltip for performance chart
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const value = payload[0].value;
      const change = ((value - startValue) / startValue * 100).toFixed(2);
      
      return (
        <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
          <p className="text-sm font-semibold text-gray-900">{new Date(data.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
          <p className="text-lg font-bold text-gray-900">${value.toLocaleString()}</p>
          <p className={`text-sm font-medium ${parseFloat(change) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
            {parseFloat(change) >= 0 ? '+' : ''}{change}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6" data-testid="portfolio-tab">
      {/* Portfolio Summary */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="clean-card p-6 card-hover fade-in-1" data-testid="risk-card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-600 uppercase tracking-wider">Risk Tolerance</h3>
            <Zap className="w-5 h-5 text-cyan-600" />
          </div>
          <p className="text-4xl font-bold text-gray-900 capitalize">{portfolio.risk_tolerance}</p>
        </div>

        <div className="clean-card p-6 card-hover fade-in-2" data-testid="roi-card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-600 uppercase tracking-wider">ROI Target</h3>
            <DollarSign className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-4xl font-bold gradient-text">{portfolio.roi_expectations}%</p>
        </div>

        <div className="clean-card p-6 card-hover fade-in-3" data-testid="return-card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-600 uppercase tracking-wider">{selectedRange} Return</h3>
            {isPositive ? (
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-600" />
            )}
          </div>
          <p className={`text-4xl font-bold ${isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}{totalReturn}%
          </p>
        </div>
      </div>

      {/* Performance Chart - Enhanced */}
      <div className="clean-card p-6 card-hover" data-testid="performance-chart">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-1">Portfolio Performance</h3>
            <p className="text-sm text-gray-600">Track your investment growth over time</p>
          </div>
          
          {/* Time Range Selector */}
          <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
            {TIME_RANGES.map((range) => (
              <Button
                key={range.label}
                onClick={() => setSelectedRange(range.label)}
                size="sm"
                variant={selectedRange === range.label ? "default" : "ghost"}
                className={`
                  px-4 py-2 text-sm font-semibold rounded-md smooth-transition
                  ${selectedRange === range.label 
                    ? 'bg-gradient-to-r from-cyan-600 to-emerald-600 text-white shadow-md' 
                    : 'text-gray-600 hover:bg-white hover:text-gray-900'
                  }
                `}
              >
                {range.label}
              </Button>
            ))}
          </div>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={performanceData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="displayDate" 
              stroke="#9ca3af"
              tick={{ fontSize: 12 }}
              tickLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis 
              stroke="#9ca3af"
              tick={{ fontSize: 12 }}
              tickLine={{ stroke: '#e5e7eb' }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke={isPositive ? "#10b981" : "#ef4444"}
              strokeWidth={2.5}
              fill="url(#colorValue)"
              dot={false}
              activeDot={{ r: 6, fill: isPositive ? "#10b981" : "#ef4444" }}
            />
          </AreaChart>
        </ResponsiveContainer>

        {/* Stats below chart */}
        <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
          <div>
            <p className="text-xs text-gray-600 mb-1">Starting Value</p>
            <p className="text-lg font-bold text-gray-900">${startValue.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Current Value</p>
            <p className="text-lg font-bold text-gray-900">${endValue.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Total Gain/Loss</p>
            <p className={`text-lg font-bold ${isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
              ${Math.abs(endValue - startValue).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Sector Allocation */}
        <div className="clean-card p-6 card-hover" data-testid="sector-chart">
          <h3 className="text-lg font-bold text-gray-900 mb-6">Sector Allocation</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sectorChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}%`}
                outerRadius={90}
                fill="#8884d8"
                dataKey="value"
              >
                {sectorChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Asset Type Allocation */}
        <div className="clean-card p-6 card-hover" data-testid="asset-type-chart">
          <h3 className="text-lg font-bold text-gray-900 mb-6">Asset Type Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={assetTypeChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#6b7280" tick={{ fontSize: 12 }} />
              <YAxis stroke="#6b7280" tick={{ fontSize: 12 }} />
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }} />
              <Bar dataKey="value" fill="url(#barGradient)" radius={[8, 8, 0, 0]} />
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity={1}/>
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0.8}/>
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="clean-card p-6 card-hover" data-testid="holdings-table">
        <h3 className="text-lg font-bold text-gray-900 mb-6">Current Holdings</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-4 px-4 text-sm font-semibold text-gray-700 uppercase tracking-wider">Ticker</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-gray-700 uppercase tracking-wider">Type</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-gray-700 uppercase tracking-wider">Sector</th>
                <th className="text-right py-4 px-4 text-sm font-semibold text-gray-700 uppercase tracking-wider">Allocation</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.allocations?.map((alloc, idx) => (
                <tr 
                  key={idx} 
                  onClick={() => {
                    setSelectedStock(alloc.ticker);
                    setSelectedHolding(alloc);
                    setShowStockDetail(true);
                  }}
                  className="border-b border-gray-100 hover:bg-cyan-50 smooth-transition cursor-pointer"
                >
                  <td className="py-4 px-4 font-bold text-cyan-600 hover:text-cyan-700">{alloc.ticker}</td>
                  <td className="py-4 px-4 text-gray-600">{alloc.asset_type}</td>
                  <td className="py-4 px-4 text-gray-600">{alloc.sector}</td>
                  <td className="py-4 px-4 text-right font-bold gradient-text">{alloc.allocation}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

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