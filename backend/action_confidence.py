"""
Action Confidence Calculator for Shot Selection Advisory System

Computes confidence scores for recommended actions using explainable,
rule-based logic. No ML models - purely based on basketball reasoning
and existing prediction signals.

Version 1.0
"""

from typing import Dict, Optional, Literal


def compute_action_confidence(
    make_probability: float,
    threshold: float,
    decision: str,
    shot_type: str,
    zone: str,
    shot_distance: float,
    time_remaining: int,
    quarter: int,
    defender_distance: Optional[float] = None,
    contest_level: Optional[str] = None,
    recommended_action: Optional[str] = None
) -> Dict[str, any]:
    """
    Compute confidence score for the recommended action.

    BASKETBALL REASONING:
    - Clear efficiency gaps → High confidence
    - Strong defensive pressure → High confidence
    - Late clock situations → Lower confidence (forced decisions)
    - Zone/distance mismatches → Higher confidence

    Args:
        make_probability: Predicted shot make probability (0-1)
        threshold: Decision threshold for this shot context (0-1)
        decision: "TAKE SHOT" or "PASS"
        shot_type: "2PT Field Goal" or "3PT Field Goal"
        zone: Shot zone name
        shot_distance: Distance from basket in feet
        time_remaining: Seconds remaining in quarter
        quarter: Current quarter (1-4+)
        defender_distance: Distance to nearest defender in feet
        contest_level: "TIGHT", "CONTESTED", "OPEN", "WIDE_OPEN"
        recommended_action: The action recommendation (for PASS decisions)

    Returns:
        Dict with:
            - action_confidence: float (0-1)
            - confidence_level: str ("Low", "Moderate", "High", "Very High")
            - confidence_reasoning: str (explanation)
    """





    prob_threshold_gap = abs(make_probability - threshold)






    if prob_threshold_gap >= 0.15:
        base_confidence = 0.85
    elif prob_threshold_gap >= 0.10:
        base_confidence = 0.70
    elif prob_threshold_gap >= 0.05:
        base_confidence = 0.55
    else:
        base_confidence = 0.40




    confidence_adjustments = []
    total_adjustment = 0.0



    if decision == "PASS" and contest_level:
        if contest_level == "TIGHT":

            total_adjustment += 0.10
            confidence_adjustments.append("tight_contest")
        elif contest_level == "CONTESTED":

            total_adjustment += 0.05
            confidence_adjustments.append("contested_shot")



    if time_remaining <= 5:

        total_adjustment -= 0.10
        confidence_adjustments.append("late_clock_pressure")
    elif time_remaining <= 10:

        total_adjustment -= 0.05
        confidence_adjustments.append("moderate_time_pressure")



    if decision == "PASS":

        if shot_type == "3PT Field Goal" and shot_distance >= 27:
            total_adjustment += 0.08
            confidence_adjustments.append("deep_three_attempt")


        elif shot_type == "2PT Field Goal" and zone == "Mid-Range" and shot_distance >= 15:
            total_adjustment += 0.06
            confidence_adjustments.append("inefficient_midrange")


        elif shot_type == "3PT Field Goal" and zone == "Above the Break 3" and shot_distance >= 25:
            total_adjustment += 0.07
            confidence_adjustments.append("difficult_angle")



    if quarter >= 4 and time_remaining <= 120:
        total_adjustment -= 0.08
        confidence_adjustments.append("clutch_situation")




    final_confidence = min(0.95, max(0.15, base_confidence + total_adjustment))




    if final_confidence >= 0.75:
        confidence_level = "Very High"
    elif final_confidence >= 0.60:
        confidence_level = "High"
    elif final_confidence >= 0.45:
        confidence_level = "Moderate"
    else:
        confidence_level = "Low"




    reasoning_parts = []


    if prob_threshold_gap >= 0.15:
        reasoning_parts.append("The shot is well below the efficiency threshold")
    elif prob_threshold_gap >= 0.10:
        reasoning_parts.append("The shot is clearly below the efficiency threshold")
    elif prob_threshold_gap >= 0.05:
        reasoning_parts.append("The shot is moderately below the efficiency threshold")
    else:
        reasoning_parts.append("The shot is marginally below the efficiency threshold")


    if "tight_contest" in confidence_adjustments:
        reasoning_parts.append("tightly contested")
    elif "contested_shot" in confidence_adjustments:
        reasoning_parts.append("actively contested")

    if "deep_three_attempt" in confidence_adjustments:
        reasoning_parts.append("from deep 3-point range")
    elif "inefficient_midrange" in confidence_adjustments:
        reasoning_parts.append("from inefficient mid-range area")
    elif "difficult_angle" in confidence_adjustments:
        reasoning_parts.append("from a difficult angle")


    if "late_clock_pressure" in confidence_adjustments:
        reasoning_parts.append("though shot clock pressure limits alternatives")
    elif "clutch_situation" in confidence_adjustments:
        reasoning_parts.append("in a clutch situation with uncertainty")


    if decision == "PASS":
        if len(reasoning_parts) <= 2:
            confidence_reasoning = f"{reasoning_parts[0]}, making this a clear passing decision."
        else:

            main_parts = ", ".join(reasoning_parts[:-1])
            last_part = reasoning_parts[-1]
            confidence_reasoning = f"{main_parts}, and {last_part}."
    else:

        confidence_reasoning = f"The shot exceeds the efficiency threshold by {prob_threshold_gap:.1%}, indicating a good scoring opportunity."




    return {
        "action_confidence": round(final_confidence, 2),
        "confidence_level": confidence_level,
        "confidence_reasoning": confidence_reasoning,
        "confidence_factors": {
            "base_confidence": round(base_confidence, 2),
            "probability_threshold_gap": round(prob_threshold_gap, 3),
            "total_adjustment": round(total_adjustment, 2),
            "active_adjustments": confidence_adjustments
        }
    }






