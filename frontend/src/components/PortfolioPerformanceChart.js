import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from "recharts";
import { TrendingUp, TrendingDown, Calendar } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TIME_PERIODS = [
  { value: '6m', label: '6 Months' },
  { value: '1y', label: '1 Year' },
  { value: '3y', label: '3 Years' },
  { value: '5y', label: '5 Years' }
];

export default function PortfolioPerformanceChart({ portfolioId }) {
  const [selectedPeriod, setSelectedPeriod] = useState('1y');
  const [performanceData, setPerformanceData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (portfolioId) {
      loadPerformanceData();
    }
  }, [portfolioId, selectedPeriod]);

  const loadPerformanceData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${API}/portfolios-v2/${portfolioId}/performance?time_period=${selectedPeriod}`,
        {
          credentials: "include",
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Merge portfolio and S&P 500 data
        if (data.sp500_comparison && data.sp500_comparison.time_series) {
          const merged = data.time_series.map((item, idx) => ({
            date: item.date,
            portfolio_return: item.return_percentage,
            sp500_return: data.sp500_comparison.time_series[idx]?.return_percentage || 0
          }));
          data.merged_time_series = merged;
        }
        
        setPerformanceData(data);
      } else {
        toast.error("Failed to load performance data");
      }
    } catch (error) {
      console.error("Error loading performance:", error);
      toast.error("Failed to load performance data");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!performanceData) {
    return null;
  }

  const { merged_time_series, return_percentage, period_stats, sp500_comparison } = performanceData;
  const isPositive = return_percentage >= 0;
  const sp500Return = sp500_comparison?.current_return || 0;
  const outperforming = return_percentage > sp500Return;

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const portfolioReturn = data.portfolio_return || 0;
      const sp500Return = data.sp500_return || 0;
      const portfolioPositive = portfolioReturn >= 0;
      const sp500Positive = sp500Return >= 0;

      return (
        <div className="bg-white border border-gray-300 rounded-lg p-3 shadow-lg">
          <p className="text-xs text-gray-600 mb-2">{data.date}</p>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-gray-600">Portfolio:</span>
              <span className={`text-sm font-bold ${portfolioPositive ? 'text-cyan-600' : 'text-red-600'}`}>
                {portfolioPositive ? '+' : ''}{portfolioReturn.toFixed(2)}%
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-gray-600">S&P 500:</span>
              <span className={`text-sm font-bold ${sp500Positive ? 'text-blue-600' : 'text-orange-600'}`}>
                {sp500Positive ? '+' : ''}{sp500Return.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900 mb-3">Historical Performance</h3>
          
          {/* All metrics in one line */}
          <div className="flex items-center gap-6">
            {/* Portfolio Return */}
            <div className="flex flex-col">
              <span className="text-xs text-gray-600 mb-1">Your Portfolio</span>
              <div className={`flex items-center gap-2 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                <span className="text-2xl font-bold">
                  {isPositive ? '+' : ''}{return_percentage.toFixed(2)}%
                </span>
              </div>
            </div>

            {/* Divider */}
            <div className="h-12 w-px bg-gray-300"></div>

            {/* S&P 500 Return */}
            {sp500_comparison && (
              <>
                <div className="flex flex-col">
                  <span className="text-xs text-gray-600 mb-1">S&P 500</span>
                  <div className={`flex items-center gap-2 ${sp500Return >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
                    {sp500Return >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                    <span className="text-2xl font-bold">
                      {sp500Return >= 0 ? '+' : ''}{sp500Return.toFixed(2)}%
                    </span>
                  </div>
                </div>

                {/* Divider */}
                <div className="h-12 w-px bg-gray-300"></div>

                {/* Outperformance */}
                <div className="flex flex-col">
                  <span className="text-xs text-gray-600 mb-1">{outperforming ? 'Outperforming' : 'Underperforming'}</span>
                  <div className={`flex items-center gap-2 ${outperforming ? 'text-green-600' : 'text-red-600'}`}>
                    <span className="text-2xl font-bold">
                      {outperforming ? '↑' : '↓'} {Math.abs(return_percentage - sp500Return).toFixed(2)}%
                    </span>
                  </div>
                </div>
              </>
            )}

            {/* Period Label */}
            <div className="flex items-center gap-2 ml-auto">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">
                {TIME_PERIODS.find(p => p.value === selectedPeriod)?.label}
              </span>
            </div>
          </div>
        </div>

        {/* Time Period Selector */}
        <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
          {TIME_PERIODS.map((period) => (
            <button
              key={period.value}
              onClick={() => setSelectedPeriod(period.value)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-all ${
                selectedPeriod === period.value
                  ? 'bg-white text-cyan-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>

      {/* Period Returns Summary */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">6 Months</div>
          <div className={`text-lg font-bold ${
            (period_stats['6m_return'] || 0) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {period_stats['6m_return'] !== null && period_stats['6m_return'] !== undefined
              ? `${period_stats['6m_return'] >= 0 ? '+' : ''}${period_stats['6m_return'].toFixed(2)}%`
              : 'N/A'}
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">1 Year</div>
          <div className={`text-lg font-bold ${
            (period_stats['1y_return'] || 0) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {period_stats['1y_return'] !== null && period_stats['1y_return'] !== undefined
              ? `${period_stats['1y_return'] >= 0 ? '+' : ''}${period_stats['1y_return'].toFixed(2)}%`
              : 'N/A'}
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">3 Years</div>
          <div className={`text-lg font-bold ${
            (period_stats['3y_return'] || 0) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {period_stats['3y_return'] !== null && period_stats['3y_return'] !== undefined
              ? `${period_stats['3y_return'] >= 0 ? '+' : ''}${period_stats['3y_return'].toFixed(2)}%`
              : 'N/A'}
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">5 Years</div>
          <div className={`text-lg font-bold ${
            (period_stats['5y_return'] || 0) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {period_stats['5y_return'] !== null && period_stats['5y_return'] !== undefined
              ? `${period_stats['5y_return'] >= 0 ? '+' : ''}${period_stats['5y_return'].toFixed(2)}%`
              : 'N/A'}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={merged_time_series} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getFullYear().toString().slice(2)}`;
              }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `${value}%`}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
              iconType="line"
            />
            <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="portfolio_return"
              name="Your Portfolio"
              stroke="#0891b2"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="sp500_return"
              name="S&P 500"
              stroke="#3b82f6"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Info Note */}
      <div className="mt-4 text-xs text-gray-500 flex items-start gap-2">
        <Calendar className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <p>
          Historical returns are calculated based on your portfolio allocations and actual stock price movements compared to S&P 500 index performance. 
          Chart shows percentage returns starting from 0% at the beginning of the selected period.
        </p>
      </div>
    </div>
  );
}
