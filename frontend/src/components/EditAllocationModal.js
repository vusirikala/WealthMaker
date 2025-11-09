import { useState, useEffect } from "react";
import { X, Save, AlertCircle, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditAllocationModal({ isOpen, onClose, portfolio, onSuccess }) {
  const [allocations, setAllocations] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen && portfolio) {
      // Initialize with current allocations
      setAllocations(portfolio.allocations || []);
    }
  }, [isOpen, portfolio]);

  if (!isOpen || !portfolio) return null;

  const addAllocation = () => {
    setAllocations([...allocations, { ticker: "", allocation_percentage: 0, sector: "Unknown", asset_type: "stock" }]);
  };

  const removeAllocation = (index) => {
    const newAllocations = allocations.filter((_, i) => i !== index);
    setAllocations(newAllocations);
  };

  const updateAllocation = (index, field, value) => {
    const newAllocations = [...allocations];
    newAllocations[index][field] = value;
    setAllocations(newAllocations);
  };

  const getTotalAllocation = () => {
    return allocations.reduce((sum, alloc) => {
      const pct = parseFloat(alloc.allocation_percentage) || 0;
      return sum + pct;
    }, 0);
  };

  const handleSubmit = async () => {
    // Validation
    const validAllocations = allocations.filter(
      a => a.ticker.trim() && parseFloat(a.allocation_percentage) > 0
    );

    if (validAllocations.length === 0) {
      toast.error("Please add at least one allocation");
      return;
    }

    const totalAllocation = getTotalAllocation();
    if (Math.abs(totalAllocation - 100) > 0.1) {
      toast.error(`Total allocation must equal 100%. Current total: ${totalAllocation.toFixed(1)}%`);
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${API}/portfolios-v2/${portfolio.portfolio_id}/allocations`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          allocations: validAllocations.map(a => ({
            ticker: a.ticker.toUpperCase(),
            allocation_percentage: parseFloat(a.allocation_percentage),
            sector: a.sector || "Unknown",
            asset_type: a.asset_type || "stock"
          }))
        }),
      });

      if (response.ok) {
        toast.success("Allocations updated successfully!");
        onSuccess();
        onClose();
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || "Failed to update allocations");
      }
    } catch (error) {
      console.error("Error updating allocations:", error);
      toast.error("Failed to update allocations");
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalAllocation = getTotalAllocation();
  const isValid = Math.abs(totalAllocation - 100) < 0.1;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Edit Allocations</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Warning if portfolio has investments */}
        {portfolio.total_invested > 0 && (
          <div className="bg-amber-50 border-l-4 border-amber-400 p-4 mx-6 mt-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600" />
              <div>
                <p className="text-sm font-semibold text-amber-900">
                  Warning: This portfolio has investments
                </p>
                <p className="text-xs text-amber-700 mt-1">
                  Changing allocations won't affect existing holdings. New investments will use the updated allocations.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-semibold text-gray-700">
                Stock Allocations
              </label>
              <Button
                onClick={addAllocation}
                size="sm"
                variant="outline"
                className="text-xs"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Stock
              </Button>
            </div>

            {allocations.map((alloc, index) => (
              <div key={index} className="flex gap-3 items-center bg-gray-50 p-3 rounded-lg">
                <Input
                  value={alloc.ticker}
                  onChange={(e) => updateAllocation(index, 'ticker', e.target.value.toUpperCase())}
                  placeholder="Ticker"
                  className="flex-1"
                />
                <div className="relative flex-1">
                  <Input
                    type="number"
                    value={alloc.allocation_percentage}
                    onChange={(e) => updateAllocation(index, 'allocation_percentage', e.target.value)}
                    placeholder="Allocation %"
                    min="0"
                    max="100"
                    step="0.1"
                    className="w-full pr-8"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">
                    %
                  </span>
                </div>
                <button
                  onClick={() => removeAllocation(index)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Total Allocation Display */}
          <div className={`mt-4 p-3 rounded-lg flex items-center justify-between ${
            isValid ? 'bg-green-50 border border-green-200' : 'bg-amber-50 border border-amber-200'
          }`}>
            <div className="flex items-center gap-2">
              <AlertCircle className={`w-4 h-4 ${isValid ? 'text-green-600' : 'text-amber-600'}`} />
              <span className={`text-sm font-semibold ${isValid ? 'text-green-900' : 'text-amber-900'}`}>
                Total Allocation:
              </span>
            </div>
            <span className={`text-lg font-bold ${isValid ? 'text-green-600' : 'text-amber-600'}`}>
              {totalAllocation.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 flex justify-end gap-3">
          <Button
            onClick={onClose}
            variant="outline"
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !isValid}
            className="bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-700 hover:to-emerald-700 text-white"
          >
            <Save className="w-4 h-4 mr-2" />
            {isSubmitting ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}
