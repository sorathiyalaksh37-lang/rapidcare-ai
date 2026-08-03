import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SeverityGauge from '../components/SeverityGauge';
import FirstAidGuide from '../components/FirstAidGuide';
import AmbulanceTracker from '../components/AmbulanceTracker';
import EmergencyAlert from '../components/EmergencyAlert';

const EMERGENCY_ICONS = {
  road_accident: '🚗', cardiac_arrest: '❤️', stroke: '🧠',
  bleeding: '🩸', fracture: '🦴', fire_burn: '🔥',
  drowning: '💧', head_injury: '🧠', unknown: '🚨',
};

export default function Dashboard({ result }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('firstaid');

  useEffect(() => {
    if (!result) navigate('/');
  }, [result, navigate]);

  if (!result) return null;

  const {
    emergency_type, severity_score, severity_level,
    survival_probability, confidence, first_aid_steps,
    warnings, nearest_hospitals, incident_id,
    processing_time_ms, injury_indicators, transcription,
    detected_keywords,
  } = result;

  const icon = EMERGENCY_ICONS[emergency_type] || '🚨';
  const survivalPct = Math.round((survival_probability || 0.5) * 100);
  const nearestHospital = nearest_hospitals?.[0];

  return (
    <div className="page animate-fade-up">
      {/* Emergency Alert Banner */}
      <EmergencyAlert
        severity={severity_level}
        emergencyType={emergency_type}
        icon={icon}
        incidentId={incident_id}
      />

      {/* Top Stats Row */}
      <div className="grid-3" style={{ marginBottom: '28px' }}>
        {/* Severity Gauge */}
        <div className="glass-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>Severity Score</p>
          <SeverityGauge score={severity_score} level={severity_level} />
        </div>

        {/* Survival Probability */}
        <div className="glass-card" style={{ padding: '28px' }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>Survival Probability</p>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '12px' }}>
            <span style={{
              fontSize: '3.5rem', fontWeight: '800', fontFamily: 'Outfit',
              color: survivalPct > 70 ? 'var(--green)' : survivalPct > 40 ? 'var(--orange)' : 'var(--red)',
            }}>
              {survivalPct}
            </span>
            <span style={{ fontSize: '1.5rem', color: 'var(--text-secondary)' }}>%</span>
          </div>
          <div style={{ height: '6px', background: 'var(--glass)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${survivalPct}%`,
              background: survivalPct > 70 ? 'linear-gradient(90deg, #10b981, #34d399)' : survivalPct > 40 ? 'linear-gradient(90deg, #f59e0b, #fbbf24)' : 'linear-gradient(90deg, #ef4444, #f87171)',
              transition: 'width 1s ease',
              borderRadius: '3px',
            }} />
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px' }}>With immediate medical care</p>
        </div>

        {/* Nearest Hospital */}
        <div className="glass-card" style={{ padding: '28px' }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>Nearest Hospital</p>
          {nearestHospital ? (
            <>
              <p style={{ fontWeight: '700', fontSize: '1rem', marginBottom: '6px', color: 'var(--text-primary)' }}>{nearestHospital.name}</p>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>{nearestHospital.city}, {nearestHospital.state}</p>
              <div style={{ display: 'flex', gap: '16px' }}>
                <div>
                  <p style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--blue)', fontFamily: 'Outfit' }}>{nearestHospital.distance_km}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>km away</p>
                </div>
                <div>
                  <p style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--green)', fontFamily: 'Outfit' }}>{nearestHospital.estimated_travel_min}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>min ETA</p>
                </div>
                <div>
                  <p style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--orange)', fontFamily: 'Outfit' }}>{nearestHospital.icu_beds_available}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ICU beds</p>
                </div>
              </div>
              <a href={`tel:${nearestHospital.phone}`} className="btn btn-ghost btn-sm" style={{ marginTop: '14px', width: '100%', justifyContent: 'center' }}>
                📞 {nearestHospital.phone || '112'}
              </a>
            </>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>Hospital data unavailable. Call 112.</p>
          )}
        </div>
      </div>

      {/* Main Content Tabs */}
      <div className="grid-2" style={{ marginBottom: '28px', alignItems: 'start' }}>
        {/* Left: Tab Content */}
        <div>
          <div style={{ display: 'flex', gap: '4px', marginBottom: '16px', background: 'var(--glass)', borderRadius: 'var(--radius-md)', padding: '4px', border: '1px solid var(--glass-border)' }}>
            {[
              { id: 'firstaid', label: '🩺 First Aid' },
              { id: 'ambulance', label: '🚑 Ambulance' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="btn btn-sm"
                style={{
                  flex: 1, justifyContent: 'center',
                  background: activeTab === tab.id ? 'linear-gradient(135deg, #ef4444, #dc2626)' : 'transparent',
                  color: activeTab === tab.id ? '#fff' : 'var(--text-secondary)',
                  border: 'none',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === 'firstaid' && (
            <FirstAidGuide steps={first_aid_steps || []} warnings={warnings || []} />
          )}
          {activeTab === 'ambulance' && (
            <AmbulanceTracker incidentId={incident_id} hospital={nearestHospital} />
          )}
        </div>

        {/* Right: AI Analysis Details */}
        <div>
          <div className="glass-card" style={{ padding: '24px', marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '16px' }}>🤖 AI Analysis Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <DetailRow label="Emergency Type" value={emergency_type?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} icon={icon} />
              <DetailRow label="AI Confidence" value={`${Math.round(confidence * 100)}%`} />
              <DetailRow label="Severity Level" value={severity_level} valueClass={`severity-${severity_level}`} />
              <DetailRow label="Processing Time" value={`${processing_time_ms}ms`} />
              {transcription && <DetailRow label="Transcription" value={`"${transcription.slice(0, 80)}..."`} />}
            </div>
          </div>

          {/* Detected Keywords */}
          {detected_keywords?.length > 0 && (
            <div className="glass-card" style={{ padding: '24px', marginBottom: '20px' }}>
              <h3 style={{ marginBottom: '12px' }}>🔍 Detected Indicators</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {detected_keywords.map(kw => (
                  <span key={kw} style={{ padding: '4px 10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', fontSize: '0.8rem', color: 'var(--red-bright)' }}>
                    {kw}
                  </span>
                ))}
                {injury_indicators?.map(ind => (
                  <span key={ind} style={{ padding: '4px 10px', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '6px', fontSize: '0.8rem', color: 'var(--blue)' }}>
                    {ind}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Emergency Numbers */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>📞 Emergency Contacts</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              {[
                { label: 'Emergency', num: '112', color: 'var(--red)' },
                { label: 'Ambulance', num: '108', color: 'var(--orange)' },
                { label: 'Police', num: '100', color: 'var(--blue)' },
                { label: 'Fire', num: '101', color: 'var(--orange)' },
              ].map(c => (
                <a key={c.label} href={`tel:${c.num}`} style={{ textDecoration: 'none', padding: '14px', background: 'var(--glass)', borderRadius: '10px', border: '1px solid var(--glass-border)', textAlign: 'center', display: 'block', transition: 'all 0.2s' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: '800', color: c.color, fontFamily: 'Outfit' }}>{c.num}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{c.label}</div>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={() => navigate('/hospitals')}>🗺️ View Hospital Map</button>
        <button className="btn btn-ghost" onClick={() => navigate('/report')}>📋 View Full Report</button>
        <button className="btn btn-ghost" onClick={() => navigate('/')}>+ New Emergency</button>
      </div>
    </div>
  );
}

function DetailRow({ label, value, icon, valueClass }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--glass-border)' }}>
      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{ fontSize: '0.9rem', fontWeight: '600' }} className={valueClass}>
        {icon && `${icon} `}{value}
      </span>
    </div>
  );
}
