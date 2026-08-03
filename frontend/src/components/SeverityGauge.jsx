import React, { useEffect, useRef, useState } from 'react';

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  SEVERE: '#f97316',
  MODERATE: '#f59e0b',
  MILD: '#10b981',
  UNKNOWN: '#475569',
};

export default function SeverityGauge({ score = 0, level = 'UNKNOWN' }) {
  const [animated, setAnimated] = useState(0);
  const color = SEVERITY_COLORS[level] || '#475569';

  useEffect(() => {
    const timeout = setTimeout(() => setAnimated(score), 100);
    return () => clearTimeout(timeout);
  }, [score]);

  const R = 70;
  const circumference = 2 * Math.PI * R;
  const progress = (animated / 100) * circumference * 0.75; // 270 degree arc
  const offset = circumference - progress;

  return (
    <div className="gauge-container">
      <svg width="180" height="140" viewBox="0 0 180 140">
        {/* Background arc */}
        <circle
          cx="90" cy="100" r={R}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="14"
          strokeDasharray={`${circumference * 0.75} ${circumference}`}
          strokeDashoffset={circumference * 0.125}
          strokeLinecap="round"
          transform="rotate(135 90 100)"
        />
        {/* Progress arc */}
        <circle
          cx="90" cy="100" r={R}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeDasharray={`${progress} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform="rotate(135 90 100)"
          style={{ transition: 'stroke-dasharray 1.2s cubic-bezier(0.4,0,0.2,1)', filter: `drop-shadow(0 0 8px ${color})` }}
        />
        {/* Score text */}
        <text x="90" y="92" textAnchor="middle" fill={color} fontFamily="Outfit" fontWeight="800" fontSize="32">
          {Math.round(animated)}
        </text>
        <text x="90" y="112" textAnchor="middle" fill="var(--text-muted)" fontFamily="Inter" fontSize="11">
          out of 100
        </text>
      </svg>

      <div style={{ textAlign: 'center', marginTop: '-8px' }}>
        <span style={{
          padding: '6px 18px',
          borderRadius: '20px',
          fontSize: '0.85rem',
          fontWeight: '700',
          background: `rgba(${level === 'CRITICAL' ? '239,68,68' : level === 'SEVERE' ? '249,115,22' : level === 'MODERATE' ? '245,158,11' : '16,185,129'},0.15)`,
          border: `1px solid ${color}40`,
          color,
          letterSpacing: '0.06em',
        }}>
          {level}
        </span>
      </div>
    </div>
  );
}
