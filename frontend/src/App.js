import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navigation from './Navigation';
import AdvisorPage from './pages/AdvisorPage';
import SessionPage from './pages/SessionPage';
import ShotChart from './ShotChart';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Navigation />
        <Routes>
          <Route path="/" element={<AdvisorPage />} />
          <Route path="/session" element={<SessionPage />} />
          <Route path="/shot-chart" element={<ShotChart />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;