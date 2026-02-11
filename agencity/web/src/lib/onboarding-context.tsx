'use client';

import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from 'react';
import type { Company, CompanyUMO, Role, ImportResult } from './api';

// =============================================================================
// TYPES
// =============================================================================

export interface OnboardingState {
  // Step 1: Company Info
  companyId: string | null;
  company: Company | null;

  // Step 2: UMO
  umo: CompanyUMO | null;

  // Step 3: Roles
  roles: Role[];

  // Step 4: LinkedIn Import
  linkedinImport: ImportResult | null;

  // Step 5: Database Import
  databaseImport: ImportResult | null;

  // Progress
  currentStep: number;
  isComplete: boolean;
}

interface OnboardingContextType {
  state: OnboardingState;
  setCompany: (company: Company) => void;
  setUMO: (umo: CompanyUMO) => void;
  addRole: (role: Role) => void;
  setLinkedinImport: (result: ImportResult) => void;
  setDatabaseImport: (result: ImportResult) => void;
  setCurrentStep: (step: number) => void;
  setComplete: () => void;
  reset: () => void;
}

// =============================================================================
// INITIAL STATE
// =============================================================================

const initialState: OnboardingState = {
  companyId: null,
  company: null,
  umo: null,
  roles: [],
  linkedinImport: null,
  databaseImport: null,
  currentStep: 1,
  isComplete: false,
};

// =============================================================================
// CONTEXT
// =============================================================================

const OnboardingContext = createContext<OnboardingContextType | undefined>(
  undefined
);

// =============================================================================
// PROVIDER
// =============================================================================

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<OnboardingState>(() => {
    // Try to restore from localStorage
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('onboarding-state');
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch {
          // Ignore parse errors
        }
      }
    }
    return initialState;
  });

  // Persist state changes
  const persistState = useCallback((newState: OnboardingState) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('onboarding-state', JSON.stringify(newState));
    }
  }, []);

  const setCompany = useCallback(
    (company: Company) => {
      const newState = {
        ...state,
        companyId: company.id,
        company,
      };
      setState(newState);
      persistState(newState);
    },
    [state, persistState]
  );

  const setUMO = useCallback(
    (umo: CompanyUMO) => {
      const newState = { ...state, umo };
      setState(newState);
      persistState(newState);
    },
    [state, persistState]
  );

  const addRole = useCallback(
    (role: Role) => {
      const newState = { ...state, roles: [...state.roles, role] };
      setState(newState);
      persistState(newState);
    },
    [state, persistState]
  );

  const setLinkedinImport = useCallback(
    (result: ImportResult) => {
      const newState = { ...state, linkedinImport: result };
      setState(newState);
      persistState(newState);
    },
    [state, persistState]
  );

  const setDatabaseImport = useCallback(
    (result: ImportResult) => {
      const newState = { ...state, databaseImport: result };
      setState(newState);
      persistState(newState);
    },
    [state, persistState]
  );

  const setCurrentStep = useCallback(
    (step: number) => {
      const newState = { ...state, currentStep: step };
      setState(newState);
      persistState(newState);
    },
    [state, persistState]
  );

  const setComplete = useCallback(() => {
    const newState = { ...state, isComplete: true };
    setState(newState);
    persistState(newState);
  }, [state, persistState]);

  const reset = useCallback(() => {
    setState(initialState);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('onboarding-state');
    }
  }, []);

  return (
    <OnboardingContext.Provider
      value={{
        state,
        setCompany,
        setUMO,
        addRole,
        setLinkedinImport,
        setDatabaseImport,
        setCurrentStep,
        setComplete,
        reset,
      }}
    >
      {children}
    </OnboardingContext.Provider>
  );
}

// =============================================================================
// HOOK
// =============================================================================

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (context === undefined) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
}
