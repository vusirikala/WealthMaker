import { useState, useEffect } from "react";
import { Plus, TrendingUp, Briefcase, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function PortfolioSidebar({ selectedPortfolioId, onSelectPortfolio, onAddPortfolio }) {
  const [portfolios, setPortfolios] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      const response = await fetch(`${API}/portfolios-v2/list`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setPortfolios(data.portfolios || []);
        
        // Auto-select first portfolio if none selected
        if (!selectedPortfolioId && data.portfolios.length > 0) {
          onSelectPortfolio(data.portfolios[0].portfolio_id);
        }
      } else {
        toast.error("Failed to load portfolios");
      }
    } catch (error) {
      console.error("Error loading portfolios:", error);
      toast.error("Failed to load portfolios");
    } finally {
      setIsLoading(false);
    }
  };

  const getPortfolioIcon = (type) => {
    if (type === 'ai') return <Briefcase className="w-4 h-4" />;
    return <Target className="w-4 h-4" />;
  };

  if (isLoading) {
    return (
      <div className="w-64 bg-white border-r border-gray-200 p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <Button
          onClick={onAddPortfolio}
          className="w-full bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white rounded-lg shadow-md"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Portfolio
        </Button>
      </div>

      {/* Portfolio List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {portfolios.length === 0 ? (
          <div className="text-center py-8 px-4">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-cyan-100 to-emerald-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-gray-700 mb-2">No Portfolios Yet</p>
            <p className="text-xs text-gray-500 leading-relaxed mb-4">
              Start building your investment portfolio by clicking the button above.
            </p>
            <div className="bg-gradient-to-r from-cyan-50 to-emerald-50 rounded-lg p-3 border border-cyan-200">
              <p className="text-xs text-gray-600">
                <span className="font-semibold text-cyan-700">Tip:</span> You can create multiple portfolios to track different investment strategies!
              </p>
            </div>
          </div>
        ) : (
          portfolios.map((portfolio) => (
            <div
              key={portfolio.portfolio_id}
              onClick={() => onSelectPortfolio(portfolio.portfolio_id)}
              className={`p-4 rounded-lg cursor-pointer transition-all ${
                selectedPortfolioId === portfolio.portfolio_id
                  ? "bg-gradient-to-r from-cyan-50 to-emerald-50 border-2 border-cyan-500 shadow-sm"
                  : "bg-gray-50 hover:bg-gray-100 border-2 border-transparent"
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getPortfolioIcon(portfolio.type)}
                  <span className="font-semibold text-gray-900 text-sm">
                    {portfolio.name}
                  </span>
                </div>
                {portfolio.type === 'ai' && (
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                    AI
                  </span>
                )}
              </div>
              
              {portfolio.goal && (
                <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                  {portfolio.goal}
                </p>
              )}
              
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">
                  {portfolio.allocations?.length || 0} assets
                </span>
                {portfolio.total_invested > 0 && (
                  <div className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3 text-emerald-600" />
                    <span className={`font-semibold ${
                      portfolio.total_return >= 0 ? 'text-emerald-600' : 'text-red-600'
                    }`}>
                      {portfolio.total_return >= 0 ? '+' : ''}
                      {portfolio.total_return_percentage?.toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
