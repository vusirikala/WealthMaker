import { useState, useEffect } from "react";
import { 
  ExternalLink, 
  Clock, 
  Newspaper,
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Briefcase,
  Building2,
  Cpu,
  Landmark,
  Shield,
  Zap,
  Globe,
  Rocket
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Icon mapping based on keywords and sectors
const getNewsIcon = (headline, ticker, index) => {
  const headlineLower = headline.toLowerCase();
  
  // Keyword-based icon selection
  if (headlineLower.includes('earnings') || headlineLower.includes('profit') || headlineLower.includes('revenue')) {
    return { icon: DollarSign, color: 'emerald' };
  }
  if (headlineLower.includes('loss') || headlineLower.includes('decline') || headlineLower.includes('down')) {
    return { icon: TrendingDown, color: 'red' };
  }
  if (headlineLower.includes('growth') || headlineLower.includes('surge') || headlineLower.includes('rally') || headlineLower.includes('gain')) {
    return { icon: TrendingUp, color: 'cyan' };
  }
  if (headlineLower.includes('technology') || headlineLower.includes('ai') || headlineLower.includes('tech') || headlineLower.includes('software')) {
    return { icon: Cpu, color: 'blue' };
  }
  if (headlineLower.includes('bank') || headlineLower.includes('financial') || headlineLower.includes('credit')) {
    return { icon: Landmark, color: 'purple' };
  }
  if (headlineLower.includes('market') || headlineLower.includes('trading') || headlineLower.includes('stock')) {
    return { icon: BarChart3, color: 'orange' };
  }
  if (headlineLower.includes('merger') || headlineLower.includes('acquisition') || headlineLower.includes('deal')) {
    return { icon: Briefcase, color: 'indigo' };
  }
  if (headlineLower.includes('launch') || headlineLower.includes('innovation') || headlineLower.includes('new')) {
    return { icon: Rocket, color: 'pink' };
  }
  if (headlineLower.includes('security') || headlineLower.includes('data') || headlineLower.includes('breach')) {
    return { icon: Shield, color: 'red' };
  }
  if (headlineLower.includes('energy') || headlineLower.includes('power') || headlineLower.includes('electric')) {
    return { icon: Zap, color: 'yellow' };
  }
  if (headlineLower.includes('global') || headlineLower.includes('international') || headlineLower.includes('worldwide')) {
    return { icon: Globe, color: 'teal' };
  }
  if (headlineLower.includes('company') || headlineLower.includes('corporate') || headlineLower.includes('business')) {
    return { icon: Building2, color: 'slate' };
  }
  
  // Fallback: rotate through icons based on index
  const fallbackIcons = [
    { icon: BarChart3, color: 'cyan' },
    { icon: TrendingUp, color: 'emerald' },
    { icon: DollarSign, color: 'blue' },
    { icon: Briefcase, color: 'indigo' },
    { icon: Cpu, color: 'purple' },
    { icon: Building2, color: 'slate' },
  ];
  
  return fallbackIcons[index % fallbackIcons.length];
};

const getIconColorClasses = (color) => {
  const colorMap = {
    cyan: 'bg-cyan-100 text-cyan-600',
    emerald: 'bg-emerald-100 text-emerald-600',
    blue: 'bg-blue-100 text-blue-600',
    red: 'bg-red-100 text-red-600',
    orange: 'bg-orange-100 text-orange-600',
    purple: 'bg-purple-100 text-purple-600',
    indigo: 'bg-indigo-100 text-indigo-600',
    pink: 'bg-pink-100 text-pink-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    teal: 'bg-teal-100 text-teal-600',
    slate: 'bg-slate-100 text-slate-600',
  };
  
  return colorMap[color] || colorMap.cyan;
};

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

      {news.map((item, idx) => {
        const { icon: IconComponent, color } = getNewsIcon(item.headline, item.ticker, idx);
        const iconColorClasses = getIconColorClasses(color);
        
        return (
          <div
            key={idx}
            data-testid="news-card"
            className="clean-card p-6 card-hover group fade-in"
          >
            <div className="flex gap-6">
              {/* Contextual Icon */}
              <div className={`flex-shrink-0 w-16 h-16 rounded-2xl ${iconColorClasses} flex items-center justify-center shadow-sm`}>
                <IconComponent className="w-8 h-8" />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className="inline-flex items-center px-3 py-1 text-xs font-semibold bg-gradient-to-r from-cyan-500 to-emerald-500 text-white rounded-full">
                        {item.ticker}
                      </span>
                      {item.source && (
                        <span className="inline-flex items-center px-3 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full border border-gray-200">
                          {item.source}
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-cyan-600 smooth-transition line-clamp-2">
                      {item.headline}
                    </h3>
                  </div>
                </div>
                
                {item.summary && (
                  <p className="text-sm text-gray-600 mb-4 line-clamp-3 leading-relaxed">
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
        );
      })}
    </div>
  );
}