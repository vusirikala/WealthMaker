import { useState, useEffect } from "react";
import { Eye, Plus, Trash2, TrendingUp, TrendingDown } from "lucide-react";
import { toast } from "sonner";
import AddStockModal from "./AddStockModal";
import StockDetailModal from "./StockDetailModal";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function WatchlistTab() {
  const [watchlist, setWatchlist] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [showStockDetail, setShowStockDetail] = useState(false);

  useEffect(() => {
    loadWatchlist();
    
    // Listen for watchlist updates
    const handleUpdate = () => loadWatchlist();
    window.addEventListener('watchlistUpdated', handleUpdate);
    
    return () => window.removeEventListener('watchlistUpdated', handleUpdate);
  }, []);

  const loadWatchlist = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API}/data/watchlist`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        // Convert to array format
        const watchlistArray = data.symbols.map(symbol => ({
          symbol,
          ...data.data[symbol]
        }));
        setWatchlist(watchlistArray);
      }
    } catch (error) {
      console.error("Failed to load watchlist:", error);
      toast.error("Failed to load watchlist");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToWatchlist = async (symbol) => {
    try {
      const response = await fetch(`${API}/data/watchlist/add?symbol=${symbol}`, {
        method: "POST",
        credentials: "include",
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(`Added ${symbol} to watchlist!`);
        loadWatchlist();
      } else {
        toast.error(data.detail || "Failed to add to watchlist");
      }
    } catch (error) {
      console.error("Error adding to watchlist:", error);
      toast.error("Failed to add to watchlist");
    }
  };

  const handleRemove = async (symbol) => {
    try {
      const response = await fetch(`${API}/data/watchlist/${symbol}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.ok) {
        toast.success(`Removed ${symbol} from watchlist`);
        loadWatchlist();
      } else {
        toast.error("Failed to remove from watchlist");
      }
    } catch (error) {
      console.error("Error removing from watchlist:", error);
      toast.error("Failed to remove from watchlist");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="w-16 h-16 spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Eye className="w-7 h-7 text-cyan-600" />
            Watchlist
          </h2>
          <p className="text-gray-600 mt-1">Track stocks you're interested in without owning them</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white rounded-lg transition-all shadow-md flex items-center gap-2 font-medium"
        >
          <Plus className="w-5 h-5" />
          Add to Watchlist
        </button>
      </div>

      {/* Empty State */}
      {watchlist.length === 0 && (
        <div className="clean-card rounded-2xl p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-2xl flex items-center justify-center">
            <Eye className="w-8 h-8 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Your Watchlist is Empty</h3>
          <p className="text-gray-600 mb-4">
            Add stocks to follow their price movements, news, and performance
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white rounded-lg transition-all font-medium inline-flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Your First Stock
          </button>
        </div>
      )}

      {/* Watchlist Grid */}
      {watchlist.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {watchlist.map((stock) => {
            const currentPrice = stock.live?.currentPrice?.price || 0;
            const change = stock.live?.currentPrice?.change || 0;
            const changePercent = stock.live?.currentPrice?.changePercent || 0;
            const isPositive = changePercent >= 0;

            return (
              <div
                key={stock.symbol}
                className="clean-card p-6 card-hover group cursor-pointer"
                onClick={() => {
                  setSelectedStock(stock.symbol);
                  setShowStockDetail(true);
                }}
              >
                {/* Header with Remove Button */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900 group-hover:text-cyan-600 transition-colors">
                      {stock.symbol}
                    </h3>
                    <p className="text-sm text-gray-600 line-clamp-1">{stock.name}</p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemove(stock.symbol);
                    }}
                    className="p-2 hover:bg-red-50 rounded-lg transition-colors group/btn"
                  >
                    <Trash2 className="w-4 h-4 text-gray-400 group-hover/btn:text-red-600" />
                  </button>
                </div>

                {/* Price */}
                <div className="mb-4">
                  <div className="text-2xl font-bold text-gray-900">
                    ${currentPrice.toFixed(2)}
                  </div>
                  <div className={`flex items-center gap-1 text-sm font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                    {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-2 gap-3 pt-4 border-t border-gray-100">
                  <div>
                    <div className="text-xs text-gray-500">52W High</div>
                    <div className="text-sm font-semibold text-gray-900">
                      ${stock.live?.currentPrice?.fiftyTwoWeekHigh?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">52W Low</div>
                    <div className="text-sm font-semibold text-gray-900">
                      ${stock.live?.currentPrice?.fiftyTwoWeekLow?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Sector Badge */}
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <span className="px-2 py-1 bg-cyan-100 text-cyan-700 text-xs font-medium rounded">
                    {stock.fundamentals?.sector || 'Unknown'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add to Watchlist Modal (reusing AddStockModal with custom handler) */}
      <AddStockModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={(data) => {
          // Override default behavior - add to watchlist instead of portfolio
          const symbol = data?.symbol;
          if (symbol) {
            handleAddToWatchlist(symbol);
          }
          setShowAddModal(false);
        }}
        isWatchlistMode={true}
      />

      {/* Stock Detail Modal */}
      <StockDetailModal
        symbol={selectedStock}
        holding={null} // No holding data for watchlist
        isOpen={showStockDetail}
        onClose={() => {
          setShowStockDetail(false);
          setSelectedStock(null);
        }}
      />
    </div>
  );
}
