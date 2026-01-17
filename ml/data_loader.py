"""
Memory-efficient data loading and preprocessing for NBA shot data.
Handles multiple CSV files without loading everything into memory at once.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class ShotDataLoader:
    """
    Efficiently loads and preprocesses NBA shot data from multiple CSV files.
    Uses column selection, efficient dtypes, and optional sampling.
    """
    
    def __init__(self, data_dir: str, sample_frac: Optional[float] = None):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Path to directory containing CSV files
            sample_frac: Optional fraction to sample from each file (for testing)
        """
        self.data_dir = Path(data_dir)
        self.sample_frac = sample_frac
        
        # Columns we actually need for ML
        self.feature_columns = [
            'SHOT_DISTANCE',
            'LOC_X',
            'LOC_Y',
            'SHOT_TYPE',
            'BASIC_ZONE',
            'ZONE_NAME',
            'QUARTER',
            'MINS_LEFT',
            'SECS_LEFT',
            'POSITION',
            'POSITION_GROUP',
            'ACTION_TYPE'
        ]
        
        self.target_column = 'SHOT_MADE'
        
        # Optimized dtypes for memory efficiency
        self.dtype_map = {
            'SHOT_DISTANCE': 'int16',
            'LOC_X': 'float32',
            'LOC_Y': 'float32',
            'SHOT_TYPE': 'category',
            'BASIC_ZONE': 'category',
            'ZONE_NAME': 'category',
            'QUARTER': 'int8',
            'MINS_LEFT': 'int8',
            'SECS_LEFT': 'int8',
            'POSITION': 'category',
            'POSITION_GROUP': 'category',
            'ACTION_TYPE': 'category',
            'SHOT_MADE': 'bool'
        }
    
    def load_all_files(self, filter_position: Optional[str] = None) -> pd.DataFrame:
        """
        Load all CSV files from the data directory.
        
        Args:
            filter_position: Optional position filter (e.g., 'PG' for point guards)
        
        Returns:
            Combined DataFrame with all shot data
        """
        csv_files = sorted(self.data_dir.glob('NBA_*.csv'))
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.data_dir}")
        
        print(f"Found {len(csv_files)} CSV files")
        
        dataframes = []
        
        for csv_file in csv_files:
            print(f"Loading {csv_file.name}...")
            
            # Read only needed columns
            df = pd.read_csv(
                csv_file,
                usecols=self.feature_columns + [self.target_column],
                dtype=self.dtype_map,
                low_memory=False
            )
            
            # Apply sampling if specified
            if self.sample_frac and self.sample_frac < 1.0:
                df = df.sample(frac=self.sample_frac, random_state=42)
            
            # Filter by position if specified
            if filter_position:
                df = df[df['POSITION'] == filter_position]
            
            # Remove rows with missing critical data
            df = df.dropna(subset=['SHOT_DISTANCE', 'LOC_X', 'LOC_Y', 'SHOT_MADE'])
            
            dataframes.append(df)
            
            print(f"  Loaded {len(df):,} rows")
        
        # Combine all dataframes
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        print(f"\nTotal rows loaded: {len(combined_df):,}")
        print(f"Memory usage: {combined_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        return combined_df
    
    def preprocess(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Preprocess the data for ML training.
        
        Args:
            df: Raw DataFrame with shot data
        
        Returns:
            Tuple of (features_df, target_series)
        """
        df = df.copy()
        
        # Convert SHOT_MADE to binary (True/False -> 1/0)
        df[self.target_column] = df[self.target_column].astype(int)
        
        # Create time remaining feature (total seconds)
        df['TIME_REMAINING'] = df['MINS_LEFT'] * 60 + df['SECS_LEFT']
        
        # Create shot angle feature (angle from basket)
        df['SHOT_ANGLE'] = np.arctan2(df['LOC_Y'], df['LOC_X']) * 180 / np.pi
        
        # Create distance from center feature
        df['DISTANCE_FROM_CENTER'] = np.sqrt(df['LOC_X']**2 + df['LOC_Y']**2)
        
        # Extract features
        feature_df = df[[
            'SHOT_DISTANCE',
            'LOC_X',
            'LOC_Y',
            'SHOT_TYPE',
            'BASIC_ZONE',
            'ZONE_NAME',
            'QUARTER',
            'MINS_LEFT',
            'SECS_LEFT',
            'TIME_REMAINING',
            'SHOT_ANGLE',
            'DISTANCE_FROM_CENTER',
            'POSITION',
            'POSITION_GROUP'
        ]].copy()
        
        target = df[self.target_column]
        
        return feature_df, target


if __name__ == "__main__":
    # Test the data loader
    loader = ShotDataLoader(
        data_dir=r"C:\Users\Aayash\Downloads\archive",
        sample_frac=0.1  # Use 10% for testing
    )
    
    df = loader.load_all_files()
    features, target = loader.preprocess(df)
    
    print(f"\nFeatures shape: {features.shape}")
    print(f"Target shape: {target.shape}")
    print(f"\nTarget distribution:")
    print(target.value_counts())
    print(f"\nShot make rate: {target.mean():.3f}")


