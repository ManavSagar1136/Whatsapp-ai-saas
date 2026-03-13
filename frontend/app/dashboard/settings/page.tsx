'use client';
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { Plus, Trash2, Save } from 'lucide-react';

interface Service {
    service_name: string;
    duration_minutes: number;
    price: number;
}

export default function SettingsPage() {
    const [services, setServices] = useState<Service[]>([{ service_name: "Consultation", duration_minutes: 30, price: 0 }]);
    const [hoursText, setHoursText] = useState('{\n  "monday": {"open": "09:00", "close": "17:00"}\n}');
    const [faqText, setFaqText] = useState('We only accept cash. Free parking in back.');
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        try {
            const { data: { session } } = await supabase.auth.getSession();
            const headers = { 
                Authorization: `Bearer ${session?.access_token || "mock"}`,
                'Content-Type': 'application/json'
            };

            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/settings/services`, {
                method: 'PUT', headers, body: JSON.stringify({ services })
            });

            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/settings/operating_hours`, {
                method: 'PUT', headers, body: JSON.stringify({ operating_hours: JSON.parse(hoursText) })
            });

            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/settings/faq`, {
                method: 'PUT', headers, body: JSON.stringify({ faq_context: faqText })
            });

            alert("Settings deployed to Meta successfully!");
        } catch(e) {
            alert("Error saving settings. Check JSON format.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="max-w-4xl">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold text-gray-900">AI Bot Configuration</h1>
                <button onClick={handleSave} disabled={saving} className="bg-blue-600 text-white px-5 py-2 rounded-lg font-medium hover:bg-blue-700 flex items-center gap-2">
                    <Save size={18} /> {saving ? "Deploying..." : "Save & Deploy"}
                </button>
            </div>

            <div className="space-y-6">
                {/* Services Section */}
                <div className="bg-white p-6 shadow-sm border border-gray-200 rounded-xl">
                    <div className="flex justify-between mb-4">
                        <h2 className="text-xl font-semibold text-gray-800">1. Services Offered</h2>
                        <button onClick={() => setServices([...services, { service_name: "", duration_minutes: 60, price: 0 }])} className="text-blue-600 text-sm font-medium flex items-center gap-1">
                            <Plus size={16} /> Add Service
                        </button>
                    </div>
                    <div className="space-y-3">
                        {services.map((s, i) => (
                            <div key={i} className="flex gap-4 items-center bg-gray-50 p-3 rounded-lg border">
                                <input type="text" value={s.service_name} onChange={e => {
                                    const next = [...services]; next[i].service_name = e.target.value; setServices(next);
                                }} placeholder="Service Name (e.g. Haircut)" className="flex-1 p-2 border rounded" />
                                
                                <input type="number" value={s.duration_minutes} onChange={e => {
                                    const next = [...services]; next[i].duration_minutes = parseInt(e.target.value)||0; setServices(next);
                                }} placeholder="Mins" className="w-24 p-2 border rounded" />
                                
                                <input type="number" value={s.price} onChange={e => {
                                    const next = [...services]; next[i].price = parseFloat(e.target.value)||0; setServices(next);
                                }} placeholder="$" className="w-24 p-2 border rounded" />
                                
                                <button onClick={() => setServices(services.filter((_, idx) => idx !== i))} className="p-2 text-red-500 hover:bg-red-50 rounded"><Trash2 size={18}/></button>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Hours Section */}
                <div className="bg-white p-6 shadow-sm border border-gray-200 rounded-xl">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">2. Operating Hours (JSON)</h2>
                    <textarea value={hoursText} onChange={(e) => setHoursText(e.target.value)} className="w-full h-32 border border-gray-300 p-3 rounded-lg font-mono text-sm" />
                </div>

                {/* FAQ Section */}
                <div className="bg-white p-6 shadow-sm border border-gray-200 rounded-xl">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">3. Custom Knowledge Base (RAG)</h2>
                    <p className="text-sm text-gray-500 mb-3">The AI will use this text to answer arbitrary questions before falling back to its internal logic.</p>
                    <textarea value={faqText} onChange={(e) => setFaqText(e.target.value)} className="w-full h-40 border border-gray-300 p-3 rounded-lg" />
                </div>
            </div>
        </div>
    );
}
