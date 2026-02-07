
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSession, createNewSession, clearSession, exportSessionCSV, updateAttemptOutcome } from '../utils/sessionTracker';
import './SessionPage.css';

const SessionPage = () => {
    const navigate = useNavigate();
    const [rawSession, setRawSession] = useState(getSession());
    const [selectedAttempt, setSelectedAttempt] = useState(null);

    // Filters state
    const [filterDecision, setFilterDecision] = useState('ALL');
    const [filterContest, setFilterContest] = useState('ALL');
    const [filterZone, setFilterZone] = useState('ALL');
    const [filterActionOnly, setFilterActionOnly] = useState(false);

    // Refresh session data on mount
    useEffect(() => {
        setRawSession(getSession());
    }, []);

    // 1. Data Normalization & Safekeeping
    const safeAttempts = useMemo(() => {
        return (rawSession.attempts || []).map(a => ({
            ...a,
            input: {
                zone: 'Unknown',
                contestLevel: 'OPEN',
                shotDistance: 0,
                // defaults to ensure no crash
                ...a.input
            },
            output: {
                makeProbability: 0,
                threshold: 0,
                decision: 'PASS',
                // defaults
                ...a.output
            }
        }));
    }, [rawSession]);

    // 2. Get Unique Zones for Filter
    const availableZones = useMemo(() => {
        const zones = new Set(safeAttempts.map(a => a.input.zone));
        return Array.from(zones).sort();
    }, [safeAttempts]);

    // 3. Filtering
    const filteredAttempts = useMemo(() => {
        return safeAttempts.filter(a => {
            if (filterDecision !== 'ALL' && a.output.decision !== filterDecision) return false;
            if (filterContest !== 'ALL' && (a.input.contestLevel || 'OPEN') !== filterContest) return false;
            if (filterZone !== 'ALL' && a.input.zone !== filterZone) return false;
            if (filterActionOnly && !a.output.recommendedAction) return false;
            return true;
        });
    }, [safeAttempts, filterDecision, filterContest, filterZone, filterActionOnly]);


    // 4. Metrics Calculation (on Filtered Data)
    const stats = useMemo(() => {
        const total = filteredAttempts.length;
        // Init Matrix Counts
        const matrix = {
            processWin: 0, // Good Decision + Make
            trustProcess: 0, // Good Decision + Miss
            foolsGold: 0, // Bad Decision + Make
            correction: 0, // Bad Decision + Miss
            unknown: 0
        };

        if (total === 0) return {
            total: 0, takes: 0, passes: 0,
            takePct: 0, passPct: 0,
            avgProb: 0, avgGap: 0,
            goodDecisionRate: 0, riskRate: 0,
            matrix
        };

        const takes = filteredAttempts.filter(a => a.output.decision === 'TAKE SHOT').length;
        const passes = total - takes;

        const sumProb = filteredAttempts.reduce((s, a) => s + (a.output.makeProbability || 0), 0);
        const sumGap = filteredAttempts.reduce((s, a) => s + ((a.output.makeProbability || 0) - (a.output.threshold || 0)), 0);

        // Decision Quality Logic
        let goodDecisions = 0;
        let riskyTakes = 0;

        filteredAttempts.forEach(a => {
            const isTake = a.output.decision === 'TAKE SHOT';
            const prob = a.output.makeProbability || 0;
            const thresh = a.output.threshold || 0;
            const contest = (a.input.contestLevel || 'OPEN');
            const isTight = contest === 'TIGHT' || contest === 'CONTESTED';

            const isGoodDecision = (isTake && prob >= thresh) || (!isTake && prob < thresh);

            if (isGoodDecision) {
                goodDecisions++;
            }

            // Risk: TAKE when < threshold AND Contested
            if (isTake && prob < thresh && isTight) {
                riskyTakes++;
            }

            // Matrix Logic (Only for TAKES usually, but applies generally if we track userOutcome on Passes? Assuming UserOutcome only on TAKES usually)
            // Let's assume tags are mostly relevant for TAKES, but user can tag PASS outcomes too if they want (e.g. teammate scored).
            // For simplicity, let's focus on TAKES for the matrix or shots where outcome is known.
            if (a.userOutcome) {
                const isMade = a.userOutcome === 'MADE';
                if (isGoodDecision) {
                    isMade ? matrix.processWin++ : matrix.trustProcess++;
                } else {
                    isMade ? matrix.foolsGold++ : matrix.correction++;
                }
            } else {
                matrix.unknown++;
            }
        });

        return {
            total,
            takes,
            passes,
            takePct: ((takes / total) * 100).toFixed(1),
            passPct: ((passes / total) * 100).toFixed(1),
            avgProb: ((sumProb / total) * 100).toFixed(1),
            avgGap: ((sumGap / total) * 100).toFixed(1),
            goodDecisionRate: ((goodDecisions / total) * 100).toFixed(1),
            riskRate: ((riskyTakes / total) * 100).toFixed(1),
            matrix
        };
    }, [filteredAttempts]);

    // 5. Calibration Data
    const calibration = useMemo(() => {
        const buckets = {
            low: { predictedSum: 0, actualMakes: 0, count: 0 }, // < 33%
            med: { predictedSum: 0, actualMakes: 0, count: 0 }, // 33-66%
            high: { predictedSum: 0, actualMakes: 0, count: 0 } // > 66%
        };

        filteredAttempts.forEach(a => {
            if (!a.userOutcome) return;
            const prob = a.output.makeProbability || 0;
            const isMade = a.userOutcome === 'MADE';

            let bucket = 'med';
            if (prob < 0.33) bucket = 'low';
            else if (prob > 0.66) bucket = 'high';

            buckets[bucket].count++;
            buckets[bucket].predictedSum += prob;
            if (isMade) buckets[bucket].actualMakes++;
        });

        return Object.keys(buckets).reduce((acc, key) => {
            const b = buckets[key];
            if (b.count === 0) {
                acc[key] = { predicted: 0, actual: 0, count: 0 };
            } else {
                acc[key] = {
                    predicted: (b.predictedSum / b.count * 100).toFixed(0),
                    actual: (b.actualMakes / b.count * 100).toFixed(0),
                    count: b.count
                };
            }
            return acc;
        }, {});
    }, [filteredAttempts]);


    // 6. Coaching Insights (Rule Based)
    const insights = useMemo(() => {
        if (filteredAttempts.length < 3) return []; // Need some data

        const msgs = [];

        // Find weakest zone (lowest avg prob)
        const zoneStats = {};
        filteredAttempts.forEach(a => {
            if (!zoneStats[a.input.zone]) zoneStats[a.input.zone] = { sum: 0, count: 0 };
            zoneStats[a.input.zone].sum += (a.output.makeProbability || 0);
            zoneStats[a.input.zone].count++;
        });

        let worstZone = null;
        let minProb = 1.0;

        Object.entries(zoneStats).forEach(([z, s]) => {
            const avg = s.sum / s.count;
            if (avg < minProb) {
                minProb = avg;
                worstZone = z;
            }
        });

        if (worstZone) {
            msgs.push(`Focus practice on **${worstZone}** (Avg Prob: ${(minProb * 100).toFixed(0)}%).`);
        }

        // Fools Gold Warning
        if (stats.matrix.foolsGold > 1 && stats.matrix.foolsGold > stats.matrix.processWin) {
            msgs.push("⚠️ **Fool's Gold Alert**: You are making bad shots. Don't let results justify poor process.");
        }

        // Trust Process Encouragement
        if (stats.matrix.trustProcess > 2) {
            msgs.push("Hint: **Trust the Process**. Good decisions that miss are just variance. Keep taking them.");
        }

        if (Number(stats.riskRate) > 20) {
            msgs.push("High Risk Rate: You are forcing too many contested shots below threshold.");
        }

        return msgs;
    }, [filteredAttempts, stats]);


    const handleNewSession = () => {
        const newS = createNewSession();
        setRawSession(newS);
        setSelectedAttempt(null);
    };

    const handleClearSession = () => {
        clearSession();
        setRawSession(getSession());
        setSelectedAttempt(null);
    };

    const handleReplay = () => {
        if (!selectedAttempt) return;
        localStorage.setItem('replay_attempt', JSON.stringify(selectedAttempt));
        navigate('/');
    };

    const handleOutcomeUpdate = (outcome) => {
        if (!selectedAttempt) return;
        const success = updateAttemptOutcome(selectedAttempt.id, outcome);
        if (success) {
            // Update local state
            setRawSession(prev => ({
                ...prev,
                attempts: prev.attempts.map(a =>
                    a.id === selectedAttempt.id ? { ...a, userOutcome: outcome } : a
                )
            }));
            // Update selected attempt view
            setSelectedAttempt(prev => ({ ...prev, userOutcome: outcome }));
        }
    };

    // Attempt List Rendering
    const AttemptRow = ({ attempt }) => (
        <tr
            onClick={() => setSelectedAttempt(attempt)}
            className={selectedAttempt?.id === attempt.id ? 'selected' : ''}
            tabIndex="0"
            onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedAttempt(attempt);
                }
            }}
        >
            <td className="mono-font">
                {new Date(attempt.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </td>
            <td>{attempt.input.zone}</td>
            <td>
                <span className={`badge contest-${(attempt.input.contestLevel || 'open').toLowerCase()}`}>
                    {attempt.input.contestLevel || 'OPEN'}
                </span>
            </td>
            <td>
                <span className={`badge decision-${attempt.output.decision === 'TAKE SHOT' ? 'take' : 'pass'}`}>
                    {attempt.output.decision === 'TAKE SHOT' ? 'TAKE' : 'PASS'}
                </span>
            </td>
            <td>
                {/* Outcome Badge in table */}
                {attempt.userOutcome ? (
                    <span className={`badge outcome-${attempt.userOutcome.toLowerCase()}`}>
                        {attempt.userOutcome}
                    </span>
                ) : (
                    <span className="dim-text">-</span>
                )}
            </td>
            <td className="mono-font">
                {(attempt.output.makeProbability * 100).toFixed(1)}%
            </td>
        </tr>
    );

    return (
        <div className="session-page container">
            {/* Header */}
            <div className="session-header">
                <h2>Session Training Log</h2>
                <div className="session-controls">
                    <button onClick={handleNewSession} className="control-btn new">New Session</button>
                    <button onClick={exportSessionCSV} className="control-btn export">Export CSV</button>
                    <button onClick={handleClearSession} className="control-btn clear">Clear Data</button>
                </div>
            </div>

            {/* Filter Bar */}
            <div className="filter-bar">
                <div className="filter-group">
                    <label>Decision:</label>
                    <select value={filterDecision} onChange={(e) => setFilterDecision(e.target.value)}>
                        <option value="ALL">All</option>
                        <option value="TAKE SHOT">Take</option>
                        <option value="PASS">Pass</option>
                    </select>
                </div>
                <div className="filter-group">
                    <label>Contest:</label>
                    <select value={filterContest} onChange={(e) => setFilterContest(e.target.value)}>
                        <option value="ALL">All</option>
                        <option value="TIGHT">Tight</option>
                        <option value="CONTESTED">Contested</option>
                        <option value="OPEN">Open</option>
                        <option value="WIDE_OPEN">Wide Open</option>
                    </select>
                </div>
                <div className="filter-group">
                    <label>Zone:</label>
                    <select value={filterZone} onChange={(e) => setFilterZone(e.target.value)}>
                        <option value="ALL">All Zones</option>
                        {availableZones.map(z => <option key={z} value={z}>{z}</option>)}
                    </select>
                </div>
                <div className="filter-group checkbox">
                    <label>
                        <input
                            type="checkbox"
                            checked={filterActionOnly}
                            onChange={(e) => setFilterActionOnly(e.target.checked)}
                        />
                        Has Action
                    </label>
                </div>
            </div>

            {/* Stats Dashboard Grid */}
            <div className="stats-dashboard">

                {/* 1. Decision Quality */}
                <div className="stat-card">
                    <h3>Decision Quality</h3>
                    <div className="stat-row">
                        <span>Good Decisions</span>
                        <span className="bold" style={{ color: stats.goodDecisionRate >= 70 ? 'green' : '#d97706' }}>
                            {stats.goodDecisionRate}%
                        </span>
                    </div>
                    <div className="stat-row">
                        <span>Risk Rate</span>
                        <span className="bold" style={{ color: stats.riskRate <= 15 ? 'green' : 'red' }}>
                            {stats.riskRate}%
                        </span>
                    </div>
                </div>

                {/* 2. Process / Outcome Matrix */}
                <div className="stat-card matrix-card">
                    <h3>Decision Matrix (Tagged)</h3>
                    <div className="matrix-grid">
                        <div className="matrix-cell win" title="Good Decision + Made">
                            <span className="matrix-cnt">{stats.matrix.processWin}</span>
                            <span className="matrix-lbl">Process Win</span>
                        </div>
                        <div className="matrix-cell trust" title="Good Decision + Missed">
                            <span className="matrix-cnt">{stats.matrix.trustProcess}</span>
                            <span className="matrix-lbl">Trust Process</span>
                        </div>
                        <div className="matrix-cell fools" title="Bad Decision + Made">
                            <span className="matrix-cnt">{stats.matrix.foolsGold}</span>
                            <span className="matrix-lbl">Fool's Gold</span>
                        </div>
                        <div className="matrix-cell correction" title="Bad Decision + Missed">
                            <span className="matrix-cnt">{stats.matrix.correction}</span>
                            <span className="matrix-lbl">Correction</span>
                        </div>
                    </div>
                </div>

                {/* 3. Calibration */}
                <div className="stat-card">
                    <h3>Calibration (Pred vs Actual)</h3>
                    <div className="stat-row small-text">
                        <span>Low (&lt;33%)</span>
                        <span>{calibration.low.predicted}% vs <strong>{calibration.low.actual}%</strong></span>
                    </div>
                    <div className="stat-row small-text">
                        <span>Med (33-66%)</span>
                        <span>{calibration.med.predicted}% vs <strong>{calibration.med.actual}%</strong></span>
                    </div>
                    <div className="stat-row small-text">
                        <span>High (&gt;66%)</span>
                        <span>{calibration.high.predicted}% vs <strong>{calibration.high.actual}%</strong></span>
                    </div>
                    <div className="dim-text" style={{ marginTop: '5px', fontSize: '0.75em' }}>Based on {stats.total - stats.matrix.unknown} tagged shots</div>
                </div>

                {/* 4. Coaching Insights */}
                <div className="stat-card coaching">
                    <h3>📋 Coaching Insights</h3>
                    {insights.length > 0 ? (
                        <ul className="insight-list">
                            {insights.map((msg, i) => <li key={i} dangerouslySetInnerHTML={{ __html: msg.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />)}
                        </ul>
                    ) : (
                        <p className="dim-text">Log shots & outcomes for insights.</p>
                    )}
                </div>
            </div>

            {/* Main Content Area */}
            <div className="content-split">
                {/* Table */}
                <div className="attempts-list-section">
                    <h3>Attempts Log</h3>
                    <div className="table-wrapper">
                        <table className="attempts-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Zone</th>
                                    <th>Contest</th>
                                    <th>Decision</th>
                                    <th>Outcome</th>
                                    <th>Make %</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredAttempts.map(attempt => (
                                    <AttemptRow key={attempt.id} attempt={attempt} />
                                ))}
                                {filteredAttempts.length === 0 && (
                                    <tr><td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>No attempts match filters.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Details Panel */}
                {selectedAttempt && (
                    <div className="details-panel">
                        <div className="details-header">
                            <h3>Attempt Details</h3>
                            <button onClick={() => setSelectedAttempt(null)} aria-label="Close">×</button>
                        </div>
                        <div className="details-content">

                            {/* Outcome Toggles */}
                            <div className="outcome-toggles">
                                <span className="label">Outcome:</span>
                                <div className="toggle-group">
                                    <button
                                        className={`outcome-btn made ${selectedAttempt.userOutcome === 'MADE' ? 'active' : ''}`}
                                        onClick={() => handleOutcomeUpdate('MADE')}
                                    >
                                        MADE
                                    </button>
                                    <button
                                        className={`outcome-btn missed ${selectedAttempt.userOutcome === 'MISSED' ? 'active' : ''}`}
                                        onClick={() => handleOutcomeUpdate('MISSED')}
                                    >
                                        MISSED
                                    </button>
                                </div>
                            </div>

                            <hr style={{ margin: '15px 0', border: '0', borderTop: '1px solid #eee' }} />

                            <div className="detail-primary-action">
                                <button className="replay-btn" onClick={handleReplay}>
                                    ↺ Replay on Court
                                </button>
                            </div>

                            <div className="detail-group">
                                <h4>Inputs</h4>
                                <div className="detail-row"><strong>Zone:</strong> {selectedAttempt.input.zone}</div>
                                <div className="detail-row"><strong>Distance:</strong> {Number(selectedAttempt.input.shotDistance).toFixed(1)} ft</div>
                                <div className="detail-row"><strong>Coords:</strong> ({Number(selectedAttempt.input.locX).toFixed(1)}, {Number(selectedAttempt.input.locY).toFixed(1)})</div>
                                <div className="detail-row"><strong>Contest:</strong> {selectedAttempt.input.contestLevel}</div>
                                <div className="detail-row"><strong>Defender:</strong> {selectedAttempt.input.defenderDistance ? Number(selectedAttempt.input.defenderDistance).toFixed(1) : 'N/A'} ft</div>
                            </div>
                            <div className="detail-group">
                                <h4>Metrics</h4>
                                <div className="detail-row"><strong>Probability:</strong> {(selectedAttempt.output.makeProbability * 100).toFixed(1)}%</div>
                                <div className="detail-row"><strong>Threshold:</strong> {(selectedAttempt.output.threshold * 100).toFixed(1)}%</div>
                                <div className="detail-row"><strong>Confidence:</strong> {(selectedAttempt.output.confidence * 100).toFixed(1)}%</div>
                                <div className="detail-row"><strong>Action:</strong> {selectedAttempt.output.recommendedAction || '-'}</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SessionPage;
