'use client';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Calendar, LayoutDashboard, Users, Activity, Settings, LogOut } from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      // In real prod: if (!session) router.push('/login');
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });
    return () => subscription.unsubscribe();
  }, [router]);

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-xl font-bold text-blue-600 tracking-tight">AI Agent SaaS</h2>
          <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider mt-1">Tenant Portal</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          <Link href="/dashboard" className="flex items-center gap-3 px-3 py-2 text-gray-700 rounded-lg hover:bg-blue-50 transition-colors">
            <LayoutDashboard size={20} /> <span className="font-medium">Overview</span>
          </Link>
          <Link href="/dashboard/appointments" className="flex items-center gap-3 px-3 py-2 text-gray-700 rounded-lg hover:bg-blue-50 transition-colors">
            <Calendar size={20} /> <span className="font-medium">Appointments</span>
          </Link>
          <Link href="/dashboard/customers" className="flex items-center gap-3 px-3 py-2 text-gray-700 rounded-lg hover:bg-blue-50 transition-colors">
            <Users size={20} /> <span className="font-medium">Customers</span>
          </Link>
          <Link href="/dashboard/analytics" className="flex items-center gap-3 px-3 py-2 text-gray-700 rounded-lg hover:bg-blue-50 transition-colors">
            <Activity size={20} /> <span className="font-medium">Analytics</span>
          </Link>
          <Link href="/dashboard/settings" className="flex items-center gap-3 px-3 py-2 text-gray-700 rounded-lg hover:bg-blue-50 transition-colors">
            <Settings size={20} /> <span className="font-medium">Settings</span>
          </Link>
        </nav>
        <div className="p-4 border-t border-gray-100">
             <button onClick={() => supabase.auth.signOut()} className="flex items-center w-full gap-3 px-3 py-2 text-gray-600 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors">
                 <LogOut size={20} /> <span className="font-medium">Sign Out</span>
             </button>
        </div>
      </aside>
      
      {/* Main Container */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-6xl mx-auto p-8">
            {children}
        </div>
      </main>
    </div>
  );
}
