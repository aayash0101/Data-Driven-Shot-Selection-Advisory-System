import React, { useState } from 'react';
import './App.css';
import Court from './Court';

const API_URL = 'http://localhost:8000';

function App() {
  const [shotDistance, setShotDistance] = useState(20);
  const [locX, setLocX] = useState(0);
  const [locY, setLocY] = useState(20);
  const [quarter, setQuarter] = useState(1);
  const [minsLeft, setMinsLeft] = useState(10);
  const [secsLeft, setSecsLeft] = useState(0);
  const [position, setPosition] = useState('PG');

  // Defender state
  const [defenderDistance, setDefenderDistance] = useState(null);
  const [contestLevel, setContestLevel] = useState('OPEN');

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Derive shot type + zone from location to avoid manual category mismatches.
  const deriveShotType = (distanceFt) => (distanceFt >= 23.0 ? '3PT Field Goal' : '2PT Field Goal');

  const deriveZone = (xFt, yFt, distanceFt) => {
    if (distanceFt >= 23.0 && Math.abs(xFt) >= 22.0 && yFt <= 14.0) {
      return xFt < 0 ? 'Left Corner 3' : 'Right Corner 3';
    }
    if (distanceFt <= 4.0) return 'Restricted Area';
    if (distanceFt <= 8.0) return 'In The Paint (Non-RA)';
    if (distanceFt < 23.0) return 'Mid-Range';
    return 'Above the Break 3';
  };

  // Core prediction call – can be used by sliders OR court clicks
  const handlePredict = async (override) => {
    setLoading(true);
    setError(null);
    setResult(null);

    const d = override?.shotDistance ?? shotDistance;
    const x = override?.locX ?? locX;
    const y = override?.locY ?? locY;
    const defDist = override?.defenderDistance ?? defenderDistance;
    const contest = override?.contestLevel ?? contestLevel;

    const derivedShotType = deriveShotType(d);
    const derivedZone = deriveZone(x, y, d);

    const payload = {
      shot_distance: d,
      loc_x: x,
      loc_y: y,
      shot_type: derivedShotType,
      zone: derivedZone,
      quarter: quarter,
      mins_left: minsLeft,
      secs_left: secsLeft,
      position: position,
      defender_distance: defDist,
      contest_level: contest
    };

    try {
      const response = await fetch(`${API_URL}/predict-shot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`API error: ${response.status} ${response.statusText} - ${text}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Called when user clicks on the court
  const handleCourtShot = ({ 
    locX: xFt, 
    locY: yFt, 
    shotDistance: distFt,
    defenderDistance: defDist,
    contestLevel: contest
  }) => {
    setLocX(xFt);
    setLocY(yFt);
    setShotDistance(distFt);
    setDefenderDistance(defDist);
    setContestLevel(contest);

    // Immediately trigger prediction using these values
    handlePredict({
      locX: xFt,
      locY: yFt,
      shotDistance: distFt,
      defenderDistance: defDist,
      contestLevel: contest
    });
  };

  // Format breakdown component for display
  const formatBreakdownComponent = (name, value) => {
    const percentage = (value * 100).toFixed(1);
    const sign = value >= 0 ? '+' : '';
    const color = value > 0 ? '#10b981' : value < 0 ? '#ef4444' : '#6b7280';
    
    return { name, percentage: `${sign}${percentage}%`, value, color };
  };

  // Component name mapping (updated with defensive pressure)
  const componentNames = {
    baseline: 'Base Ability',
    location_quality: 'Location Quality',
    shot_type_value: 'Shot Type Value',
    time_context: 'Time Context',
    defensive_pressure: 'Defensive Pressure'
  };

  // Action icon mapping for visual display
  const getActionIcon = (action) => {
    if (action?.includes('Swing')) return '🔄';
    if (action?.includes('Attack')) return '⚡';
    if (action?.includes('Reset')) return '🔁';
    if (action?.includes('Inside')) return '🎯';
    if (action?.includes('Drive')) return '💨';
    if (action?.includes('Best')) return '⏱️';
    if (action?.includes('Relocate')) return '🔀';
    return '🏀';
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🏀 Shot Selection Advisor</h1>
        <p>Data-driven shot selection advice with defender impact modeling & action recommendations</p>
      </header>

      <div className="container">
        <div className="input-panel">
          <h2>Shot Context</h2>

          {/* Interactive Court */}
          <Court onShotSelected={handleCourtShot} />

          {/* Display current court-derived coordinates */}
          <div className="coords-display">
            <div><strong>LOC_X:</strong> {locX.toFixed(2)} ft</div>
            <div><strong>LOC_Y:</strong> {locY.toFixed(2)} ft</div>
            <div><strong>SHOT_DISTANCE:</strong> {shotDistance.toFixed(2)} ft</div>
            <div><strong>SHOT_TYPE (auto):</strong> {deriveShotType(shotDistance)}</div>
            <div><strong>ZONE (auto):</strong> {deriveZone(locX, locY, shotDistance)}</div>
            
            {/* Defender info display */}
            {defenderDistance !== null && (
              <>
                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #ddd' }}>
                  <strong>DEFENDER_DISTANCE:</strong> {defenderDistance.toFixed(2)} ft
                </div>
                <div>
                  <strong>CONTEST_LEVEL:</strong> 
                  <span style={{
                    marginLeft: '8px',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.9em',
                    fontWeight: 'bold',
                    backgroundColor: 
                      contestLevel === 'TIGHT' ? '#fee2e2' :
                      contestLevel === 'CONTESTED' ? '#fed7aa' :
                      contestLevel === 'OPEN' ? '#fef3c7' : '#d1fae5',
                    color: 
                      contestLevel === 'TIGHT' ? '#991b1b' :
                      contestLevel === 'CONTESTED' ? '#9a3412' :
                      contestLevel === 'OPEN' ? '#854d0e' : '#065f46'
                  }}>
                    {contestLevel}
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Existing controls */}
          <div className="input-group">
            <label>
              Shot Distance (ft): {shotDistance.toFixed(1)}
              <input
                type="range"
                min="0"
                max="30"
                value={shotDistance}
                onChange={(e) => setShotDistance(parseFloat(e.target.value))}
              />
            </label>
          </div>

          <div className="input-group">
            <label>
              Location X: {locX.toFixed(1)}
              <input
                type="range"
                min="-25"
                max="25"
                step="0.5"
                value={locX}
                onChange={(e) => setLocX(parseFloat(e.target.value))}
              />
            </label>
          </div>

          <div className="input-group">
            <label>
              Location Y: {locY.toFixed(1)}
              <input
                type="range"
                min="0"
                max="50"
                step="0.5"
                value={locY}
                onChange={(e) => setLocY(parseFloat(e.target.value))}
              />
            </label>
          </div>

          <div className="input-group">
            <label>
              Quarter:
              <input
                type="number"
                min="1"
                max="5"
                value={quarter}
                onChange={(e) => setQuarter(parseInt(e.target.value, 10))}
              />
            </label>
          </div>

          <div className="input-group">
            <label>
              Minutes Left: {minsLeft}
              <input
                type="range"
                min="0"
                max="12"
                value={minsLeft}
                onChange={(e) => setMinsLeft(parseInt(e.target.value, 10))}
              />
            </label>
          </div>

          <div className="input-group">
            <label>
              Seconds Left: {secsLeft}
              <input
                type="range"
                min="0"
                max="59"
                value={secsLeft}
                onChange={(e) => setSecsLeft(parseInt(e.target.value, 10))}
              />
            </label>
          </div>

          <div className="input-group">
            <label>
              Position:
              <select value={position} onChange={(e) => setPosition(e.target.value)}>
                <option value="PG">PG</option>
                <option value="SG">SG</option>
                <option value="SF">SF</option>
                <option value="PF">PF</option>
                <option value="C">C</option>
              </select>
            </label>
          </div>

          <button
            className="predict-button"
            onClick={() => handlePredict()}
            disabled={loading}
          >
            {loading ? 'Predicting...' : 'Predict Shot'}
          </button>
        </div>

        <div className="result-panel">
          <h2>Advisory</h2>

          {error && (
            <div className="error">
              <p>Error: {error}</p>
              <p>Make sure the backend API is running on {API_URL}</p>
            </div>
          )}

          {result && (
            <>
              <div
                className={`result ${
                  result.decision === 'TAKE SHOT' ? 'take-shot' : 'pass'
                }`}
              >
                <div className="decision">
                  <h3>{result.decision}</h3>
                </div>

                <div className="metrics">
                  <div className="metric">
                    <label>Make Probability:</label>
                    <span>{(result.make_probability * 100).toFixed(1)}%</span>
                  </div>
                  <div className="metric">
                    <label>Threshold:</label>
                    <span>{(result.threshold * 100).toFixed(1)}%</span>
                  </div>
                  <div className="metric">
                    <label>Confidence:</label>
                    <span>{(result.confidence * 100).toFixed(1)}%</span>
                  </div>
                  
                  {/* Display contest info */}
                  {result.contest_level && (
                    <div className="metric">
                      <label>Contest:</label>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.9em',
                        fontWeight: 'bold',
                        backgroundColor: 
                          result.contest_level === 'TIGHT' ? '#fee2e2' :
                          result.contest_level === 'CONTESTED' ? '#fed7aa' :
                          result.contest_level === 'OPEN' ? '#fef3c7' : '#d1fae5',
                        color: 
                          result.contest_level === 'TIGHT' ? '#991b1b' :
                          result.contest_level === 'CONTESTED' ? '#9a3412' :
                          result.contest_level === 'OPEN' ? '#854d0e' : '#065f46'
                      }}>
                        {result.contest_level}
                      </span>
                    </div>
                  )}
                  
                  {result.defender_distance !== null && result.defender_distance !== undefined && (
                    <div className="metric">
                      <label>Defender Distance:</label>
                      <span>{result.defender_distance.toFixed(1)} ft</span>
                    </div>
                  )}
                </div>

                <div className="explanation">
                  <h4>Explanation:</h4>
                  <ul>
                    {result.explanation.map((exp, idx) => (
                      <li key={idx}>{exp}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* NEW: Action Recommendation Panel (only for PASS decisions) */}
              {result.decision === 'PASS' && result.recommended_action && (
                <div className="action-recommendation">
                  <h3>
                    {getActionIcon(result.recommended_action)} Recommended Action
                  </h3>
                  <div className="action-card">
                    <div className="action-title">
                      {result.recommended_action}
                    </div>
                    <div className="action-reasoning">
                      {result.action_reasoning}
                    </div>
                  </div>
                </div>
              )}

              {/* Shot Quality Breakdown Panel */}
              {result.shot_quality_breakdown && (
                <div className="quality-breakdown">
                  <h3>Shot Quality Breakdown</h3>
                  <div className="breakdown-divider"></div>
                  
                  <div className="breakdown-components">
                    {Object.entries(result.shot_quality_breakdown).map(([key, value]) => {
                      const formatted = formatBreakdownComponent(componentNames[key] || key, value);
                      return (
                        <div 
                          key={key} 
                          className={`breakdown-item ${key === 'defensive_pressure' ? 'defensive-pressure' : ''}`}
                        >
                          <div className="breakdown-label">{formatted.name}:</div>
                          <div 
                            className="breakdown-value"
                            style={{ color: formatted.color, fontWeight: 'bold' }}
                          >
                            {formatted.percentage}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  <div className="breakdown-divider"></div>
                  
                  <div className="breakdown-total">
                    <div className="breakdown-label">Final Probability:</div>
                    <div className="breakdown-value" style={{ fontWeight: 'bold', fontSize: '1.1em' }}>
                      {(result.make_probability * 100).toFixed(1)}%
                    </div>
                  </div>
                  
                  <div className="breakdown-note">
                    Components show how shot location, type, timing, and <strong>defensive pressure</strong> 
                    contribute to the predicted make probability.
                  </div>
                </div>
              )}

              {/* Defender Impact Details Panel */}
              {result.defender_impact_details && result.defender_distance !== null && (
                <div className="defender-impact-details">
                  <h3>🛡️ Defender Impact Analysis</h3>
                  <div className="breakdown-divider"></div>
                  
                  <div className="impact-metrics">
                    <div className="impact-metric">
                      <label>Distance Decay Factor:</label>
                      <span>{result.defender_impact_details.distance_decay.toFixed(3)}</span>
                    </div>
                    <div className="impact-metric">
                      <label>Contest Multiplier:</label>
                      <span>{result.defender_impact_details.contest_multiplier.toFixed(3)}</span>
                    </div>
                    <div className="impact-metric">
                      <label>Combined Impact Factor:</label>
                      <span style={{ fontWeight: 'bold' }}>
                        {result.defender_impact_details.impact_factor.toFixed(3)}
                      </span>
                    </div>
                    <div className="impact-metric">
                      <label>Net Adjustment:</label>
                      <span style={{ 
                        fontWeight: 'bold',
                        color: result.defender_impact_details.percentage_adjustment < 0 ? '#ef4444' : '#10b981'
                      }}>
                        {result.defender_impact_details.percentage_adjustment.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="breakdown-note">
                    Defender impact uses exponential distance decay combined with contest quality 
                    multipliers to realistically model defensive pressure.
                  </div>
                </div>
              )}
            </>
          )}

          {!result && !error && !loading && (
            <div className="placeholder">
              <p>
                Click anywhere on the court to place shooter and defender, or 
                adjust the shot parameters and click "Predict Shot" to get advice.
              </p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .action-recommendation {
          margin-top: 20px;
          padding: 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 12px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .action-recommendation h3 {
          margin: 0 0 16px 0;
          color: white;
          font-size: 1.3em;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .action-card {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .action-title {
          font-size: 1.4em;
          font-weight: bold;
          color: #2d3748;
          margin-bottom: 12px;
          padding-bottom: 12px;
          border-bottom: 2px solid #e2e8f0;
        }

        .action-reasoning {
          font-size: 1.05em;
          line-height: 1.6;
          color: #4a5568;
          font-weight: 500;
        }

        .quality-breakdown,
        .defender-impact-details {
          margin-top: 20px;
          padding: 20px;
          background: #f7fafc;
          border-radius: 12px;
          border: 1px solid #e2e8f0;
        }

        .quality-breakdown h3,
        .defender-impact-details h3 {
          margin: 0 0 16px 0;
          color: #2d3748;
          font-size: 1.2em;
        }

        .breakdown-divider {
          height: 1px;
          background: linear-gradient(to right, transparent, #cbd5e0, transparent);
          margin: 16px 0;
        }

        .breakdown-components,
        .impact-metrics {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .breakdown-item,
        .impact-metric {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          background: white;
          border-radius: 6px;
          border: 1px solid #e2e8f0;
        }

        .breakdown-item.defensive-pressure {
          background: #fff5f5;
          border-color: #fc8181;
        }

        .breakdown-label,
        .impact-metric label {
          font-weight: 600;
          color: #4a5568;
        }

        .breakdown-value,
        .impact-metric span {
          font-size: 1.1em;
        }

        .breakdown-total {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 8px;
          margin-top: 8px;
        }

        .breakdown-note {
          margin-top: 16px;
          font-size: 0.9em;
          color: #718096;
          line-height: 1.5;
        }
      `}</style>
    </div>
  );
}

export default App;