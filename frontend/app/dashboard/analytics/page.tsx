'use client';
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function AnalyticsPage() {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const { data: { session } } = await supabase.auth.getSession();
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics`, {
                    headers: { Authorization: `Bearer ${session?.access_token || "mock"}` }
                });
                if (res.ok) {
                    const rawData = await res.json();
                    setData(rawData);
                }
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchAnalytics();
    }, []);

    if (loading) return <div className="p-8 text-center text-gray-500">Loading charts...</div>;
    if (data.length === 0) return <div className="p-8 text-center text-gray-500">No analytics data available for the last 30 days.</div>;

    const kpis = {
        totalBookings: data.reduce((sum, d) => sum + d.appointments_booked, 0),
        newUsers: data.reduce((sum, d) => sum + d.new_customers, 0),
        repeatUsers: data.reduce((sum, d) => sum + d.repeat_customers, 0),
        avgConversion: (data.reduce((sum, d) => sum + parseFloat(d.conversion_rate || 0), 0) / data.length).toFixed(1)
    };

    return (
        <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Performance Analytics</h1>
            
            {/* KPI Cards */}
            <div className="grid grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <p className="text-sm text-gray-500 font-medium mb-1">Total Bookings</p>
                    <p className="text-3xl font-bold text-gray-900">{kpis.totalBookings}</p>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <p className="text-sm text-gray-500 font-medium mb-1">Avg Conversion</p>
                    <p className="text-3xl font-bold text-blue-600">{kpis.avgConversion}%</p>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <p className="text-sm text-gray-500 font-medium mb-1">New Customers</p>
                    <p className="text-3xl font-bold text-gray-900">{kpis.newUsers}</p>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <p className="text-sm text-gray-500 font-medium mb-1">Returning</p>
                    <p className="text-3xl font-bold text-gray-900">{kpis.repeatUsers}</p>
                </div>
            </div>

            {/* Charts */}
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mb-8">
                <h3 className="text-xl font-bold text-gray-900 mb-6">Conversations & Bookings (30 Days)</h3>
                <div className="h-80 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                            <XAxis dataKey="metric_date" stroke="#6B7280" fontSize={12} tickLine={false} />
                            <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
                            <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                            <Legend />
                            <Line type="monotone" dataKey="total_conversations" name="Unique Conversations" stroke="#3B82F6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                            <Line type="monotone" dataKey="appointments_booked" name="Appointments" stroke="#10B981" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <h3 className="text-xl font-bold text-gray-900 mb-6">Pipeline Conversion Rate %</h3>
                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                            <XAxis dataKey="metric_date" stroke="#6B7280" fontSize={12} tickLine={false} />
                            <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
                            <Tooltip />
                            <Line type="monotone" dataKey="conversion_rate" name="Booking Conversion %" stroke="#8B5CF6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
