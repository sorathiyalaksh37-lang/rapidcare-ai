import React from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ReportView({ result }) {
  const navigate = useNavigate();

  const handleDownloadPDF = async () => {
    if (!result) return;
    try {
      const incidentData = {
        incident_id: result.incident_id,
        input_text: result.input_text,
        emergency_type: result.emergency_type,
        confidence: result.confidence,
        detected_keywords: result.detected_keywords,
        injury_indicators: result.injury_indicators,
        severity_data: {
          severity_score: result.severity_score,
          severity_level: result.severity_level,
          survival_probability: result.survival_probability,
          contributing_factors: result.contributing_factors,
        },
        firstaid_data: {
          steps: result.first_aid_steps,
          warnings: result.warnings,
          required_specialties: result.required_specialties,
        },
        hospitals: result.nearest_hospitals || [],
        has_image: result.has_image,
        has_voice: result.has_voice,
        processing_time_ms: result.processing_time_ms,
        ai_mode: result.ai_mode,
      };
      const response = await axios.post(`${API_BASE}/api/reports/generate-pdf`, { incident_data: incidentData }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapidcare_report_${result.incident_id?.slice(0, 8)}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('PDF download failed. Please ensure the backend is running.');
    }
  };

  if (!result) {
    return (
      <div className="page animate-fade-up" style={{ textAlign: 'center', paddingTop: '80px' }}>
        <div style={{ fontSize: '4rem', marginBottom: '20px' }}>📋</div>
        <h2>No Report Available</h2>
        <p style={{ marginBottom: '24px' }}>Complete an emergency analysis to generate a report.</p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>🚨 Start Emergency Analysis</button>
      </div>
    );
  }

  const report = result.report;
  const { emergency_type, severity_score, severity_level, survival_probability,
    first_aid_steps, warnings, nearest_hospitals, incident_id, processing_time_ms } = result;

  return (
    <div className="page page-sm animate-fade-up">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', marginBottom: '6px' }}>🚨 Emergency Report</h1>
          <p style={{ fontSize: '0.85rem' }}>Incident ID: <code style={{ background: 'var(--glass)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.8rem' }}>{incident_id?.slice(0, 16)}...</code></p>
        </div>
        <button className="btn btn-primary" onClick={handleDownloadPDF}>
          ⬇️ Download PDF
        </button>
      </div>

      {/* Incident Summary */}
      <Section title="📊 Incident Summary">
        <div className="grid-3">
          <StatBox label="Emergency Type" value={emergency_type?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} />
          <StatBox label="Severity Level" value={severity_level} cls={`severity-${severity_level}`} />
          <StatBox label="Severity Score" value={`${severity_score}/100`} />
          <StatBox label="Survival Probability" value={`${Math.round(survival_probability * 100)}%`} />
          <StatBox label="AI Confidence" value={`${Math.round((result.confidence || 0) * 100)}%`} />
          <StatBox label="Processing Time" value={`${processing_time_ms}ms`} />
        </div>
      </Section>

      {/* First Aid Steps */}
      <Section title="🩺 First Aid Protocol">
        {(first_aid_steps || []).map((step, i) => (
          <div key={i} className="step-item" style={{ animationDelay: `${i * 0.05}s` }}>
            <div className="step-number">{i + 1}</div>
            <p style={{ color: 'var(--text-primary)', fontSize: '0.9rem', lineHeight: '1.5' }}>{step}</p>
          </div>
        ))}
      </Section>

      {/* Warnings */}
      {warnings?.length > 0 && (
        <Section title="⚠️ Critical Warnings">
          {warnings.map((w, i) => (
            <div key={i} className="warning-banner">
              <span style={{ fontSize: '1.1rem', flex: '0 0 auto' }}>⚠️</span>
              <span style={{ fontSize: '0.9rem' }}>{w}</span>
            </div>
          ))}
        </Section>
      )}

      {/* Hospital Assignment */}
      <Section title="🏥 Hospital Assignment">
        {nearest_hospitals?.slice(0, 3).map((h, i) => (
          <div key={h.id || i} className="hospital-card" style={{ marginBottom: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <div>
                <b>{h.name}</b> {i === 0 && <span className="section-badge badge-green" style={{ fontSize: '0.65rem' }}>Primary</span>}
                <p style={{ fontSize: '0.8rem', marginTop: '2px' }}>{h.address}</p>
              </div>
              <div style={{ textAlign: 'right', fontSize: '0.85rem' }}>
                <div style={{ color: 'var(--blue)', fontWeight: '700' }}>{h.distance_km} km</div>
                <div style={{ color: 'var(--text-muted)' }}>{h.estimated_travel_min} min ETA</div>
              </div>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>📞 {h.phone} · 🛏 {h.icu_beds_available} ICU beds · ⭐ {h.rating}</p>
          </div>
        ))}
      </Section>

      {/* Emergency Contacts */}
      <Section title="📞 Emergency Contacts">
        <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))' }}>
          {[['112', 'Emergency'], ['108', 'Ambulance'], ['101', 'Fire'], ['100', 'Police'], ['1070', 'Disaster']].map(([num, label]) => (
            <a key={num} href={`tel:${num}`} style={{ textDecoration: 'none', padding: '16px', background: 'var(--glass)', borderRadius: '10px', border: '1px solid var(--glass-border)', textAlign: 'center', display: 'block' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--red)', fontFamily: 'Outfit' }}>{num}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>{label}</div>
            </a>
          ))}
        </div>
      </Section>

      {/* Footer */}
      <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        Generated by RapidCare AI v1.0 · {new Date().toLocaleString()}
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="glass-card" style={{ padding: '24px', marginBottom: '20px' }}>
      <h3 style={{ marginBottom: '16px', fontSize: '1rem' }}>{title}</h3>
      {children}
    </div>
  );
}

function StatBox({ label, value, cls }) {
  return (
    <div style={{ padding: '14px', background: 'var(--glass)', borderRadius: '10px', border: '1px solid var(--glass-border)' }}>
      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>{label}</p>
      <p style={{ fontWeight: '700', fontSize: '1rem' }} className={cls}>{value}</p>
    </div>
  );
}
