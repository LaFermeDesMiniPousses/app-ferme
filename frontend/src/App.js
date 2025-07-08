import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Zone Card Component
const ZoneCard = ({ zone, onVisit, isVisited }) => {
  const [showGame, setShowGame] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [gameResult, setGameResult] = useState(null);
  const [showQR, setShowQR] = useState(false);
  const [qrCode, setQRCode] = useState('');

  const handleGameSubmit = async () => {
    try {
      const formData = new FormData();
      formData.append('selected_answer', selectedAnswer);
      
      const response = await axios.post(`${API}/zones/${zone.id}/game/answer`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setGameResult(response.data);
      setTimeout(() => {
        setShowGame(false);
        setGameResult(null);
        setSelectedAnswer('');
      }, 3000);
    } catch (error) {
      console.error('Error submitting game answer:', error);
    }
  };

  const handleGenerateQR = async () => {
    try {
      const response = await axios.get(`${API}/zones/${zone.id}/qr`);
      setQRCode(response.data.qr_code);
      setShowQR(true);
    } catch (error) {
      console.error('Error generating QR code:', error);
    }
  };

  const handleVisit = () => {
    onVisit(zone.id);
  };

  return (
    <div className={`zone-card ${isVisited ? 'visited' : ''}`}>
      <div className="zone-header">
        <h3 className="zone-title">{zone.name}</h3>
        {isVisited && <span className="visited-badge">✓ Visitée</span>}
      </div>
      
      {zone.image_base64 && (
        <img 
          src={`data:image/jpeg;base64,${zone.image_base64}`} 
          alt={zone.name}
          className="zone-image"
        />
      )}
      
      <p className="zone-description">{zone.description}</p>
      
      {zone.video_url && (
        <div className="zone-video">
          <iframe 
            src={zone.video_url} 
            title={`${zone.name} video`}
            frameBorder="0"
            allowFullScreen
          ></iframe>
        </div>
      )}
      
      {zone.audio_base64 && (
        <audio controls className="zone-audio">
          <source src={`data:audio/mpeg;base64,${zone.audio_base64}`} type="audio/mpeg" />
          Votre navigateur ne supporte pas l'audio.
        </audio>
      )}
      
      <div className="zone-actions">
        <button className="cta-button" onClick={handleVisit}>
          {zone.cta_text}
        </button>
        
        <button className="visit-button" onClick={handleVisit}>
          Je suis ici !
        </button>
        
        {zone.game && (
          <button className="game-button" onClick={() => setShowGame(true)}>
            🎮 Jeu
          </button>
        )}
        
        <button className="qr-button" onClick={handleGenerateQR}>
          📱 QR Code
        </button>
      </div>
      
      {/* Game Modal */}
      {showGame && zone.game && (
        <div className="game-modal">
          <div className="game-content">
            <h4>🎮 {zone.game.question}</h4>
            
            <div className="game-options">
              {zone.game.options.map((option, index) => (
                <label key={index} className="game-option">
                  <input
                    type="radio"
                    name="answer"
                    value={option}
                    checked={selectedAnswer === option}
                    onChange={(e) => setSelectedAnswer(e.target.value)}
                  />
                  {option}
                </label>
              ))}
            </div>
            
            <div className="game-actions">
              <button 
                className="submit-button" 
                onClick={handleGameSubmit}
                disabled={!selectedAnswer}
              >
                Valider
              </button>
              <button 
                className="cancel-button" 
                onClick={() => setShowGame(false)}
              >
                Annuler
              </button>
            </div>
            
            {gameResult && (
              <div className={`game-result ${gameResult.is_correct ? 'correct' : 'incorrect'}`}>
                <p>{gameResult.is_correct ? '✅ Correct !' : '❌ Incorrect'}</p>
                <p>{gameResult.explanation}</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* QR Code Modal */}
      {showQR && (
        <div className="qr-modal">
          <div className="qr-content">
            <h4>📱 QR Code pour {zone.name}</h4>
            {qrCode && (
              <img 
                src={`data:image/png;base64,${qrCode}`} 
                alt="QR Code"
                className="qr-image"
              />
            )}
            <p>Scannez ce code pour accéder directement à cette zone</p>
            <button className="close-button" onClick={() => setShowQR(false)}>
              Fermer
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  const [zones, setZones] = useState([]);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      setLoading(true);
      
      // Initialize sample data
      await axios.post(`${API}/init-sample-data`);
      
      // Create session
      const sessionResponse = await axios.post(`${API}/session`);
      setSession(sessionResponse.data);
      
      // Load zones
      const zonesResponse = await axios.get(`${API}/zones`);
      setZones(zonesResponse.data);
      
    } catch (error) {
      console.error('Error initializing app:', error);
      setError('Erreur lors du chargement de l\'application');
    } finally {
      setLoading(false);
    }
  };

  const handleZoneVisit = async (zoneId) => {
    if (!session) return;
    
    try {
      await axios.post(`${API}/session/${session.id}/visit/${zoneId}`);
      
      // Update session
      const sessionResponse = await axios.get(`${API}/session/${session.id}`);
      setSession(sessionResponse.data);
    } catch (error) {
      console.error('Error marking zone as visited:', error);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <h2>🌾 Chargement de la ferme...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">
          <h2>❌ {error}</h2>
          <button onClick={initializeApp}>Réessayer</button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🌾 La Ferme des Mini-Pousses</h1>
        <p>Découvrez notre ferme pédagogique interactive !</p>
        
        {session && (
          <div className="progress-bar">
            <p>
              Zones visitées: {session.visited_zones.length} / {session.total_zones}
            </p>
            <div className="progress">
              <div 
                className="progress-fill" 
                style={{ 
                  width: `${(session.visited_zones.length / session.total_zones) * 100}%` 
                }}
              ></div>
            </div>
          </div>
        )}
      </header>
      
      <main className="app-main">
        <div className="zones-grid">
          {zones.map((zone) => (
            <ZoneCard
              key={zone.id}
              zone={zone}
              onVisit={handleZoneVisit}
              isVisited={session?.visited_zones.includes(zone.id)}
            />
          ))}
        </div>
      </main>
      
      <footer className="app-footer">
        <p>© 2025 La Ferme des Mini-Pousses - Une aventure pédagogique interactive</p>
      </footer>
    </div>
  );
};

export default App;