import React, { useEffect, useRef, useState } from 'react';

const STEPS = [
  { label: 'Emergency detected', icon: '🚨' },
  { label: 'Ambulance dispatched', icon: '📟' },
  { label: 'En route to scene', icon: '🚑' },
  { label: 'Arrival in 5 minutes', icon: '⏱️' },
  { label: 'Arrived at scene', icon: '🏁' },
  { label: 'Patient assessed', icon: '🩺' },
];

export default function AmbulanceTracker({ incidentId, hospital }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!incidentId) return;
    const WS_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace('http', 'ws');
    try {
      const ws = new WebSocket(`${WS_URL}/ws/live/${incidentId}`);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.event === 'ambulance_update') {
          setCurrentStep(data.step);
          setMessages(prev => [...prev, data.status]);
        }
      };
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
    } catch {
      setConnected(false);
    }

    return () => wsRef.current?.close();
  }, [incidentId]);

  // Simulate progress even without WS connection
  useEffect(() => {
    if (connected) return;
    const timers = STEPS.map((_, i) =>
      setTimeout(() => setCurrentStep(s => Math.max(s, i + 1)), (i + 1) * 4000)
    );
    return () => timers.forEach(clearTimeout);
  }, [connected]);

  return (
    <div className="glass-card" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3>🚑 Ambulance Status</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}>
          <span className={connected ? 'animate-blink' : ''} style={{ color: connected ? 'var(--green)' : 'var(--text-muted)' }}>●</span>
          <span style={{ color: 'var(--text-muted)' }}>{connected ? 'Live' : 'Simulated'}</span>
        </div>
      </div>

      {hospital && (
        <div style={{ padding: '12px 14px', background: 'rgba(59,130,246,0.08)', borderRadius: '8px', border: '1px solid rgba(59,130,246,0.2)', marginBottom: '20px', fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--blue)' }}>🏥 {hospital.name}</span>
          <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>ETA: ~{hospital.estimated_travel_min} min</span>
        </div>
      )}

      {/* Step tracker */}
      <div>
        {STEPS.map((step, i) => (
          <div key={i}>
            <div className="tracker-step">
              <div className={`tracker-dot ${i < currentStep ? 'done' : i === currentStep ? 'active' : ''}`} />
              <div style={{ flex: 1 }}>
                <p style={{
                  fontSize: '0.9rem',
                  color: i < currentStep ? 'var(--green)' : i === currentStep ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontWeight: i === currentStep ? '600' : '400',
                  transition: 'color 0.4s ease',
                }}>
                  {step.icon} {step.label}
                  {i === currentStep && <span style={{ marginLeft: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }} className="animate-blink">● in progress</span>}
                </p>
              </div>
              {i < currentStep && <span style={{ color: 'var(--green)', fontSize: '0.85rem' }}>✓</span>}
            </div>
            {i < STEPS.length - 1 && <div className={`tracker-line ${i < currentStep ? 'done' : ''}`} style={{ marginLeft: '6px' }} />}
          </div>
        ))}
      </div>

      {currentStep >= STEPS.length && (
        <div style={{ textAlign: 'center', padding: '16px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px', marginTop: '16px', color: 'var(--green)', fontWeight: '600' }}>
          ✅ Medical team on scene — patient receiving care
        </div>
      )}
    </div>
  );
}
