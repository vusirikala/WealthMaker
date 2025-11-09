import { useState, useEffect } from "react";
import { Plus, Eye, Trash2, TrendingUp, TrendingDown, RefreshCw, Edit2 } from "lucide-react";
import { toast } from "sonner";
import StockDetailModal from "./StockDetailModal";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MultiWatchlistDashboard() {
  const [watchlists, setWatchlists] = useState([]);
  const [selectedWatchlist, setSelectedWatchlist] = useState(null);
  const [watchlistData, setWatchlistData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddWatchlistModal, setShowAddWatchlistModal] = useState(false);
  const [showAddTickerModal, setShowAddTickerModal] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState("");
  const [newTicker, setNewTicker] = useState("");
  const [selectedStock, setSelectedStock] = useState(null);
  const [showStockDetail, setShowStockDetail] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    loadWatchlists();
  }, []);

  useEffect(() => {
    if (selectedWatchlist) {
      loadWatchlistData();
    }
  }, [selectedWatchlist]);

  const loadWatchlists = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API}/watchlists/list`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setWatchlists(data.watchlists);
        if (data.watchlists.length > 0 && !selectedWatchlist) {
          setSelectedWatchlist(data.watchlists[0].id);
        }
      }
    } catch (error) {
      console.error("Error loading watchlists:", error);
      toast.error("Failed to load watchlists");
    } finally {
      setIsLoading(false);
    }
  };

  const loadWatchlistData = async () => {
    if (!selectedWatchlist) return;

    try {
      const response = await fetch(`${API}/watchlists/${selectedWatchlist}`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setWatchlistData(data.watchlist);
      }
    } catch (error) {
      console.error("Error loading watchlist data:", error);
      toast.error("Failed to load watchlist data");
    }
  };

  const handleCreateWatchlist = async (e) => {
    e.preventDefault();
    if (!newWatchlistName.trim()) return;

    try {
      const response = await fetch(`${API}/watchlists/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name: newWatchlistName }),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success("Watchlist created!");
        setNewWatchlistName("");
        setShowAddWatchlistModal(false);
        loadWatchlists();
        setSelectedWatchlist(data.watchlist.id);
      } else {
        toast.error("Failed to create watchlist");
      }
    } catch (error) {
      console.error("Error creating watchlist:", error);
      toast.error("Failed to create watchlist");
    }
  };

  const handleAddTicker = async (e) => {
    e.preventDefault();
    if (!newTicker.trim()) return;

    try {
      const response = await fetch(
        `${API}/watchlists/${selectedWatchlist}/add-ticker`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ ticker: newTicker.toUpperCase() }),
        }
      );

      if (response.ok) {
        toast.success(`${newTicker.toUpperCase()} added!`);
        setNewTicker("");
        setShowAddTickerModal(false);
        loadWatchlistData();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to add ticker");
      }
    } catch (error) {
      console.error("Error adding ticker:", error);
      toast.error("Failed to add ticker");
    }
  };

  const handleRemoveTicker = async (ticker) => {
    if (!confirm(`Remove ${ticker} from watchlist?`)) return;

    try {
      const response = await fetch(
        `${API}/watchlists/${selectedWatchlist}/ticker/${ticker}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (response.ok) {
        toast.success(`${ticker} removed`);
        loadWatchlistData();
      } else {
        toast.error("Failed to remove ticker");
      }
    } catch (error) {
      console.error("Error removing ticker:", error);
      toast.error("Failed to remove ticker");
    }
  };

  const handleDeleteWatchlist = async () => {
    if (!confirm("Delete this watchlist?")) return;

    try {
      const response = await fetch(`${API}/watchlists/${selectedWatchlist}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.ok) {
        toast.success("Watchlist deleted");
        setSelectedWatchlist(null);
        loadWatchlists();
      } else {
        toast.error("Failed to delete watchlist");
      }
    } catch (error) {
      console.error("Error deleting watchlist:", error);
      toast.error("Failed to delete watchlist");
    }
  };

  return (
    <div className="h-full flex gap-6">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">Watchlists</h2>
          <button
            onClick={() => setShowAddWatchlistModal(true)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5 text-cyan-600" />
          </button>
        </div>

        <div className="space-y-2">
          {watchlists.map((watchlist) => (
            <button
              key={watchlist.id}
              onClick={() => setSelectedWatchlist(watchlist.id)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                selectedWatchlist === watchlist.id
                  ? "bg-gradient-to-r from-cyan-500 to-emerald-500 text-white"
                  : "hover:bg-gray-50 text-gray-700"
              }`}
            >
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4" />
                <span className="font-medium">{watchlist.name}</span>
              </div>
              <div className="text-xs opacity-75 mt-1">
                {watchlist.ticker_count} stocks
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 bg-white rounded-xl border border-gray-200 p-6 overflow-auto">
        {!selectedWatchlist ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Eye className="w-16 h-16 mb-4 text-gray-300" />
            <p>Create a watchlist to get started</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {watchlistData?.name || "Loading..."}
              </h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={loadWatchlistData}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
                <button
                  onClick={() => setShowAddTickerModal(true)}
                  className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-600 hover:to-emerald-600 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Stock
                </button>
                <button
                  onClick={handleDeleteWatchlist}
                  className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Stocks Table */}
            {watchlistData && watchlistData.tickers.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Symbol
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Name
                      </th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">
                        Price
                      </th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">
                        24h Change
                      </th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">
                        % Change
                      </th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {watchlistData.tickers.map((stock) => (
                      <tr
                        key={stock.ticker}
                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
                        onClick={() => {
                          setSelectedStock(stock.ticker);
                          setShowStockDetail(true);
                        }}
                      >
                        <td className="py-4 px-4">
                          <span className="font-bold text-gray-900">
                            {stock.ticker}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-gray-600">{stock.name}</span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className="font-semibold text-gray-900">
                            ${stock.current_price.toFixed(2)}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span
                            className={`font-semibold ${
                              stock.price_change >= 0
                                ? "text-green-600"
                                : "text-red-600"
                            }`}
                          >
                            {stock.price_change >= 0 ? "+" : ""}
                            {stock.price_change.toFixed(2)}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <div
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full font-semibold ${
                              stock.price_change_pct >= 0
                                ? "bg-green-100 text-green-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {stock.price_change_pct >= 0 ? (
                              <TrendingUp className="w-4 h-4" />
                            ) : (
                              <TrendingDown className="w-4 h-4" />
                            )}
                            {stock.price_change_pct >= 0 ? "+" : ""}
                            {stock.price_change_pct.toFixed(2)}%
                          </div>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRemoveTicker(stock.ticker);
                            }}
                            className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                <Plus className="w-16 h-16 mb-4 text-gray-300" />
                <p>No stocks in this watchlist</p>
                <button
                  onClick={() => setShowAddTickerModal(true)}
                  className="mt-4 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors"
                >
                  Add Your First Stock
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Add Watchlist Modal */}
      {showAddWatchlistModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Create New Watchlist
            </h3>
            <form onSubmit={handleCreateWatchlist}>
              <input
                type="text"
                value={newWatchlistName}
                onChange={(e) => setNewWatchlistName(e.target.value)}
                placeholder="Watchlist name (e.g., Tech Stocks)"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent mb-4"
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddWatchlistModal(false);
                    setNewWatchlistName("");
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-600 hover:to-emerald-600 text-white rounded-lg transition-colors"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Ticker Modal */}
      {showAddTickerModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Add Stock to Watchlist
            </h3>
            <form onSubmit={handleAddTicker}>
              <input
                type="text"
                value={newTicker}
                onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
                placeholder="Ticker symbol (e.g., AAPL)"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent mb-4"
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddTickerModal(false);
                    setNewTicker("");
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-600 hover:to-emerald-600 text-white rounded-lg transition-colors"
                >
                  Add
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Stock Detail Modal */}
      <StockDetailModal
        symbol={selectedStock}
        isOpen={showStockDetail}
        onClose={() => {
          setShowStockDetail(false);
          setSelectedStock(null);
        }}
      />
    </div>
  );
}
