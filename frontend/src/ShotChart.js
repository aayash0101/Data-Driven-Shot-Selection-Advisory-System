import React, { useState, useEffect, useRef } from 'react';
import './ShotChart.css';

const API_URL = 'http://localhost:8000';

// Court dimensions (must match Court.js)
const SVG_WIDTH = 500;
const SVG_HEIGHT = 470;
const COURT_WIDTH_FT = 50;
const COURT_LENGTH_FT = 50;

/**
 * Convert feet coordinates to pixel coordinates
 */
const feetToPixels = (xFt, yFt) => {
  const xPx = ((xFt + 25) / COURT_WIDTH_FT) * SVG_WIDTH;
  const yPx = SVG_HEIGHT - (yFt / COURT_LENGTH_FT) * SVG_HEIGHT;
  return { xPx, yPx };
};

/**
 * Draw NBA half-court (non-interactive version from Court.js)
 */
function drawCourt(ctx) {
  const basketX = SVG_WIDTH / 2;
  const basketY = SVG_HEIGHT - 20;
  const threePointRadiusFt = 23.75;
  const threePointRadiusPx = (threePointRadiusFt / COURT_LENGTH_FT) * SVG_HEIGHT;

  // Clear canvas
  ctx.clearRect(0, 0, SVG_WIDTH, SVG_HEIGHT);

  // Court background - wood texture
  const gradient = ctx.createLinearGradient(0, 0, SVG_WIDTH, SVG_HEIGHT);
  gradient.addColorStop(0, '#d4a574');
  gradient.addColorStop(0.5, '#c89968');
  gradient.addColorStop(1, '#b8885a');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, SVG_WIDTH, SVG_HEIGHT);

  // Border
  ctx.strokeStyle = '#8b6f47';
  ctx.lineWidth = 5;
  ctx.strokeRect(0, 0, SVG_WIDTH, SVG_HEIGHT);

  // White court lines
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2.5;
  ctx.globalAlpha = 0.9;

  // Half-court line
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(SVG_WIDTH, 0);
  ctx.stroke();

  // Paint (key)
  const paintWidth = 16 * (SVG_WIDTH / COURT_WIDTH_FT);
  const paintHeight = 19 * (SVG_HEIGHT / COURT_LENGTH_FT);
  ctx.fillStyle = 'rgba(184, 136, 90, 0.15)';
  ctx.fillRect(
    SVG_WIDTH / 2 - paintWidth / 2,
    SVG_HEIGHT - paintHeight,
    paintWidth,
    paintHeight
  );
  ctx.strokeRect(
    SVG_WIDTH / 2 - paintWidth / 2,
    SVG_HEIGHT - paintHeight,
    paintWidth,
    paintHeight
  );

  // Free throw circle
  ctx.beginPath();
  ctx.arc(
    SVG_WIDTH / 2,
    SVG_HEIGHT - paintHeight,
    6 * (SVG_WIDTH / COURT_WIDTH_FT),
    0,
    2 * Math.PI
  );
  ctx.stroke();

  // Restricted area arc
  ctx.beginPath();
  ctx.arc(
    basketX,
    basketY,
    4 * (SVG_HEIGHT / COURT_LENGTH_FT),
    Math.PI,
    2 * Math.PI
  );
  ctx.stroke();

  // Three-point arc
  ctx.beginPath();
  ctx.arc(
    basketX,
    basketY,
    threePointRadiusPx,
    (200 * Math.PI) / 180,
    (340 * Math.PI) / 180
  );
  ctx.stroke();

  // Three-point corner lines
  ctx.beginPath();
  ctx.moveTo(30, basketY - threePointRadiusPx * 0.75);
  ctx.lineTo(30, SVG_HEIGHT);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(SVG_WIDTH - 30, basketY - threePointRadiusPx * 0.75);
  ctx.lineTo(SVG_WIDTH - 30, SVG_HEIGHT);
  ctx.stroke();

  // Basket - backboard
  ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.fillRect(basketX - 25, basketY - 3, 50, 6);
  ctx.strokeRect(basketX - 25, basketY - 3, 50, 6);

  // Basket - rim
  ctx.strokeStyle = '#ff6b35';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(basketX, basketY, 8, 0, 2 * Math.PI);
  ctx.stroke();

  ctx.fillStyle = '#ff6b35';
  ctx.beginPath();
  ctx.arc(basketX, basketY, 2.5, 0, 2 * Math.PI);
  ctx.fill();

  // Baseline
  ctx.strokeStyle = '#8b6f47';
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.moveTo(0, SVG_HEIGHT);
  ctx.lineTo(SVG_WIDTH, SVG_HEIGHT);
  ctx.stroke();

  ctx.globalAlpha = 1.0;
}

