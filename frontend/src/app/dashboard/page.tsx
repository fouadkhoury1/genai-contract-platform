'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/auth';
import { ArrowRight } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const u = authService.getUser();
    if (!u) {
      router.replace('/login');
    } else {
      setUser(u);
    }
    setLoading(false);
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#121417' }}>
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full h-full bg-white flex flex-col justify-start items-start">
      <div className="w-full min-h-screen overflow-hidden flex flex-col justify-start items-start" style={{ background: '#121417' }}>
        <div className="w-full flex flex-col justify-start items-start">
          {/* Header */}
          <div className="w-full px-10 py-3 border-b flex justify-between items-center" style={{ borderColor: '#E5E8EB' }}>
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
          <div className="w-full flex-1 px-40 py-5 flex justify-center items-start">
            <div className="flex-1 max-w-4xl overflow-hidden flex flex-col justify-start items-start">
              {/* Dashboard Overview */}
              <div className="w-full p-4 flex justify-between items-start flex-wrap">
                <div className="flex-1 min-w-72 flex flex-col justify-start items-start gap-3">
                  <div className="w-full flex flex-col justify-start items-start">
                    <div className="w-full text-white text-3xl font-bold leading-10" style={{ fontFamily: 'Inter' }}>
                      Dashboard Overview
                    </div>
                  </div>
                  <div className="w-full flex flex-col justify-start items-start">
                    <div className="w-full text-sm font-normal leading-5" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
                      Welcome to the GenAI Platform, your central hub for managing and analyzing contracts with the power of artificial intelligence. Explore key features and insights to streamline your contract workflows.
                    </div>
                  </div>
                </div>
              </div>

              {/* Spacer */}
              <div className="w-full h-5"></div>

              {/* Contracts Section */}
              <div className="w-full p-4 flex flex-col justify-start items-start">
                <div className="w-full rounded-xl flex justify-between items-start">
                  <div className="w-152 h-43 flex flex-col justify-start items-start gap-4">
                    <div className="w-full flex flex-col justify-start items-start gap-1">
                      <div className="w-full flex flex-col justify-start items-start">
                        <div className="w-full text-white text-base font-bold leading-5" style={{ fontFamily: 'Inter' }}>
                          Contracts
                        </div>
                      </div>
                      <div className="w-full flex flex-col justify-start items-start">
                        <div className="w-full text-sm font-normal leading-5" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
                          View and manage your contracts
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => router.push('/contracts')}
                      className="h-8 max-w-120 min-w-21 px-4 pr-2 overflow-hidden rounded-2xl flex justify-center items-center gap-1"
                      style={{ background: '#293038' }}
                    >
                      <div className="overflow-hidden flex flex-col justify-start items-center">
                        <div className="text-center text-white text-sm font-medium leading-5" style={{ fontFamily: 'Inter' }}>
                          View Contracts
                        </div>
                      </div>
                      <div className="flex flex-col justify-start items-center">
                        <div className="w-4.5 flex-1 relative overflow-hidden">
                          <ArrowRight className="w-4.5 h-4.5 text-white" />
                        </div>
                      </div>
                    </button>
                  </div>
                  <div className="flex-1 h-43 relative rounded-xl bg-gray-200"></div>
                </div>
              </div>

              {/* Clients Section */}
              <div className="w-full p-4 flex flex-col justify-start items-start">
                <div className="w-full rounded-xl flex justify-between items-start">
                  <div className="w-152 h-43 flex flex-col justify-start items-start gap-4">
                    <div className="w-full flex flex-col justify-start items-start gap-1">
                      <div className="w-full flex flex-col justify-start items-start">
                        <div className="w-full text-white text-base font-bold leading-5" style={{ fontFamily: 'Inter' }}>
                          Clients
                        </div>
                      </div>
                      <div className="w-full flex flex-col justify-start items-start">
                        <div className="w-full text-sm font-normal leading-5" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
                          Manage your clients
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => router.push('/clients')}
                      className="h-8 max-w-120 min-w-21 px-4 pr-2 overflow-hidden rounded-2xl flex justify-center items-center gap-1"
                      style={{ background: '#293038' }}
                    >
                      <div className="overflow-hidden flex flex-col justify-start items-center">
                        <div className="text-center text-white text-sm font-medium leading-5" style={{ fontFamily: 'Inter' }}>
                          Manage Clients
                        </div>
                      </div>
                      <div className="flex flex-col justify-start items-center">
                        <div className="w-4.5 flex-1 relative overflow-hidden">
                          <ArrowRight className="w-4.5 h-4.5 text-white" />
                        </div>
                      </div>
                    </button>
                  </div>
                  <div className="flex-1 h-43 relative rounded-xl bg-gray-200"></div>
                </div>
              </div>

              {/* Analyze Contract Section */}
              <div className="w-full p-4 flex flex-col justify-start items-start">
                <div className="w-full rounded-xl flex justify-between items-start">
                  <div className="w-152 h-43 flex flex-col justify-start items-start gap-4">
                    <div className="w-full flex flex-col justify-start items-start gap-1">
                      <div className="w-full flex flex-col justify-start items-start">
                        <div className="w-full text-white text-base font-bold leading-5" style={{ fontFamily: 'Inter' }}>
                          Analyze Contract
                        </div>
                      </div>
                      <div className="w-full flex flex-col justify-start items-start">
                        <div className="w-full text-sm font-normal leading-5" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
                          Run AI analysis on a new contract
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => router.push('/analyze')}
                      className="h-8 max-w-120 min-w-21 px-4 pr-2 overflow-hidden rounded-2xl flex justify-center items-center gap-1"
                      style={{ background: '#293038' }}
                    >
                      <div className="overflow-hidden flex flex-col justify-start items-center">
                        <div className="text-center text-white text-sm font-medium leading-5" style={{ fontFamily: 'Inter' }}>
                          Analyze Contract
                        </div>
                      </div>
                      <div className="flex flex-col justify-start items-center">
                        <div className="w-4.5 flex-1 relative overflow-hidden">
                          <ArrowRight className="w-4.5 h-4.5 text-white" />
                        </div>
                      </div>
                    </button>
                  </div>
                  <div className="flex-1 h-43 relative rounded-xl bg-gray-200"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}