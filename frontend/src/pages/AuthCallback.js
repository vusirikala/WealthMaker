import { useEffect } from "react";

export default function AuthCallback() {
  useEffect(() => {
    // Extract session_id from URL hash
    const hash = window.location.hash;
    
    if (hash && hash.includes("session_id=")) {
      const sessionId = hash.split("session_id=")[1].split("&")[0];
      
      // Send message to opener window
      if (window.opener) {
        window.opener.postMessage(
          { type: 'AUTH_SUCCESS', sessionId },
          window.location.origin
        );
        
        // Close popup after a short delay
        setTimeout(() => {
          window.close();
        }, 500);
      }
    }
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-4 spinner"></div>
        <p className="text-lg font-medium text-gray-900">Completing sign in...</p>
        <p className="text-sm text-gray-600 mt-2">This window will close automatically.</p>
      </div>
    </div>
  );
}
