'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/auth';
import { Eye, EyeOff, Lock, User } from 'lucide-react';
import toast from 'react-hot-toast';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true);
    try {
      await authService.login(data);
      toast.success('Login successful!');
      router.replace('/dashboard');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: '#121417', fontFamily: 'Inter' }}>
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="w-4 h-4 bg-white"></div>
            <h1 className="text-lg font-bold text-white" style={{ fontFamily: 'Inter' }}>
              GenAI Platform
            </h1>
          </div>
          <h2 className="text-3xl font-bold text-white" style={{ fontFamily: 'Inter' }}>Welcome Back</h2>
          <p className="mt-2 text-sm" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>Sign in to your account</p>
        </div>

        <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-8 border border-white/10">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-white mb-2" style={{ fontFamily: 'Inter' }}>
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5" style={{ color: '#9CABBA' }} />
                </div>
                <input
                  {...register('username')}
                  type="text"
                  id="username"
                  className="appearance-none block w-full pl-10 pr-3 py-3 border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-white/30 focus:border-white/30 sm:text-sm transition-all duration-200 text-white bg-white/5 backdrop-blur-sm"
                  style={{ fontFamily: 'Inter', backgroundColor: '#293038' }}
                  placeholder="Enter your username"
                />
              </div>
              {errors.username && (
                <p className="mt-1 text-sm text-red-400" style={{ fontFamily: 'Inter' }}>{errors.username.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white mb-2" style={{ fontFamily: 'Inter' }}>
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5" style={{ color: '#9CABBA' }} />
                </div>
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  className="appearance-none block w-full pl-10 pr-10 py-3 border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-white/30 focus:border-white/30 sm:text-sm transition-all duration-200 text-white bg-white/5 backdrop-blur-sm"
                  style={{ fontFamily: 'Inter', backgroundColor: '#293038' }}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center hover:text-white/80 transition-colors duration-200"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" style={{ color: '#9CABBA' }} />
                  ) : (
                    <Eye className="h-5 w-5" style={{ color: '#9CABBA' }} />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-400" style={{ fontFamily: 'Inter' }}>{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:bg-white/10"
              style={{ fontFamily: 'Inter', backgroundColor: '#293038' }}
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm" style={{ color: '#9CABBA', fontFamily: 'Inter' }}>
              Don't have an account?{' '}
              <a href="/register" className="font-medium text-white hover:text-white/80 transition-colors duration-200" style={{ fontFamily: 'Inter' }}>
                Sign up
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 