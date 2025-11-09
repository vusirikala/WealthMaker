import { X, Download, FileText, FileSpreadsheet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "sonner";
import jsPDF from "jspdf";
import "jspdf-autotable";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ExportPortfolioModal({ isOpen, onClose, portfolio }) {
  const [isExporting, setIsExporting] = useState(false);

  if (!isOpen || !portfolio) return null;

  const handleExportCSV = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(
        `${API}/portfolios-v2/${portfolio.portfolio_id}/export/csv`,
        {
          credentials: "include",
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${portfolio.name.replace(/\s+/g, "_")}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("Portfolio exported to CSV");
      } else {
        toast.error("Failed to export portfolio");
      }
    } catch (error) {
      console.error("Error exporting CSV:", error);
      toast.error("Failed to export portfolio");
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportPDF = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(
        `${API}/portfolios-v2/${portfolio.portfolio_id}/export/json`,
        {
          credentials: "include",
        }
      );

      if (response.ok) {
        const data = await response.json();
        generatePDF(data.portfolio);
        toast.success("Portfolio exported to PDF");
      } else {
        toast.error("Failed to export portfolio");
      }
    } catch (error) {
      console.error("Error exporting PDF:", error);
      toast.error("Failed to export portfolio");
    } finally {
      setIsExporting(false);
    }
  };

  const generatePDF = (portfolioData) => {
    const doc = new jsPDF();
    
    // Title
    doc.setFontSize(20);
    doc.setTextColor(6, 182, 212); // Cyan
    doc.text("Portfolio Report", 14, 20);
    
    // Portfolio Info
    doc.setFontSize(12);
    doc.setTextColor(0, 0, 0);
    doc.text(`Portfolio: ${portfolioData.name}`, 14, 35);
    
    if (portfolioData.goal) {
      const goalLines = doc.splitTextToSize(`Goal: ${portfolioData.goal}`, 180);
      doc.setFontSize(10);
      doc.text(goalLines, 14, 42);
    }
    
    doc.setFontSize(10);
    const yPos = portfolioData.goal ? 52 : 42;
    doc.text(`Risk Tolerance: ${portfolioData.risk_tolerance}`, 14, yPos);
    doc.text(`Expected ROI: ${portfolioData.roi_expectations}%`, 14, yPos + 7);
    doc.text(`Type: ${portfolioData.type === 'ai' ? 'AI-Generated' : 'Manual'}`, 14, yPos + 14);
    doc.text(`Report Date: ${new Date().toLocaleDateString()}`, 14, yPos + 21);
    
    // Summary Stats
    let currentY = yPos + 35;
    doc.setFontSize(14);
    doc.setTextColor(6, 182, 212);
    doc.text("Portfolio Summary", 14, currentY);
    
    doc.setFontSize(10);
    doc.setTextColor(0, 0, 0);
    currentY += 10;
    
    const summaryData = [
      ['Total Invested', `$${portfolioData.total_invested?.toLocaleString() || '0.00'}`],
      ['Current Value', `$${portfolioData.current_value?.toLocaleString() || '0.00'}`],
      ['Total Return', `$${portfolioData.total_return?.toLocaleString() || '0.00'}`],
      ['Return %', `${portfolioData.total_return_percentage?.toFixed(2) || '0.00'}%`]
    ];
    
    doc.autoTable({
      startY: currentY,
      head: [['Metric', 'Value']],
      body: summaryData,
      theme: 'grid',
      headStyles: { fillColor: [6, 182, 212] },
      margin: { left: 14 },
    });
    
    currentY = doc.lastAutoTable.finalY + 15;
    
    // Holdings Table
    if (portfolioData.holdings && portfolioData.holdings.length > 0) {
      doc.setFontSize(14);
      doc.setTextColor(6, 182, 212);
      doc.text("Holdings", 14, currentY);
      currentY += 7;
      
      const holdingsData = portfolioData.holdings.map(h => {
        const gainLoss = h.current_value - h.cost_basis;
        const returnPct = h.cost_basis > 0 ? (gainLoss / h.cost_basis * 100) : 0;
        return [
          h.ticker,
          h.shares.toFixed(4),
          `$${h.purchase_price.toFixed(2)}`,
          `$${h.current_price.toFixed(2)}`,
          `$${h.current_value.toFixed(2)}`,
          `${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}%`
        ];
      });
      
      doc.autoTable({
        startY: currentY,
        head: [['Ticker', 'Shares', 'Buy Price', 'Current', 'Value', 'Return']],
        body: holdingsData,
        theme: 'striped',
        headStyles: { fillColor: [6, 182, 212] },
        margin: { left: 14 },
      });
      
      currentY = doc.lastAutoTable.finalY + 15;
    }
    
    // Check if we need a new page
    if (currentY > 240) {
      doc.addPage();
      currentY = 20;
    }
    
    // Allocations Table
    if (portfolioData.allocations && portfolioData.allocations.length > 0) {
      doc.setFontSize(14);
      doc.setTextColor(6, 182, 212);
      doc.text("Target Allocations", 14, currentY);
      currentY += 7;
      
      const allocationsData = portfolioData.allocations.map(a => [
        a.ticker,
        `${a.allocation_percentage}%`,
        a.sector || 'Unknown',
        a.asset_type || 'stock'
      ]);
      
      doc.autoTable({
        startY: currentY,
        head: [['Ticker', 'Allocation', 'Sector', 'Type']],
        body: allocationsData,
        theme: 'striped',
        headStyles: { fillColor: [6, 182, 212] },
        margin: { left: 14 },
      });
    }
    
    // Footer
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(128, 128, 128);
      doc.text(
        `Generated by WealthMaker - Page ${i} of ${pageCount}`,
        doc.internal.pageSize.width / 2,
        doc.internal.pageSize.height - 10,
        { align: 'center' }
      );
    }
    
    // Save the PDF
    doc.save(`${portfolioData.name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center">
              <Download className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Export Portfolio</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-gray-600 text-sm">
            Export "{portfolio.name}" portfolio data in your preferred format.
          </p>

          <div className="space-y-3">
            {/* PDF Export */}
            <button
              onClick={handleExportPDF}
              disabled={isExporting}
              className="w-full p-4 rounded-xl border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all group text-left"
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-red-100 group-hover:bg-red-200 rounded-lg flex items-center justify-center transition-colors">
                  <FileText className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Export as PDF</h3>
                  <p className="text-xs text-gray-600">
                    Formatted report with charts and tables
                  </p>
                </div>
              </div>
            </button>

            {/* CSV Export */}
            <button
              onClick={handleExportCSV}
              disabled={isExporting}
              className="w-full p-4 rounded-xl border-2 border-gray-200 hover:border-green-500 hover:bg-green-50 transition-all group text-left"
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-green-100 group-hover:bg-green-200 rounded-lg flex items-center justify-center transition-colors">
                  <FileSpreadsheet className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Export as CSV</h3>
                  <p className="text-xs text-gray-600">
                    Spreadsheet format for Excel/Google Sheets
                  </p>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 flex justify-end">
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