if __name__ == "__main__":
    """
    Test cases demonstrating confidence calculation across various scenarios
    """

    test_scenarios = [
        {
            "name": "Clear PASS - Tight Contest on Three",
            "params": {
                "make_probability": 0.26,
                "threshold": 0.38,
                "decision": "PASS",
                "shot_type": "3PT Field Goal",
                "zone": "Right Corner 3",
                "shot_distance": 23.5,
                "time_remaining": 14,
                "quarter": 2,
                "defender_distance": 2.2,
                "contest_level": "TIGHT",
                "recommended_action": "Swing Pass"
            }
        },
        {
            "name": "Marginal PASS - Late Clock",
            "params": {
                "make_probability": 0.36,
                "threshold": 0.40,
                "decision": "PASS",
                "shot_type": "2PT Field Goal",
                "zone": "Mid-Range",
                "shot_distance": 15.0,
                "time_remaining": 3,
                "quarter": 4,
                "defender_distance": 5.5,
                "contest_level": "CONTESTED",
                "recommended_action": "Take Best Available Shot"
            }
        },
        {
            "name": "Strong PASS - Deep Three",
            "params": {
                "make_probability": 0.25,
                "threshold": 0.35,
                "decision": "PASS",
                "shot_type": "3PT Field Goal",
                "zone": "Above the Break 3",
                "shot_distance": 27.5,
                "time_remaining": 18,
                "quarter": 1,
                "defender_distance": 7.5,
                "contest_level": "OPEN",
                "recommended_action": "Relocate for Better Look"
            }
        },
        {
            "name": "Clear TAKE - Wide Open Corner",
            "params": {
                "make_probability": 0.47,
                "threshold": 0.35,
                "decision": "TAKE SHOT",
                "shot_type": "3PT Field Goal",
                "zone": "Left Corner 3",
                "shot_distance": 23.0,
                "time_remaining": 16,
                "quarter": 3,
                "defender_distance": 13.0,
                "contest_level": "WIDE_OPEN",
                "recommended_action": None
            }
        },
        {
            "name": "Clutch Uncertainty - 4th Quarter",
            "params": {
                "make_probability": 0.32,
                "threshold": 0.38,
                "decision": "PASS",
                "shot_type": "2PT Field Goal",
                "zone": "Mid-Range",
                "shot_distance": 16.0,
                "time_remaining": 90,
                "quarter": 4,
                "defender_distance": 4.8,
                "contest_level": "CONTESTED",
                "recommended_action": "Drive or Kick"
            }
        }
    ]

    print("=" * 80)
    print("ACTION CONFIDENCE CALCULATOR - TEST SCENARIOS")
    print("=" * 80)
    print()

    for scenario in test_scenarios:
        print(f"📊 {scenario['name']}")
        print("-" * 80)

        result = compute_action_confidence(**scenario['params'])

        print(f"Decision: {scenario['params']['decision']}")
        if scenario['params']['recommended_action']:
            print(f"Recommended Action: {scenario['params']['recommended_action']}")
        print(f"Make Probability: {scenario['params']['make_probability']:.1%}")
        print(f"Threshold: {scenario['params']['threshold']:.1%}")
        print()
        print(f"✅ Confidence Score: {result['action_confidence']:.2f}")
        print(f"✅ Confidence Level: {result['confidence_level']}")
        print(f"✅ Reasoning: {result['confidence_reasoning']}")
        print()
        print(f"Factors:")
        print(f"  - Base Confidence: {result['confidence_factors']['base_confidence']:.2f}")
        print(f"  - Prob-Threshold Gap: {result['confidence_factors']['probability_threshold_gap']:.3f}")
        print(f"  - Adjustments: {result['confidence_factors']['total_adjustment']:+.2f}")
        print(f"  - Active Factors: {', '.join(result['confidence_factors']['active_adjustments']) if result['confidence_factors']['active_adjustments'] else 'None'}")
        print()
        print()