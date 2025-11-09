import { useState } from "react";
import { Info } from "lucide-react";

export default function InfoTooltip({ text, className = "" }) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block ml-1">
      <button
        type="button"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsVisible(!isVisible);
        }}
        className={`text-gray-400 hover:text-cyan-600 transition-colors ${className}`}
      >
        <Info className="w-3.5 h-3.5" />
      </button>
      
      {isVisible && (
        <div className="absolute z-50 left-0 top-6 w-64 bg-gray-900 text-white text-xs rounded-lg p-3 shadow-xl">
          <div className="absolute -top-1 left-2 w-2 h-2 bg-gray-900 transform rotate-45"></div>
          {text}
        </div>
      )}
    </div>
  );
}
