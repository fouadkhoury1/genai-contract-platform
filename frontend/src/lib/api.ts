import axios from 'axios';

// API base URL - adjust this to match your Django backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Auth endpoints
  login: '/api/auth/login/',
  register: '/api/auth/register/',
  
  // Contract endpoints
  contracts: '/api/contracts/',
  contractAnalysis: (id: string) => `/api/contracts/${id}/analysis/`,
  contractEvaluation: '/api/contracts/evaluate/',
  
  // Client endpoints
  clients: '/api/clients/',
  
  // Service endpoints
  health: '/api/health/',
  ready: '/api/ready/',
  metrics: '/api/metrics/',
  logs: '/api/logs/',
} as const; 