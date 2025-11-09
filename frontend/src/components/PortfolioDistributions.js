import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { toast } from "sonner";
import InfoTooltip from "./InfoTooltip";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GEO_COLORS = {
  'US': '#06b6d4',
  'International Developed': '#10b981',
  'Emerging Markets': '#f59e0b',
  'Unknown': '#9ca3af'
};

const CAP_COLORS = {
  'Mega Cap': '#8b5cf6',
  'Large Cap': '#06b6d4',
  'Mid Cap': '#10b981',
  'Small Cap': '#f59e0b',
  'Unknown': '#9ca3af'
};

export default function PortfolioDistributions({ portfolioId }) {
  const [distributions, setDistributions] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (portfolioId) {
      loadDistributions();
    }
  }, [portfolioId]);

  const loadDistributions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${API}/portfolios-v2/${portfolioId}/distributions`,
        {
          credentials: "include",
        }
      );

      if (response.ok) {
        const data = await response.json();
        setDistributions(data);
      } else {
        toast.error("Failed to load distributions");
      }
    } catch (error) {
      console.error("Error loading distributions:", error);
      toast.error("Failed to load distributions");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-6">
        {[1, 2].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!distributions || (distributions.geography?.length === 0 && distributions.market_cap?.length === 0)) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-2">Portfolio Distributions</h3>
        <p className="text-sm text-gray-500">No allocation data available</p>
      </div>
    );
  }

  const { geography, market_cap } = distributions;

  // Prepare data with colors
  const geoData = geography?.map(item => ({
    ...item,
    color: GEO_COLORS[item.name] || '#9ca3af'
  })) || [];

  const capData = market_cap?.map(item => ({
    ...item,
    color: CAP_COLORS[item.name] || '#9ca3af'
  })) || [];

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Geographic Distribution */}
      {geoData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">🌍 Geographic Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={geoData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {geoData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">
              Shows geographic exposure. Diversification across regions reduces country-specific risks.
            </p>
          </div>
        </div>
      )}

      {/* Market Cap Distribution */}
      {capData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">💼 Market Cap Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={capData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {capData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">
              <strong>Mega Cap:</strong> $200B+, <strong>Large Cap:</strong> $10-200B, 
              <strong> Mid Cap:</strong> $2-10B, <strong>Small Cap:</strong> &lt;$2B
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
