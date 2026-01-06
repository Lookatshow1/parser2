const TOKEN_KEY = "ads_access_token";
const REFRESH_KEY = "ads_refresh_token";
const ORG_KEY = "ads_active_org";

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(REFRESH_KEY);
}

export function setRefreshToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(REFRESH_KEY, token);
}

export function clearRefreshToken() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(REFRESH_KEY);
}

export function getOrgId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(ORG_KEY);
}

export function setOrgId(orgId: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(ORG_KEY, orgId);
}

export function clearOrgId() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(ORG_KEY);
}
