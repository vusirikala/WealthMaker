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
    <div className="flex h-full">
      {/* Left Sidebar - Portfolio List */}
      <PortfolioSidebar
        selectedPortfolioId={selectedPortfolioId}
        onSelectPortfolio={setSelectedPortfolioId}
        onAddPortfolio={() => setShowAddModal(true)}
      />

      {/* Main Content - Portfolio View */}
      <div className="flex-1 flex flex-col relative">
        <PortfolioView
          portfolioId={selectedPortfolioId}
          onChatToggle={() => setShowChat(!showChat)}
        />
      </div>

      {/* Chat Sliding Panel (from right) */}
      {showChat && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/20 z-40 transition-opacity"
            onClick={() => setShowChat(false)}
          />
          
          {/* Chat Panel */}
          <div className="fixed top-0 right-0 h-full w-full md:w-[500px] bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col">
            {/* Chat Header */}
            <div className="bg-gradient-to-r from-cyan-600 to-emerald-600 text-white p-4 flex items-center justify-between shadow-md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-lg">AI Financial Advisor</h3>
                  <p className="text-xs text-white/80">Get personalized investment advice</p>
                </div>
              </div>
              <button
                onClick={() => setShowChat(false)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Chat Content */}
            <div className="flex-1 overflow-hidden">
              <ChatTab portfolioId={selectedPortfolioId} />
            </div>
          </div>
        </>
      )}

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
