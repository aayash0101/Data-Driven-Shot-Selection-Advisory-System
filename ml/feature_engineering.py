"""
Feature engineering for NBA shot data.
Converts categorical features to numerical representations.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from typing import Tuple, Dict


class FeatureEngineer:
    """
    Handles feature engineering and encoding for shot data.
    """
    
    def __init__(self):
        """Initialize feature encoders."""
        self.label_encoders = {}
        self.onehot_encoders = {}
        self.feature_names = []
        self.is_fitted = False
    
    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Fit encoders and transform features.
        
        Args:
            X: DataFrame with raw features
        
        Returns:
            NumPy array of engineered features
        """
        X = X.copy()
        
        # Numerical features (keep as-is)
        numerical_features = [
            'SHOT_DISTANCE',
            'LOC_X',
            'LOC_Y',
            'QUARTER',
            'MINS_LEFT',
            'SECS_LEFT',
            'TIME_REMAINING',
            'SHOT_ANGLE',
            'DISTANCE_FROM_CENTER'
        ]
        
        # Categorical features to one-hot encode
        categorical_features = [
            'SHOT_TYPE',
            'BASIC_ZONE',
            'ZONE_NAME',
            'POSITION',
            'POSITION_GROUP'
        ]
        
        feature_list = []
        self.feature_names = []
        
        # Add numerical features
        for col in numerical_features:
            if col in X.columns:
                feature_list.append(X[col].values.reshape(-1, 1))
                self.feature_names.append(col)
        
        # One-hot encode categorical features
        for col in categorical_features:
            if col in X.columns:
                # Handle missing values - convert categorical to string first
                if pd.api.types.is_categorical_dtype(X[col]):
                    X[col] = X[col].astype(str)
                X[col] = X[col].fillna('Unknown')
                
                # One-hot encode
                encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
                encoded = encoder.fit_transform(X[[col]])
                
                # Store encoder for later use
                self.onehot_encoders[col] = encoder
                
                # Add feature names
                categories = encoder.categories_[0]
                for cat in categories:
                    self.feature_names.append(f"{col}_{cat}")
                
                feature_list.append(encoded)
        
        # Combine all features
        X_engineered = np.hstack(feature_list)
        
        self.is_fitted = True
        
        print(f"Engineered {X_engineered.shape[1]} features from {len(numerical_features)} numerical and {len(categorical_features)} categorical columns")
        
        return X_engineered
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform features using fitted encoders.
        
        Args:
            X: DataFrame with raw features
        
        Returns:
            NumPy array of engineered features
        """
        if not self.is_fitted:
            raise ValueError("FeatureEngineer must be fitted before transform")
        
        X = X.copy()
        
        # Numerical features
        numerical_features = [
            'SHOT_DISTANCE',
            'LOC_X',
            'LOC_Y',
            'QUARTER',
            'MINS_LEFT',
            'SECS_LEFT',
            'TIME_REMAINING',
            'SHOT_ANGLE',
            'DISTANCE_FROM_CENTER'
        ]
        
        categorical_features = [
            'SHOT_TYPE',
            'BASIC_ZONE',
            'ZONE_NAME',
            'POSITION',
            'POSITION_GROUP'
        ]
        
        feature_list = []
        
        # Add numerical features
        for col in numerical_features:
            if col in X.columns:
                feature_list.append(X[col].values.reshape(-1, 1))
        
        # One-hot encode categorical features
        for col in categorical_features:
            if col in X.columns:
                # Handle missing values - convert categorical to string first
                if pd.api.types.is_categorical_dtype(X[col]):
                    X[col] = X[col].astype(str)
                X[col] = X[col].fillna('Unknown')
                
                encoder = self.onehot_encoders[col]
                encoded = encoder.transform(X[[col]])
                feature_list.append(encoded)
        
        # Combine all features
        X_engineered = np.hstack(feature_list)
        
        return X_engineered
    
    def get_feature_names(self) -> list:
        """Get list of feature names."""
        return self.feature_names

