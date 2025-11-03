import { useState, useEffect } from "react";
import { ExternalLink, Calendar, TrendingUp } from "lucide-react";
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
      <div className="glass-card rounded-3xl p-8 text-center border border-purple-500/30" data-testid="no-news">
        <p className="text-gray-400">No news available. Add stocks to your portfolio to see related news.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="news-tab">
      {news.map((item, idx) => (
        <div
          key={idx}
          data-testid="news-card"
          className="glass-card rounded-3xl p-6 neon-glow border border-purple-500/30 hover-lift group stagger-item"
        >
          <div className="flex gap-6">
            {item.image && (
              <div className="relative overflow-hidden rounded-2xl flex-shrink-0 w-40 h-40">
                <img
                  src={item.image}
                  alt={item.headline}
                  className="w-full h-full object-cover group-hover:scale-110 smooth-transition"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-purple-900/50 to-transparent"></div>
              </div>
            )}
            <div className="flex-1">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <span className="inline-block px-4 py-1.5 text-xs font-bold bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full mb-3 neon-glow">
                    {item.ticker}
                  </span>
                  <h3 className="text-xl font-bold text-white mb-2 group-hover:gradient-text smooth-transition">
                    {item.headline}
                  </h3>
                </div>
              </div>
              
              {item.summary && (
                <p className="text-sm text-gray-300 mb-4 line-clamp-2 leading-relaxed">
                  {item.summary}
                </p>
              )}
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-teal-400" />
                    {formatDate(item.datetime)}
                  </span>
                  {item.source && (
                    <span className="flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
                      {item.source}
                    </span>
                  )}
                </div>
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 text-white px-5 py-2 rounded-full smooth-transition hover-lift"
                  >
                    Read more
                    <ExternalLink className="w-4 h-4" />
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