import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from "recharts";
import { TrendingUp, TrendingDown, DollarSign } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];

export default function PortfolioTab() {
  const [portfolio, setPortfolio] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadPortfolio();
  }, []);

  const loadPortfolio = async () => {
    try {
      const response = await fetch(`${API}/portfolio`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
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
        <div className="text-slate-600">Loading portfolio...</div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="glass rounded-2xl p-8 text-center">
        <p className="text-slate-600">No portfolio data available</p>
      </div>
    );
  }

  // Prepare data for charts
  const sectorData = {};
  const assetTypeData = {};
  
  portfolio.allocations?.forEach((alloc) => {
    // Sector aggregation
    if (sectorData[alloc.sector]) {
      sectorData[alloc.sector] += alloc.allocation;
    } else {
      sectorData[alloc.sector] = alloc.allocation;
    }
    
    // Asset type aggregation
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

  // Mock historical performance data
  const performanceData = [
    { month: 'Jan', value: 10000 },
    { month: 'Feb', value: 10500 },
    { month: 'Mar', value: 10300 },
    { month: 'Apr', value: 11200 },
    { month: 'May', value: 11800 },
    { month: 'Jun', value: 12100 },
  ];

  const totalReturn = ((performanceData[performanceData.length - 1].value - performanceData[0].value) / performanceData[0].value * 100).toFixed(2);

  return (
    <div className="space-y-6" data-testid="portfolio-tab">
      {/* Portfolio Summary */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="glass rounded-2xl p-6 shadow-lg" data-testid="risk-card">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-slate-600">Risk Tolerance</h3>
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-slate-800 capitalize">{portfolio.risk_tolerance}</p>
        </div>

        <div className="glass rounded-2xl p-6 shadow-lg" data-testid="roi-card">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-slate-600">ROI Expectations</h3>
            <DollarSign className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-3xl font-bold text-slate-800">{portfolio.roi_expectations}%</p>
        </div>

        <div className="glass rounded-2xl p-6 shadow-lg" data-testid="return-card">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-slate-600">6-Month Return</h3>
            {totalReturn >= 0 ? (
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-600" />
            )}
          </div>
          <p className={`text-3xl font-bold ${totalReturn >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
            {totalReturn >= 0 ? '+' : ''}{totalReturn}%
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Sector Allocation */}
        <div className="glass rounded-2xl p-6 shadow-lg" data-testid="sector-chart">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Sector Allocation</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sectorChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {sectorChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Asset Type Allocation */}
        <div className="glass rounded-2xl p-6 shadow-lg" data-testid="asset-type-chart">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Asset Type Allocation</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={assetTypeChartData}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="glass rounded-2xl p-6 shadow-lg" data-testid="performance-chart">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">Portfolio Performance</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData}>
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={3} name="Portfolio Value ($)" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Holdings Table */}
      <div className="glass rounded-2xl p-6 shadow-lg" data-testid="holdings-table">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">Current Holdings</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Ticker</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Asset Type</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Sector</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-slate-600">Allocation</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.allocations?.map((alloc, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4 font-medium text-slate-800">{alloc.ticker}</td>
                  <td className="py-3 px-4 text-slate-600">{alloc.asset_type}</td>
                  <td className="py-3 px-4 text-slate-600">{alloc.sector}</td>
                  <td className="py-3 px-4 text-right font-semibold text-blue-600">{alloc.allocation}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}