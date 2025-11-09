import { useState } from "react";
import PortfolioSidebar from "./PortfolioSidebar";
import PortfolioView from "./PortfolioView";
import AddPortfolioModal from "./AddPortfolioModal";
import ManualPortfolioBuilder from "./ManualPortfolioBuilder";
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

        {/* Chat Panel (Expandable from bottom) */}
        {showChat && (
          <div className="absolute bottom-0 left-0 right-0 h-96 bg-white border-t-2 border-gray-300 shadow-2xl z-40">
            <div className="h-full">
              <ChatTab portfolioId={selectedPortfolioId} />
            </div>
          </div>
        )}
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

      {/* TODO: AI Portfolio Builder */}
      {showAIBuilder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md">
            <h2 className="text-2xl font-bold mb-4">AI Portfolio Builder</h2>
            <p className="text-gray-600 mb-4">
              AI Portfolio Builder coming soon! For now, use the manual builder or chat to create portfolios.
            </p>
            <button
              onClick={() => setShowAIBuilder(false)}
              className="w-full px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
