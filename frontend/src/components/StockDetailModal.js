import { useState, useEffect } from "react";
import { X, TrendingUp, TrendingDown, Calendar, DollarSign, Newspaper, BarChart3 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { toast } from "sonner";
import InfoTooltip from "./InfoTooltip";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function StockDetailModal({ symbol, holding, isOpen, onClose }) {
  const [assetData, setAssetData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isOpen && symbol) {
      loadAssetData();
    }
  }, [isOpen, symbol]);

  const loadAssetData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API}/data/asset/${symbol}`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setAssetData(data);
      } else {
        toast.error("Failed to load stock details");
      }
    } catch (error) {
      console.error("Error loading asset data:", error);
      toast.error("Failed to load stock details");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const currentPrice = assetData?.live?.currentPrice?.price || holding?.current_price || 0;
  const change = assetData?.live?.currentPrice?.change || 0;
  const changePercent = assetData?.live?.currentPrice?.changePercent || 0;
  const isPositive = changePercent >= 0;

  // Prepare chart data from monthly prices
  const chartData = assetData?.historical?.priceHistory?.monthlyPrices?.slice(-12).map(item => ({
    month: item.month,
    price: item.close
  })) || [];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-gray-900">{symbol}</h2>
              <span className="px-3 py-1 bg-cyan-100 text-cyan-700 rounded-full text-sm font-medium">
                {assetData?.assetType || "Stock"}
              </span>
            </div>
            <p className="text-gray-600 mt-1">{assetData?.name || "Loading..."}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="p-6 space-y-6">
            {/* Current Price & Your Position */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Current Market Price */}
              <div className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-xl p-6">
                <div className="text-sm text-gray-600 mb-2">Current Market Price</div>
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  ${currentPrice.toFixed(2)}
                </div>
                <div className={`flex items-center gap-2 text-lg font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                  {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                  {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
                </div>
              </div>

              {/* Your Position */}
              {holding && (
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6">
                  <div className="text-sm text-gray-600 mb-2">Your Position</div>
                  <div className="text-3xl font-bold text-gray-900 mb-2">
                    ${holding.total_value?.toFixed(2) || 0}
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Shares:</span>
                      <span className="font-semibold">{holding.quantity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Avg Cost:</span>
                      <span className="font-semibold">${holding.purchase_price?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Gain/Loss:</span>
                      <span className={`font-semibold ${holding.unrealized_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${holding.unrealized_gain_loss?.toFixed(2)} ({holding.unrealized_gain_loss_percentage?.toFixed(2)}%)
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Price Chart */}
            {chartData.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart3 className="w-5 h-5 text-cyan-600" />
                  <h3 className="text-lg font-bold text-gray-900">12-Month Price History</h3>
                </div>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => value.split('-')[1]} // Show only month
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }}
                      domain={['auto', 'auto']}
                    />
                    <Tooltip 
                      formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
                      labelFormatter={(label) => `Month: ${label}`}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="price" 
                      stroke="#06b6d4" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-xs text-gray-600 mb-1">52W High</div>
                <div className="text-lg font-bold text-gray-900">
                  ${assetData?.live?.currentPrice?.fiftyTwoWeekHigh?.toFixed(2) || 'N/A'}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-xs text-gray-600 mb-1">52W Low</div>
                <div className="text-lg font-bold text-gray-900">
                  ${assetData?.live?.currentPrice?.fiftyTwoWeekLow?.toFixed(2) || 'N/A'}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-xs text-gray-600 mb-1">1Y Return</div>
                <div className="text-lg font-bold text-gray-900">
                  {assetData?.historical?.priceHistory?.oneYearReturn?.toFixed(2) || 0}%
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-xs text-gray-600 mb-1">3Y Return</div>
                <div className="text-lg font-bold text-gray-900">
                  {assetData?.historical?.priceHistory?.threeYearReturn?.toFixed(2) || 0}%
                </div>
              </div>
            </div>

            {/* Asset-Type Specific Information */}
            {assetData?.fundamentals && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                {/* For Regular Stocks - Show Company Info */}
                {assetData.assetType === 'stock' && assetData.fundamentals.employees && (
                  <>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Company Information</h3>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-gray-600">Sector</div>
                        <div className="font-semibold text-gray-900">{assetData.fundamentals.sector || 'N/A'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Industry</div>
                        <div className="font-semibold text-gray-900">{assetData.fundamentals.industry || 'N/A'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Market Cap</div>
                        <div className="font-semibold text-gray-900">
                          {assetData.fundamentals.marketCap ? `$${(assetData.fundamentals.marketCap / 1e9).toFixed(2)}B` : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Employees</div>
                        <div className="font-semibold text-gray-900">
                          {assetData.fundamentals.employees?.toLocaleString() || 'N/A'}
                        </div>
                      </div>
                    </div>
                    {assetData.fundamentals.description && (
                      <div>
                        <div className="text-sm text-gray-600 mb-2">About</div>
                        <p className="text-sm text-gray-700 leading-relaxed">
                          {assetData.fundamentals.description.slice(0, 300)}...
                        </p>
                      </div>
                    )}
                  </>
                )}

                {/* For ETFs/Index Funds - Show Fund Info */}
                {(assetData.assetType === 'etf' || assetData.assetType === 'fund' || assetData.assetType === 'bond' || !assetData.fundamentals.employees) && (
                  <>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      {assetData.assetType === 'bond' ? 'Bond Fund Information' : 
                       assetData.assetType === 'etf' ? 'ETF Information' : 
                       'Fund Information'}
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-gray-600">Type</div>
                        <div className="font-semibold text-gray-900">
                          {assetData.fundamentals.quoteType === 'ETF' ? 'ETF' :
                           assetData.fundamentals.quoteType === 'MUTUALFUND' ? 'Mutual Fund' :
                           assetData.fundamentals.category || 
                           assetData.assetType?.toUpperCase() || 'Fund'}
                        </div>
                      </div>
                      
                      {assetData.fundamentals.fundFamily && (
                        <div>
                          <div className="text-sm text-gray-600">Fund Family</div>
                          <div className="font-semibold text-gray-900">
                            {assetData.fundamentals.fundFamily}
                          </div>
                        </div>
                      )}
                      
                      <div>
                        <div className="text-sm text-gray-600 flex items-center">
                          Total Assets (AUM)
                          <InfoTooltip text="Assets Under Management (AUM) - the total market value of all investments in the fund. Larger funds tend to be more stable and liquid." />
                        </div>
                        <div className="font-semibold text-gray-900">
                          {assetData.fundamentals.totalAssets && assetData.fundamentals.totalAssets > 0
                            ? `$${(assetData.fundamentals.totalAssets / 1e9).toFixed(2)}B` 
                            : assetData.fundamentals.marketCap && assetData.fundamentals.marketCap > 0
                            ? `$${(assetData.fundamentals.marketCap / 1e9).toFixed(2)}B`
                            : 'N/A'}
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-sm text-gray-600 flex items-center">
                          Expense Ratio
                          <InfoTooltip text="Annual fee charged by the fund as a percentage of your investment. For example, 0.20% means you pay $2 per year for every $1,000 invested. Lower is better." />
                        </div>
                        <div className="font-semibold text-gray-900">
                          {assetData.fundamentals.expenseRatio && assetData.fundamentals.expenseRatio > 0
                            ? `${(assetData.fundamentals.expenseRatio * 100).toFixed(2)}%` 
                            : 'N/A'}
                        </div>
                      </div>
                      
                      {assetData.fundamentals.yield && assetData.fundamentals.yield > 0 && (
                        <div>
                          <div className="text-sm text-gray-600 flex items-center">
                            Dividend Yield
                            <InfoTooltip text="Annual dividend income as a percentage of the current price. Calculated as (Annual Dividend / Current Price) × 100." />
                          </div>
                          <div className="font-semibold text-gray-900">
                            {(assetData.fundamentals.yield * 100).toFixed(2)}%
                          </div>
                        </div>
                      )}
                      
                      {assetData.fundamentals.ytdReturn && assetData.fundamentals.ytdReturn !== 0 && (
                        <div>
                          <div className="text-sm text-gray-600">YTD Return</div>
                          <div className={`font-semibold ${assetData.fundamentals.ytdReturn > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {assetData.fundamentals.ytdReturn > 0 ? '+' : ''}{(assetData.fundamentals.ytdReturn * 100).toFixed(2)}%
                          </div>
                        </div>
                      )}
                      
                      {assetData.fundamentals.threeYearAverageReturn && assetData.fundamentals.threeYearAverageReturn !== 0 && (
                        <div>
                          <div className="text-sm text-gray-600">3-Year Avg Return</div>
                          <div className={`font-semibold ${assetData.fundamentals.threeYearAverageReturn > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {assetData.fundamentals.threeYearAverageReturn > 0 ? '+' : ''}{(assetData.fundamentals.threeYearAverageReturn * 100).toFixed(2)}%
                          </div>
                        </div>
                      )}
                      
                      {assetData.fundamentals.fiveYearAverageReturn && assetData.fundamentals.fiveYearAverageReturn !== 0 && (
                        <div>
                          <div className="text-sm text-gray-600">5-Year Avg Return</div>
                          <div className={`font-semibold ${assetData.fundamentals.fiveYearAverageReturn > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {assetData.fundamentals.fiveYearAverageReturn > 0 ? '+' : ''}{(assetData.fundamentals.fiveYearAverageReturn * 100).toFixed(2)}%
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {assetData.fundamentals.longBusinessSummary && (
                      <div className="mb-4">
                        <div className="text-sm text-gray-600 mb-2">About This Fund</div>
                        <p className="text-sm text-gray-700 leading-relaxed">
                          {assetData.fundamentals.longBusinessSummary?.slice(0, 500) || assetData.fundamentals.description?.slice(0, 500)}
                          {(assetData.fundamentals.longBusinessSummary?.length > 500 || assetData.fundamentals.description?.length > 500) && '...'}
                        </p>
                      </div>
                    )}
                    
                    {/* Top Holdings */}
                    {assetData.fundamentals.topHoldings && assetData.fundamentals.topHoldings.length > 0 && (
                      <div className="mt-4">
                        <div className="text-sm text-gray-600 mb-3 font-semibold">Top Holdings</div>
                        <div className="space-y-2">
                          {assetData.fundamentals.topHoldings.map((holding, idx) => (
                            <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                              <div>
                                <div className="font-semibold text-gray-900 text-sm">{holding.symbol || holding.name}</div>
                                {holding.name && holding.symbol && (
                                  <div className="text-xs text-gray-600">{holding.name}</div>
                                )}
                              </div>
                              <div className="font-semibold text-cyan-600">
                                {(holding.percentage * 100).toFixed(2)}%
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Recent News */}
            {assetData?.live?.recentNews && assetData.live.recentNews.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Newspaper className="w-5 h-5 text-cyan-600" />
                  <h3 className="text-lg font-bold text-gray-900">Recent News</h3>
                </div>
                <div className="space-y-4">
                  {assetData.live.recentNews.slice(0, 5).map((news, idx) => (
                    <div key={idx} className="border-b border-gray-100 pb-4 last:border-b-0">
                      <a 
                        href={news.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-gray-900 font-semibold hover:text-cyan-600 transition-colors"
                      >
                        {news.title || news.headline}
                      </a>
                      <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                        <span>{news.source}</span>
                        <span>•</span>
                        <span>{new Date(news.timestamp || news.datetime).toLocaleDateString()}</span>
                        {news.sentiment && (
                          <>
                            <span>•</span>
                            <span className={`px-2 py-0.5 rounded ${
                              news.sentiment === 'positive' ? 'bg-green-100 text-green-700' :
                              news.sentiment === 'negative' ? 'bg-red-100 text-red-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {news.sentiment}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upcoming Events */}
            {assetData?.live?.upcomingEvents && assetData.live.upcomingEvents.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Calendar className="w-5 h-5 text-cyan-600" />
                  <h3 className="text-lg font-bold text-gray-900">Upcoming Events</h3>
                </div>
                <div className="space-y-3">
                  {assetData.live.upcomingEvents.map((event, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <div className="text-sm font-semibold text-cyan-600 min-w-[80px]">
                        {new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{event.title}</div>
                        {event.description && (
                          <div className="text-sm text-gray-600 mt-1">{event.description}</div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">Impact: {event.impact}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 p-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
