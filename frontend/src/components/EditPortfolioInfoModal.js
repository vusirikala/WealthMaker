import { X, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useState, useEffect } from "react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditPortfolioInfoModal({ isOpen, onClose, portfolio, onSuccess }) {
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");
  const [riskTolerance, setRiskTolerance] = useState("medium");
  const [roiExpectations, setRoiExpectations] = useState(10);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen && portfolio) {
      setName(portfolio.name || "");
      setGoal(portfolio.goal || "");
      setRiskTolerance(portfolio.risk_tolerance || "medium");
      setRoiExpectations(portfolio.roi_expectations || 10);
    }
  }, [isOpen, portfolio]);

  if (!isOpen || !portfolio) return null;

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error("Portfolio name is required");
      return;
    }

    setIsSaving(true);

    try {
      const response = await fetch(`${API}/portfolios-v2/${portfolio.portfolio_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          name: name.trim(),
          goal: goal.trim(),
          type: portfolio.type,
          risk_tolerance: riskTolerance,
          roi_expectations: roiExpectations,
          allocations: portfolio.allocations || [],
        }),
      });

      if (response.ok) {
        toast.success("Portfolio updated successfully");
        onSuccess();
        onClose();
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || "Failed to update portfolio");
      }
    } catch (error) {
      console.error("Error updating portfolio:", error);
      toast.error("Failed to update portfolio");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Edit Portfolio Info</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Portfolio Name *
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Retirement Fund, Growth Portfolio"
              className="w-full"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Goal / Description
            </label>
            <Textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="Describe the purpose of this portfolio..."
              className="w-full resize-none"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Risk Tolerance
              </label>
              <select
                value={riskTolerance}
                onChange={(e) => setRiskTolerance(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Expected ROI (%)
              </label>
              <Input
                type="number"
                value={roiExpectations}
                onChange={(e) => setRoiExpectations(parseFloat(e.target.value))}
                min="0"
                max="100"
                step="0.5"
                className="w-full"
              />
            </div>
          </div>

          {portfolio.type === 'ai' && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <p className="text-sm text-purple-900">
                💡 <strong>AI Portfolio:</strong> Changing risk tolerance or ROI expectations won't automatically adjust allocations. Use the chat to request portfolio rebalancing.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 flex justify-end gap-3">
          <Button
            onClick={onClose}
            variant="outline"
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving || !name.trim()}
            className="bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white"
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}
