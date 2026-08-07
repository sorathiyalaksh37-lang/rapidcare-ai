import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeEmergency } from '../services/api';

const QUICK_SCENARIOS = [
  { icon: '🚗', label: 'Road Accident', text: 'Serious road accident on highway, person is unconscious and bleeding from head, not responding to voice.' },
  { icon: '❤️', label: 'Heart Attack', text: 'Person collapsed suddenly, clutching chest, not breathing, no pulse detected.' },
  { icon: '🧠', label: 'Stroke', text: 'Person has sudden face drooping on one side, arm weakness, slurred speech.' },
  { icon: '🔥', label: 'Burn Injury', text: 'Person has severe burn from fire on arms and chest, blisters forming, screaming in pain.' },
  { icon: '💧', label: 'Drowning', text: 'Child pulled from swimming pool, unconscious, not breathing.' },
  { icon: '🦴', label: 'Fracture', text: 'Bone fracture on leg from fall, visible deformity, cannot move.' },
];

export default function EmergencyInput({ onResult }) {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [location, setLocation] = useState(null);
  const [isLoadingLocation, setIsLoadingLocation] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const fileInputRef = useRef(null);

  // Auto-fetch location on component mount
  useEffect(() => {
    getLocation();
  }, []);

  // ── Location ──────────────────────────────────────────────────────────
  const getLocation = useCallback(() => {
    if (navigator.geolocation) {
      setIsLoadingLocation(true);
      setError('');
      navigator.geolocation.getCurrentPosition(
        pos => {
          setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          setIsLoadingLocation(false);
        },
        (err) => {
          setIsLoadingLocation(false);
          let errorMsg = 'Location access failed: ';
          if (err.code === err.PERMISSION_DENIED) {
            errorMsg += 'Please enable location permissions in your browser settings.';
          } else if (err.code === err.POSITION_UNAVAILABLE) {
            errorMsg += 'Location information is unavailable. Using default location.';
          } else if (err.code === err.TIMEOUT) {
            errorMsg += 'Location request timed out. Using default location.';
          }
          setError(errorMsg);
          // Only use default as last resort
          setLocation({ lat: 19.0760, lng: 72.8777 }); // Default Mumbai
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    } else {
      setError('Geolocation is not supported by your browser.');
      setLocation({ lat: 19.0760, lng: 72.8777 }); // Default Mumbai
    }
  }, []);

  // ── Image Drop ────────────────────────────────────────────────────────
  const handleImageFile = (file) => {
    if (!file || !file.type.startsWith('image/')) return;
    setImage(file);
    const reader = new FileReader();
    reader.onload = e => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    handleImageFile(e.dataTransfer.files[0]);
  }, []);

  // ── Voice Recording ───────────────────────────────────────────────────
  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        const mr = new MediaRecorder(stream);
        mr.ondataavailable = e => audioChunksRef.current.push(e.data);
        mr.onstop = () => {
          const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          setAudioBlob(blob);
          stream.getTracks().forEach(t => t.stop());
        };
        mr.start();
        mediaRecorderRef.current = mr;
        setIsRecording(true);
        setAudioBlob(null);
      } catch {
        setError('Microphone access denied. Please allow microphone permissions.');
      }
    }
  };

  // ── Submit ────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!text && !image && !audioBlob) {
      setError('Please provide at least one input: text, image, or voice recording.');
      return;
    }
    setError('');
    setIsLoading(true);
    setAnalysisProgress('Starting analysis...');

    try {
      const audioFile = audioBlob ? new File([audioBlob], 'audio.webm', { type: 'audio/webm' }) : null;
      
      // Simulate progress updates
      setTimeout(() => setAnalysisProgress('Processing inputs...'), 500);
      setTimeout(() => setAnalysisProgress('Analyzing emergency type...'), 1500);
      setTimeout(() => setAnalysisProgress('Finding nearby hospitals...'), 3000);
      
      const result = await analyzeEmergency({
        text: text || undefined,
        image: image || undefined,
        audio: audioFile || undefined,
        latitude: location?.lat,
        longitude: location?.lng,
      });
      
      setAnalysisProgress('Complete!');
      onResult(result);
      navigate('/dashboard');
    } catch (err) {
      setAnalysisProgress('');
      setError(err.response?.data?.detail || 'Analysis failed. Please check if the backend is running.');
    } finally {
      setIsLoading(false);
      setTimeout(() => setAnalysisProgress(''), 500);
    }
  };

  return (
    <div className="page page-sm animate-fade-up">
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <div style={{ fontSize: '4rem', marginBottom: '16px', display: 'inline-block', animation: 'pulse-ring 2s infinite' }}>🚨</div>
        <h1 style={{ background: 'linear-gradient(135deg, #f87171, #ef4444, #dc2626)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          AI Emergency Assistant
        </h1>
        <p style={{ marginTop: '12px', fontSize: '1.05rem', maxWidth: '560px', margin: '12px auto 0' }}>
          Describe the emergency through text, image, or voice. Our AI will analyze the situation and provide instant guidance.
        </p>
      </div>

      {/* Quick Scenarios */}
      <div style={{ marginBottom: '32px' }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>
          Quick Scenarios
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {QUICK_SCENARIOS.map(s => (
            <button
              key={s.label}
              className="btn btn-ghost btn-sm"
              onClick={() => setText(s.text)}
            >
              {s.icon} {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Input Card */}
      <div className="glass-card" style={{ padding: '32px', marginBottom: '24px' }}>

        {/* Text Input */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '10px', color: 'var(--text-secondary)' }}>
            📝 Describe the Emergency
          </label>
          <textarea
            className="input-field"
            rows={5}
            placeholder="Describe what happened: injuries, victim's condition, location details..."
            value={text}
            onChange={e => setText(e.target.value)}
          />
        </div>

        {/* Image Upload */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '10px', color: 'var(--text-secondary)' }}>
            📸 Upload Injury Image <span style={{ color: 'var(--text-muted)', fontWeight: '400' }}>(optional)</span>
          </label>
          <div
            className={`upload-zone ${isDragging ? 'drag-over' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={onDrop}
          >
            <input ref={fileInputRef} type="file" accept="image/*" onChange={e => handleImageFile(e.target.files[0])} />
            {imagePreview ? (
              <div style={{ position: 'relative' }}>
                <img src={imagePreview} alt="Preview" style={{ maxHeight: '200px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} />
                <button className="btn btn-ghost btn-sm" style={{ marginTop: '12px', display: 'block', margin: '12px auto 0' }}
                  onClick={e => { e.stopPropagation(); setImage(null); setImagePreview(null); }}>
                  ✕ Remove
                </button>
              </div>
            ) : (
              <>
                <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🖼️</div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  Drag & drop an image or <span style={{ color: 'var(--red-bright)' }}>click to browse</span>
                </p>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>Supports JPG, PNG, WebP</p>
              </>
            )}
          </div>
        </div>

        {/* Voice Input */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '10px', color: 'var(--text-secondary)' }}>
            🎤 Voice Description <span style={{ color: 'var(--text-muted)', fontWeight: '400' }}>(optional)</span>
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              className={`btn ${isRecording ? 'btn-danger' : 'btn-ghost'}`}
              onClick={toggleRecording}
              style={isRecording ? { animation: 'pulse-ring 1s infinite' } : {}}
            >
              {isRecording ? '⏹ Stop Recording' : '🎤 Start Recording'}
            </button>
            {audioBlob && !isRecording && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--green)', fontSize: '0.9rem' }}>
                <span className="animate-blink">●</span> Audio captured — ready to analyze
              </div>
            )}
            {isRecording && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--red)', fontSize: '0.9rem' }}>
                <span className="animate-blink">●</span> Recording...
              </div>
            )}
          </div>
        </div>

        {/* Location */}
        <div style={{ marginBottom: '28px' }}>
          <button 
            className="btn btn-ghost btn-sm" 
            onClick={getLocation}
            disabled={isLoadingLocation}
          >
            {isLoadingLocation ? (
              <>
                <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
                Fetching location...
              </>
            ) : location ? (
              <>
                📍 Location: {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
                <span style={{ marginLeft: '8px', color: 'var(--green)', fontSize: '0.85rem' }}>✓</span>
              </>
            ) : (
              '📍 Use My Location'
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: '8px', padding: '12px 16px', color: 'var(--red-bright)', marginBottom: '20px', fontSize: '0.9rem' }}>
            ⚠️ {error}
          </div>
        )}

        {/* Submit */}
        <button
          className="btn btn-primary btn-lg"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={handleSubmit}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }} />
              {analysisProgress || 'Analyzing Emergency...'}
            </>
          ) : (
            '🚨 Analyze Emergency'
          )}
        </button>
      </div>

      {/* Info Footer */}
      <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
        {[
          { icon: '🤖', text: 'AI-Powered Analysis' },
          { icon: '🏥', text: 'Real-Time Hospital Routing' },
          { icon: '📋', text: 'Auto-Generated Report' },
          { icon: '🔒', text: 'Privacy Protected' },
        ].map(item => (
          <div key={item.text} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {item.icon} {item.text}
          </div>
        ))}
      </div>
    </div>
  );
}
