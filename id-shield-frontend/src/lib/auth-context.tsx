import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { User } from '../types';
import { api } from './api';
import { DEMO_MODE, DEMO_USER } from './demo-context';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isDemoMode: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(DEMO_MODE ? DEMO_USER : null);
  const [isLoading, setIsLoading] = useState(!DEMO_MODE);

  useEffect(() => {
    if (DEMO_MODE) {
      return;
    }
    const token = api.getToken();
    if (token) {
      api.getCurrentUser()
        .then(setUser)
        .catch(() => {
          api.setToken(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    if (DEMO_MODE) {
      setUser(DEMO_USER);
      return;
    }
    const response = await api.login(email, password);
    setUser(response.user);
  };

  const logout = () => {
    if (DEMO_MODE) {
      return;
    }
    api.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: DEMO_MODE || !!user,
        isDemoMode: DEMO_MODE,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
