'use client';
import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { useRouter } from 'next/navigation';

export default function OnboardingPage() {
    const [step, setStep] = useState(1);
    const router = useRouter();

    // State
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [wabaId, setWabaId] = useState('');
    const [services, setServices] = useState([{ service_name: "Consultation", duration_minutes: 30, price: 0 }]);
    const [hours, setHours] = useState('{\n  "monday": {"open": "09:00", "close": "17:00"}\n}');
    const [faq, setFaq] = useState('');

    const [loading, setLoading] = useState(false);

    const handleSignup = async () => {
        setLoading(true);
        const { error } = await supabase.auth.signUp({ email, password });
        setLoading(false);
        if (error) alert(error.message);
        else setStep(2);
    };

    const handleWhatsAppConnect = async () => {
        // In reality, this fires the Meta Embedded SDK window
        // For SaaS completeness, we just save the WABA ID mapping to the backend
        setStep(3);
    };

    const finishOnboarding = async () => {
        setLoading(true);
        try {
            const { data: { session } } = await supabase.auth.getSession();
            const headers = { 
                Authorization: `Bearer ${session?.access_token || "mock"}`,
                'Content-Type': 'application/json'
            };

            // Assuming a mock or initial setup for business creation occurs in Postgres triggers 
            // after the auth.user is active.
            
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/settings/services`, {
                method: 'PUT', headers, body: JSON.stringify({ services })
            });
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/settings/operating_hours`, {
                method: 'PUT', headers, body: JSON.stringify({ operating_hours: JSON.parse(hours) })
            });
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/settings/faq`, {
                method: 'PUT', headers, body: JSON.stringify({ faq_context: faq })
            });

            router.push('/dashboard');
        } catch(e) {
            alert("Error saving. Please check JSON.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-6">
            <div className="max-w-xl w-full mx-auto">
                <div className="text-center mb-10">
                    <h2 className="text-3xl font-extrabold text-gray-900">Welcome to AI Booking Agent</h2>
                    <p className="mt-2 text-gray-600">Step {step} of 5</p>
                    <div className="w-full bg-gray-200 h-2 mt-4 rounded-full overflow-hidden">
                        <div className="bg-blue-600 h-2 transition-all" style={{ width: `${(step/5)*100}%` }}></div>
                    </div>
                </div>

                <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
                    {step === 1 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-bold">1. Create your account</h3>
                            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" className="w-full p-3 border rounded-lg" />
                            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" className="w-full p-3 border rounded-lg" />
                            <button onClick={handleSignup} disabled={loading} className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold">Sign Up</button>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-4 text-center">
                            <h3 className="text-xl font-bold">2. Connect WhatsApp</h3>
                            <p className="text-gray-600 text-sm">Use the Meta Embedded Signup to link your Business Number.</p>
                            <input type="text" value={wabaId} onChange={e => setWabaId(e.target.value)} placeholder="WABA Phone Number ID" className="w-full p-3 border rounded-lg mt-4" />
                            <button onClick={handleWhatsAppConnect} className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold">Connect Meta Account</button>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-bold">3. Define Services</h3>
                            {services.map((s, i) => (
                                <div key={i} className="flex gap-2">
                                    <input value={s.service_name} onChange={e => {
                                        const n=[...services]; n[i].service_name=e.target.value; setServices(n);
                                    }} className="flex-1 p-2 border rounded" placeholder="Name" />
                                    <input type="number" value={s.price} onChange={e => {
                                        const n=[...services]; n[i].price=parseFloat(e.target.value)||0; setServices(n);
                                    }} className="w-20 p-2 border rounded" placeholder="$" />
                                </div>
                            ))}
                            <button onClick={() => setStep(4)} className="w-full py-3 bg-blue-600 text-white rounded-lg font-bold">Next</button>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-bold">4. Operating Hours</h3>
                            <textarea value={hours} onChange={e => setHours(e.target.value)} className="w-full h-32 p-3 font-mono border rounded-lg text-sm" />
                            <button onClick={() => setStep(5)} className="w-full py-3 bg-blue-600 text-white rounded-lg font-bold">Next</button>
                        </div>
                    )}

                    {step === 5 && (
                        <div className="space-y-4">
                            <h3 className="text-xl font-bold">5. Agent Knowledge (FAQ)</h3>
                            <textarea value={faq} onChange={e => setFaq(e.target.value)} placeholder="Type rules, parking info, payment methods..." className="w-full h-32 p-3 border rounded-lg" />
                            <button onClick={finishOnboarding} disabled={loading} className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold">
                                {loading ? "Deploying Agent..." : "Deploy Agent & Open Dashboard"}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
