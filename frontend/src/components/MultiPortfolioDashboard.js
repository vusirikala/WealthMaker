import { useState } from "react";
import PortfolioSidebar from "./PortfolioSidebar";
import PortfolioView from "./PortfolioView";
import AddPortfolioModal from "./AddPortfolioModal";
import ManualPortfolioBuilder from "./ManualPortfolioBuilder";
import AIPortfolioBuilder from "./AIPortfolioBuilder";
import ChatTab from "./ChatTab";

export default function MultiPortfolioDashboard() {
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showManualBuilder, setShowManualBuilder] = useState(false);
  const [showAIBuilder, setShowAIBuilder] = useState(false);
  const [showChat, setShowChat] = useState(false);

  // Close chat when portfolio changes
  const handlePortfolioSelect = (portfolioId) => {
    setSelectedPortfolioId(portfolioId);
    setShowChat(false); // Close chat to force reload with new portfolio
  };

  const handlePortfolioTypeSelect = (type) => {
    if (type === 'manual') {
      setShowManualBuilder(true);
    } else if (type === 'ai') {
      setShowAIBuilder(true);
    }
  };

  const handlePortfolioCreated = (portfolio) => {
    // Select the newly created portfolio
    setSelectedPortfolioId(portfolio.portfolio_id);
    // Refresh sidebar (it will reload portfolios)
    window.location.reload(); // Simple approach, can be improved with state management
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left Sidebar - Portfolio List */}
      <PortfolioSidebar
        selectedPortfolioId={selectedPortfolioId}
        onSelectPortfolio={handlePortfolioSelect}
        onAddPortfolio={() => setShowAddModal(true)}
      />

      {/* Main Content - Portfolio View */}
      <div 
        className={`flex-1 flex flex-col transition-all duration-300 ease-in-out overflow-y-auto ${
          showChat ? 'mr-0 md:mr-[400px]' : 'mr-0'
        }`}
      >
        <PortfolioView
          portfolioId={selectedPortfolioId}
          onChatToggle={() => setShowChat(!showChat)}
        />
      </div>

      {/* Chat Sliding Panel (from right) - Fixed position but pushes content */}
      <div 
        className={`fixed top-0 right-0 h-full w-full md:w-[400px] bg-white shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col border-l border-gray-200 ${
          showChat ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{ zIndex: 30 }}
      >
        {/* Chat Header */}
        <div className="bg-gradient-to-r from-cyan-600 to-emerald-600 text-white p-4 shadow-md flex-shrink-0 relative">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center flex-shrink-0">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0 pr-16">
              <h3 className="font-bold text-base truncate">AI Financial Advisor</h3>
              <p className="text-xs text-white/80 truncate">Portfolio-specific advice</p>
            </div>
          </div>
          
          {/* Close Button - Highly visible and prominent */}
          <button
            onClick={() => setShowChat(false)}
            className="absolute top-4 right-4 w-12 h-12 bg-white hover:bg-gray-50 text-gray-900 rounded-full transition-all flex items-center justify-center shadow-2xl hover:shadow-3xl border-2 border-gray-300 hover:border-cyan-500 z-[100]"
            title="Close chat"
            aria-label="Close chat"
            style={{ 
              boxShadow: '0 10px 40px rgba(0,0,0,0.3), 0 0 0 1px rgba(0,0,0,0.1)',
            }}
          >
            <svg className="w-7 h-7 font-bold" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Chat Content */}
        <div className="flex-1 overflow-hidden">
          <ChatTab 
            key={selectedPortfolioId || 'global'} 
            portfolioId={selectedPortfolioId}
            isVisible={showChat}
          />
        </div>
      </div>

      {/* Modals */}
      <AddPortfolioModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSelectType={handlePortfolioTypeSelect}
      />

      <ManualPortfolioBuilder
        isOpen={showManualBuilder}
        onClose={() => setShowManualBuilder(false)}
        onSuccess={handlePortfolioCreated}
      />

      <AIPortfolioBuilder
        isOpen={showAIBuilder}
        onClose={() => setShowAIBuilder(false)}
        onSuccess={handlePortfolioCreated}
      />
    </div>
  );
}
