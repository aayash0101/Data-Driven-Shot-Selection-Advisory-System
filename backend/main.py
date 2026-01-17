"""
FastAPI backend for shot selection advisory system.
Extended with defender-based contest modeling and coach-like feedback.

Version 3.3 - Added confidence scoring for action recommendations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal, Dict
from enum import Enum
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import modules (this ensures they're available for pickle)
from ml.shot_advisory import ShotAdvisor
from ml.data_loader import ShotDataLoader
from ml.feature_engineering import FeatureEngineer

# Import shot quality analyzer and defender impact model
from shot_quality_breakdown import ShotQualityAnalyzer
from defender_impact import DefenderImpactModel, ContestLevel

# Import coach feedback generator
from coach_feedback import generate_coach_feedback

# Import action recommender
from action_recommender import get_action_recommendation

# Import NEW action confidence calculator
from action_confidence import compute_action_confidence

app = FastAPI(title="Shot Selection Advisory API v3.3")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS & SCHEMAS
# ============================================================================

# Global model objects
model = None
feature_engineer = None
shot_advisor = None
quality_analyzer = ShotQualityAnalyzer()


class ShotRequest(BaseModel):
    """Request model for shot prediction."""
    shot_distance: float
    loc_x: float
    loc_y: float
    shot_type: str
    zone: str
    quarter: int
    mins_left: int
    secs_left: int
    position: Optional[str] = "PG"
    action_type: Optional[str] = "Jump Shot"
    
    # Defender data (optional for backward compatibility)
    defender_distance: Optional[float] = None
    contest_level: Optional[str] = "OPEN"


class ShotResponse(BaseModel):
    """Response model for shot prediction."""
    decision: str
    make_probability: float
    threshold: float
    confidence: float
    explanation: list
    
    # Contest info in response
    contest_level: Optional[str] = None
    defender_distance: Optional[float] = None
    
    # Shot quality breakdown
    shot_quality_breakdown: Optional[Dict[str, float]] = None
    
    # Defender impact details
    defender_impact_details: Optional[Dict[str, float]] = None
    
    # Action recommendation (only populated for PASS decisions)
    recommended_action: Optional[str] = None
    action_reasoning: Optional[str] = None
    
    # NEW: Action confidence fields
    action_confidence: Optional[float] = None
    confidence_level: Optional[str] = None
    confidence_reasoning: Optional[str] = None
    confidence_factors: Optional[Dict] = None


def load_models():
    """Load trained models and feature engineer."""
    global model, feature_engineer, shot_advisor
    
    # Ensure parent directory is in path for pickle imports
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Check if model directory exists
    model_dir = parent_dir / "ml" / "models"
    if not model_dir.exists():
        print(f"Model directory not found: {model_dir}")
        print("Please train models first by running:")
        print("  cd ml")
        print("  python train_model.py")
        return False
    
    # Check for required model files
    required_files = ["feature_engineer.pkl", "gradient_boosting.pkl"]
    missing_files = [f for f in required_files if not (model_dir / f).exists()]
    
    if missing_files:
        print(f"Missing model files: {', '.join(missing_files)}")
        print(f"Model directory: {model_dir.absolute()}")
        print("\nPlease train models first by running:")
        print("  cd ml")
        print("  python train_model.py")
        print("\nOr for faster training (10% of data):")
        print("  python train_model.py --sample 0.1")
        return False
    
    try:
        # Ensure parent directory is in path so ml.feature_engineering can be imported
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        
        # Also add ml directory to path for pickle compatibility
        ml_dir = parent_dir / "ml"
        if str(ml_dir) not in sys.path:
            sys.path.insert(0, str(ml_dir))
        
        # Import both ways to ensure pickle can find the module
        try:
            import ml.feature_engineering
        except ImportError:
            pass
        
        try:
            import feature_engineering
        except ImportError:
            pass
        
        # Load feature engineer with custom unpickler
        with open(model_dir / "feature_engineer.pkl", "rb") as f:
            class CustomUnpickler(pickle.Unpickler):
                def find_class(self, module, name):
                    try:
                        return super().find_class(module, name)
                    except (AttributeError, ImportError, ModuleNotFoundError):
                        if module == 'feature_engineering':
                            module = 'ml.feature_engineering'
                        elif module == 'data_loader':
                            module = 'ml.data_loader'
                        elif module == 'shot_advisory':
                            module = 'ml.shot_advisory'
                        try:
                            return super().find_class(module, name)
                        except (AttributeError, ImportError, ModuleNotFoundError):
                            if module.startswith('ml.'):
                                module = module[3:]
                            return super().find_class(module, name)
            
            unpickler = CustomUnpickler(f)
            feature_engineer = unpickler.load()
        
        # Load main model (Gradient Boosting)
        with open(model_dir / "gradient_boosting.pkl", "rb") as f:
            model = pickle.load(f)
        
        # Initialize shot advisor
        shot_advisor = ShotAdvisor()
        
        print("✓ Models loaded successfully")
        print("✓ Defender impact model initialized")
        print("✓ Coach feedback system ready")
        print("✓ Action recommendation system ready")
        print("✓ Action confidence calculator ready")
        return True
    except ImportError as e:
        print(f"Import error loading models: {e}")
        print(f"Python path: {sys.path[:3]}")
        return False
    except Exception as e:
        print(f"Error loading models: {e}")
        import traceback
        traceback.print_exc()
        print("Please train models first by running: python ml/train_model.py")
        return False


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load models on startup."""
    success = load_models()
    if not success:
        print("\n⚠️  WARNING: Models not loaded. API will not function until models are trained.")
        print("   The /health endpoint will show 'not_ready' status.")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Shot Selection Advisory API",
        "version": "3.3-action-confidence",
        "features": [
            "ML-based shot prediction",
            "Defender impact modeling (continuous + discrete)",
            "Shot quality breakdown with defensive pressure",
            "Natural language coach feedback system",
            "Action-based recommendations for PASS decisions",
            "Confidence scoring for recommended actions",
            "Contest-aware decision thresholds"
        ],
        "endpoints": {
            "/predict-shot": "POST - Predict shot selection advice with coach feedback and action recommendations",
            "/health": "GET - Health check",
            "/defender-impact-demo": "GET - Demo defender impact calculations",
            "/feedback-examples": "GET - Demo coach feedback system",
            "/action-examples": "GET - Demo action recommendation system",
            "/confidence-examples": "GET - Demo action confidence scoring"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    if model is None or feature_engineer is None:
        return {
            "status": "not_ready", 
            "message": "Models not loaded. Please train models first.",
            "instructions": {
                "step1": "cd ml",
                "step2": "python train_model.py",
                "step3": "Restart the backend server"
            }
        }
    return {
        "status": "ready", 
        "message": "API is ready with defender modeling, coach feedback, action recommendations, and confidence scoring", 
        "version": "3.3-action-confidence"
    }


@app.get("/defender-impact-demo")
async def defender_impact_demo():
    """
    Demo endpoint showing defender impact calculations.
    Useful for understanding model behavior.
    """
    test_cases = [
        {"distance": 0, "contest": "TIGHT", "description": "Hand-in-face (worst case)"},
        {"distance": 2.5, "contest": "TIGHT", "description": "Tight closeout on 3PT"},
        {"distance": 5, "contest": "CONTESTED", "description": "Active contest"},
        {"distance": 8, "contest": "OPEN", "description": "Late rotation"},
        {"distance": 15, "contest": "WIDE_OPEN", "description": "Wide-open shot"},
    ]
    
    results = []
    for case in test_cases:
        try:
            contest_enum = ContestLevel(case["contest"])
        except (ValueError, KeyError):
            contest_enum = ContestLevel.OPEN
        
        impact = DefenderImpactModel.compute_defender_impact(
            case["distance"],
            contest_enum
        )
        
        explanation = DefenderImpactModel.get_explanation(
            case["distance"],
            contest_enum,
            impact
        )
        
        # Show effect on a typical 40% shot
        base_prob = 0.40
        adjusted_prob, _ = DefenderImpactModel.apply_defender_adjustment(
            base_prob,
            case["distance"],
            contest_enum
        )
        
        results.append({
            "scenario": case["description"],
            "distance_ft": case["distance"],
            "contest_level": case["contest"],
            "impact_factor": round(impact["impact_factor"], 3),
            "percentage_adjustment": round(impact["percentage_adjustment"], 1),
            "example_40pct_shot": {
                "base": "40.0%",
                "adjusted": f"{adjusted_prob*100:.1f}%",
                "change": f"{(adjusted_prob - base_prob)*100:+.1f} pp"
            },
            "explanation": explanation
        })
    
    return {
        "message": "Defender Impact Model Demonstration",
        "model_parameters": {
            "max_penalty": "35% (at 0 ft)",
            "decay_rate": "0.25 (exponential)",
            "contest_multipliers": {
                "TIGHT": "0.85",
                "CONTESTED": "0.92",
                "OPEN": "0.97",
                "WIDE_OPEN": "1.00"
            }
        },
        "test_cases": results
    }


@app.get("/feedback-examples")
async def feedback_examples():
    """
    Demo endpoint showing coach feedback examples.
    Displays various PASS scenarios with natural language explanations.
    """
    scenarios = [
        {
            "name": "Tight Defense on Three",
            "decision": "PASS",
            "make_probability": 0.26,
            "threshold": 0.35,
            "shot_type": "3PT Field Goal",
            "zone": "Above the Break 3",
            "shot_distance": 24.5,
            "time_remaining": 14,
            "quarter": 2,
            "defender_distance": 1.8,
            "contest_level": "TIGHT"
        },
        {
            "name": "Contested Corner Three",
            "decision": "PASS",
            "make_probability": 0.31,
            "threshold": 0.38,
            "shot_type": "3PT Field Goal",
            "zone": "Right Corner 3",
            "shot_distance": 23.2,
            "time_remaining": 18,
            "quarter": 3,
            "defender_distance": 4.5,
            "contest_level": "CONTESTED"
        },
        {
            "name": "Poor Mid-Range Location",
            "decision": "PASS",
            "make_probability": 0.33,
            "threshold": 0.41,
            "shot_type": "2PT Field Goal",
            "zone": "Mid-Range",
            "shot_distance": 17.0,
            "time_remaining": 22,
            "quarter": 1,
            "defender_distance": 8.5,
            "contest_level": "OPEN"
        },
        {
            "name": "Late Clock Forced Shot",
            "decision": "PASS",
            "make_probability": 0.29,
            "threshold": 0.36,
            "shot_type": "2PT Field Goal",
            "zone": "Mid-Range",
            "shot_distance": 15.0,
            "time_remaining": 3,
            "quarter": 4,
            "defender_distance": 6.0,
            "contest_level": "CONTESTED"
        },
        {
            "name": "Wide Open Corner (TAKE)",
            "decision": "TAKE SHOT",
            "make_probability": 0.47,
            "threshold": 0.35,
            "shot_type": "3PT Field Goal",
            "zone": "Left Corner 3",
            "shot_distance": 23.0,
            "time_remaining": 16,
            "quarter": 3,
            "defender_distance": 13.0,
            "contest_level": "WIDE_OPEN"
        }
    ]
    
    results = []
    for scenario in scenarios:
        feedback = generate_coach_feedback(**scenario)
        results.append({
            "scenario": scenario["name"],
            "decision": scenario["decision"],
            "context": {
                "shot": f"{scenario['shot_type']} from {scenario['zone']}",
                "distance": f"{scenario['shot_distance']:.1f} ft",
                "defender": f"{scenario['defender_distance']:.1f} ft away ({scenario['contest_level']})",
                "time": f"Q{scenario['quarter']}, {scenario['time_remaining']}s left"
            },
            "probabilities": {
                "make_probability": f"{scenario['make_probability']:.1%}",
                "threshold": f"{scenario['threshold']:.1%}"
            },
            "coach_feedback": feedback
        })
    
    return {
        "message": "Coach Feedback System Examples",
        "description": "Natural language explanations for shot decisions",
        "scenarios": results
    }


@app.get("/action-examples")
async def action_examples():
    """
    Demo endpoint showing action recommendation examples.
    Displays various PASS scenarios with recommended next actions.
    """
    scenarios = [
        {
            "name": "Tight Contest on Three - Good Zone",
            "make_probability": 0.28,
            "shot_type": "3PT Field Goal",
            "zone": "Right Corner 3",
            "shot_distance": 23.5,
            "time_remaining": 14,
            "quarter": 2,
            "defender_distance": 2.2,
            "contest_level": "TIGHT"
        },
        {
            "name": "Heavily Contested Mid-Range",
            "make_probability": 0.32,
            "shot_type": "2PT Field Goal",
            "zone": "Mid-Range",
            "shot_distance": 16.0,
            "time_remaining": 12,
            "quarter": 3,
            "defender_distance": 4.8,
            "contest_level": "CONTESTED"
        },
        {
            "name": "Poor Long-Range Shot",
            "make_probability": 0.25,
            "shot_type": "3PT Field Goal",
            "zone": "Above the Break 3",
            "shot_distance": 27.5,
            "time_remaining": 18,
            "quarter": 1,
            "defender_distance": 7.5,
            "contest_level": "OPEN"
        },
        {
            "name": "Late Clock Situation",
            "make_probability": 0.31,
            "shot_type": "2PT Field Goal",
            "zone": "Mid-Range",
            "shot_distance": 15.0,
            "time_remaining": 3,
            "quarter": 4,
            "defender_distance": 5.5,
            "contest_level": "CONTESTED"
        },
        {
            "name": "Marginal Quality - Time Available",
            "make_probability": 0.34,
            "shot_type": "3PT Field Goal",
            "zone": "Above the Break 3",
            "shot_distance": 24.0,
            "time_remaining": 20,
            "quarter": 2,
            "defender_distance": 9.0,
            "contest_level": "OPEN"
        }
    ]
    
    results = []
    for scenario in scenarios:
        action_rec = get_action_recommendation(**scenario)
        
        results.append({
            "scenario": scenario["name"],
            "context": {
                "shot": f"{scenario['shot_type']} from {scenario['zone']}",
                "distance": f"{scenario['shot_distance']:.1f} ft",
                "defender": f"{scenario['defender_distance']:.1f} ft away ({scenario['contest_level']})",
                "time": f"Q{scenario['quarter']}, {scenario['time_remaining']}s remaining",
                "make_probability": f"{scenario['make_probability']:.1%}"
            },
            "recommendation": {
                "action": action_rec['action'],
                "reasoning": action_rec['reasoning'],
                "primary_reason": action_rec['primary_reason']
            }
        })
    
    return {
        "message": "Action Recommendation System Examples",
        "description": "Basketball-intelligent next actions for PASS decisions",
        "scenarios": results
    }


@app.get("/confidence-examples")
async def confidence_examples():
    """
    NEW: Demo endpoint showing action confidence scoring examples.
    Displays various PASS scenarios with confidence assessments.
    """
    scenarios = [
        {
            "name": "Very Clear PASS - Tight Contest on Deep Three",
            "make_probability": 0.24,
            "threshold": 0.35,
            "decision": "PASS",
            "shot_type": "3PT Field Goal",
            "zone": "Above the Break 3",
            "shot_distance": 28.0,
            "time_remaining": 16,
            "quarter": 2,
            "defender_distance": 2.0,
            "contest_level": "TIGHT",
            "recommended_action": "Swing Pass"
        },
        {
            "name": "Clear PASS - Contested Mid-Range",
            "make_probability": 0.31,
            "threshold": 0.41,
            "decision": "PASS",
            "shot_type": "2PT Field Goal",
            "zone": "Mid-Range",
            "shot_distance": 17.0,
            "time_remaining": 14,
            "quarter": 3,
            "defender_distance": 5.0,
            "contest_level": "CONTESTED",
            "recommended_action": "Drive or Kick"
        },
        {
            "name": "Marginal PASS - Late Clock Pressure",
            "make_probability": 0.36,
            "threshold": 0.40,
            "decision": "PASS",
            "shot_type": "2PT Field Goal",
            "zone": "Mid-Range",
            "shot_distance": 15.0,
            "time_remaining": 3,
            "quarter": 4,
            "defender_distance": 6.0,
            "contest_level": "CONTESTED",
            "recommended_action": "Take Best Available Shot"
        },
        {
            "name": "Uncertain PASS - Clutch Situation",
            "make_probability": 0.34,
            "threshold": 0.39,
            "decision": "PASS",
            "shot_type": "3PT Field Goal",
            "zone": "Right Corner 3",
            "shot_distance": 23.5,
            "time_remaining": 90,
            "quarter": 4,
            "defender_distance": 7.0,
            "contest_level": "OPEN",
            "recommended_action": "Reset Offense"
        },
        {
            "name": "Moderate PASS - Good Zone But Open",
            "make_probability": 0.33,
            "threshold": 0.38,
            "decision": "PASS",
            "shot_type": "3PT Field Goal",
            "zone": "Left Corner 3",
            "shot_distance": 23.0,
            "time_remaining": 18,
            "quarter": 2,
            "defender_distance": 9.0,
            "contest_level": "OPEN",
            "recommended_action": "Relocate for Better Look"
        }
    ]
    
    results = []
    for scenario in scenarios:
        confidence_result = compute_action_confidence(**scenario)
        
        results.append({
            "scenario": scenario["name"],
            "context": {
                "shot": f"{scenario['shot_type']} from {scenario['zone']}",
                "distance": f"{scenario['shot_distance']:.1f} ft",
                "defender": f"{scenario['defender_distance']:.1f} ft away ({scenario['contest_level']})",
                "time": f"Q{scenario['quarter']}, {scenario['time_remaining']}s remaining",
                "make_probability": f"{scenario['make_probability']:.1%}",
                "threshold": f"{scenario['threshold']:.1%}",
                "gap": f"{abs(scenario['make_probability'] - scenario['threshold']):.1%}"
            },
            "action": scenario["recommended_action"],
            "confidence": {
                "score": confidence_result['action_confidence'],
                "level": confidence_result['confidence_level'],
                "reasoning": confidence_result['confidence_reasoning'],
                "factors": confidence_result['confidence_factors']
            }
        })
    
    return {
        "message": "Action Confidence Scoring Examples",
        "description": "Explainable confidence assessments for recommended actions",
        "methodology": {
            "base_calculation": "Probability-threshold gap determines base confidence",
            "adjustments": [
                "Tight defense → increases PASS confidence",
                "Late clock → decreases confidence (forced decisions)",
                "Poor shot locations → increases PASS confidence",
                "Clutch situations → decreases confidence (uncertainty)"
            ],
            "confidence_levels": {
                "Very High": "≥ 0.75",
                "High": "0.60 - 0.74",
                "Moderate": "0.45 - 0.59",
                "Low": "< 0.45"
            }
        },
        "scenarios": results
    }


@app.post("/predict-shot", response_model=ShotResponse)
async def predict_shot(request: ShotRequest):
    """
    Predict shot selection advice with coach-like feedback, action recommendations,
    and confidence scoring.
    
    Workflow:
    1. Get ML base prediction
    2. Apply defender impact adjustment
    3. Compute shot quality breakdown with defensive pressure
    4. Get base advisory decision
    5. Generate natural language coach feedback
    6. If PASS decision, generate action recommendation
    7. [NEW] Compute confidence score for recommended action
    
    Returns decision, probabilities, breakdown, explanations, recommended action,
    and confidence assessment.
    """
    if model is None or feature_engineer is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Models not loaded",
                "message": "Please train models first by running: python ml/train_model.py",
                "quick_start": "cd ml && python train_model.py --sample 0.1"
            }
        )
    
    try:
        # ====================================================================
        # STEP 0: Prepare features (existing logic)
        # ====================================================================
        time_remaining = request.mins_left * 60 + request.secs_left
        shot_angle = np.arctan2(request.loc_y, request.loc_x) * 180 / np.pi
        distance_from_center = np.sqrt(request.loc_x**2 + request.loc_y**2)
        
        # Map zone to ZONE_NAME
        zone_name_mapping = {
            'Restricted Area': 'Center',
            'In The Paint (Non-RA)': 'Center',
            'Mid-Range': 'Center',
            'Above the Break 3': 'Center',
            'Left Corner 3': 'Left Side',
            'Right Corner 3': 'Right Side',
            'Left Side 3': 'Left Side Center',
            'Right Side 3': 'Right Side Center'
        }
        zone_name = zone_name_mapping.get(request.zone, 'Center')
        
        # Create feature DataFrame
        feature_dict = {
            'SHOT_DISTANCE': [request.shot_distance],
            'LOC_X': [request.loc_x],
            'LOC_Y': [request.loc_y],
            'SHOT_TYPE': [request.shot_type],
            'BASIC_ZONE': [request.zone],
            'ZONE_NAME': [zone_name],
            'QUARTER': [request.quarter],
            'MINS_LEFT': [request.mins_left],
            'SECS_LEFT': [request.secs_left],
            'TIME_REMAINING': [time_remaining],
            'SHOT_ANGLE': [shot_angle],
            'DISTANCE_FROM_CENTER': [distance_from_center],
            'POSITION': [request.position],
            'POSITION_GROUP': [request.position[0] if request.position else 'G']
        }
        
        features_df = pd.DataFrame(feature_dict)
        
        # Engineer features
        X = feature_engineer.transform(features_df)
        
        # ====================================================================
        # STEP 1: Get ML base prediction
        # ====================================================================
        base_make_probability = model.predict_proba(X)[0, 1]
        
        # ====================================================================
        # STEP 2: Apply defender impact adjustment
        # ====================================================================
        contest_enum = None
        if request.contest_level:
            try:
                contest_enum = ContestLevel(request.contest_level)
            except (ValueError, KeyError):
                contest_enum = ContestLevel.OPEN
        
        adjusted_probability, impact_breakdown = DefenderImpactModel.apply_defender_adjustment(
            base_probability=base_make_probability,
            defender_distance=request.defender_distance,
            contest_level=contest_enum
        )
        
        # ====================================================================
        # STEP 3: Compute shot quality breakdown (with defender data)
        # ====================================================================
        breakdown = quality_analyzer.compute_breakdown(
            make_probability=adjusted_probability,
            shot_type=request.shot_type,
            zone=request.zone,
            shot_distance=request.shot_distance,
            time_remaining=time_remaining,
            quarter=request.quarter,
            defender_distance=request.defender_distance,
            contest_level=request.contest_level
        )
        
        # ====================================================================
        # STEP 4: Get base advisory decision
        # ====================================================================
        base_advice = shot_advisor.advise(
            make_probability=adjusted_probability,
            shot_type=request.shot_type,
            zone=request.zone,
            distance=request.shot_distance,
            time_remaining=time_remaining,
            quarter=request.quarter
        )
        
        # ====================================================================
        # STEP 5: Generate coach-like feedback
        # ====================================================================
        coach_explanations = generate_coach_feedback(
            decision=base_advice['decision'],
            make_probability=adjusted_probability,
            threshold=base_advice['threshold'],
            shot_type=request.shot_type,
            zone=request.zone,
            shot_distance=request.shot_distance,
            time_remaining=time_remaining,
            quarter=request.quarter,
            defender_distance=request.defender_distance,
            contest_level=request.contest_level
        )
        
        # ====================================================================
        # STEP 6: Generate action recommendation for PASS decisions
        # ====================================================================
        recommended_action = None
        action_reasoning = None
        action_confidence_score = None
        confidence_level = None
        confidence_reasoning = None
        confidence_factors = None
        
        if base_advice['decision'] == 'PASS':
            action_rec = get_action_recommendation(
                make_probability=adjusted_probability,
                shot_type=request.shot_type,
                zone=request.zone,
                shot_distance=request.shot_distance,
                time_remaining=time_remaining,
                quarter=request.quarter,
                defender_distance=request.defender_distance,
                contest_level=request.contest_level
            )
            
            recommended_action = action_rec['action']
            action_reasoning = action_rec['reasoning']
            
            # ================================================================
            # STEP 7: NEW - Compute confidence for the recommended action
            # ================================================================
            confidence_result = compute_action_confidence(
                make_probability=adjusted_probability,
                threshold=base_advice['threshold'],
                decision=base_advice['decision'],
                shot_type=request.shot_type,
                zone=request.zone,
                shot_distance=request.shot_distance,
                time_remaining=time_remaining,
                quarter=request.quarter,
                defender_distance=request.defender_distance,
                contest_level=request.contest_level,
                recommended_action=recommended_action
            )
            
            action_confidence_score = confidence_result['action_confidence']
            confidence_level = confidence_result['confidence_level']
            confidence_reasoning = confidence_result['confidence_reasoning']
            confidence_factors = confidence_result['confidence_factors']
        
        # ====================================================================
        # STEP 8: Return comprehensive response
        # ====================================================================
        return ShotResponse(
            decision=base_advice['decision'],
            make_probability=adjusted_probability,
            threshold=base_advice['threshold'],
            confidence=base_advice['confidence'],
            explanation=coach_explanations,
            contest_level=request.contest_level,
            defender_distance=request.defender_distance,
            shot_quality_breakdown=breakdown,
            defender_impact_details=impact_breakdown,
            recommended_action=recommended_action,
            action_reasoning=action_reasoning,
            action_confidence=action_confidence_score,
            confidence_level=confidence_level,
            confidence_reasoning=confidence_reasoning,
            confidence_factors=confidence_factors
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}\n\nDetails:\n{error_details}"
        )


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("Shot Selection Advisory API v3.3 - Action Confidence System")
    print("="*70)
    print("\nStarting server...")
    print("Visit http://localhost:8000/docs for interactive API documentation")
    print("Visit http://localhost:8000/defender-impact-demo to see model behavior")
    print("Visit http://localhost:8000/feedback-examples to see coach feedback examples")
    print("Visit http://localhost:8000/action-examples to see action recommendations")
    print("Visit http://localhost:8000/confidence-examples to see confidence scoring")
    print("\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)