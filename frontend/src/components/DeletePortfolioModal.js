import { X, AlertTriangle, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DeletePortfolioModal({ isOpen, onClose, portfolio, onSuccess }) {
  const [confirmText, setConfirmText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  if (!isOpen || !portfolio) return null;

  const handleDelete = async () => {
    if (confirmText !== portfolio.name) {
      toast.error("Portfolio name doesn't match");
      return;
    }

    setIsDeleting(true);

    try {
      const response = await fetch(`${API}/portfolios-v2/${portfolio.portfolio_id}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.ok) {
        toast.success("Portfolio deleted successfully");
        onSuccess();
        onClose();
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || "Failed to delete portfolio");
      }
    } catch (error) {
      console.error("Error deleting portfolio:", error);
      toast.error("Failed to delete portfolio");
    } finally {
      setIsDeleting(false);
    }
  };

  const isConfirmValid = confirmText === portfolio.name;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between bg-red-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-500 rounded-xl flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Delete Portfolio</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-900">
              <strong>Warning:</strong> This action cannot be undone. All portfolio data, including investment history and allocations, will be permanently deleted.
            </p>
          </div>

          <div>
            <p className="text-gray-900 font-semibold mb-2">
              You are about to delete:
            </p>
            <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
              <p className="font-bold text-gray-900">{portfolio.name}</p>
              {portfolio.goal && (
                <p className="text-sm text-gray-600 mt-1">{portfolio.goal}</p>
              )}
              {portfolio.total_invested > 0 && (
                <p className="text-sm text-gray-600 mt-2">
                  Total Invested: ${portfolio.total_invested.toLocaleString()}
                </p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Type the portfolio name to confirm:
            </label>
            <Input
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder={portfolio.name}
              className="w-full"
              autoFocus
            />
            <p className="text-xs text-gray-500 mt-1">
              This helps prevent accidental deletions
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 flex justify-end gap-3">
          <Button
            onClick={onClose}
            variant="outline"
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDelete}
            disabled={isDeleting || !isConfirmValid}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            {isDeleting ? "Deleting..." : "Delete Portfolio"}
          </Button>
        </div>
      </div>
    </div>
  );
}
