
export const SESSION_KEY = 'shot_advisor_session_v1';

// Generate a simple ID
const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2);

// Get current session or create new one
export const getSession = () => {
  const stored = localStorage.getItem(SESSION_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch (e) {
      console.error("Error parsing session data", e);
    }
  }
  return createNewSession();
};

// Create a completely new session
export const createNewSession = () => {
  const newSession = {
    sessionId: new Date().toISOString(),
    startedAt: new Date().toISOString(),
    attempts: []
  };
  saveSession(newSession);
  return newSession;
};

// Save session to local storage
const saveSession = (session) => {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
};

// Log a new attempt
export const logAttempt = (inputData, outputData) => {
  const currentSession = getSession();

  const attempt = {
    id: generateId(),
    createdAt: new Date().toISOString(),
    input: {
      locX: inputData.loc_x,
      locY: inputData.loc_y,
      shotDistance: inputData.shot_distance,
      shotType: inputData.shot_type,
      zone: inputData.zone,
      quarter: inputData.quarter,
      minsLeft: inputData.mins_left,
      secsLeft: inputData.secs_left,
      position: inputData.position,
      defenderDistance: inputData.defender_distance,
      contestLevel: inputData.contest_level
    },
    output: {
      decision: outputData.decision,
      makeProbability: outputData.make_probability,
      threshold: outputData.threshold,
      confidence: outputData.confidence,
      recommendedAction: outputData.recommended_action
    },
    userOutcome: null
  };

  currentSession.attempts.unshift(attempt); // Add to beginning (latest first)
  saveSession(currentSession);
  return attempt;
};

// Update outcome for an attempt (MADE / MISSED / null)
export const updateAttemptOutcome = (attemptId, outcome) => {
  const currentSession = getSession();
  const attemptIndex = currentSession.attempts.findIndex(a => a.id === attemptId);

  if (attemptIndex !== -1) {
    currentSession.attempts[attemptIndex].userOutcome = outcome;
    saveSession(currentSession);
    return true;
  }
  return false;
};

// Clear session data
export const clearSession = () => {
  localStorage.removeItem(SESSION_KEY);
};

// Export to CSV
export const exportSessionCSV = () => {
  const session = getSession();
  if (!session.attempts.length) return;

  const headers = [
    'Time', 'Zone', 'Shot Type', 'Distance', 'Input X', 'Input Y',
    'Contest Level', 'Decision', 'Make Probability', 'Confidence', 'Action', 'Outcome'
  ];

  const rows = session.attempts.map(a => [
    new Date(a.createdAt).toLocaleTimeString(),
    a.input.zone,
    a.input.shotType,
    a.input.shotDistance,
    a.input.locX,
    a.input.locY,
    a.input.contestLevel,
    a.output.decision,
    (a.output.makeProbability * 100).toFixed(1) + '%',
    (a.output.confidence * 100).toFixed(1) + '%',
    a.output.recommendedAction || '',
    a.userOutcome || 'UNKNOWN'
  ]);

  const csvContent = "data:text/csv;charset=utf-8,"
    + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `session_shots_${session.sessionId}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
