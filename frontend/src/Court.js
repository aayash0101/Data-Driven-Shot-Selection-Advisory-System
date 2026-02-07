import React, { useState } from 'react';
import './Court.css';

const COURT_WIDTH_FT = 50;
const COURT_LENGTH_FT = 50;


const calculateDistance = (x1, y1, x2, y2) => {
  const dx = x2 - x1;
  const dy = y2 - y1;
  return Math.sqrt(dx * dx + dy * dy);
};


const getContestLevel = (distance) => {
  if (distance === null || distance === undefined) return 'OPEN';
  if (distance <= 3) return 'TIGHT';
  if (distance <= 6) return 'CONTESTED';
  if (distance <= 10) return 'OPEN';
  return 'WIDE_OPEN';
};


function Court({ onShotSelected }) {
  const SVG_WIDTH = 500;
  const SVG_HEIGHT = 470;

  const [shooterMarker, setShooterMarker] = useState(null);
  const [defenderMarker, setDefenderMarker] = useState(null);
  const [clickCount, setClickCount] = useState(0);

  const handleClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const xPx = e.clientX - rect.left;
    const yPx = e.clientY - rect.top;


    const locX = (xPx / SVG_WIDTH) * COURT_WIDTH_FT - COURT_WIDTH_FT / 2;


    const locY = ((SVG_HEIGHT - yPx) / SVG_HEIGHT) * COURT_LENGTH_FT;

    if (clickCount === 0) {

      const shotDistance = Math.sqrt(locX * locX + locY * locY);

      setShooterMarker({ x: xPx, y: yPx, locX, locY });
      setDefenderMarker(null);
      setClickCount(1);

      if (onShotSelected) {
        onShotSelected({
          locX,
          locY,
          shotDistance,
          defenderDistance: null,
          contestLevel: 'OPEN'
        });
      }
    } else if (clickCount === 1) {

      setDefenderMarker({ x: xPx, y: yPx, locX, locY });
      setClickCount(2);


      const defenderDistance = calculateDistance(
        shooterMarker.locX,
        shooterMarker.locY,
        locX,
        locY
      );

      const contestLevel = getContestLevel(defenderDistance);
      const shotDistance = Math.sqrt(
        shooterMarker.locX * shooterMarker.locX +
        shooterMarker.locY * shooterMarker.locY
      );

      if (onShotSelected) {
        onShotSelected({
          locX: shooterMarker.locX,
          locY: shooterMarker.locY,
          shotDistance,
          defenderDistance,
          contestLevel,
          defenderLocX: locX,
          defenderLocY: locY
        });
      }
    } else {

      setShooterMarker(null);
      setDefenderMarker(null);
      setClickCount(0);

      if (onShotSelected) {
        onShotSelected({
          locX: 0,
          locY: 20,
          shotDistance: 20,
          defenderDistance: null,
          contestLevel: 'OPEN'
        });
      }
    }
  };

  const basketX = SVG_WIDTH / 2;
  const basketY = SVG_HEIGHT - 20;
  const threePointRadiusFt = 23.75;
  const threePointRadiusPx = (threePointRadiusFt / COURT_LENGTH_FT) * SVG_HEIGHT;

  return (
    <div className="court-container">
      <svg
        width={SVG_WIDTH}
        height={SVG_HEIGHT}
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        onClick={handleClick}
        className="court-svg"
      >
        {}
        <defs>
          <linearGradient id="woodGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#d4a574', stopOpacity: 1 }} />
            <stop offset="50%" style={{ stopColor: '#c89968', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#b8885a', stopOpacity: 1 }} />
          </linearGradient>
          <filter id="shadow">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.3"/>
          </filter>
        </defs>
        <rect
          x="0"
          y="0"
          width={SVG_WIDTH}
          height={SVG_HEIGHT}
          fill="url(#woodGradient)"
          stroke="#8b6f47"
          strokeWidth="5"
        />

        {}
        <line
          x1="0"
          y1="0"
          x2={SVG_WIDTH}
          y2="0"
          stroke="#ffffff"
          strokeWidth="3"
          opacity="0.9"
        />

        {}
        <rect
          x={SVG_WIDTH / 2 - (16 * (SVG_WIDTH / COURT_WIDTH_FT)) / 2}
          y={SVG_HEIGHT - (19 * (SVG_HEIGHT / COURT_LENGTH_FT))}
          width={16 * (SVG_WIDTH / COURT_WIDTH_FT)}
          height={19 * (SVG_HEIGHT / COURT_LENGTH_FT)}
          fill="rgba(184, 136, 90, 0.15)"
          stroke="#ffffff"
          strokeWidth="2.5"
          opacity="0.9"
        />

        {}
        <circle
          cx={SVG_WIDTH / 2}
          cy={SVG_HEIGHT - (19 * (SVG_HEIGHT / COURT_LENGTH_FT))}
          r={6 * (SVG_WIDTH / COURT_WIDTH_FT)}
          fill="none"
          stroke="#ffffff"
          strokeWidth="2.5"
          opacity="0.9"
        />

        {}
        <path
          d={describeArc(
            basketX,
            basketY,
            (4 * (SVG_HEIGHT / COURT_LENGTH_FT)),
            180,
            360
          )}
          fill="none"
          stroke="#ffffff"
          strokeWidth="2.5"
          opacity="0.9"
        />

        {}
        <rect
          x={basketX - 25}
          y={basketY - 3}
          width="50"
          height="6"
          fill="rgba(255, 255, 255, 0.3)"
          stroke="#ffffff"
          strokeWidth="2"
          rx="1"
        />
        <circle
          cx={basketX}
          cy={basketY}
          r="8"
          fill="none"
          stroke="#ff6b35"
          strokeWidth="3"
        />
        <circle
          cx={basketX}
          cy={basketY}
          r="2.5"
          fill="#ff6b35"
        />

        {}
        <path
          d={describeArc(
            basketX,
            basketY,
            threePointRadiusPx,
            200,
            340
          )}
          fill="none"
          stroke="#ffffff"
          strokeWidth="2.5"
          opacity="0.9"
        />
        {}
        <line
          x1="30"
          y1={basketY - threePointRadiusPx * 0.75}
          x2="30"
          y2={SVG_HEIGHT}
          stroke="#ffffff"
          strokeWidth="2.5"
          opacity="0.9"
        />
        <line
          x1={SVG_WIDTH - 30}
          y1={basketY - threePointRadiusPx * 0.75}
          x2={SVG_WIDTH - 30}
          y2={SVG_HEIGHT}
          stroke="#ffffff"
          strokeWidth="2.5"
          opacity="0.9"
        />

        {}
        <line
          x1="0"
          y1={SVG_HEIGHT}
          x2={SVG_WIDTH}
          y2={SVG_HEIGHT}
          stroke="#8b6f47"
          strokeWidth="5"
        />

        {}
        {shooterMarker && defenderMarker && (
          <>
            <line
              x1={shooterMarker.x}
              y1={shooterMarker.y}
              x2={defenderMarker.x}
              y2={defenderMarker.y}
              stroke="#4a5568"
              strokeWidth="2.5"
              strokeDasharray="8,4"
              opacity="0.7"
            />

            {}
            <rect
              x={(shooterMarker.x + defenderMarker.x) / 2 - 30}
              y={(shooterMarker.y + defenderMarker.y) / 2 - 22}
              width="60"
              height="20"
              fill="rgba(255, 255, 255, 0.95)"
              stroke="#4a5568"
              strokeWidth="1.5"
              rx="4"
            />
            <text
              x={(shooterMarker.x + defenderMarker.x) / 2}
              y={(shooterMarker.y + defenderMarker.y) / 2 - 8}
              fill="#2d3748"
              fontSize="13"
              fontWeight="bold"
              textAnchor="middle"
              style={{ pointerEvents: 'none' }}
            >
              {calculateDistance(
                shooterMarker.locX,
                shooterMarker.locY,
                defenderMarker.locX,
                defenderMarker.locY
              ).toFixed(1)} ft
            </text>
          </>
        )}

        {}
        {shooterMarker && (
          <>
            <circle
              cx={shooterMarker.x}
              cy={shooterMarker.y}
              r="12"
              fill="#3b82f6"
              stroke="#ffffff"
              strokeWidth="3"
              filter="url(#shadow)"
            />
            <circle
              cx={shooterMarker.x}
              cy={shooterMarker.y}
              r="6"
              fill="#1e40af"
              opacity="0.5"
            />
            <rect
              x={shooterMarker.x - 32}
              y={shooterMarker.y - 28}
              width="64"
              height="18"
              fill="rgba(59, 130, 246, 0.95)"
              stroke="#ffffff"
              strokeWidth="1.5"
              rx="4"
            />
            <text
              x={shooterMarker.x}
              y={shooterMarker.y - 15}
              fill="#ffffff"
              fontSize="12"
              fontWeight="bold"
              textAnchor="middle"
              style={{ pointerEvents: 'none' }}
            >
              Shooter
            </text>
          </>
        )}

        {}
        {defenderMarker && (
          <>
            <circle
              cx={defenderMarker.x}
              cy={defenderMarker.y}
              r="12"
              fill="#ef4444"
              stroke="#ffffff"
              strokeWidth="3"
              filter="url(#shadow)"
            />
            <circle
              cx={defenderMarker.x}
              cy={defenderMarker.y}
              r="6"
              fill="#991b1b"
              opacity="0.5"
            />
            <rect
              x={defenderMarker.x - 35}
              y={defenderMarker.y - 28}
              width="70"
              height="18"
              fill="rgba(239, 68, 68, 0.95)"
              stroke="#ffffff"
              strokeWidth="1.5"
              rx="4"
            />
            <text
              x={defenderMarker.x}
              y={defenderMarker.y - 15}
              fill="#ffffff"
              fontSize="12"
              fontWeight="bold"
              textAnchor="middle"
              style={{ pointerEvents: 'none' }}
            >
              Defender
            </text>
          </>
        )}
      </svg>

      <div className="court-hint">
        {clickCount === 0 && "Click to place shooter (blue)"}
        {clickCount === 1 && "Click to place defender (red)"}
        {clickCount === 2 && "Click anywhere to reset"}
      </div>

      {}
      {shooterMarker && defenderMarker && (
        <div className={`contest-indicator ${getContestLevel(calculateDistance(
          shooterMarker.locX, shooterMarker.locY,
          defenderMarker.locX, defenderMarker.locY
        )).toLowerCase().replace('_', '-')}`}>
          Contest Level: {getContestLevel(calculateDistance(
            shooterMarker.locX, shooterMarker.locY,
            defenderMarker.locX, defenderMarker.locY
          ))}
        </div>
      )}
    </div>
  );
}


function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  };
}

function describeArc(x, y, radius, startAngle, endAngle) {
  const start = polarToCartesian(x, y, radius, endAngle);
  const end = polarToCartesian(x, y, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

  const d = [
    'M', start.x, start.y,
    'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y,
  ].join(' ');

  return d;
}

export default Court;