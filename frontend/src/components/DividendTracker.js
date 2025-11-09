import { useState, useEffect } from "react";
import { DollarSign, TrendingUp, Calendar } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DividendTracker({ portfolioId }) {
  const [dividendData, setDividendData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (portfolioId) {
      loadDividendData();
    }
  }, [portfolioId]);

  const loadDividendData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${API}/portfolios-v2/${portfolioId}/dividends`,
        {
          credentials: "include",
        }
      );

      if (response.ok) {
        const data = await response.json();
        setDividendData(data);
      } else {
        toast.error("Failed to load dividend data");
      }
    } catch (error) {
      console.error("Error loading dividend data:", error);
      toast.error("Failed to load dividend data");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!dividendData) {
    return null;
  }

  const { total_annual_income, monthly_income, dividend_yield, dividend_stocks } = dividendData;

  const hasDividends = dividend_stocks && dividend_stocks.length > 0;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">💰 Dividend & Income Tracking</h3>
      
      {!hasDividends ? (
        <div className="text-center py-8">
          <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-500">No dividend-paying stocks in portfolio</p>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-5 h-5 text-green-600" />
                <span className="text-sm font-semibold text-gray-700">Annual Income</span>
              </div>
              <div className="text-2xl font-bold text-green-700">
                ${total_annual_income?.toLocaleString() || '0'}
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-semibold text-gray-700">Monthly Income</span>
              </div>
              <div className="text-2xl font-bold text-blue-700">
                ${monthly_income?.toLocaleString() || '0'}
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-semibold text-gray-700">Portfolio Yield</span>
              </div>
              <div className="text-2xl font-bold text-purple-700">
                {dividend_yield?.toFixed(2) || '0'}%
              </div>
            </div>
          </div>

          {/* Dividend Stocks Table */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Dividend-Paying Holdings</h4>
            <div className="space-y-2">
              {dividend_stocks.map((stock, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1">
                    <div className="font-bold text-gray-900">{stock.ticker}</div>
                    {stock.shares && (
                      <div className="text-xs text-gray-600">
                        {stock.shares.toFixed(2)} shares × ${stock.dividend_per_share}/share
                      </div>
                    )}
                  </div>
                  
                  <div className="text-right">
                    {stock.annual_income ? (
                      <>
                        <div className="font-bold text-green-600">
                          ${stock.annual_income.toLocaleString()}/year
                        </div>
                        <div className="text-xs text-gray-600">
                          {stock.yield?.toFixed(2)}% yield
                        </div>
                      </>
                    ) : (
                      <div className="text-sm text-gray-600">
                        {stock.yield?.toFixed(2)}% yield · {stock.allocation}% allocation
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Info Note */}
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-blue-900">
              <strong>Note:</strong> Dividend income is based on current dividend rates. 
              {!total_annual_income && " Invest in the portfolio to see actual dividend income projections."}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
