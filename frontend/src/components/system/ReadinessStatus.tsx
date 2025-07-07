'use client';

import { useEffect, useState } from 'react';
import { api, endpoints } from '@/lib/api';
import { CheckCircle, XCircle, Database } from 'lucide-react';

interface ReadinessStatus {
  status: 'ready' | 'not ready';
  error?: string;
}

export default function ReadinessStatus() {
  const [readiness, setReadiness] = useState<ReadinessStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  useEffect(() => {
    const fetchReadiness = async () => {
      try {
        const response = await api.get(endpoints.ready);
        setReadiness(response.data);
        setLastChecked(new Date());
        setError(null);
      } catch (err) {
        setError('Failed to fetch readiness status');
        console.error('Readiness check error:', err);
      }
    };

    fetchReadiness();
    const interval = setInterval(fetchReadiness, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="p-4 bg-red-900/20 text-red-400 rounded-md border border-red-900/50">
        <p>{error}</p>
      </div>
    );
  }

  if (!readiness) {
    return (
      <div className="flex items-center justify-center h-40">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
      </div>
    );
  }

  const isReady = readiness.status === 'ready';

  return (
    <div className="space-y-6">
      <div className={`p-4 rounded-xl ${
        isReady 
          ? 'bg-green-900/30 text-green-400' 
          : 'bg-red-900/30 text-red-400'
      }`}>
        <div className="flex items-center gap-2">
          {isReady ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <XCircle className="w-5 h-5" />
          )}
          <p className="font-semibold">
            Status: {isReady ? 'Ready' : 'Not Ready'}
          </p>
        </div>
        <p className="text-sm mt-1 text-[#9CABBA]">
          Last Checked: {lastChecked.toLocaleString()}
        </p>
        {readiness.error && (
          <p className="text-sm mt-2 text-red-400">
            Error: {readiness.error}
          </p>
        )}
      </div>

      <div className="space-y-3">
        <h3 className="text-[#9CABBA] font-medium">Database Connection:</h3>
        <div className="grid gap-3">
          <div className={`flex items-center justify-between p-3 rounded-xl ${
            isReady ? 'bg-green-900/30' : 'bg-red-900/30'
          }`}>
            <div className="flex items-center gap-2 text-white">
              <Database className="w-4 h-4" />
              <span>MongoDB</span>
            </div>
            <div className={`flex items-center gap-2 ${
              isReady ? 'text-green-400' : 'text-red-400'
            }`}>
              {isReady ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">Connected</span>
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">Disconnected</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 