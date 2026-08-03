import React, { useState } from 'react';

export default function FirstAidGuide({ steps = [], warnings = [] }) {
  const [completedSteps, setCompletedSteps] = useState(new Set());

  const toggleStep = (i) => {
    setCompletedSteps(prev => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  return (
    <div>
      {/* Warnings first */}
      {warnings.map((w, i) => (
        <div key={i} className="warning-banner" style={{ marginBottom: '8px' }}>
          <span style={{ fontSize: '1rem', flex: '0 0 auto' }}>⚠️</span>
          <span style={{ fontSize: '0.88rem' }}>{w}</span>
        </div>
      ))}

      {warnings.length > 0 && <div style={{ height: '12px' }} />}

      {/* Steps */}
      <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {completedSteps.size} / {steps.length} steps completed
        </span>
        <button className="btn btn-ghost btn-sm" onClick={() => setCompletedSteps(new Set())}>Reset</button>
      </div>

      {/* Progress bar */}
      <div style={{ height: '4px', background: 'var(--glass)', borderRadius: '2px', marginBottom: '16px', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${steps.length ? (completedSteps.size / steps.length) * 100 : 0}%`,
          background: 'linear-gradient(90deg, #10b981, #34d399)',
          transition: 'width 0.5s ease',
          borderRadius: '2px',
        }} />
      </div>

      {steps.map((step, i) => (
        <div
          key={i}
          className="step-item"
          style={{
            animationDelay: `${i * 0.07}s`,
            opacity: completedSteps.has(i) ? 0.5 : 1,
            cursor: 'pointer',
          }}
          onClick={() => toggleStep(i)}
        >
          <div className="step-number" style={{
            background: completedSteps.has(i) ? 'linear-gradient(135deg, #10b981, #059669)' : undefined,
          }}>
            {completedSteps.has(i) ? '✓' : i + 1}
          </div>
          <p style={{
            color: completedSteps.has(i) ? 'var(--text-muted)' : 'var(--text-primary)',
            fontSize: '0.9rem',
            lineHeight: '1.5',
            textDecoration: completedSteps.has(i) ? 'line-through' : 'none',
            transition: 'all 0.3s ease',
          }}>
            {step}
          </p>
        </div>
      ))}

      {steps.length === 0 && (
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
          No first aid steps available
        </p>
      )}

      {completedSteps.size === steps.length && steps.length > 0 && (
        <div style={{ textAlign: 'center', padding: '16px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px', marginTop: '12px', color: 'var(--green)' }}>
          ✅ All first aid steps completed! Await medical professionals.
        </div>
      )}
    </div>
  );
}
