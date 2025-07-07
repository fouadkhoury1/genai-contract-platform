'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/auth';
import { clientService, FrontendClient } from '@/services/clients';
import { transformContract } from '@/services/contracts';
import { 
  User, 
  Plus, 
  MoreVertical, 
  Search, 
  ChevronLeft,
  ChevronRight,
  Eye,
  Mail,
  Building
} from 'lucide-react';
import toast from 'react-hot-toast';
import { createPortal } from 'react-dom';

export default function ClientsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [clients, setClients] = useState<FrontendClient[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createEmail, setCreateEmail] = useState('');
  const [createCompanyId, setCreateCompanyId] = useState('');
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ top: number; left: number } | null>(null);
  const menuButtonRefs = useRef<{ [key: string]: HTMLButtonElement | null }>({});
  const menuRef = useRef<HTMLDivElement | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editClient, setEditClient] = useState<FrontendClient | null>(null);
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editCompanyId, setEditCompanyId] = useState('');
  const [editLoading, setEditLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const clientsPerPage = 6;
  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (client.email && client.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (client.company_id && client.company_id.toLowerCase().includes(searchQuery.toLowerCase()))
  );
  const totalClients = filteredClients.length;
  const totalPages = Math.ceil(totalClients / clientsPerPage);
  const paginatedClients = filteredClients.slice(
    (currentPage - 1) * clientsPerPage,
    currentPage * clientsPerPage
  );
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedClient, setSelectedClient] = useState<FrontendClient | null>(null);
  const [clientContracts, setClientContracts] = useState<any[]>([]);
  const [loadingContracts, setLoadingContracts] = useState(false);
  const [editActive, setEditActive] = useState(true);

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

  // Fetch clients from backend
  const fetchClients = async () => {
    try {
      const fetchedClients = await clientService.getClients();
      setClients(fetchedClients);
    } catch (error) {
      toast.error('Failed to fetch clients');
    }
  };

  useEffect(() => {
    const u = authService.getUser();
    if (!u) {
      router.replace('/login');
    } else {
      setUser(u);
      fetchClients();
    }
    setLoading(false);
  }, [router]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusLabel = (status: string) => {
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

  const getContractStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return '#10B981';
      case 'rejected':
      case 'completed':
        return '#EF4444';
      case 'analyzing':
        return '#3B82F6';
      case 'pending':
        return '#F59E0B';
      default:
        return '#6B7280';
    }
  };

  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim()) {
      toast.error('Please enter a client name.');
      return;
    }
    
    setCreating(true);
    try {
      const newClient = await clientService.createClient({
        name: createName.trim(),
        email: createEmail.trim() || undefined,
        company_id: createCompanyId.trim() || undefined,
      });
      
      setClients(prev => [newClient, ...prev]);
      setShowCreateModal(false);
      setCreateName('');
      setCreateEmail('');
      setCreateCompanyId('');
      toast.success('Client created successfully!');
    } catch (error: any) {
      toast.error(error.message || 'Failed to create client');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteClient = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this client?')) return;
    try {
      await clientService.deleteClient(id);
      toast.success('Client deleted successfully!');
      fetchClients();
    } catch (err) {
      toast.error('Failed to delete client.');
    } finally {
      setOpenMenuId(null);
    }
  };

  const handleViewClient = async (client: FrontendClient) => {
    try {
      setSelectedClient(client);
      setLoadingContracts(true);
      setShowViewModal(true);
      const contracts = await clientService.getClientContracts(client.id);
      setClientContracts(contracts.map(transformContract));
    } catch (error) {
      toast.error('Failed to fetch client contracts');
    } finally {
      setLoadingContracts(false);
    }
  };

  const openEditModal = (client: FrontendClient) => {
    setEditClient(client);
    setEditName(client.name);
    setEditEmail(client.email || '');
    setEditCompanyId(client.company_id || '');
    setEditActive(client.active !== false);
    setEditModalOpen(true);
    setOpenMenuId(null);
    setMenuPosition(null);
  };

  const closeEditModal = () => {
    setEditModalOpen(false);
    setEditClient(null);
    setEditName('');
    setEditEmail('');
    setEditCompanyId('');
    setEditActive(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editClient || !editName.trim()) {
      toast.error('Please enter a client name.');
      return;
    }
    
    setEditLoading(true);
    try {
      const updatedClient = await clientService.updateClient(editClient.id, {
        name: editName.trim(),
        email: editEmail.trim() || undefined,
        company_id: editCompanyId.trim() || undefined,
        active: editActive,
      } as any);
      
      setClients(prev => prev.map(client => 
        client.id === editClient.id ? updatedClient : client
      ));
      closeEditModal();
      toast.success('Client updated successfully!');
    } catch (error: any) {
      toast.error(error.message || 'Failed to update client');
    } finally {
      setEditLoading(false);
    }
  };

  const handleMenuButtonClick = (clientId: string) => {
    const button = menuButtonRefs.current[clientId];
    if (button) {
      const rect = button.getBoundingClientRect();
      setMenuPosition({ top: rect.bottom + 5, left: rect.left });
      setOpenMenuId(clientId);
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
              <span>Clients</span>
            </p>
          </div>

          {/* Page Title Section */}
          <div className="py-6 h-[120px] flex items-center justify-between">
            <div>
              <h1 className="text-5xl font-bold text-white" style={{ fontFamily: 'Inter' }}>
                Clients
              </h1>
              <p className="text-base mt-2" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
                Manage your client relationships
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button
                type="button"
                className="h-10 px-6 bg-[#293038] text-white rounded-xl text-sm font-medium gap-2 flex items-center hover:opacity-90 transition-all duration-200"
                style={{ fontFamily: 'Inter' }}
                onClick={() => setShowCreateModal(true)}
              >
                <Plus className="w-4 h-4" />
                New Client
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
                placeholder="Search clients..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-10 border border-white/20 rounded-xl pl-10 pr-4 text-white text-sm placeholder-[#9CABBA] bg-[#23262B] focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ fontFamily: 'Inter' }}
              />
            </div>
          </div>

          {/* Clients Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 py-6">
            {paginatedClients.map((client) => (
              <div
                key={client.id}
                className="relative overflow-hidden rounded-2xl transition-transform duration-200 ease-out hover:scale-[1.02]"
                style={{ width: '100%', height: 280, background: '#23262B' }}
              >
                {/* Top (Preview) Section */}
                <div
                  className="absolute flex items-center justify-center rounded-t-2xl"
                  style={{ width: 'calc(100% - 12px)', height: 140, left: 6, top: 6, background: '#23262B' }}
                >
                  <User 
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
                      backgroundColor: '#10B981' // Green for active clients
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
                          {client.name}
                        </h3>
                        <p 
                          className="text-xs whitespace-nowrap"
                          style={{ color: '#6B7580', fontFamily: 'Inter', fontSize: '11px' }}
                        >
                          {client.company_id || 'No ID'}
                        </p>
                      </div>
                      <div className="flex justify-between items-center">
                        <p 
                          className="text-xs"
                          style={{ color: '#6B757F', fontFamily: 'Inter', fontSize: '12px' }}
                        >
                          {client.email || 'No email'}
                        </p>
                        <p 
                          className="text-xs"
                          style={{ color: '#646D77', fontFamily: 'Inter', fontSize: '11px' }}
                        >
                          {formatDate(client.created_at)}
                        </p>
                      </div>
                    </div>
                    
                    {/* Bottom Section */}
                    <div className="flex justify-between items-center">
                      {client.active !== false ? (
                        <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-green-600/20 text-green-400 border border-green-400" style={{ fontFamily: 'Inter', minWidth: 70, textAlign: 'center', fontWeight: 700, letterSpacing: 0.2, borderRadius: 9999, fontSize: 13 }}>
                          Active
                        </span>
                      ) : (
                        <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-red-600/20 text-red-400 border border-red-400" style={{ fontFamily: 'Inter', minWidth: 70, textAlign: 'center', fontWeight: 700, letterSpacing: 0.2, borderRadius: 9999, fontSize: 13 }}>
                          Not Active
                        </span>
                      )}
                      
                      <div className="flex items-center gap-2">
                        <button 
                          onClick={() => handleViewClient(client)}
                          className="h-6 px-3 text-white rounded text-xs font-medium flex items-center gap-1 hover:opacity-90 transition-opacity"
                          style={{ backgroundColor: '#293038', fontFamily: 'Inter', fontSize: '10px' }}
                        >
                          <Eye className="w-3 h-3" />
                          View
                        </button>
                        <button
                          ref={(el) => {
                            menuButtonRefs.current[client.id] = el;
                          }}
                          onClick={() => handleMenuButtonClick(client.id)}
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
              {`Showing ${totalClients === 0 ? 0 : (currentPage - 1) * clientsPerPage + 1}-${Math.min(currentPage * clientsPerPage, totalClients)} of ${totalClients} clients`}
            </p>
          </div>
        </div>
      </main>

      {/* Create Client Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#181A1D] rounded-2xl p-8 w-full max-w-md shadow-xl relative">
            <button
              className="absolute top-4 right-4 text-[#9CABBA] hover:text-white"
              onClick={() => setShowCreateModal(false)}
            >
              ×
            </button>
            <h2 className="text-xl font-bold mb-4 text-white">Create New Client</h2>
            <form onSubmit={handleCreateClient} className="flex flex-col gap-4">
              <input
                type="text"
                placeholder="Client Name *"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={createName}
                onChange={e => setCreateName(e.target.value)}
                required
              />
              <input
                type="email"
                placeholder="Email Address"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={createEmail}
                onChange={e => setCreateEmail(e.target.value)}
              />
              <input
                type="text"
                placeholder="Company ID"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={createCompanyId}
                onChange={e => setCreateCompanyId(e.target.value)}
              />
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 h-10 px-4 border border-white/20 text-white rounded-xl text-sm font-medium hover:opacity-90 transition-all duration-200"
                  style={{ fontFamily: 'Inter' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 h-10 px-4 bg-[#3B82F6] text-white rounded-xl text-sm font-medium hover:bg-[#2563EB] transition-all duration-200 disabled:opacity-50"
                  style={{ fontFamily: 'Inter' }}
                >
                  {creating ? 'Creating...' : 'Create Client'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Client Modal */}
      {editModalOpen && editClient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#181A1D] rounded-2xl p-8 w-full max-w-md shadow-xl relative">
            <button
              className="absolute top-4 right-4 text-[#9CABBA] hover:text-white"
              onClick={closeEditModal}
            >
              ×
            </button>
            <h2 className="text-xl font-bold mb-4 text-white">Edit Client</h2>
            <form onSubmit={handleEditSubmit} className="flex flex-col gap-4">
              <input
                type="text"
                placeholder="Client Name *"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={editName}
                onChange={e => setEditName(e.target.value)}
                required
              />
              <input
                type="email"
                placeholder="Email Address"
                className="h-10 px-4 rounded-xl border border-white/20 bg-[#23262B] text-white text-sm focus:outline-none"
                style={{ fontFamily: 'Inter' }}
                value={editEmail}
                onChange={e => setEditEmail(e.target.value)}
              />
              <div className="flex items-center gap-2 mt-2">
                <input
                  type="checkbox"
                  id="edit-active"
                  checked={editActive}
                  onChange={e => setEditActive(e.target.checked)}
                  className="form-checkbox h-4 w-4 text-green-500 border-gray-300 rounded focus:ring-green-500"
                />
                <label htmlFor="edit-active" className="text-sm text-white" style={{ fontFamily: 'Inter' }}>
                  Active
                </label>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeEditModal}
                  className="flex-1 h-10 px-4 border border-white/20 text-white rounded-xl text-sm font-medium hover:opacity-90 transition-all duration-200"
                  style={{ fontFamily: 'Inter' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editLoading}
                  className="flex-1 h-10 px-4 bg-[#3B82F6] text-white rounded-xl text-sm font-medium hover:bg-[#2563EB] transition-all duration-200 disabled:opacity-50"
                  style={{ fontFamily: 'Inter' }}
                >
                  {editLoading ? 'Updating...' : 'Update Client'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Client Contracts Modal */}
      {showViewModal && selectedClient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#181A1D] rounded-2xl p-8 w-full max-w-4xl shadow-xl relative max-h-[80vh] overflow-hidden">
            <button
              className="absolute top-4 right-4 text-[#9CABBA] hover:text-white"
              onClick={() => setShowViewModal(false)}
            >
              ×
            </button>
            <h2 className="text-xl font-bold mb-4 text-white">Contracts for {selectedClient.name}</h2>
            
            {loadingContracts ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
              </div>
            ) : clientContracts.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-[#9CABBA] text-lg">No contracts found for this client.</p>
              </div>
            ) : (
              <div className="overflow-y-auto max-h-[60vh]">
                <div className="space-y-3">
                  {clientContracts.map((contract: any) => (
                    <div
                      key={contract.id}
                      className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-[#23262B] hover:bg-[#2A2D31] transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-white font-semibold text-sm">
                            {contract.title}
                          </h3>
                          <span
                            className="text-xs font-bold px-3 py-1 rounded-full"
                            style={{ 
                              backgroundColor: getContractStatusColor(contract.status || 'pending'),
                              color: '#fff'
                            }}
                          >
                            {getStatusLabel(contract.status || 'pending')}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-[#6B757F]">
                            {formatDate(contract.date || contract.created_at)}
                          </span>
                          <span className={`text-xs font-medium ${contract.signed ? 'text-green-400' : 'text-red-400'}`}>
                            {contract.signed ? 'Signed' : 'Not Signed'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowViewModal(false)}
                className="px-6 py-2 bg-[#293038] text-white rounded-xl text-sm font-medium hover:opacity-90 transition-all duration-200"
                style={{ fontFamily: 'Inter' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dropdown Menu */}
      {openMenuId && menuPosition && createPortal(
        <DropdownMenu
          top={menuPosition.top}
          left={menuPosition.left}
          onView={() => {
            const client = clients.find(c => c.id === openMenuId);
            if (client) handleViewClient(client);
          }}
          onEdit={() => {
            const client = clients.find(c => c.id === openMenuId);
            if (client) openEditModal(client);
          }}
          onDelete={() => handleDeleteClient(openMenuId)}
          onClose={() => {
            setOpenMenuId(null);
            setMenuPosition(null);
          }}
        />,
        document.body
      )}
    </div>
  );
}

function DropdownMenu({ top, left, onView, onEdit, onDelete, onClose }: { top: number; left: number; onView: () => void; onEdit: () => void; onDelete: () => void; onClose: () => void }) {
  const menuRef = useRef<HTMLDivElement | null>(null);
  function handleEscape(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  useEffect(() => {
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-[#23262B] border border-white/10 rounded-lg shadow-lg py-1 min-w-[120px]"
      style={{ top, left }}
    >
      <button
        onClick={onEdit}
        className="w-full px-4 py-2 text-left text-white hover:bg-white/10 transition-colors text-sm"
        style={{ fontFamily: 'Inter' }}
      >
        Edit
      </button>
      <div className="border-t border-white/10 my-1"></div>
      <button
        onClick={onDelete}
        className="w-full px-4 py-2 text-left text-red-400 hover:bg-white/10 transition-colors text-sm"
        style={{ fontFamily: 'Inter' }}
      >
        Delete
      </button>
    </div>
  );
} 