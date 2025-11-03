import { useState, useEffect } from "react";
import { ExternalLink, Calendar } from "lucide-react";
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
        <div className="text-slate-600">Loading news...</div>
      </div>
    );
  }

  if (news.length === 0) {
    return (
      <div className="glass rounded-2xl p-8 text-center" data-testid="no-news">
        <p className="text-slate-600">No news available. Add stocks to your portfolio to see related news.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="news-tab">
      {news.map((item, idx) => (
        <div
          key={idx}
          data-testid="news-card"
          className="glass rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all"
        >
          <div className="flex gap-4">
            {item.image && (
              <img
                src={item.image}
                alt={item.headline}
                className="w-32 h-32 object-cover rounded-lg flex-shrink-0"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
            <div className="flex-1">
              <div className="flex items-start justify-between gap-4 mb-2">
                <div>
                  <span className="inline-block px-3 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full mb-2">
                    {item.ticker}
                  </span>
                  <h3 className="text-lg font-semibold text-slate-800 mb-2">
                    {item.headline}
                  </h3>
                </div>
              </div>
              
              {item.summary && (
                <p className="text-sm text-slate-600 mb-3 line-clamp-2">
                  {item.summary}
                </p>
              )}
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {formatDate(item.datetime)}
                  </span>
                  {item.source && (
                    <span>{item.source}</span>
                  )}
                </div>
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium"
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