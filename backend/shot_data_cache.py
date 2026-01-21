"""
Shot data caching module for efficient chart rendering.
Loads NBA shot data once and caches it in memory.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache
import os
from typing import Dict, List, Optional

# Coordinate conversion constants
COORD_SCALE = 9.853054474858238
Y_OFFSET = 5.8

# Court boundaries in feet
X_MIN_FT = -25
X_MAX_FT = 25
Y_MIN_FT = 0
Y_MAX_FT = 50


def get_data_directory() -> Path:
    """Get NBA data directory from environment or use default."""
    data_dir = os.environ.get('NBA_DATA_DIR', r'C:\Users\Aayash\Downloads\archive')
    return Path(data_dir)


@lru_cache(maxsize=1)
def load_shot_data() -> pd.DataFrame:
    """
    Load and cache all shot data from CSV files.
    Only loads required columns for performance.
    Returns DataFrame with converted coordinates in feet.
    """
    data_dir = get_data_directory()
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Try NBA_*.csv first, fallback to *.csv
    csv_files = list(data_dir.glob('NBA_*.csv'))
    if not csv_files:
        csv_files = list(data_dir.glob('*.csv'))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    
    print(f"Loading shot data from {len(csv_files)} files in {data_dir}...")
    
    # Required columns
    columns = ['LOC_X', 'LOC_Y', 'SHOT_MADE', 'SHOT_TYPE', 'BASIC_ZONE']
    
    dataframes = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(
                csv_file,
                usecols=columns,
                dtype={
                    'LOC_X': 'float32',
                    'LOC_Y': 'float32',
                    'SHOT_MADE': 'bool',
                    'SHOT_TYPE': 'category',
                    'BASIC_ZONE': 'category'
                }
            )
            dataframes.append(df)
        except Exception as e:
            print(f"Warning: Could not load {csv_file.name}: {e}")
            continue
    
    if not dataframes:
        raise ValueError("No data could be loaded from CSV files")
    
    # Combine all data
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    # Drop rows with missing coordinates
    combined_df = combined_df.dropna(subset=['LOC_X', 'LOC_Y', 'SHOT_MADE'])
    
    # Convert coordinates to feet
    combined_df['x_ft'] = COORD_SCALE * combined_df['LOC_X']
    combined_df['y_ft'] = COORD_SCALE * (combined_df['LOC_Y'] - Y_OFFSET)
    
    # Filter to court boundaries
    mask = (
        (combined_df['x_ft'] >= X_MIN_FT) & 
        (combined_df['x_ft'] <= X_MAX_FT) &
        (combined_df['y_ft'] >= Y_MIN_FT) & 
        (combined_df['y_ft'] <= Y_MAX_FT)
    )
    combined_df = combined_df[mask]
    
    print(f"Loaded {len(combined_df):,} shots")
    print(f"Memory usage: {combined_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    return combined_df


def get_shot_metadata() -> Dict:
    """Get metadata about loaded shot data."""
    df = load_shot_data()
    
    return {
        'count': len(df),
        'x_min': float(df['x_ft'].min()),
        'x_max': float(df['x_ft'].max()),
        'y_min': float(df['y_ft'].min()),
        'y_max': float(df['y_ft'].max()),
        'data_dir': str(get_data_directory()),
        'shot_types': sorted(df['SHOT_TYPE'].unique().tolist()),
        'zones': sorted(df['BASIC_ZONE'].unique().tolist())
    }


def sample_shots(
    limit: int = 15000,
    made: Optional[str] = 'all',
    shot_type: Optional[str] = 'all',
    zone: Optional[str] = 'all'
) -> List[Dict]:
    """
    Sample shots with filters.
    
    Args:
        limit: Maximum number of shots to return
        made: 'all', 'made', or 'missed'
        shot_type: 'all' or specific shot type
        zone: 'all' or specific zone
    
    Returns:
        List of dicts with {x, y, made}
    """
    df = load_shot_data()
    
    # Apply filters
    if made == 'made':
        df = df[df['SHOT_MADE'] == True]
    elif made == 'missed':
        df = df[df['SHOT_MADE'] == False]
    
    if shot_type != 'all':
        df = df[df['SHOT_TYPE'] == shot_type]
    
    if zone != 'all':
        df = df[df['BASIC_ZONE'] == zone]
    
    # Sample if needed
    if len(df) > limit:
        df = df.sample(n=limit, random_state=42)
    
    # Return minimal data
    return [
        {
            'x': float(row['x_ft']),
            'y': float(row['y_ft']),
            'made': bool(row['SHOT_MADE'])
        }
        for _, row in df.iterrows()
    ]