'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/auth';
import { contractService, FrontendContract, transformContract } from '@/services/contracts';
import { 
  FileText, 
  Upload, 
  Download, 
  MoreVertical, 
  Search, 
  Grid3X3,
  List,
  ChevronLeft,
  ChevronRight,
  Eye,
  Plus
} from 'lucide-react';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import { createPortal } from 'react-dom';

export default function ContractsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [contracts, setContracts] = useState<FrontendContract[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [clientFilter, setClientFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadClient, setUploadClient] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [selectedContract, setSelectedContract] = useState<FrontendContract | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ top: number; left: number } | null>(null);
  const menuButtonRefs = useRef<{ [key: string]: HTMLButtonElement | null }>({});
  const menuRef = useRef<HTMLDivElement | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editContract, setEditContract] = useState<FrontendContract | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editClient, setEditClient] = useState('');
  const [editSigned, setEditSigned] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const contractsPerPage = 6;
  const totalContracts = contracts.length;
  const totalPages = Math.ceil(totalContracts / contractsPerPage);
  const paginatedContracts = contracts.slice(
    (currentPage - 1) * contractsPerPage,
    currentPage * contractsPerPage
  );
  const [showReanalyzeForm, setShowReanalyzeForm] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [reanalyzeTitle, setReanalyzeTitle] = useState('');
  const reanalyzeFileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'clauses'>('analysis');
  const [extractingClauses, setExtractingClauses] = useState(false);
  const [clauses, setClauses] = useState<any[]>([]);
  const [clausesError, setClausesError] = useState<string | null>(null);

  // List of known error messages from backend
  const KNOWN_ANALYSIS_ERRORS = [
    'Contract analysis temporarily unavailable due to connection issues. Please try again later.',
    'Contract analysis temporarily unavailable due to network timeout. Please try again later.',
    'Contract analysis failed: No successful chunk analyses.',
    'Contract analysis failed: No analysis available.',
  ];

  // Close menu on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuId(null);
        setMenuPosition(null);
      }
    }
    if (openMenuId) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [openMenuId]);

  // Fetch contracts from backend
  const fetchContracts = async () => {
    try {
      const fetchedContracts = await contractService.getContracts();
      setContracts(fetchedContracts);
    } catch (error) {
      console.error('Failed to fetch contracts:', error);
      // You could show a toast notification here
    }
  };

  useEffect(() => {
    const u = authService.getUser();
    if (!u) {
      router.replace('/login');
    } else {
      setUser(u);
      fetchContracts();
    }
    setLoading(false);
  }, [router]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, statusFilter, clientFilter, dateFilter]);

  const getStatusColor = (status: FrontendContract['status']) => {
    switch (status) {
      case 'approved': return '#10B981'; // success
      case 'rejected': return '#EF4444'; // error
      case 'analyzing': return '#3B82F6'; // info
      case 'pending': return '#F59E0B'; // warning
      case 'completed': return '#6B7280'; // gray
      default: return '#6B7280';
    }
  };

  const getStatusBadge = (status: FrontendContract['status']) => {
    switch (status) {
      case 'approved':
        return 'bg-green-500/20 text-green-400';
      case 'rejected':
      case 'completed':
        return 'bg-red-500/20 text-red-400';
      case 'analyzing':
        return 'bg-blue-500/20 text-blue-400 animate-pulse';
      case 'pending':
        return 'bg-yellow-500/20 text-yellow-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  const getStatusLabel = (status: FrontendContract['status']) => {
    switch (status) {
      case 'approved':
        return 'Approved';
      case 'rejected':
      case 'completed':
        return 'Not Approved';
      case 'analyzing':
        return 'Analyzing';
      case 'pending':
        return 'Pending';
      default:
        return 'Unknown';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB');
  };

  const handleUploadContract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadTitle || !uploadClient || !uploadFile) {
      toast.error('Please fill all fields and select a file.');
      return;
    }
    
    // Create immediate contract entry with "analyzing" status
    const immediateContract: FrontendContract = {
      id: `temp-${Date.now()}`, // Temporary ID
      title: uploadTitle,
      client: uploadClient,
      status: 'analyzing',
      uploadDate: new Date().toISOString().split('T')[0],
      fileSize: `${(uploadFile.size / 1024).toFixed(1)} KB`,
      analysisResults: undefined
    };
    
    // Add to contracts list immediately
    setContracts(prev => [immediateContract, ...prev]);
    
    // Close modal and reset form
    setShowUploadModal(false);
    setUploadTitle('');
    setUploadClient('');
    setUploadFile(null);
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('title', uploadTitle);
      formData.append('client', uploadClient);
      formData.append('signed', 'false');
      formData.append('file', uploadFile);
      
      const response = await contractService.createContractWithFile(formData);
      
      // Replace the temporary contract with the real one
      setContracts(prev => prev.map(contract => 
        contract.id === immediateContract.id 
          ? transformContract({
              _id: response.contract_id,
              title: uploadTitle,
              client: uploadClient,
              signed: false,
              text: '', // We don't have the text in response
              date: new Date().toISOString().split('T')[0],
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              analysis: response.analysis ? { analysis: response.analysis, model_used: response.model_used || 'DeepSeek Reasoning Model (Live)' } : undefined,
              model_used: response.model_used || 'DeepSeek Reasoning Model (Live)',
              analysis_date: new Date().toISOString(),
              approved: response.approved,
              evaluation_reasoning: response.evaluation_reasoning
            })
          : contract
      ));
      
      toast.success('Contract uploaded and analyzed successfully!');
    } catch (err) {
      // Remove the temporary contract on error
      setContracts(prev => prev.filter(contract => contract.id !== immediateContract.id));
      toast.error('Failed to upload contract.');
    } finally {
      setUploading(false);
    }
  };

  const handleViewAnalysis = async (contract: FrontendContract) => {
    try {
      if (!contract.id || contract.id === 'undefined' || contract.id === 'null') {
        toast.error('Invalid contract ID');
        return;
      }
      
      // Get the full contract data first
      const fullContract = await contractService.getContract(contract.id);
      
      // If the contract already has analysis results, use those
      if (fullContract.analysis && fullContract.evaluation_reasoning) {
        setSelectedContract({
          ...fullContract,
          analysisResults: {
            approved: fullContract.approved,
            reasoning: fullContract.analysis,
            clauseCount: fullContract.clauses?.length || 0
          }
        });
        setShowAnalysisModal(true);
        return;
      }
      
      // Otherwise, fetch detailed analysis from backend
      const analysis = await contractService.getContractAnalysis(contract.id);
      
      // Check for error in the response
      if ((analysis as any).error) {
        toast.error((analysis as any).error);
        return;
      }
      
      setSelectedContract({
        ...fullContract,
        analysisResults: {
          approved: fullContract.approved,
          reasoning: analysis.analysis,
          clauseCount: fullContract.clauses?.length || 0
        }
      });
      setShowAnalysisModal(true);
    } catch (error) {
      console.error('Error fetching analysis:', error);
      toast.error('Failed to fetch analysis details');
    }
  };

  const handleDeleteContract = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this contract?')) return;
    try {
      await contractService.deleteContract(id);
      toast.success('Contract deleted successfully!');
      fetchContracts();
    } catch (err) {
      toast.error('Failed to delete contract.');
    } finally {
      setOpenMenuId(null);
    }
  };

  const openEditModal = (contract: FrontendContract) => {
    setEditContract(contract);
    setEditTitle(contract.title);
    setEditClient(contract.client || '');
    setEditSigned(!!contract.signed);
    setEditModalOpen(true);
    setOpenMenuId(null);
  };

  const closeEditModal = () => {
    setEditModalOpen(false);
    setEditContract(null);
    setEditTitle('');
    setEditClient('');
    setEditSigned(false);
    setEditLoading(false);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editContract) return;
    if (!editTitle.trim() || !editClient.trim()) {
      toast.error('Title and client are required.');
      return;
    }
    setEditLoading(true);
    try {
      await contractService.updateContract(editContract.id, {
        title: editTitle,
        client: editClient,
        signed: editSigned,
      });
      toast.success('Contract updated successfully!');
      fetchContracts();
      closeEditModal();
    } catch (err) {
      toast.error('Failed to update contract.');
    } finally {
      setEditLoading(false);
    }
  };

  const handleEditContract = (contract: FrontendContract) => {
    openEditModal(contract);
  };

  // Helper to get date range
  function isWithinDateRange(dateString: string, filter: string) {
    const date = new Date(dateString);
    const now = new Date();
    if (filter === 'today') {
      return date.toDateString() === now.toDateString();
    }
    if (filter === 'week') {
      const weekAgo = new Date(now);
      weekAgo.setDate(now.getDate() - 7);
      return date >= weekAgo && date <= now;
    }
    if (filter === 'month') {
      return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
    }
    return true;
  }

  // Extract unique client names from contracts
  const uniqueClients = Array.from(new Set(contracts.map(c => c.client).filter(Boolean))).sort();

  // Compute filtered contracts
  const filteredContracts = contracts.filter(contract => {
    // Search filter (title or client)
    const searchLower = searchQuery.toLowerCase();
    const matchesSearch =
      contract.title.toLowerCase().includes(searchLower) ||
      (contract.client && contract.client.toLowerCase().includes(searchLower));
    if (searchQuery && !matchesSearch) return false;

    // Status filter
    if (statusFilter !== 'all') {
      if (statusFilter === 'approved' && contract.status !== 'approved') return false;
      if (statusFilter === 'rejected' && contract.status !== 'rejected' && contract.analysisResults?.approved !== false) return false;
      if (statusFilter === 'analyzing' && contract.status !== 'analyzing') return false;
      if (statusFilter === 'pending' && contract.status !== 'pending') return false;
      if (statusFilter === 'completed' && contract.status !== 'completed') return false;
    }

    // Client filter
    if (clientFilter !== 'all' && contract.client) {
      if (contract.client !== clientFilter) return false;
    }

    // Date filter
    if (dateFilter !== 'all') {
      if (!isWithinDateRange(contract.uploadDate, dateFilter)) return false;
    }

    return true;
  });

  const handleMenuButtonClick = (contractId: string) => {
    if (openMenuId === contractId) {
      setOpenMenuId(null);
      setMenuPosition(null);
      return;
    }
    const button = menuButtonRefs.current[contractId];
    if (button) {
      const rect = button.getBoundingClientRect();
      setMenuPosition({
        top: rect.top + window.scrollY - 8, // 8px above the button
        left: rect.right + window.scrollX - 160, // align right edge, menu width ~160px
      });
      setOpenMenuId(contractId);
    }
  };

  const handleReanalyzeContract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedContract) return;

    const file = reanalyzeFileInputRef.current?.files?.[0];
    if (!file) {
      toast.error('Please select a file to reanalyze.');
      return;
    }

    setReanalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', reanalyzeTitle || selectedContract.title);
      formData.append('client', selectedContract.client || '');

      const result = await contractService.reanalyzeContract(selectedContract.id, formData);

      // Check for error in the response
      if ((result as any).error) {
        toast.error((result as any).error);
        setReanalyzing(false);
        return;
      }

      // Update the selected contract with new analysis
      setSelectedContract({
        ...selectedContract,
        title: reanalyzeTitle || selectedContract.title,
        status: result.approved ? 'approved' : 'rejected',
        analysisResults: {
          approved: result.approved,
          reasoning: result.evaluation_reasoning || result.analysis,
          clauseCount: 0
        }
      });

      // Update the contract in the list
      setContracts(prevContracts =>
        prevContracts.map(c =>
          c.id === selectedContract.id
            ? {
                ...c,
                title: reanalyzeTitle || selectedContract.title,
                status: result.approved ? 'approved' : 'rejected',
                analysisResults: {
                  approved: result.approved,
                  reasoning: result.evaluation_reasoning || result.analysis,
                  clauseCount: 0
                }
              }
            : c
        )
      );

      toast.success('Contract reanalyzed successfully!');
      setReanalyzeTitle('');
      if (reanalyzeFileInputRef.current) {
        reanalyzeFileInputRef.current.value = '';
      }
      setShowReanalyzeForm(false);
    } catch (error) {
      console.error('Error reanalyzing contract:', error);
      toast.error('Failed to reanalyze contract.');
    } finally {
      setReanalyzing(false);
    }
  };

  const handleExtractClauses = async (contract: FrontendContract) => {
    setExtractingClauses(true);
    setClausesError(null);
    try {
      const result = await contractService.extractClauses(contract.id);
      if ((result as any).error) {
        setClausesError((result as any).error);
        setClauses([]);
      } else {
        setClauses(result.clauses || []);
        setClausesError(null);
        setActiveTab('clauses');
        toast.success(`${result.clause_count || 0} clauses extracted successfully`);
      }
    } catch (error) {
      setClausesError('Failed to extract clauses');
      setClauses([]);
      toast.error('Failed to extract clauses');
    } finally {
      setExtractingClauses(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#121417' }}>
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen" style={{ background: '#121417', fontFamily: 'Inter' }}>
      {/* Header - Matching Dashboard Design */}
      <div className="w-full px-10 py-3 border-b border-white/10 flex justify-between items-center">
        <div className="flex justify-start items-center gap-4">
          <div className="flex flex-col justify-start items-start">
            <div className="w-4 flex-1 relative overflow-hidden">
              <div className="w-4 h-4 absolute bg-white" style={{ left: 0, top: 0 }}></div>
            </div>
          </div>
          <div className="flex flex-col justify-start items-start">
            <div className="text-white text-lg font-bold leading-6" style={{ fontFamily: 'Inter' }}>
              GenAI Platform
            </div>
          </div>
        </div>
        <div className="flex-1 flex justify-end items-start gap-8">
          <div className="w-21 h-10 max-w-120 min-w-21 px-4 overflow-hidden rounded-full flex justify-center items-center" style={{ background: '#293038' }}>
            <div className="overflow-hidden flex flex-col justify-start items-center">
              <button
                onClick={() => authService.logout()}
                className="text-center text-white text-sm font-bold leading-5"
                style={{ fontFamily: 'Inter' }}
              >
                Logout
              </button>
            </div>
          </div>
          <div className="w-10 h-10 relative rounded-full overflow-hidden">
            <div className="w-10 h-10 bg-orange-400 rounded-full flex items-center justify-center text-sm font-semibold text-white">
              {user.username.charAt(0).toUpperCase()}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main>
        <div className="container mx-auto px-10">
          {/* Breadcrumb */}
          <div className="h-10 flex items-center">
            <p className="text-sm" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
              <button onClick={() => router.push('/dashboard')} className="hover:text-white transition-colors">
                Dashboard
              </button>
              <span className="mx-2">/</span>
              <span>Contracts</span>
            </p>
          </div>

          {/* Page Title Section */}
          <div className="py-6 h-[120px] flex items-center justify-between">
            <div>
              <h1 className="text-5xl font-bold text-white" style={{ fontFamily: 'Inter' }}>
                Contracts
              </h1>
              <p className="text-base mt-2" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
                Manage and analyze your legal documents
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button
                type="button"
                className="h-10 px-6 bg-[#293038] text-white rounded-xl text-sm font-medium gap-2 flex items-center hover:opacity-90 transition-all duration-200"
                style={{ fontFamily: 'Inter' }}
                onClick={() => setShowUploadModal(true)}
              >
                <Upload className="w-4 h-4" />
                Upload Contract
              </button>
            </div>
          </div>

          {/* Filters & Search Bar */}
          <div className="my-5 p-6 border rounded-2xl flex items-center gap-4" style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', borderColor: 'rgba(255, 255, 255, 0.1)', backdropFilter: 'blur(10px)' }}>
            {/* Search */}
            <div className="relative flex-grow">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CABBA]" />
              <input
                type="text"
                placeholder="Search contracts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-10 border border-white/20 rounded-xl pl-10 pr-4 text-white text-sm placeholder-[#9CABBA] bg-[#23262B] focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ fontFamily: 'Inter' }}
              />
            </div>

            {/* Status Filter */}
            <select 
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 px-6 border border-white/20 rounded-xl text-white text-sm bg-[#23262B] appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{ fontFamily: 'Inter' }}
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="analyzing">Analyzing</option>
              <option value="completed">Completed</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>

            {/* Client Filter */}
            <select 
              value={clientFilter}
              onChange={(e) => setClientFilter(e.target.value)}
              className="h-10 px-6 border border-white/20 rounded-xl text-white text-sm bg-[#23262B] appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{ fontFamily: 'Inter' }}
            >
              <option value="all">All Clients</option>
              {uniqueClients.map(client => (
                <option key={client} value={client}>{client}</option>
              ))}
            </select>

            {/* Date Filter */}
            <select 
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="h-10 px-6 border border-white/20 rounded-xl text-white text-sm bg-[#23262B] appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{ fontFamily: 'Inter' }}
            >
              <option value="all">All Dates</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
            </select>
          </div>

          {/* Contracts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 py-6">
            {paginatedContracts.map((contract) => (
              <div
                key={contract.id}
                className="relative overflow-hidden rounded-2xl transition-transform duration-200 ease-out hover:scale-[1.02]"
                style={{ width: '100%', height: 280, background: '#23262B' }}
              >
                {/* Top (Preview) Section */}
                <div
                  className="absolute flex items-center justify-center rounded-t-2xl"
                  style={{ width: 'calc(100% - 12px)', height: 140, left: 6, top: 6, background: '#23262B' }}
                >
                  <FileText 
                    className="absolute text-gray-600"
                    style={{ width: 32, height: 40, left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
                  />
                  <div 
                    className="absolute rounded-full"
                    style={{ 
                      width: 12, 
                      height: 12, 
                      right: 12, 
                      top: 12,
                      backgroundColor: getStatusColor(contract.status)
                    }}
                  />
                </div>

                {/* Bottom (Content) Section */}
                <div
                  className="absolute rounded-b-2xl"
                  style={{ width: 'calc(100% - 12px)', height: 128, left: 6, top: 146, background: '#23262B' }}
                >
                  <div className="absolute inset-0 p-4 flex flex-col justify-between">
                    {/* Top Section */}
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <h3 
                          className="text-sm font-bold text-white leading-tight pr-2"
                          style={{ fontFamily: 'Inter', fontSize: '14px' }}
                        >
                          {contract.title}
                        </h3>
                        <p 
                          className="text-xs whitespace-nowrap"
                          style={{ color: '#6B7580', fontFamily: 'Inter', fontSize: '11px' }}
                        >
                          {contract.fileSize}
                        </p>
                      </div>
                      <div className="flex justify-between items-center">
                        <p 
                          className="text-xs"
                          style={{ color: '#6B757F', fontFamily: 'Inter', fontSize: '12px' }}
                        >
                          {contract.client || 'No client'}
                        </p>
                        <p 
                          className="text-xs"
                          style={{ color: '#646D77', fontFamily: 'Inter', fontSize: '11px' }}
                        >
                          {formatDate(contract.uploadDate)}
                        </p>
                      </div>
                    </div>
                    
                    {/* Bottom Section */}
                    <div className="flex justify-between items-center">
                      <span
                        className={`text-xs font-bold px-4 py-2 rounded-full ${getStatusBadge(contract.status)}`}
                        style={{ fontFamily: 'Inter', color: '#fff', boxShadow: '0 1px 2px 0 rgba(0,0,0,0.04)' }}
                      >
                        {getStatusLabel(contract.status)}
                      </span>
                      
                      <div className="flex items-center gap-2">
                        <button 
                          onClick={() => handleViewAnalysis(contract)}
                          className="h-6 px-3 text-white rounded text-xs font-medium flex items-center gap-1 hover:opacity-90 transition-opacity"
                          style={{ backgroundColor: '#293038', fontFamily: 'Inter', fontSize: '10px' }}
                        >
                          <Eye className="w-3 h-3" />
                          View
                        </button>
                        <button
                          ref={(el) => {
                            menuButtonRefs.current[contract.id] = el;
                          }}
                          onClick={() => handleMenuButtonClick(contract.id)}
                          className="w-6 h-6 flex items-center justify-center rounded hover:bg-[#23262B] transition-colors"
                          style={{ color: '#9CABBA' }}
                        >
                          <MoreVertical className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <div className="h-[60px] flex items-center justify-center gap-8">
            <div className="flex items-center gap-2">
              <button
                className="w-8 h-8 flex items-center justify-center rounded text-white"
                style={{ backgroundColor: '#293038' }}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: totalPages }, (_, i) => (
                <button
                  key={i + 1}
                  className={`w-8 h-8 flex items-center justify-center rounded ${currentPage === i + 1 ? 'text-white' : ''}`}
                  style={{
                    backgroundColor: currentPage === i + 1 ? '#293038' : undefined,
                    color: currentPage === i + 1 ? '#fff' : '#9CABBA',
                    fontFamily: 'Inter',
                  }}
                  onClick={() => setCurrentPage(i + 1)}
                >
                  {i + 1}
                </button>
              ))}
              <button
                className="w-8 h-8 flex items-center justify-center rounded text-white"
                style={{ backgroundColor: '#293038' }}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
              {`Showing ${totalContracts === 0 ? 0 : (currentPage - 1) * contractsPerPage + 1}-${Math.min(currentPage * contractsPerPage, totalContracts)} of ${totalContracts} contracts`}
            </p>
          </div>
        </div>
      </main>

      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#181A1D] rounded-2xl p-8 w-full max-w-md shadow-xl relative">
            <button
              className="absolute top-4 right-4 text-[#9CABBA] hover:text-white"
              onClick={() => setShowUploadModal(false)}
            >
              ×
            </button>
            <h2 className="text-xl font-bold mb-4 text-white">Upload Contract</h2>
            <form onSubmit={handleUploadContract} className="flex flex-col gap-4">
              <input
                type="text"
                placeholder="Title"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={uploadTitle}
                onChange={e => setUploadTitle(e.target.value)}
              />
              <input
                type="text"
                placeholder="Client"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={uploadClient}
                onChange={e => setUploadClient(e.target.value)}
              />
              <div className="relative">
                <input
                  id="contract-file-upload"
                  type="file"
                  accept=".pdf,.txt"
                  className="hidden"
                  ref={fileInputRef}
                  onChange={e => setUploadFile(e.target.files?.[0] || null)}
                />
                <label
                  htmlFor="contract-file-upload"
                  className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm flex items-center justify-center cursor-pointer w-full focus:outline-none"
                  style={{ fontFamily: 'Inter' }}
                >
                  {uploadFile ? uploadFile.name : 'Choose File (PDF or TXT)'}
                </label>
              </div>
              <button
                type="submit"
                className="h-10 px-6 bg-[#293038] text-white rounded-xl text-sm font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-all duration-200"
                style={{ fontFamily: 'Inter' }}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Analysis Modal */}
      {showAnalysisModal && selectedContract && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#181A1D] rounded-2xl p-8 w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-xl relative" style={{ fontFamily: 'Inter', zIndex: 10000 }}>
            <button
              className="absolute top-4 right-4 text-[#9CABBA] hover:text-white text-2xl"
              onClick={() => setShowAnalysisModal(false)}
            >
              ×
            </button>
            <div className="space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">{selectedContract.title}</h2>
                  <div className="flex items-center gap-4 mb-2">
                    <p className="text-[#9CABBA]">Client: {selectedContract.client}</p>
                    <span className={`px-3 py-1 rounded-full text-sm ${getStatusBadge(selectedContract.status)}`}>
                      {getStatusLabel(selectedContract.status)}
                    </span>
                  </div>
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => setShowReanalyzeForm(true)}
                      className="h-8 px-4 text-white rounded text-xs font-medium hover:opacity-90 transition-opacity"
                      style={{ backgroundColor: '#293038', fontFamily: 'Inter', fontSize: '12px' }}
                    >
                      Reanalyze
                    </button>
                    <button
                      onClick={() => handleExtractClauses(selectedContract)}
                      className="h-8 px-4 text-white rounded text-xs font-medium hover:opacity-90 transition-opacity"
                      style={{ backgroundColor: extractingClauses ? '#6B7280' : '#23262B', fontFamily: 'Inter', fontSize: '12px' }}
                      disabled={extractingClauses}
                    >
                      {extractingClauses ? 'Extracting...' : 'Extract Clauses'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-2 border-b border-[#23262B] mb-2">
                <button
                  className={`px-4 py-2 text-sm font-medium rounded-t ${activeTab === 'analysis' ? 'bg-[#23262B] text-white' : 'text-[#9CABBA]'}`}
                  onClick={() => setActiveTab('analysis')}
                >
                  AI Analysis
                </button>
                <button
                  className={`px-4 py-2 text-sm font-medium rounded-t ${activeTab === 'clauses' ? 'bg-[#23262B] text-white' : 'text-[#9CABBA]'}`}
                  onClick={() => setActiveTab('clauses')}
                >
                  Extracted Clauses
                </button>
              </div>

              {/* Tab Content */}
              {activeTab === 'analysis' && (
                showReanalyzeForm ? (
                  <div className="bg-[#23262B] rounded-xl p-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-semibold text-white" style={{ fontFamily: 'Inter' }}>Reanalyze Contract</h3>
                      <button
                        onClick={() => {
                          setShowReanalyzeForm(false);
                          setReanalyzeTitle('');
                          if (reanalyzeFileInputRef.current) {
                            reanalyzeFileInputRef.current.value = '';
                          }
                        }}
                        className="text-[#9CABBA] hover:text-white"
                      >
                        ×
                      </button>
                    </div>
                    <form onSubmit={handleReanalyzeContract} className="space-y-4">
                      <label className="block text-sm font-medium text-[#9CABBA] mb-2" style={{ fontFamily: 'Inter' }}>
                        New Title (optional)
                      </label>
                      <input
                        type="text"
                        value={reanalyzeTitle}
                        onChange={(e) => setReanalyzeTitle(e.target.value)}
                        placeholder={selectedContract.title}
                        className="w-full h-10 px-3 bg-[#181A1D] border border-[#2A2D31] rounded-lg text-white placeholder-[#6B7280] focus:outline-none focus:ring-2 focus:ring-blue-500"
                        style={{ fontFamily: 'Inter' }}
                      />
                      <div>
                        <label className="block text-sm font-medium text-[#9CABBA] mb-2" style={{ fontFamily: 'Inter' }}>
                          Upload New Contract File
                        </label>
                        <div className="flex gap-4">
                          <input
                            ref={reanalyzeFileInputRef}
                            type="file"
                            accept=".pdf,.txt"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file && !reanalyzeTitle) {
                                setReanalyzeTitle(file.name.split('.')[0]);
                              }
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => reanalyzeFileInputRef.current?.click()}
                            className="h-10 px-4 bg-[#181A1D] border border-[#2A2D31] rounded-lg text-white text-sm font-medium hover:bg-[#23262B] transition-colors flex items-center gap-2"
                            style={{ fontFamily: 'Inter' }}
                          >
                            <Upload className="w-4 h-4" />
                            Select File
                          </button>
                          <button
                            type="submit"
                            disabled={reanalyzing || !reanalyzeFileInputRef.current?.files?.[0]}
                            className="h-10 px-6 bg-blue-500 rounded-lg text-white text-sm font-medium hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            style={{ fontFamily: 'Inter' }}
                          >
                            {reanalyzing ? (
                              <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Analyzing...
                              </>
                            ) : (
                              'Analyze Contract'
                            )}
                          </button>
                        </div>
                      </div>
                    </form>
                  </div>
                ) : (
                  selectedContract.analysisResults ? (
                    <div className="bg-[#23262B] rounded-xl p-6" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                      <h3 className="text-lg font-semibold mb-4 text-white" style={{ fontFamily: 'Inter' }}>AI Analysis Results</h3>
                      <div className="text-sm text-[#9CABBA] leading-relaxed" style={{ fontFamily: 'Inter' }}>
                        {KNOWN_ANALYSIS_ERRORS.includes(selectedContract.analysisResults.reasoning.trim()) ? (
                          <span>No analysis results available. Please try reanalyzing the contract.</span>
                        ) : (
                          <AnalysisMarkdown markdown={selectedContract.analysisResults.reasoning} />
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-[#9CABBA]" style={{ fontFamily: 'Inter' }}>No analysis results available</p>
                    </div>
                  )
                )
              )}
              {activeTab === 'clauses' && (
                <div className="bg-[#23262B] rounded-xl p-6" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                  <h3 className="text-lg font-semibold mb-4 text-white" style={{ fontFamily: 'Inter' }}>Extracted Clauses</h3>
                  {clausesError ? (
                    <div className="text-red-400 mb-2">{clausesError}</div>
                  ) : extractingClauses ? (
                    <div className="text-[#9CABBA]">Extracting clauses...</div>
                  ) : clauses.length === 0 ? (
                    <div className="text-[#9CABBA]">No clauses extracted yet. Click "Extract Clauses" to begin.</div>
                  ) : (
                    <div className="space-y-4">
                      {clauses.map((clause, idx) => (
                        <div key={idx} className="p-4 rounded-lg bg-[#181A1D] border border-[#23262B]">
                          <div className="flex flex-wrap gap-2 mb-1">
                            <span className="text-xs font-semibold text-blue-400">{clause.type}</span>
                            <span className={`text-xs font-semibold rounded px-2 py-0.5 ${clause.risk_level === 'high' ? 'bg-red-500/20 text-red-400' : clause.risk_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>{clause.risk_level}</span>
                          </div>
                          <div className="text-sm text-white mb-2" style={{ fontFamily: 'Inter' }}>
                            {clause.content}
                          </div>
                          {clause.obligations && clause.obligations.length > 0 && (
                            <div className="text-xs text-[#9CABBA]">
                              <span className="font-semibold">Obligations:</span> {clause.obligations.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {editModalOpen && editContract && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#181A1D] rounded-2xl p-8 w-full max-w-md shadow-xl relative" style={{ fontFamily: 'Inter' }}>
            <button
              className="absolute top-4 right-4 text-[#9CABBA] hover:text-white text-2xl"
              onClick={closeEditModal}
            >
              ×
            </button>
            <h2 className="text-xl font-bold mb-4 text-white">Edit Contract</h2>
            <form onSubmit={handleEditSubmit} className="flex flex-col gap-4">
              <input
                type="text"
                placeholder="Title"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={editTitle}
                onChange={e => setEditTitle(e.target.value)}
              />
              <input
                type="text"
                placeholder="Client"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={editClient}
                onChange={e => setEditClient(e.target.value)}
              />
              <label className="flex items-center gap-2 text-white text-sm" style={{ fontFamily: 'Inter' }}>
                <input
                  type="checkbox"
                  checked={editSigned}
                  onChange={e => setEditSigned(e.target.checked)}
                  className="accent-blue-500"
                />
                Signed
              </label>
              <div className="flex gap-4 mt-2">
                <button
                  type="button"
                  className="h-10 px-6 bg-[#23262B] text-white rounded-xl text-sm font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-all duration-200 border border-white/20"
                  style={{ fontFamily: 'Inter' }}
                  onClick={closeEditModal}
                  disabled={editLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="h-10 px-6 bg-[#293038] text-white rounded-xl text-sm font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-all duration-200"
                  style={{ fontFamily: 'Inter' }}
                  disabled={editLoading}
                >
                  {editLoading ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {openMenuId && menuPosition && (
        <DropdownMenu
          top={menuPosition.top}
          left={menuPosition.left}
          onEdit={() => handleEditContract(contracts.find(c => c.id === openMenuId)!)}
          onDelete={() => handleDeleteContract(openMenuId)}
          onClose={() => {
            setOpenMenuId(null);
            setMenuPosition(null);
          }}
        />
      )}
    </div>
  );
}

function AnalysisMarkdown({ markdown }: { markdown: string }) {
  // Remove the first summary line if it matches the pattern
  const lines = markdown.split('\n');
  if (lines[0].match(/^\d+\. \*\*.+\*\*/)) {
    lines.shift();
  }
  const cleanedText = lines.join('\n');
  return (
    <ReactMarkdown
      components={{
        h1: ({node, ...props}) => <h1 style={{fontFamily: 'Inter', fontWeight: 700, fontSize: '1.5rem', color: 'white', marginBottom: 12}} {...props} />,
        h2: ({node, ...props}) => <h2 style={{fontFamily: 'Inter', fontWeight: 600, fontSize: '1.2rem', color: 'white', marginBottom: 10}} {...props} />,
        h3: ({node, ...props}) => <h3 style={{fontFamily: 'Inter', fontWeight: 600, fontSize: '1.1rem', color: 'white', marginBottom: 8}} {...props} />,
        strong: ({node, ...props}) => <strong style={{color: 'white'}} {...props} />,
        li: ({node, ...props}) => <li style={{marginBottom: 4, fontFamily: 'Inter', color: '#9CABBA'}} {...props} />,
        p: ({node, ...props}) => <p style={{marginBottom: 8, fontFamily: 'Inter', color: '#9CABBA'}} {...props} />,
        ul: ({node, ...props}) => <ul style={{marginBottom: 8, paddingLeft: 20}} {...props} />,
      }}
    >
      {cleanedText}
    </ReactMarkdown>
  );
}

function DropdownMenu({ top, left, onEdit, onDelete, onClose }: { top: number; left: number; onEdit: () => void; onDelete: () => void; onClose: () => void }) {
  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return createPortal(
    <div
      style={{
        position: 'absolute',
        top,
        left,
        zIndex: 9999,
        minWidth: 160,
        background: '#23262B',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 12,
        boxShadow: '0 8px 32px 0 rgba(0,0,0,0.25)',
        fontFamily: 'Inter',
        padding: '8px 0',
      }}
    >
      <button
        onClick={onEdit}
        className="px-4 py-2 text-left text-sm text-white hover:bg-[#293038] transition-colors w-full"
      >
        Edit
      </button>
      <div className="h-px bg-white/10 my-1 w-full" />
      <button
        onClick={onDelete}
        className="px-4 py-2 text-left text-sm text-red-400 hover:bg-red-500/20 transition-colors w-full"
      >
        Delete
      </button>
    </div>,
    document.body
  );
}