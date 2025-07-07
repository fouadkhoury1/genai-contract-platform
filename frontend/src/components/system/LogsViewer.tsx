'use client';

import { useEffect, useState } from 'react';
import { api, endpoints } from '@/lib/api';
import { Search, X } from 'lucide-react';

interface LogEntry {
  _id: string;
  user: string | null;
  endpoint: string;
  method: string;
  date: string;
  status: number;
}

interface LogsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: LogEntry[];
}

export default function LogsViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    user: '',
    endpoint: '',
    date: '',
    status: '',
  });
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  const [debouncedFilters, setDebouncedFilters] = useState(filters);

  // Debounce filter changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilters(filters);
    }, 500);

    return () => clearTimeout(timer);
  }, [filters]);

  // Fetch logs when debounced filters or page changes
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        const queryParams = new URLSearchParams({
          page: page.toString(),
        });

        // Only add filters that have values
        if (debouncedFilters.user.trim()) {
          queryParams.append('user', debouncedFilters.user.trim());
        }
        if (debouncedFilters.endpoint.trim()) {
          queryParams.append('endpoint', debouncedFilters.endpoint.trim());
        }
        if (debouncedFilters.date.trim()) {
          // Ensure date is in YYYY-MM-DD format
          const dateValue = debouncedFilters.date.trim();
          if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
            queryParams.append('date', dateValue);
          }
        }
        if (debouncedFilters.status.trim()) {
          // Ensure status is a valid number
          const statusValue = parseInt(debouncedFilters.status.trim());
          if (!isNaN(statusValue)) {
            queryParams.append('status', statusValue.toString());
          }
        }

        const response = await api.get<LogsResponse>(`${endpoints.logs}?${queryParams}`);
        setLogs(response.data.results);
        setTotalPages(Math.ceil(response.data.count / 10)); // Assuming page_size=10
        setError(null);
      } catch (err) {
        setError('Failed to fetch logs');
        console.error('Logs fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, [debouncedFilters, page]);

  const handleFilterChange = (key: keyof typeof filters, value: string) => {
    // Validate date format
    if (key === 'date' && value) {
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      if (!dateRegex.test(value) && value.length === 10) {
        return; // Don't update if invalid format
      }
    }

    // Validate status as number
    if (key === 'status' && value) {
      const statusValue = parseInt(value);
      if (isNaN(statusValue) && value !== '') {
        return; // Don't update if not a number
      }
    }

    if (value && !activeFilters.includes(key)) {
      setActiveFilters([...activeFilters, key]);
    } else if (!value) {
      setActiveFilters(activeFilters.filter(f => f !== key));
    }

    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1); // Reset to first page when filters change
  };

  const clearFilter = (key: keyof typeof filters) => {
    handleFilterChange(key, '');
  };

  const clearAllFilters = () => {
    setFilters({ user: '', endpoint: '', date: '', status: '' });
    setActiveFilters([]);
    setPage(1);
  };

  if (error) {
    return (
      <div className="p-4 bg-red-900/30 text-red-400 rounded-xl">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* User Filter */}
        <div className="relative">
          <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-[#9CABBA]" />
          </div>
          <input
            type="text"
            placeholder="Filter by user"
            className="pl-10 pr-8 py-2 w-full bg-[#1A1D21]/60 rounded-xl text-white placeholder:text-[#9CABBA] focus:outline-none focus:ring-2 focus:ring-[#2D3139]"
            value={filters.user}
            onChange={(e) => handleFilterChange('user', e.target.value)}
          />
          {activeFilters.includes('user') && (
            <button
              onClick={() => clearFilter('user')}
              className="absolute inset-y-0 right-3 flex items-center"
            >
              <X className="h-4 w-4 text-[#9CABBA] hover:text-white" />
            </button>
          )}
        </div>

        {/* Endpoint Filter */}
        <div className="relative">
          <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-[#9CABBA]" />
          </div>
          <input
            type="text"
            placeholder="Filter by endpoint"
            className="pl-10 pr-8 py-2 w-full bg-[#1A1D21]/60 rounded-xl text-white placeholder:text-[#9CABBA] focus:outline-none focus:ring-2 focus:ring-[#2D3139]"
            value={filters.endpoint}
            onChange={(e) => handleFilterChange('endpoint', e.target.value)}
          />
          {activeFilters.includes('endpoint') && (
            <button
              onClick={() => clearFilter('endpoint')}
              className="absolute inset-y-0 right-3 flex items-center"
            >
              <X className="h-4 w-4 text-[#9CABBA] hover:text-white" />
            </button>
          )}
        </div>

        {/* Date Filter */}
        <div className="relative">
          <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-[#9CABBA]" />
          </div>
          <input
            type="text"
            placeholder="Filter by date (YYYY-MM-DD)"
            className="pl-10 pr-8 py-2 w-full bg-[#1A1D21]/60 rounded-xl text-white placeholder:text-[#9CABBA] focus:outline-none focus:ring-2 focus:ring-[#2D3139]"
            value={filters.date}
            onChange={(e) => handleFilterChange('date', e.target.value)}
          />
          {activeFilters.includes('date') && (
            <button
              onClick={() => clearFilter('date')}
              className="absolute inset-y-0 right-3 flex items-center"
            >
              <X className="h-4 w-4 text-[#9CABBA] hover:text-white" />
            </button>
          )}
        </div>

        {/* Status Filter */}
        <div className="relative">
          <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-[#9CABBA]" />
          </div>
          <input
            type="text"
            placeholder="Filter by status code"
            className="pl-10 pr-8 py-2 w-full bg-[#1A1D21]/60 rounded-xl text-white placeholder:text-[#9CABBA] focus:outline-none focus:ring-2 focus:ring-[#2D3139]"
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
          />
          {activeFilters.includes('status') && (
            <button
              onClick={() => clearFilter('status')}
              className="absolute inset-y-0 right-3 flex items-center"
            >
              <X className="h-4 w-4 text-[#9CABBA] hover:text-white" />
            </button>
          )}
        </div>
      </div>

      {/* Active Filters Summary */}
      {activeFilters.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {activeFilters.map(filter => (
            <div
              key={filter}
              className="flex items-center gap-2 px-3 py-1 bg-[#2D3139]/60 rounded-lg text-sm"
            >
              <span className="text-[#9CABBA]">{filter}:</span>
              <span className="text-white">{filters[filter as keyof typeof filters]}</span>
              <button
                onClick={() => clearFilter(filter as keyof typeof filters)}
                className="ml-1 text-[#9CABBA] hover:text-white"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
          <button
            onClick={clearAllFilters}
            className="text-sm text-[#9CABBA] hover:text-white"
          >
            Clear all filters
          </button>
        </div>
      )}

      {/* Logs Table */}
      <div className="overflow-x-auto bg-[#1A1D21]/60 rounded-xl">
        <table className="w-full border-collapse">
          <thead>
            <tr className="text-left border-b border-[#2D3139]">
              <th className="p-4 text-[#9CABBA]">Date</th>
              <th className="p-4 text-[#9CABBA]">User</th>
              <th className="p-4 text-[#9CABBA]">Method</th>
              <th className="p-4 text-[#9CABBA]">Endpoint</th>
              <th className="p-4 text-[#9CABBA]">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="p-4 text-center">
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-[#9CABBA] border-t-transparent"></div>
                  </div>
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-4 text-center text-[#9CABBA]">
                  No logs found
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log._id} className="border-b border-[#2D3139]">
                  <td className="p-4 text-white">
                    {new Date(log.date).toLocaleString()}
                  </td>
                  <td className="p-4 text-white">{log.user || 'Anonymous'}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded-lg text-sm font-medium ${
                      log.method === 'GET' ? 'bg-blue-900/30 text-blue-400' :
                      log.method === 'POST' ? 'bg-green-900/30 text-green-400' :
                      log.method === 'PUT' ? 'bg-yellow-900/30 text-yellow-400' :
                      log.method === 'DELETE' ? 'bg-red-900/30 text-red-400' :
                      'bg-gray-900/30 text-gray-400'
                    }`}>
                      {log.method}
                    </span>
                  </td>
                  <td className="p-4 text-white">{log.endpoint}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded-lg text-sm font-medium ${
                      log.status < 300 ? 'bg-green-900/30 text-green-400' :
                      log.status < 400 ? 'bg-blue-900/30 text-blue-400' :
                      log.status < 500 ? 'bg-yellow-900/30 text-yellow-400' :
                      'bg-red-900/30 text-red-400'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className={`px-4 py-2 rounded-xl transition-colors ${
            page === 1
              ? 'bg-[#1A1D21]/60 text-[#9CABBA] cursor-not-allowed'
              : 'bg-[#2D3139]/80 text-white hover:bg-[#3D424A]'
          }`}
        >
          Previous
        </button>
        <span className="text-[#9CABBA]">
          Page {page} of {totalPages}
        </span>
        <button
          onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          disabled={page === totalPages}
          className={`px-4 py-2 rounded-xl transition-colors ${
            page === totalPages
              ? 'bg-[#1A1D21]/60 text-[#9CABBA] cursor-not-allowed'
              : 'bg-[#2D3139]/80 text-white hover:bg-[#3D424A]'
          }`}
        >
          Next
        </button>
      </div>
    </div>
  );
} 