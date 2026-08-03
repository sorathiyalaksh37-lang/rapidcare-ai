import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useNavigate } from 'react-router-dom';

// Fix Leaflet icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const hospitalIcon = L.divIcon({
  html: `<div style="background:linear-gradient(135deg,#3b82f6,#1d4ed8);width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;border:2px solid rgba(255,255,255,0.3);box-shadow:0 0 16px rgba(59,130,246,0.5)">🏥</div>`,
  className: '',
  iconSize: [36, 36],
  iconAnchor: [18, 18],
});

const userIcon = L.divIcon({
  html: `<div style="background:linear-gradient(135deg,#ef4444,#dc2626);width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;border:3px solid rgba(255,255,255,0.4);box-shadow:0 0 24px rgba(239,68,68,0.6);animation:pulse 1.5s infinite">📍</div>`,
  className: '',
  iconSize: [44, 44],
  iconAnchor: [22, 22],
});

function FitBounds({ hospitals, userPos }) {
  const map = useMap();
  useEffect(() => {
    if (hospitals?.length && userPos) {
      const bounds = [[userPos.lat, userPos.lng], ...hospitals.map(h => [h.latitude, h.longitude])];
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [hospitals, userPos, map]);
  return null;
}

export default function HospitalMap({ result }) {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(null);
  const hospitals = result?.nearest_hospitals || [];
  const userPos = { lat: 19.0760, lng: 72.8777 };

  return (
    <div className="page animate-fade-up">
      <div className="section-title">
        <h2>🗺️ Hospital Map</h2>
        <span className="section-badge badge-blue">Live Routing</span>
      </div>

      {!result && (
        <div className="glass-card" style={{ padding: '32px', textAlign: 'center', marginBottom: '24px' }}>
          <p style={{ marginBottom: '16px' }}>No emergency analysis yet. Complete an analysis first to see hospital routing.</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>🚨 Start Emergency Analysis</button>
        </div>
      )}

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* Map */}
        <div>
          <div style={{ height: '520px', borderRadius: 'var(--radius-lg)', overflow: 'hidden', border: '1px solid var(--glass-border)', boxShadow: 'var(--shadow-card)' }}>
            <MapContainer
              center={[userPos.lat, userPos.lng]}
              zoom={12}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; OpenStreetMap contributors'
              />

              {/* User Location */}
              <Marker position={[userPos.lat, userPos.lng]} icon={userIcon}>
                <Popup><b>🚨 Emergency Location</b></Popup>
              </Marker>
              <Circle
                center={[userPos.lat, userPos.lng]}
                radius={500}
                pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.08 }}
              />

              {/* Hospitals */}
              {hospitals.map((h, i) => (
                <Marker key={h.id || i} position={[h.latitude, h.longitude]} icon={hospitalIcon}
                  eventHandlers={{ click: () => setSelected(h) }}>
                  <Popup>
                    <b>{h.name}</b><br />
                    📏 {h.distance_km} km · ⏱ {h.estimated_travel_min} min<br />
                    📞 {h.phone}
                  </Popup>
                </Marker>
              ))}

              {hospitals.length > 0 && <FitBounds hospitals={hospitals} userPos={userPos} />}
            </MapContainer>
          </div>
        </div>

        {/* Hospital List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
            {hospitals.length} hospitals found · sorted by proximity & specialty match
          </p>
          {hospitals.map((h, i) => (
            <div
              key={h.id || i}
              className={`hospital-card ${i === 0 ? 'recommended' : ''}`}
              onClick={() => setSelected(selected?.id === h.id ? null : h)}
              style={{ border: selected?.id === h.id ? '1px solid rgba(59,130,246,0.5)' : undefined }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 style={{ fontSize: '0.95rem' }}>{h.name}</h3>
                    {i === 0 && <span className="section-badge badge-green" style={{ fontSize: '0.68rem' }}>Recommended</span>}
                  </div>
                  <p style={{ fontSize: '0.8rem', marginTop: '2px' }}>{h.city}, {h.state}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--blue)', fontFamily: 'Outfit' }}>{h.distance_km} km</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{h.estimated_travel_min} min</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '10px' }}>
                {h.trauma_center && <span className="hospital-chip" style={{ color: 'var(--red-bright)', borderColor: 'rgba(239,68,68,0.3)' }}>Trauma ✓</span>}
                {h.helipad && <span className="hospital-chip">🚁 Helipad</span>}
                {h.blood_bank && <span className="hospital-chip">🩸 Blood Bank</span>}
                {h.specialties?.slice(0, 3).map(s => <span key={s} className="hospital-chip">{s}</span>)}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  🛏 {h.icu_beds_available} ICU beds · ⭐ {h.rating}
                </span>
                <a href={`tel:${h.phone}`} className="btn btn-ghost btn-sm" onClick={e => e.stopPropagation()}>
                  📞 Call
                </a>
              </div>
            </div>
          ))}

          {hospitals.length === 0 && (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '12px' }}>🏥</div>
              <p>Complete an emergency analysis to see nearby hospitals</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
