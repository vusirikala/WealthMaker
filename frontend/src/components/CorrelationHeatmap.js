import { useState, useEffect } from "react";
import { toast } from "sonner";
import InfoTooltip from "./InfoTooltip";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CorrelationHeatmap({ portfolioId }) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (portfolioId) {
      loadCorrelations();
    }
  }, [portfolioId]);

  const loadCorrelations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${API}/portfolios-v2/${portfolioId}/correlations`,
        {
          credentials: "include",
        }
      );

      if (response.ok) {
        const result = await response.json();
        setData(result);
      } else {
        toast.error("Failed to load correlations");
      }
    } catch (error) {
      console.error("Error loading correlations:", error);
      toast.error("Failed to load correlations");
    } finally {
      setIsLoading(false);
    }
  };

  const getColor = (value) => {
    // Value is between -1 and 1
    // -1 (uncorrelated/inverse) = green
    // 0 (no correlation) = yellow
    // 1 (highly correlated) = red
    
    if (value === 1) return "bg-gray-300"; // Diagonal (self-correlation)
    
    const absValue = Math.abs(value);
    
    if (absValue < 0.3) {
      // Low correlation - green (good diversification)
      return "bg-green-500";
    } else if (absValue < 0.5) {
      // Moderate correlation - yellow
      return "bg-yellow-500";
    } else if (absValue < 0.7) {
      // High correlation - orange
      return "bg-orange-500";
    } else {
      // Very high correlation - red (poor diversification)
      return "bg-red-500";
    }
  };

  const getTextColor = (value) => {
    if (value === 1) return "text-gray-700";
    const absValue = Math.abs(value);
    return absValue > 0.3 ? "text-white" : "text-gray-900";
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

  if (!data || !data.correlations || data.correlations.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-2">Correlation Heatmap</h3>
        <p className="text-sm text-gray-500">Need at least 2 stocks for correlation analysis</p>
      </div>
    );
  }

  const { correlations, tickers } = data;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">🔗 Correlation Heatmap</h3>
      
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Header Row */}
          <div className="flex">
            <div className="w-16"></div>
            {tickers.map((ticker) => (
              <div key={ticker} className="w-16 text-center">
                <span className="text-xs font-semibold text-gray-700">{ticker}</span>
              </div>
            ))}
          </div>

          {/* Heatmap Rows */}
          {correlations.map((row, i) => (
            <div key={i} className="flex items-center mt-1">
              <div className="w-16 text-right pr-2">
                <span className="text-xs font-semibold text-gray-700">{tickers[i]}</span>
              </div>
              {row.map((value, j) => (
                <div
                  key={j}
                  className={`w-16 h-12 flex items-center justify-center ${getColor(value)} transition-all hover:scale-110 cursor-pointer`}
                  title={`${tickers[i]} vs ${tickers[j]}: ${value.toFixed(2)}`}
                >
                  <span className={`text-xs font-bold ${getTextColor(value)}`}>
                    {value.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-gray-600">Low (&lt;0.3) - Good diversification</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 rounded"></div>
            <span className="text-gray-600">Moderate (0.3-0.5)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-500 rounded"></div>
            <span className="text-gray-600">High (0.5-0.7)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className="text-gray-600">Very High (&gt;0.7) - Poor diversification</span>
          </div>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          Correlation shows how stocks move together. Lower values (green) indicate better diversification.
        </p>
      </div>
    </div>
  );
}
