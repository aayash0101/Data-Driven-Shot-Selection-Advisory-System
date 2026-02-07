"""
Train ML models for shot prediction.
Includes baseline Logistic Regression and Gradient Boosting models.
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from typing import Optional
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import warnings
warnings.filterwarnings('ignore')

from data_loader import ShotDataLoader
from feature_engineering import FeatureEngineer


def train_models(
    data_dir: str,
    output_dir: str = "ml/models",
    sample_frac: Optional[float] = None,
    filter_position: Optional[str] = None
):
    """
    Train baseline and main models on NBA shot data.

    Args:
        data_dir: Path to directory containing CSV files
        output_dir: Directory to save trained models
        sample_frac: Optional fraction to sample (for faster testing)
        filter_position: Optional position filter (e.g., 'PG')
    """

    if Path(output_dir).is_absolute():
        output_path = Path(output_dir)
    else:

        script_dir = Path(__file__).parent
        output_path = script_dir / output_dir
    output_path.mkdir(parents=True, exist_ok=True)


    print("=" * 60)
    print("LOADING DATA")
    print("=" * 60)
    loader = ShotDataLoader(data_dir=data_dir, sample_frac=sample_frac)
    df = loader.load_all_files(filter_position=filter_position)


    print("\n" + "=" * 60)
    print("PREPROCESSING DATA")
    print("=" * 60)
    features_df, target = loader.preprocess(df)


    print("\n" + "=" * 60)
    print("ENGINEERING FEATURES")
    print("=" * 60)
    feature_engineer = FeatureEngineer()
    X = feature_engineer.fit_transform(features_df)
    y = target.values


    with open(output_path / "feature_engineer.pkl", "wb") as f:
        pickle.dump(feature_engineer, f)
    print(f"\nSaved feature engineer to {output_path / 'feature_engineer.pkl'}")


    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTrain set: {X_train.shape[0]:,} samples")
    print(f"Test set: {X_test.shape[0]:,} samples")
    print(f"Positive class rate (train): {y_train.mean():.3f}")
    print(f"Positive class rate (test): {y_test.mean():.3f}")


    print("\n" + "=" * 60)
    print("TRAINING BASELINE: LOGISTIC REGRESSION")
    print("=" * 60)

    lr_model = LogisticRegression(
        max_iter=500,
        random_state=42,
        n_jobs=1
    )

    lr_model.fit(X_train, y_train)


    y_pred_lr = lr_model.predict(X_test)
    y_proba_lr = lr_model.predict_proba(X_test)[:, 1]

    lr_accuracy = accuracy_score(y_test, y_pred_lr)
    lr_auc = roc_auc_score(y_test, y_proba_lr)

    print(f"\nLogistic Regression Results:")
    print(f"  Accuracy: {lr_accuracy:.4f}")
    print(f"  ROC-AUC: {lr_auc:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred_lr))


    with open(output_path / "logistic_regression.pkl", "wb") as f:
        pickle.dump(lr_model, f)
    print(f"\nSaved baseline model to {output_path / 'logistic_regression.pkl'}")


    print("\n" + "=" * 60)
    print("TRAINING MAIN MODEL: GRADIENT BOOSTING")
    print("=" * 60)

    gb_model = GradientBoostingClassifier(
        n_estimators=50,
        learning_rate=0.1,
        max_depth=4,
        random_state=42,
        verbose=1
    )

    gb_model.fit(X_train, y_train)


    y_pred_gb = gb_model.predict(X_test)
    y_proba_gb = gb_model.predict_proba(X_test)[:, 1]

    gb_accuracy = accuracy_score(y_test, y_pred_gb)
    gb_auc = roc_auc_score(y_test, y_proba_gb)

    print(f"\nGradient Boosting Results:")
    print(f"  Accuracy: {gb_accuracy:.4f}")
    print(f"  ROC-AUC: {gb_auc:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred_gb))


    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE (Top 20)")
    print("=" * 60)

    feature_importance = pd.DataFrame({
        'feature': feature_engineer.get_feature_names(),
        'importance': gb_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(feature_importance.head(20).to_string(index=False))


    feature_importance.to_csv(output_path / "feature_importance.csv", index=False)
    print(f"\nSaved feature importance to {output_path / 'feature_importance.csv'}")


    with open(output_path / "gradient_boosting.pkl", "wb") as f:
        pickle.dump(gb_model, f)
    print(f"\nSaved main model to {output_path / 'gradient_boosting.pkl'}")


    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    print(f"Baseline (Logistic Regression):")
    print(f"  Accuracy: {lr_accuracy:.4f}, ROC-AUC: {lr_auc:.4f}")
    print(f"\nMain Model (Gradient Boosting):")
    print(f"  Accuracy: {gb_accuracy:.4f}, ROC-AUC: {gb_auc:.4f}")
    print(f"\nModels saved to: {output_path}")

    return {
        'lr_model': lr_model,
        'gb_model': gb_model,
        'feature_engineer': feature_engineer,
        'lr_accuracy': lr_accuracy,
        'lr_auc': lr_auc,
        'gb_accuracy': gb_accuracy,
        'gb_auc': gb_auc
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train shot selection models')
    parser.add_argument('--sample', type=float, default=0.1,
                        help='Fraction of data to sample (default: 0.1 for faster training)')
    parser.add_argument('--position', type=str, default=None,
                        help='Filter by position (e.g., PG) or None for all positions')
    parser.add_argument('--full-data', action='store_true',
                        help='Use full dataset (warning: may take 30+ minutes)')

    args = parser.parse_args()

    sample_frac = None if args.full_data else args.sample

    print("=" * 60)
    print("TRAINING CONFIGURATION")
    print("=" * 60)
    print(f"Data sampling: {sample_frac if sample_frac else 'Full dataset'}")
    print(f"Position filter: {args.position if args.position else 'All positions'}")
    print(f"Estimated time: {'30-60 minutes' if not sample_frac else '2-5 minutes'}")
    print("=" * 60)
    print()


    results = train_models(
        data_dir=r"C:\Users\Aayash\Downloads\archive",
        output_dir="ml/models",
        sample_frac=sample_frac,
        filter_position=args.position
    )
