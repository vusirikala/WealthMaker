import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Zap } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#a855f7', '#14b8a6', '#fb7185', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];

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
        <div className="w-16 h-16 spinner"></div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="glass-card rounded-3xl p-8 text-center border border-purple-500/30">
        <p className="text-gray-400">No portfolio data available</p>
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
        <div className="glass-card rounded-3xl p-6 neon-glow border border-purple-500/30 hover-lift stagger-item" data-testid="risk-card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Risk Tolerance</h3>
            <Zap className="w-5 h-5 text-purple-400" />
          </div>
          <p className="text-4xl font-black gradient-text capitalize">{portfolio.risk_tolerance}</p>
        </div>

        <div className="glass-card rounded-3xl p-6 neon-glow border border-teal-500/30 hover-lift stagger-item" data-testid="roi-card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">ROI Target</h3>
            <DollarSign className="w-5 h-5 text-teal-400" />
          </div>
          <p className="text-4xl font-black gradient-text">{portfolio.roi_expectations}%</p>
        </div>

        <div className="glass-card rounded-3xl p-6 neon-glow border border-pink-500/30 hover-lift stagger-item" data-testid="return-card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">6-Month Return</h3>
            {totalReturn >= 0 ? (
              <TrendingUp className="w-5 h-5 text-teal-400" />
            ) : (
              <TrendingDown className="w-5 h-5 text-pink-600" />
            )}
          </div>
          <p className={`text-4xl font-black ${totalReturn >= 0 ? 'text-teal-400' : 'text-pink-400'}`}>
            {totalReturn >= 0 ? '+' : ''}{totalReturn}%
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Sector Allocation */}
        <div className="glass-card rounded-3xl p-6 neon-glow border border-purple-500/30 hover-lift" data-testid="sector-chart">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <span className="gradient-text">Sector Allocation</span>
          </h3>
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
              <Tooltip contentStyle={{ background: '#18122b', border: '1px solid #a855f7', borderRadius: '12px', color: 'white' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Asset Type Allocation */}
        <div className="glass-card rounded-3xl p-6 neon-glow border border-teal-500/30 hover-lift" data-testid="asset-type-chart">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <span className="gradient-text">Asset Type Distribution</span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={assetTypeChartData}>
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip contentStyle={{ background: '#18122b', border: '1px solid #14b8a6', borderRadius: '12px', color: 'white' }} />
              <Bar dataKey="value" fill="url(#colorGradient)" radius={[12, 12, 0, 0]} />
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#14b8a6" stopOpacity={1}/>
                  <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.8}/>
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="glass-card rounded-3xl p-6 neon-glow border border-pink-500/30 hover-lift" data-testid="performance-chart">
        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <span className="gradient-text">Portfolio Performance</span>
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData}>
            <XAxis dataKey="month" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip contentStyle={{ background: '#18122b', border: '1px solid #fb7185', borderRadius: '12px', color: 'white' }} />
            <Legend wrapperStyle={{ color: 'white' }} />
            <Line type="monotone" dataKey="value" stroke="url(#lineGradient)" strokeWidth={3} name="Portfolio Value ($)" dot={{ fill: '#fb7185', r: 5 }} />
            <defs>
              <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#a855f7" />
                <stop offset="50%" stopColor="#14b8a6" />
                <stop offset="100%" stopColor="#fb7185" />
              </linearGradient>
            </defs>
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Holdings Table */}
      <div className="glass-card rounded-3xl p-6 neon-glow border border-purple-500/30 hover-lift" data-testid="holdings-table">
        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <span className="gradient-text">Current Holdings</span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-purple-500/30">
                <th className="text-left py-4 px-4 text-sm font-semibold text-purple-300 uppercase tracking-wider">Ticker</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-purple-300 uppercase tracking-wider">Type</th>
                <th className="text-left py-4 px-4 text-sm font-semibold text-purple-300 uppercase tracking-wider">Sector</th>
                <th className="text-right py-4 px-4 text-sm font-semibold text-purple-300 uppercase tracking-wider">Allocation</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.allocations?.map((alloc, idx) => (
                <tr key={idx} className="border-b border-purple-500/10 hover:bg-purple-500/10 smooth-transition">
                  <td className="py-4 px-4 font-bold text-white">{alloc.ticker}</td>
                  <td className="py-4 px-4 text-gray-300">{alloc.asset_type}</td>
                  <td className="py-4 px-4 text-gray-300">{alloc.sector}</td>
                  <td className="py-4 px-4 text-right font-bold gradient-text">{alloc.allocation}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}