'use client';
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { Search } from 'lucide-react';

interface Customer {
  phone: string;
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchCustomers = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/customers`, {
        headers: { Authorization: `Bearer ${session?.access_token || "mock"}` }
      });
      if (res.ok) {
        setCustomers(await res.json());
      }
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchCustomers(); }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Customer CRM</h1>
          <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input type="text" placeholder="Search numbers..." className="pl-10 pr-4 py-2 border rounded-lg w-64 focus:ring-2 outline-none" />
          </div>
      </div>
      
      <div className="bg-white shadow-sm border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
             <div className="p-8 text-center text-gray-500">Loading CRM data...</div>
        ) : (
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-gray-600 text-sm">
              <th className="py-4 px-6 font-medium">Phone Number</th>
              <th className="py-4 px-6 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {customers.map((cust, idx) => (
              <tr key={idx} className="hover:bg-gray-50/50 transition-colors">
                <td className="py-4 px-6 font-medium text-gray-900">{cust.phone}</td>
                <td className="py-4 px-6">
                    <span className="bg-blue-100 text-blue-700 px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide">
                        Active
                    </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        )}
      </div>
    </div>
  );
}
