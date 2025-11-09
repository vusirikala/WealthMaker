import { X, Bot, Edit3 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AddPortfolioModal({ isOpen, onClose, onSelectType }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Create New Portfolio</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 mb-6">
            Choose how you'd like to create your portfolio
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* AI Portfolio Builder */}
            <div
              onClick={() => {
                onSelectType('ai');
                onClose();
              }}
              className="group cursor-pointer border-2 border-gray-200 rounded-xl p-6 hover:border-cyan-500 hover:shadow-lg transition-all"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                Build with AI
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Let our AI assistant guide you through creating a personalized portfolio based on your goals and risk tolerance.
              </p>
              <ul className="space-y-2 text-xs text-gray-500">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full"></div>
                  Answer a few questions
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full"></div>
                  AI suggests optimal allocations
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full"></div>
                  Review and adjust before saving
                </li>
              </ul>
            </div>

            {/* Manual Portfolio Builder */}
            <div
              onClick={() => {
                onSelectType('manual');
                onClose();
              }}
              className="group cursor-pointer border-2 border-gray-200 rounded-xl p-6 hover:border-emerald-500 hover:shadow-lg transition-all"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Edit3 className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                Build Manually
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Create your portfolio from scratch by selecting stocks and setting allocation percentages yourself.
              </p>
              <ul className="space-y-2 text-xs text-gray-500">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                  Full control over selections
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                  Add and adjust stocks anytime
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                  Perfect for experienced investors
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 flex justify-end">
          <Button
            onClick={onClose}
            variant="outline"
            className="px-6"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
