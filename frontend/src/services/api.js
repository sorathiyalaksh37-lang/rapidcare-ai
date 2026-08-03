import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

/**
 * Analyze emergency — multi-modal (text, image, audio)
 */
export async function analyzeEmergency({ text, image, audio, latitude, longitude }) {
  const form = new FormData();
  if (text) form.append('text', text);
  if (image) form.append('image', image);
  if (audio) form.append('audio', audio);
  if (latitude != null) form.append('latitude', latitude);
  if (longitude != null) form.append('longitude', longitude);

  const res = await api.post('/api/emergency/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

/**
 * Find nearby hospitals
 */
export async function findHospitals({ latitude, longitude, specialties = 'trauma', limit = 5 }) {
  const res = await api.get('/api/hospitals/nearby', {
    params: { latitude, longitude, specialties, limit },
  });
  return res.data;
}

/**
 * Generate report PDF URL
 */
export function getReportPdfUrl(incidentData) {
  return `${API_BASE}/api/reports/generate-pdf`;
}

/**
 * Health check
 */
export async function checkHealth() {
  const res = await api.get('/health');
  return res.data;
}

export default api;
