import { api, endpoints } from '@/lib/api';

export interface BackendContract {
  _id: string;
  title: string;
  client?: string;
  signed: boolean;
  date?: string;
  created_at: string;
  analysis?: string;
  model_used?: string;
  analysis_date?: string;
  approved?: boolean;
  evaluation_reasoning?: string;
  clauses?: string[];
  text?: string;
}

export interface FrontendContract {
  id: string;
  title: string;
  client?: string;
  signed: boolean;
  uploadDate: string;
  status: 'pending' | 'analyzing' | 'completed' | 'approved' | 'rejected';
  fileSize: string;
  analysisResults?: {
    approved: boolean;
    reasoning: string;
    clauseCount: number;
  };
  clauses?: string[];
  analysis?: string;
  evaluation_reasoning?: string;
  approved?: boolean;
}

interface CreateContractResponse {
  message: string;
  contract_id: string;
}

interface UpdateContractResponse {
  message: string;
}

interface DeleteContractResponse {
  message: string;
}

export interface ContractAnalysisResponse {
  analysis: string;
  model_used: string;
  analysis_date?: string;
  contract_title?: string;
  contract_client?: string;
}

interface CreateContractWithFileResponse {
  message: string;
  contract_id: string;
  analysis?: string;
  model_used?: string;
  approved?: boolean;
  evaluation_reasoning?: string;
}

export interface ReanalyzeContractResponse {
  message: string;
  analysis: string;
  model_used: string;
  approved: boolean;
  evaluation_reasoning: string;
}

export function transformContract(contract: BackendContract): FrontendContract {
  return {
    id: contract._id,
    title: contract.title,
    client: contract.client,
    signed: contract.signed,
    uploadDate: contract.date || contract.created_at,
    status: contract.approved ? 'approved' : contract.approved === false ? 'rejected' : 'pending',
    fileSize: '1.2 MB', // TODO: Add actual file size
    analysisResults: contract.analysis && typeof contract.analysis === 'string' ? {
      approved: contract.approved === true,
      reasoning: contract.analysis,
      clauseCount: contract.clauses?.length || 0
    } : undefined,
    clauses: contract.clauses || [],
    analysis: typeof contract.analysis === 'string' ? contract.analysis : undefined,
    evaluation_reasoning: contract.evaluation_reasoning,
    approved: contract.approved
  };
}

export const contractService = {
  // Get all contracts
  async getContracts(): Promise<FrontendContract[]> {
    try {
      const response = await api.get<BackendContract[]>(endpoints.contracts);
      return response.data.map(transformContract);
    } catch (error) {
      console.error('Error fetching contracts:', error);
      throw error;
    }
  },

  // Get contract by ID
  async getContract(id: string): Promise<FrontendContract> {
    try {
      const response = await api.get<BackendContract>(`${endpoints.contracts}${id}/`);
      return transformContract(response.data);
    } catch (error) {
      console.error('Error fetching contract:', error);
      throw error;
    }
  },

  // Create new contract
  async createContract(contractData: {
    title: string;
    client: string;
    text: string;
    signed?: boolean;
    date?: string;
  }): Promise<CreateContractResponse> {
    try {
      const response = await api.post<CreateContractResponse>(endpoints.contracts, contractData);
      return response.data;
    } catch (error) {
      console.error('Error creating contract:', error);
      throw error;
    }
  },

  // Update contract
  async updateContract(id: string, contractData: Partial<BackendContract>): Promise<UpdateContractResponse> {
    try {
      const response = await api.put<UpdateContractResponse>(`${endpoints.contracts}${id}/`, contractData);
      return response.data;
    } catch (error) {
      console.error('Error updating contract:', error);
      throw error;
    }
  },

  // Delete contract
  async deleteContract(id: string): Promise<DeleteContractResponse> {
    try {
      const response = await api.delete<DeleteContractResponse>(`${endpoints.contracts}${id}/`);
      return response.data;
    } catch (error) {
      console.error('Error deleting contract:', error);
      throw error;
    }
  },

  // Get contract analysis
  async getContractAnalysis(id: string): Promise<ContractAnalysisResponse> {
    try {
      const response = await api.get<ContractAnalysisResponse>(endpoints.contractAnalysis(id));
      return response.data;
    } catch (error) {
      console.error('Error fetching contract analysis:', error);
      throw error;
    }
  },

  // Create new contract with file upload (PDF or text)
  async createContractWithFile(formData: FormData): Promise<CreateContractWithFileResponse> {
    try {
      const response = await api.post<CreateContractWithFileResponse>(endpoints.contracts, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading contract with file:', error);
      throw error;
    }
  },

  // Reanalyze contract with new file
  async reanalyzeContract(id: string, formData: FormData): Promise<ReanalyzeContractResponse> {
    try {
      const response = await api.post<ReanalyzeContractResponse>(
        endpoints.reanalyzeContract(id),
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error reanalyzing contract:', error);
      throw error;
    }
  },

  // Extract clauses from contract
  async extractClauses(id: string): Promise<any> {
    try {
      const response = await api.post(`/api/contracts/${id}/clauses/`);
      return response.data;
    } catch (error) {
      console.error('Error extracting clauses:', error);
      throw error;
    }
  }
}; 