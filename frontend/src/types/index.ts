// Authentication types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: {
    id: string;
    username: string;
    email: string;
  };
}

// Contract types
export interface Contract {
  _id: string;
  title: string;
  text: string;
  client_id?: string;
  analysis?: ContractAnalysis;
  model_used?: string;
  analysis_date?: string;
  created_at: string;
  updated_at: string;
}

export interface ContractAnalysis {
  analysis: string;
  model_used: string;
}

export interface ContractEvaluation {
  approved: boolean;
  reasoning: string;
}

export interface CreateContractData {
  title: string;
  text: string;
  client_id?: string;
}

// Client types
export interface Client {
  _id: string;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateClientData {
  name: string;
  email: string;
  phone?: string;
  company?: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next?: string;
  previous?: string;
}

// Service types
export interface HealthCheck {
  status: string;
  timestamp: string;
}

export interface Metrics {
  request_count: number;
  average_latency: number;
}

export interface LogEntry {
  timestamp: string;
  method: string;
  path: string;
  status_code: number;
  response_time: number;
  user_agent: string;
} 