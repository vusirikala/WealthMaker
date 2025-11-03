import { useState, useEffect } from "react";
import { ExternalLink, Calendar, TrendingUp, Clock, Newspaper } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function NewsTab() {
  const [news, setNews] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadNews();
  }, []);

  const loadNews = async () => {
    try {
      const response = await fetch(`${API}/news`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setNews(data);
      }
    } catch (error) {
      console.error("Failed to load news:", error);
      toast.error("Failed to load news");
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (datetime) => {
    if (!datetime) return "Recently";
    const date = new Date(datetime);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return "Just now";
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="w-16 h-16 spinner"></div>
      </div>
    );
  }

  if (news.length === 0) {
    return (
      <div className="clean-card rounded-2xl p-12 text-center" data-testid="no-news">
        <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-2xl flex items-center justify-center">
          <Newspaper className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No News Available</h3>
        <p className="text-gray-600">Add stocks to your portfolio to see related news and market updates.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="news-tab">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Latest Market News</h2>
        <p className="text-gray-600">Stay updated with news for stocks in your portfolio</p>
      </div>

      {news.map((item, idx) => (
        <div
          key={idx}
          data-testid="news-card"
          className="clean-card p-6 card-hover group fade-in"
        >
          <div className="flex gap-6">
            {item.image && (
              <div className="relative overflow-hidden rounded-xl flex-shrink-0 w-48 h-32 bg-gray-100">
                <img
                  src={item.image}
                  alt={item.headline}
                  className="w-full h-full object-cover group-hover:scale-105 smooth-transition"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="inline-flex items-center px-3 py-1 text-xs font-semibold bg-gradient-to-r from-cyan-500 to-emerald-500 text-white rounded-full">
                      {item.ticker}
                    </span>
                    {item.source && (
                      <span className="text-xs text-gray-500 font-medium">{item.source}</span>
                    )}
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-cyan-600 smooth-transition line-clamp-2">
                    {item.headline}
                  </h3>
                </div>
              </div>
              
              {item.summary && (
                <p className="text-sm text-gray-600 mb-4 line-clamp-2 leading-relaxed">
                  {item.summary}
                </p>
              )}
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-cyan-600" />
                    {formatDate(item.datetime)}
                  </span>
                </div>
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-600 hover:text-cyan-700 smooth-transition group"
                  >
                    Read Article
                    <ExternalLink className="w-4 h-4 group-hover:translate-x-1 smooth-transition" />
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}