/**
 * Draw shot dots on canvas
 */
function drawShots(ctx, shots) {
  shots.forEach(shot => {
    const { xPx, yPx } = feetToPixels(shot.x, shot.y);
    
    ctx.fillStyle = shot.made 
      ? 'rgba(16, 185, 129, 0.5)'  // Green for made
      : 'rgba(239, 68, 68, 0.5)';   // Red for missed
    
    ctx.beginPath();
    ctx.arc(xPx, yPx, 2.5, 0, 2 * Math.PI);
    ctx.fill();
  });
}

function ShotChart() {
  const canvasRef = useRef(null);
  
  const [shots, setShots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metadata, setMetadata] = useState(null);
  
  // Filters
  const [madeFilter, setMadeFilter] = useState('all');
  const [shotTypeFilter, setShotTypeFilter] = useState('all');
  const [zoneFilter, setZoneFilter] = useState('all');
  
  // Load metadata on mount
  useEffect(() => {
    fetch(`${API_URL}/shots/meta`)
      .then(res => res.json())
      .then(data => setMetadata(data))
      .catch(err => console.error('Failed to load metadata:', err));
  }, []);
  
  // Load shots when filters change
  useEffect(() => {
    loadShots();
  }, [madeFilter, shotTypeFilter, zoneFilter]);
  
  // Redraw canvas when shots change
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    drawCourt(ctx);
    drawShots(ctx, shots);
  }, [shots]);
  
  const loadShots = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        limit: '15000',
        made: madeFilter,
        shot_type: shotTypeFilter,
        zone: zoneFilter
      });
      
      const response = await fetch(`${API_URL}/shots/sample?${params}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      setShots(data.shots);
    } catch (err) {
      setError(err.message);
      console.error('Error loading shots:', err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="shot-chart-page">
      <div className="page-header">
        <h1>NBA Shot Chart</h1>
        <p>Visualize shot location data with interactive filters</p>
      </div>
      
      <div className="chart-container">
        <div className="filters-panel">
          <h3>Filters</h3>
          
          <div className="filter-group">
            <label>Shot Result:</label>
            <select value={madeFilter} onChange={(e) => setMadeFilter(e.target.value)}>
              <option value="all">All Shots</option>
              <option value="made">Made Only</option>
              <option value="missed">Missed Only</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Shot Type:</label>
            <select value={shotTypeFilter} onChange={(e) => setShotTypeFilter(e.target.value)}>
              <option value="all">All Types</option>
              <option value="2PT Field Goal">2PT Field Goal</option>
              <option value="3PT Field Goal">3PT Field Goal</option>
            </select>
          </div>
          
          {metadata && metadata.zones && (
            <div className="filter-group">
              <label>Zone:</label>
              <select value={zoneFilter} onChange={(e) => setZoneFilter(e.target.value)}>
                <option value="all">All Zones</option>
                {metadata.zones.map(zone => (
                  <option key={zone} value={zone}>{zone}</option>
                ))}
              </select>
            </div>
          )}
          
          <div className="stats-display">
            <div className="stat-item">
              <span className="stat-label">Shots Displayed:</span>
              <span className="stat-value">{shots.length.toLocaleString()}</span>
            </div>
            
            {metadata && (
              <div className="stat-item">
                <span className="stat-label">Total Available:</span>
                <span className="stat-value">{metadata.count.toLocaleString()}</span>
              </div>
            )}
            
            {shots.length > 0 && (
              <>
                <div className="stat-item">
                  <span className="stat-label">Made:</span>
                  <span className="stat-value stat-made">
                    {shots.filter(s => s.made).length.toLocaleString()}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Missed:</span>
                  <span className="stat-value stat-missed">
                    {shots.filter(s => !s.made).length.toLocaleString()}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">FG%:</span>
                  <span className="stat-value">
                    {((shots.filter(s => s.made).length / shots.length) * 100).toFixed(1)}%
                  </span>
                </div>
              </>
            )}
          </div>
          
          <div className="legend">
            <h4>Legend</h4>
            <div className="legend-item">
              <span className="legend-dot made"></span>
              <span>Made Shot</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot missed"></span>
              <span>Missed Shot</span>
            </div>
          </div>
        </div>
        
        <div className="chart-display">
          {error && (
            <div className="error-message">
              <p>Error: {error}</p>
              <p>Make sure the backend is running on {API_URL}</p>
            </div>
          )}
          
          {loading && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <p>Loading shots...</p>
            </div>
          )}
          
          <div className="court-wrapper">
            <canvas
              ref={canvasRef}
              width={SVG_WIDTH}
              height={SVG_HEIGHT}
              className="shot-canvas"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default ShotChart;