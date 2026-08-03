import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import EmergencyInput from './pages/EmergencyInput';
import Dashboard from './pages/Dashboard';
import HospitalMap from './pages/HospitalMap';
import ReportView from './pages/ReportView';
import './index.css';

function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-logo">
        <div className="logo-icon">🚨</div>
        <span>RapidCare <span style={{ color: 'var(--red)' }}>AI</span></span>
      </NavLink>
      <div className="navbar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          🏥 Emergency
        </NavLink>
        <NavLink to="/hospitals" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          🗺️ Hospitals
        </NavLink>
        <NavLink to="/report" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          📋 Report
        </NavLink>
        <span className="nav-badge">AI</span>
      </div>
    </nav>
  );
}

export default function App() {
  const [analysisResult, setAnalysisResult] = useState(null);

  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<EmergencyInput onResult={setAnalysisResult} />} />
        <Route path="/dashboard" element={<Dashboard result={analysisResult} />} />
        <Route path="/hospitals" element={<HospitalMap result={analysisResult} />} />
        <Route path="/report" element={<ReportView result={analysisResult} />} />
      </Routes>
    </BrowserRouter>
  );
}
