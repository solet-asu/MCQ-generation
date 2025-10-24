// app/util/session.ts

const SESSION_KEY = "api_session_id";

/**
 * Get or create a session ID for this browser tab.
 * Uses sessionStorage so it auto-clears when tab closes.
 */
export function getSessionId(): string {
  // Check if we're in the browser
  if (typeof window === "undefined") {
    return ""; // SSR fallback
  }

  // Try to get existing session
  let sessionId = sessionStorage.getItem(SESSION_KEY);

  // If no session exists, create one
  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem(SESSION_KEY, sessionId);
    console.log(`[Session] New session created: ${sessionId}`);
  }

  return sessionId;
}

// Generate a simple unique session ID
function generateSessionId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  // Fallback: timestamp + random
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

//  Clear the session (for testing purposes)
export function clearSession(): void {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(SESSION_KEY);
    console.log("[Session] Session cleared");
  }
}

// Check if a session exists
export function hasSession(): boolean {
  if (typeof window === "undefined") return false;
  return !!sessionStorage.getItem(SESSION_KEY);
}
