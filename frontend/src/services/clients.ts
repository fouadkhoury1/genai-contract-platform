import { authService } from './auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface BackendClient {
  _id: string;
  name: string;
  email?: string;
  company_id?: string;
  created_at: string;
  active?: boolean;
}

export interface FrontendClient {
  id: string;
  name: string;
  email?: string;
  company_id?: string;
  created_at: string;
  contractCount?: number;
  active?: boolean;
}

// Transform backend client to frontend format
const transformClient = (backendClient: BackendClient): FrontendClient => {
  return {
    id: backendClient._id,
    name: backendClient.name,
    email: backendClient.email,
    company_id: backendClient.company_id,
    created_at: backendClient.created_at,
    active: backendClient.active !== false,
  };
};

class ClientService {
  private getHeaders(): HeadersInit {
    const token = authService.getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  }

  async getClients(): Promise<FrontendClient[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/clients/`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const backendClients: BackendClient[] = await response.json();
      return backendClients.map(transformClient);
    } catch (error) {
      throw error;
    }
  }

  async createClient(clientData: { name: string; email?: string; company_id?: string }): Promise<FrontendClient> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/clients/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(clientData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const backendClient: BackendClient = await response.json();
      return transformClient(backendClient);
    } catch (error) {
      throw error;
    }
  }

  async updateClient(clientId: string, clientData: { name?: string; email?: string; company_id?: string }): Promise<FrontendClient> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/clients/${clientId}/`, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(clientData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const backendClient: BackendClient = await response.json();
      return transformClient(backendClient);
    } catch (error) {
      throw error;
    }
  }

  async deleteClient(clientId: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/clients/${clientId}/`, {
        method: 'DELETE',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      throw error;
    }
  }

  async getClientContracts(clientId: string): Promise<any[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/clients/${clientId}/contracts/`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }
}

export const clientService = new ClientService(); 