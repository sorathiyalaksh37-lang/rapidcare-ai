import React from 'react';

const SEVERITY_CONFIG = {
  CRITICAL: {
    bg: 'linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05))',
    border: 'rgba(239,68,68,0.35)',
    glow: '0 0 40px rgba(239,68,68,0.12)',
    color: '#ef4444',
    iconBg: 'rgba(239,68,68,0.2)',
    label: '🔴 CRITICAL EMERGENCY',
    pulse: true,
  },
  SEVERE: {
    bg: 'linear-gradient(135deg, rgba(249,115,22,0.15), rgba(249,115,22,0.05))',
    border: 'rgba(249,115,22,0.35)',
    glow: '0 0 30px rgba(249,115,22,0.1)',
    color: '#f97316',
    iconBg: 'rgba(249,115,22,0.2)',
    label: '🟠 SEVERE EMERGENCY',
    pulse: false,
  },
  MODERATE: {
    bg: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(245,158,11,0.04))',
    border: 'rgba(245,158,11,0.3)',
    glow: '0 0 20px rgba(245,158,11,0.08)',
    color: '#f59e0b',
    iconBg: 'rgba(245,158,11,0.15)',
    label: '🟡 MODERATE EMERGENCY',
    pulse: false,
  },
  MILD: {
    bg: 'linear-gradient(135deg, rgba(16,185,129,0.1), rgba(16,185,129,0.03))',
    border: 'rgba(16,185,129,0.25)',
    glow: '',
    color: '#10b981',
    iconBg: 'rgba(16,185,129,0.15)',
    label: '🟢 MILD EMERGENCY',
    pulse: false,
  },
  UNKNOWN: {
    bg: 'linear-gradient(135deg, rgba(100,116,139,0.12), rgba(100,116,139,0.04))',
    border: 'rgba(100,116,139,0.25)',
    glow: '',
    color: '#64748b',
    iconBg: 'rgba(100,116,139,0.15)',
    label: '⚪ EMERGENCY DETECTED',
    pulse: false,
  },
};

export default function EmergencyAlert({ severity = 'UNKNOWN', emergencyType, icon = '🚨', incidentId }) {
  const cfg = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.UNKNOWN;
  const typeLabel = emergencyType?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Unknown';

  return (
    <div style={{
      background: cfg.bg,
      border: `1px solid ${cfg.border}`,
      borderRadius: '20px',
      boxShadow: cfg.glow,
      padding: '20px 28px',
      marginBottom: '28px',
      display: 'flex',
      alignItems: 'center',
      gap: '20px',
      animation: 'fadeUp 0.4s ease forwards',
    }}>
      {/* Icon */}
      <div style={{
        width: '60px', height: '60px',
        borderRadius: '16px',
        background: cfg.iconBg,
        border: `1px solid ${cfg.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1.9rem',
        flexShrink: 0,
        animation: cfg.pulse ? 'pulse-ring 1.5s infinite' : 'none',
      }}>
        {icon}
      </div>

      {/* Text */}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', color: cfg.color, letterSpacing: '0.1em', marginBottom: '4px' }}>
          {cfg.label}
        </div>
        <div style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--text-primary)', fontFamily: 'Outfit' }}>
          {typeLabel}
        </div>
        {incidentId && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            ID: {incidentId.slice(0, 12)}...
          </div>
        )}
      </div>

      {/* Emergency call */}
      <a href="tel:112" style={{
        textDecoration: 'none',
        background: 'linear-gradient(135deg, #ef4444, #dc2626)',
        color: '#fff',
        padding: '12px 20px',
        borderRadius: '12px',
        fontWeight: '700',
        fontSize: '0.9rem',
        boxShadow: '0 0 20px rgba(239,68,68,0.3)',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        flexShrink: 0,
        transition: 'transform 0.2s ease',
      }}>
        📞 Call 112
      </a>
    </div>
  );
}
