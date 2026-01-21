import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

function Navigation() {
  const location = useLocation();
  
  return (
    <nav className="main-nav">
      <div className="nav-container">
        <div className="nav-brand">🏀 NBA Shot Analytics</div>
        <div className="nav-links">
          <Link 
            to="/" 
            className={location.pathname === '/' ? 'nav-link active' : 'nav-link'}
          >
            Advisor
          </Link>
          <Link 
            to="/shot-chart" 
            className={location.pathname === '/shot-chart' ? 'nav-link active' : 'nav-link'}
          >
            Shot Chart
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;