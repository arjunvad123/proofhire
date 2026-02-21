"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";

interface AgencityState {
  companyId: string | null;
  companyName: string | null;
  isReady: boolean;
}

interface AgencityContextValue extends AgencityState {
  setCompany: (id: string, name: string, apiKey: string) => void;
  clearCompany: () => void;
}

const AgencityContext = createContext<AgencityContextValue | null>(null);

const STORAGE_KEY = "agencity_company";

export function AgencityProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AgencityState>({
    companyId: null,
    companyName: null,
    isReady: false,
  });

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const { companyId, companyName } = JSON.parse(stored);
        setState({ companyId, companyName, isReady: true });
      } catch {
        setState((s) => ({ ...s, isReady: true }));
      }
    } else {
      setState((s) => ({ ...s, isReady: true }));
    }
  }, []);

  function setCompany(id: string, name: string, apiKey: string) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ companyId: id, companyName: name }));
    localStorage.setItem("agencity_api_key", apiKey);
    setState({ companyId: id, companyName: name, isReady: true });
  }

  function clearCompany() {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem("agencity_api_key");
    setState({ companyId: null, companyName: null, isReady: true });
  }

  return (
    <AgencityContext.Provider value={{ ...state, setCompany, clearCompany }}>
      {children}
    </AgencityContext.Provider>
  );
}

export function useAgencity() {
  const ctx = useContext(AgencityContext);
  if (!ctx) {
    throw new Error("useAgencity must be used within AgencityProvider");
  }
  return ctx;
}
