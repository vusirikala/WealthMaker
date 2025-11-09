import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, AlertTriangle, Shield, Activity, BarChart3 } from "lucide-react";
import { toast } from "sonner";
import InfoTooltip from "./InfoTooltip";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function RiskMetricsDashboard({ portfolioId }) {
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (portfolioId) {
      loadRiskMetrics();
    }
  }, [portfolioId]);

  const loadRiskMetrics = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${API}/portfolios-v2/${portfolioId}/risk-metrics`,
        {
          credentials: "include",
        }
      );

      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      } else {
        toast.error("Failed to load risk metrics");
      }
    } catch (error) {
      console.error("Error loading risk metrics:", error);
      toast.error("Failed to load risk metrics");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!metrics || (metrics.beta === null && metrics.sharpe_ratio === null)) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-2">Risk Metrics</h3>
        <p className="text-sm text-gray-500">Insufficient data to calculate risk metrics</p>
      </div>
    );
  }

  const { beta, sharpe_ratio, volatility, max_drawdown } = metrics;

  // Interpretations
  const getBetaColor = () => {
    if (beta === null) return "gray";
    if (beta < 0.8) return "green";
    if (beta <= 1.2) return "blue";
    return "red";
  };

  const getSharpeColor = () => {
    if (sharpe_ratio === null) return "gray";
    if (sharpe_ratio > 2) return "green";
    if (sharpe_ratio > 1) return "blue";
    if (sharpe_ratio > 0) return "yellow";
    return "red";
  };

  const getVolatilityColor = () => {
    if (volatility === null) return "gray";
    if (volatility < 15) return "green";
    if (volatility < 25) return "blue";
    return "red";
  };

  const getDrawdownColor = () => {
    if (max_drawdown === null) return "gray";
    if (max_drawdown > -10) return "green";
    if (max_drawdown > -20) return "blue";
    return "red";
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Risk Metrics</h3>
      
      <div className="grid grid-cols-4 gap-4">
        {/* Beta */}
        <div className={`bg-gradient-to-br from-${getBetaColor()}-50 to-${getBetaColor()}-100 rounded-lg p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <Activity className={`w-5 h-5 text-${getBetaColor()}-600`} />
            <span className="text-sm font-semibold text-gray-700">Beta</span>
          </div>
          <div className={`text-2xl font-bold text-${getBetaColor()}-700`}>
            {beta !== null ? beta.toFixed(2) : 'N/A'}
          </div>
          <p className="text-xs text-gray-600 mt-1">
            {beta === null ? 'No data' : beta < 1 ? 'Less volatile' : beta > 1 ? 'More volatile' : 'Market pace'}
          </p>
        </div>

        {/* Sharpe Ratio */}
        <div className={`bg-gradient-to-br from-${getSharpeColor()}-50 to-${getSharpeColor()}-100 rounded-lg p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className={`w-5 h-5 text-${getSharpeColor()}-600`} />
            <span className="text-sm font-semibold text-gray-700">Sharpe Ratio</span>
          </div>
          <div className={`text-2xl font-bold text-${getSharpeColor()}-700`}>
            {sharpe_ratio !== null ? sharpe_ratio.toFixed(2) : 'N/A'}
          </div>
          <p className="text-xs text-gray-600 mt-1">
            {sharpe_ratio === null ? 'No data' : sharpe_ratio > 1 ? 'Good returns' : 'Needs improvement'}
          </p>
        </div>

        {/* Volatility */}
        <div className={`bg-gradient-to-br from-${getVolatilityColor()}-50 to-${getVolatilityColor()}-100 rounded-lg p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className={`w-5 h-5 text-${getVolatilityColor()}-600`} />
            <span className="text-sm font-semibold text-gray-700">Volatility</span>
          </div>
          <div className={`text-2xl font-bold text-${getVolatilityColor()}-700`}>
            {volatility !== null ? `${volatility.toFixed(1)}%` : 'N/A'}
          </div>
          <p className="text-xs text-gray-600 mt-1">
            {volatility === null ? 'No data' : volatility < 15 ? 'Low risk' : volatility < 25 ? 'Moderate' : 'High risk'}
          </p>
        </div>

        {/* Max Drawdown */}
        <div className={`bg-gradient-to-br from-${getDrawdownColor()}-50 to-${getDrawdownColor()}-100 rounded-lg p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className={`w-5 h-5 text-${getDrawdownColor()}-600`} />
            <span className="text-sm font-semibold text-gray-700">Max Drawdown</span>
          </div>
          <div className={`text-2xl font-bold text-${getDrawdownColor()}-700`}>
            {max_drawdown !== null ? `${max_drawdown.toFixed(1)}%` : 'N/A'}
          </div>
          <p className="text-xs text-gray-600 mt-1">
            {max_drawdown === null ? 'No data' : max_drawdown > -10 ? 'Low decline' : max_drawdown > -20 ? 'Moderate' : 'High decline'}
          </p>
        </div>
      </div>

      {/* Explanations */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-xs text-gray-600">
          <strong>Beta:</strong> Measures volatility vs market. &lt;1 = less volatile, &gt;1 = more volatile. 
          <strong className="ml-3">Sharpe Ratio:</strong> Risk-adjusted returns. &gt;1 is good, &gt;2 is excellent.
          <strong className="ml-3">Volatility:</strong> Annual price fluctuation. 
          <strong className="ml-3">Max Drawdown:</strong> Largest peak-to-trough decline.
        </p>
      </div>
    </div>
  );
}
