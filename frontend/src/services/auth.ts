import { api, endpoints } from '@/lib/api';
import type { LoginCredentials, RegisterCredentials, AuthResponse } from '@/types';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post(endpoints.login, credentials);
    const { token, user } = response.data;
    
    // Store token in localStorage
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  },

  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await api.post(endpoints.register, credentials);
    const { token, user } = response.data;
    
    // Store token in localStorage
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  },

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  },

  getToken(): string | null {
    return localStorage.getItem('token');
  },

  getUser() {
    if (typeof window === 'undefined') return null;
    const user = localStorage.getItem('user');
    try {
      return user ? JSON.parse(user) : null;
    } catch {
      localStorage.removeItem('user');
      return null;
    }
  },

  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    return !!this.getToken();
  },
}; 