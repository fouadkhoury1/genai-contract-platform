import { api, endpoints } from '@/lib/api';

export interface BackendContract {
  _id: string;
  title: string;
  text: string;
  client: string;
  signed: boolean;
  date: string;
  analysis?: {
    analysis: string;
    model_used: string;
  };
  model_used?: string;
  analysis_date?: string;
  created_at: string;
  updated_at: string;
  approved?: boolean;
  evaluation_reasoning?: string;
}

export interface FrontendContract {
  id: string;
  title: string;
  client?: string;
  signed?: boolean;
  status: 'pending' | 'analyzing' | 'completed' | 'approved' | 'rejected';
  uploadDate: string;
  fileSize: string;
  analysisResults?: {
    approved: boolean;
    reasoning: string;
    clauseCount: number;
  };
}

// Transform backend contract to frontend format
export const transformContract = (backendContract: BackendContract): FrontendContract => {
  // Determine status based on explicit approved boolean first, then fall back to analysis parsing
  let status: FrontendContract['status'] = 'pending';
  
  if (backendContract.approved !== undefined) {
    // Use explicit approved boolean from backend
    status = backendContract.approved ? 'approved' : 'rejected';
  } else if (backendContract.analysis && backendContract.analysis.analysis) {
    // Fallback: parse analysis text for approval status
    const analysisText = backendContract.analysis.analysis.toLowerCase();
    if (analysisText.includes('approved') || analysisText.includes('acceptable') || analysisText.includes('compliant')) {
      status = 'approved';
    } else if (analysisText.includes('rejected') || analysisText.includes('unacceptable') || analysisText.includes('non-compliant')) {
      status = 'rejected';
    } else {
      status = 'completed';
    }
  } else if (!backendContract.analysis && backendContract.analysis_date) {
    status = 'analyzing';
  }

  // Estimate file size based on text length (rough approximation)
  const estimatedSize = Math.max(0.1, (backendContract.text?.length || 1000) / 1024).toFixed(1);

  const transformedContract = {
    id: backendContract._id,
    title: backendContract.title,
    client: backendContract.client,
    signed: backendContract.signed,
    status,
    uploadDate: backendContract.date || backendContract.created_at.split('T')[0],
    fileSize: `${estimatedSize} KB`,
    analysisResults: (backendContract.analysis && backendContract.analysis.analysis) ? {
      approved: status === 'approved',
      reasoning: backendContract.evaluation_reasoning || backendContract.analysis.analysis,
      clauseCount: 0 // We don't have this data from backend
    } : undefined
  };
  
  return transformedContract;
};

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
  }): Promise<{ message: string; contract_id: string }> {
    try {
      const response = await api.post(endpoints.contracts, contractData);
      return response.data;
    } catch (error) {
      console.error('Error creating contract:', error);
      throw error;
    }
  },

  // Update contract
  async updateContract(id: string, contractData: Partial<BackendContract>): Promise<{ message: string }> {
    try {
      const response = await api.put(`${endpoints.contracts}${id}/`, contractData);
      return response.data;
    } catch (error) {
      console.error('Error updating contract:', error);
      throw error;
    }
  },

  // Delete contract
  async deleteContract(id: string): Promise<{ message: string }> {
    try {
      const response = await api.delete(`${endpoints.contracts}${id}/`);
      return response.data;
    } catch (error) {
      console.error('Error deleting contract:', error);
      throw error;
    }
  },

  // Get contract analysis
  async getContractAnalysis(id: string): Promise<{
    analysis: string;
    model_used: string;
    analysis_date: string;
    contract_title: string;
    contract_client: string;
  }> {
    try {
      const response = await api.get(endpoints.contractAnalysis(id));
      return response.data;
    } catch (error) {
      console.error('Error fetching contract analysis:', error);
      throw error;
    }
  },

  // Create new contract with file upload (PDF or text)
  async createContractWithFile(formData: FormData): Promise<{ 
    message: string; 
    contract_id: string;
    analysis?: string;
    model_used?: string;
    approved?: boolean;
    evaluation_reasoning?: string;
  }> {
    try {
      const response = await api.post(endpoints.contracts, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading contract with file:', error);
      throw error;
    }
  }
}; 