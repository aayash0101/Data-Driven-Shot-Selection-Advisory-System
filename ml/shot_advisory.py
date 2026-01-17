"""
Shot selection advisory logic.
Provides interpretable recommendations based on ML predictions and context.
"""

from typing import Dict, List
import numpy as np


class ShotAdvisor:
    """
    Rule-based advisory system on top of ML predictions.
    Provides dynamic thresholds and explanations.
    """
    
    def __init__(self):
        """Initialize shot advisor with default thresholds."""
        # Base threshold for shot selection
        self.base_threshold = 0.45
        
        # Threshold adjustments by shot type
        self.shot_type_thresholds = {
            '3PT Field Goal': 0.35,  # Lower threshold for 3s (more valuable)
            '2PT Field Goal': 0.50   # Higher threshold for 2s
        }
        
        # Threshold adjustments by zone
        self.zone_thresholds = {
            'Restricted Area': 0.40,           # High-value shots
            'In The Paint (Non-RA)': 0.45,
            'Mid-Range': 0.55,                 # Lower efficiency
            'Above the Break 3': 0.35,         # Open 3s
            'Left Corner 3': 0.35,
            'Right Corner 3': 0.35,
            'Right Side 3': 0.35,
            'Left Side 3': 0.35
        }
        
        # Late clock adjustment (last 5 seconds of quarter)
        self.late_clock_threshold = 0.30  # Lower threshold when time is running out
    
    def get_threshold(
        self,
        shot_type: str,
        zone: str,
        time_remaining: float,
        quarter: int
    ) -> float:
        """
        Calculate dynamic threshold based on context.
        
        Args:
            shot_type: Type of shot (e.g., '3PT Field Goal')
            zone: Zone name (e.g., 'Above the Break 3')
            time_remaining: Seconds remaining in quarter
            quarter: Quarter number (1-4)
        
        Returns:
            Dynamic threshold for shot selection
        """
        threshold = self.base_threshold
        
        # Adjust for shot type
        if shot_type in self.shot_type_thresholds:
            threshold = self.shot_type_thresholds[shot_type]
        
        # Adjust for zone
        if zone in self.zone_thresholds:
            threshold = min(threshold, self.zone_thresholds[zone])
        
        # Late clock adjustment (last 5 seconds)
        if time_remaining <= 5.0:
            threshold = min(threshold, self.late_clock_threshold)
        
        # Overtime adjustment (if quarter > 4)
        if quarter > 4:
            threshold *= 0.95  # Slightly lower in OT
        
        return threshold
    
    def get_explanation(
        self,
        make_probability: float,
        threshold: float,
        shot_type: str,
        zone: str,
        distance: float,
        time_remaining: float,
        quarter: int
    ) -> List[str]:
        """
        Generate human-readable explanation for the decision.
        
        Args:
            make_probability: ML model's predicted probability
            threshold: Dynamic threshold used
            shot_type: Type of shot
            zone: Zone name
            distance: Shot distance in feet
            time_remaining: Seconds remaining
            quarter: Quarter number
        
        Returns:
            List of explanation strings
        """
        explanations = []
        
        # Probability explanation
        prob_pct = make_probability * 100
        threshold_pct = threshold * 100
        
        if make_probability >= threshold:
            explanations.append(f"Shot make probability ({prob_pct:.1f}%) exceeds threshold ({threshold_pct:.1f}%)")
        else:
            explanations.append(f"Shot make probability ({prob_pct:.1f}%) below threshold ({threshold_pct:.1f}%)")
        
        # Shot type explanation
        if shot_type == '3PT Field Goal':
            explanations.append("3-point shots are valuable - lower threshold applied")
        elif shot_type == '2PT Field Goal':
            explanations.append("2-point shots require higher efficiency")
        
        # Zone explanation
        if zone in ['Restricted Area', 'In The Paint (Non-RA)']:
            explanations.append("High-value shot location near the basket")
        elif '3' in zone:
            explanations.append("3-point zone - efficient shot if open")
        elif 'Mid-Range' in zone:
            explanations.append("Mid-range shots are less efficient - higher bar")
        
        # Distance explanation
        if distance >= 25:
            explanations.append(f"Long-range shot ({distance:.0f} ft) - lower expected efficiency")
        elif distance <= 5:
            explanations.append(f"Close-range shot ({distance:.0f} ft) - high-value opportunity")
        
        # Time explanation
        if time_remaining <= 5.0:
            explanations.append("Late clock situation - take available shots")
        elif time_remaining <= 10.0:
            explanations.append("Clock winding down - consider shot quality")
        
        # Quarter context
        if quarter >= 4:
            explanations.append("Late game - shot selection becomes critical")
        
        return explanations
    
    def advise(
        self,
        make_probability: float,
        shot_type: str,
        zone: str,
        distance: float,
        time_remaining: float,
        quarter: int
    ) -> Dict:
        """
        Provide shot selection advice.
        
        Args:
            make_probability: ML model's predicted probability (0-1)
            shot_type: Type of shot
            zone: Zone name
            distance: Shot distance in feet
            time_remaining: Seconds remaining in quarter
            quarter: Quarter number
        
        Returns:
            Dictionary with decision, probability, threshold, confidence, and explanation
        """
        # Calculate dynamic threshold
        threshold = self.get_threshold(shot_type, zone, time_remaining, quarter)
        
        # Make decision
        decision = "TAKE SHOT" if make_probability >= threshold else "PASS"
        
        # Calculate confidence (distance from threshold)
        confidence = abs(make_probability - threshold)
        
        # Generate explanation
        explanation = self.get_explanation(
            make_probability, threshold, shot_type, zone,
            distance, time_remaining, quarter
        )
        
        return {
            "decision": decision,
            "make_probability": round(make_probability, 4),
            "threshold": round(threshold, 4),
            "confidence": round(confidence, 4),
            "explanation": explanation
        }


if __name__ == "__main__":
    # Test the advisor
    advisor = ShotAdvisor()
    
    # Test case 1: Open 3-pointer
    result1 = advisor.advise(
        make_probability=0.42,
        shot_type="3PT Field Goal",
        zone="Above the Break 3",
        distance=24.5,
        time_remaining=12.0,
        quarter=2
    )
    print("Test 1: Open 3-pointer")
    print(result1)
    print()
    
    # Test case 2: Mid-range shot
    result2 = advisor.advise(
        make_probability=0.48,
        shot_type="2PT Field Goal",
        zone="Mid-Range",
        distance=18.0,
        time_remaining=8.0,
        quarter=3
    )
    print("Test 2: Mid-range shot")
    print(result2)
    print()
    
    # Test case 3: Late clock situation
    result3 = advisor.advise(
        make_probability=0.35,
        shot_type="3PT Field Goal",
        zone="Above the Break 3",
        distance=25.0,
        time_remaining=3.0,
        quarter=4
    )
    print("Test 3: Late clock 3-pointer")
    print(result3)


