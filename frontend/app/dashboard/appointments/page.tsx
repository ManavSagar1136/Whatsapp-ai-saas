'use client';
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { Trash2 } from 'lucide-react';

interface Appointment {
  id: string;
  customer_phone: string;
  service_type: string;
  start_time: string;
  status: string;
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAppointments = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token || "mock_token";
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/appointments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAppointments(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const cancelAppointment = async (id: string) => {
      if(!confirm("Are you sure you want to delete this appointment?")) return;
      const { data: { session } } = await supabase.auth.getSession();
      
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/appointments/${id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${session?.access_token || "mock"}` }
      });
      fetchAppointments();
  }

  useEffect(() => {
    fetchAppointments();
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Appointments Calendar</h1>
      
      <div className="bg-white shadow-sm border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
             <div className="p-8 text-center text-gray-500">Loading schedule...</div>
        ) : (
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-gray-600 text-sm">
              <th className="py-4 px-6 font-medium">Service</th>
              <th className="py-4 px-6 font-medium">Customer Phone</th>
              <th className="py-4 px-6 font-medium">Start Time</th>
              <th className="py-4 px-6 font-medium">Status</th>
              <th className="py-4 px-6 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {appointments.length === 0 ? (
                <tr><td colSpan={5} className="py-8 text-center text-gray-500">No appointments found.</td></tr>
            ) : appointments.map(app => (
              <tr key={app.id} className="hover:bg-gray-50/50 transition-colors">
                <td className="py-4 px-6 font-medium text-gray-900 capitalize">{app.service_type}</td>
                <td className="py-4 px-6 text-gray-600">{app.customer_phone}</td>
                <td className="py-4 px-6 text-gray-600">{new Date(app.start_time).toLocaleString()}</td>
                <td className="py-4 px-6">
                    <span className="bg-green-100 text-green-700 px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide">
                        {app.status}
                    </span>
                </td>
                <td className="py-4 px-6 text-right">
                    <button onClick={() => cancelAppointment(app.id)} className="text-red-500 hover:text-red-700 transition-colors p-2 rounded-lg hover:bg-red-50">
                        <Trash2 size={18} />
                    </button>
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
