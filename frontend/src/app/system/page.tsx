'use client';

import { Suspense } from 'react';
import HealthStatus from '@/components/system/HealthStatus';
import ReadinessStatus from '@/components/system/ReadinessStatus';
import LogsViewer from '@/components/system/LogsViewer';

export default function SystemPage() {
  return (
    <div className="w-full min-h-screen" style={{ background: '#121417' }}>
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col gap-6">
          {/* Header */}
          <div className="flex flex-col gap-3">
            <h1 className="text-3xl font-bold text-white">System Monitoring</h1>
            <p className="text-[#9CABBA]">Monitor system health, readiness, and logs in real-time</p>
          </div>
          
          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-[#1A1D21] rounded-xl p-6 border border-white/10">
              <h2 className="text-xl font-semibold text-white mb-4">Health Status</h2>
              <Suspense fallback={
                <div className="flex items-center justify-center h-40">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
                </div>
              }>
                <HealthStatus />
              </Suspense>
            </div>
            
            <div className="bg-[#1A1D21] rounded-xl p-6 border border-white/10">
              <h2 className="text-xl font-semibold text-white mb-4">Readiness Status</h2>
              <Suspense fallback={
                <div className="flex items-center justify-center h-40">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
                </div>
              }>
                <ReadinessStatus />
              </Suspense>
            </div>
          </div>
          
          {/* Logs Section */}
          <div className="bg-[#1A1D21] rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">System Logs</h2>
            <Suspense fallback={
              <div className="flex items-center justify-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
              </div>
            }>
              <LogsViewer />
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
} 