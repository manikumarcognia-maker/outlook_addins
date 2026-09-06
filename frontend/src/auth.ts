/**
 * Office SSO scaffolding. When a real backend exists, only this module changes.
 * Real API keys and secrets must never live in this frontend bundle.
 */
export async function getAccessToken(): Promise<string> {
  if (typeof Office === "undefined") {
    return "mock-token-for-dev";
  }

  try {
    if (Office.auth?.getAccessToken) {
      return await Office.auth.getAccessToken({ allowSignInPrompt: true });
    }
  } catch {
    // SSO not configured yet — use mock token for local development.
  }

  return "mock-token-for-dev";
}
