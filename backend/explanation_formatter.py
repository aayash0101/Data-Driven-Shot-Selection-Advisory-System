"""
Explanation Formatter for Shot Selection Advisory System

Provides two distinct explanation styles for the same prediction:
- Player Mode: Short, action-focused, direct
- Coach Mode: Detailed, analytical, teaching-focused

Version 1.0
"""

from typing import Dict, List, Optional, Literal


def format_player_explanation(
    decision: str,
    make_probability: float,
    threshold: float,
    shot_type: str,
    zone: str,
    shot_distance: float,
    defender_distance: Optional[float] = None,
    contest_level: Optional[str] = None,
    time_remaining: int = None
) -> List[str]:
    """
    Generate concise, action-focused explanation for players.

    PLAYER MODE PHILOSOPHY:
    - Maximum 1-2 bullet points
    - Simple, direct language
    - Focus on what to do, not why
    - No technical jargon or percentages

    Args:
        decision: "TAKE SHOT" or "PASS"
        make_probability: Predicted make probability (0-1)
        threshold: Decision threshold (0-1)
        shot_type: "2PT Field Goal" or "3PT Field Goal"
        zone: Shot zone name
        shot_distance: Distance from basket in feet
        defender_distance: Distance to nearest defender (optional)
        contest_level: Contest quality (optional)
        time_remaining: Seconds remaining (optional)

    Returns:
        List of 1-2 short explanation strings
    """
    explanations = []

    if decision == "TAKE SHOT":

        if contest_level in ["WIDE_OPEN", "OPEN"]:
            explanations.append("You're open with a clean look. Let it fly.")
        elif zone in ["Left Corner 3", "Right Corner 3"]:
            explanations.append("Corner three with good spacing. Take the shot.")
        elif shot_distance <= 5:
            explanations.append("You're at the rim. Attack strong.")
        else:
            explanations.append("This is a good shot for you. Be confident.")

    else:

        if contest_level == "TIGHT":
            explanations.append("Defender's hand is in your face. Move the ball.")

        elif contest_level == "CONTESTED" and zone == "Mid-Range":
            explanations.append("Contested long two isn't efficient. Find a better look.")

        elif shot_type == "3PT Field Goal" and shot_distance >= 27:
            explanations.append("Too deep for a good look. Reset or drive.")

        elif contest_level in ["TIGHT", "CONTESTED"]:
            explanations.append("The defense is on you. Pass to create space.")

        elif zone == "Mid-Range" and shot_distance >= 15:
            explanations.append("Long two isn't your best option. Get closer or kick out.")

        elif time_remaining is not None and time_remaining <= 5:
            explanations.append("Clock's running down. Make a quick decision.")

        else:
            explanations.append("Not your shot right now. Keep the ball moving.")

    return explanations


def format_coach_explanation(
    decision: str,
    make_probability: float,
    threshold: float,
    shot_type: str,
    zone: str,
    shot_distance: float,
    defender_distance: Optional[float] = None,
    contest_level: Optional[str] = None,
    time_remaining: int = None,
    quarter: int = None
) -> List[str]:
    """
    Generate detailed, analytical explanation for coaches.

    COACH MODE PHILOSOPHY:
    - Multi-factor reasoning (3-5 points)
    - Reference specific metrics and thresholds
    - Explain basketball principles
    - Connect to broader strategy

    Args:
        decision: "TAKE SHOT" or "PASS"
        make_probability: Predicted make probability (0-1)
        threshold: Decision threshold (0-1)
        shot_type: "2PT Field Goal" or "3PT Field Goal"
        zone: Shot zone name
        shot_distance: Distance from basket in feet
        defender_distance: Distance to nearest defender (optional)
        contest_level: Contest quality (optional)
        time_remaining: Seconds remaining (optional)
        quarter: Current quarter (optional)

    Returns:
        List of detailed explanation strings
    """
    explanations = []

    prob_gap = abs(make_probability - threshold)

    if decision == "TAKE SHOT":

        if prob_gap >= 0.10:
            explanations.append(
                f"Make probability ({make_probability:.1%}) significantly exceeds "
                f"the efficiency threshold ({threshold:.1%}) for this situation."
            )
        else:
            explanations.append(
                f"Make probability ({make_probability:.1%}) meets the efficiency "
                f"threshold ({threshold:.1%}), making this a viable shot."
            )


        if zone in ["Left Corner 3", "Right Corner 3"]:
            explanations.append(
                "Corner three-pointers are among the highest-efficiency shots in basketball "
                "due to shorter distance (22-23.75 ft) and floor spacing."
            )
        elif zone == "Restricted Area":
            explanations.append(
                "Shots in the restricted area have the highest expected value, "
                "especially with verticality and proper finishing technique."
            )
        elif shot_type == "3PT Field Goal":
            explanations.append(
                f"Three-point attempt from {shot_distance:.1f} feet in the {zone} "
                "offers positive expected value when open."
            )
        else:
            explanations.append(
                f"Shot selection from {zone} ({shot_distance:.1f} ft) aligns "
                "with efficient offensive principles."
            )


        if contest_level == "WIDE_OPEN":
            explanations.append(
                f"Defender is {defender_distance:.1f} feet away, providing minimal "
                "defensive pressure. This is an ideal catch-and-shoot opportunity."
            )
        elif contest_level == "OPEN":
            explanations.append(
                "Late defensive rotation creates a window for the shot. "
                "Shooter should be in rhythm and balanced."
            )


        if time_remaining is not None and time_remaining <= 5:
            explanations.append(
                "With shot clock winding down, this represents the best available "
                "scoring opportunity. Execution is critical."
            )

    else:





        if prob_gap >= 0.10:
            explanations.append(
                f"Make probability ({make_probability:.1%}) is well below the "
                f"efficiency threshold ({threshold:.1%}) for this zone and situation."
            )
        elif prob_gap >= 0.05:
            explanations.append(
                f"Make probability ({make_probability:.1%}) falls short of the "
                f"target efficiency ({threshold:.1%}), suggesting a better opportunity exists."
            )
        else:
            explanations.append(
                f"Make probability ({make_probability:.1%}) is marginally below "
                f"threshold ({threshold:.1%}). Consider alternative options."
            )


        if defender_distance is not None and contest_level:
            if contest_level == "TIGHT":
                explanations.append(
                    f"Defender closeout at {defender_distance:.1f} feet creates tight "
                    "contest, significantly reducing shot quality. Historical data shows "
                    "hand-in-face defense lowers make probability by 15-20 percentage points."
                )
            elif contest_level == "CONTESTED":
                explanations.append(
                    f"Active defensive contest from {defender_distance:.1f} feet away "
                    "reduces expected shot value. Driving or passing creates better looks."
                )


        if shot_type == "2PT Field Goal" and zone == "Mid-Range" and shot_distance >= 15:
            explanations.append(
                f"Long two-point attempts ({shot_distance:.1f} ft) are historically "
                "inefficient compared to driving to the rim or stepping back for a three. "
                "Advanced analytics favor threes and layups over mid-range shots."
            )
        elif shot_type == "3PT Field Goal" and shot_distance >= 27:
            explanations.append(
                f"Deep three-pointer from {shot_distance:.1f} feet is beyond optimal "
                "range for most players. Expected value decreases significantly past 26 feet."
            )
        elif zone not in ["Left Corner 3", "Right Corner 3", "Restricted Area"]:
            explanations.append(
                f"Shot from {zone} at {shot_distance:.1f} feet doesn't align with "
                "high-efficiency zone preferences (corners, rim, select above-the-break areas)."
            )


        if time_remaining is not None:
            if time_remaining <= 5:
                explanations.append(
                    "Despite late shot clock, this is still a forced attempt. "
                    "Better offensive execution earlier in the possession would prevent this situation."
                )
            elif time_remaining >= 15:
                explanations.append(
                    f"With {time_remaining} seconds remaining, there's time to create "
                    "a higher-quality shot through ball movement and player movement."
                )


        if quarter is not None and quarter >= 4 and time_remaining is not None and time_remaining <= 120:
            explanations.append(
                "In clutch situations, shot selection becomes even more critical. "
                "Maximizing expected points per possession is essential."
            )

    return explanations


def get_coaching_insight(
    decision: str,
    make_probability: float,
    threshold: float,
    shot_type: str,
    zone: str,
    shot_distance: float,
    defender_distance: Optional[float] = None,
    contest_level: Optional[str] = None,
    recommended_action: Optional[str] = None
) -> str:
    """
    Generate a single coaching insight or teaching point.

    COACHING INSIGHT PHILOSOPHY:
    - One sentence teaching moment
    - Connects to broader basketball principles
    - Actionable for future possessions

    Args:
        decision: "TAKE SHOT" or "PASS"
        make_probability: Predicted make probability
        threshold: Decision threshold
        shot_type: Shot type
        zone: Shot zone
        shot_distance: Distance from basket (FIXED: added)
        defender_distance: Distance to defender (optional)
        contest_level: Contest quality (optional)
        recommended_action: The recommended action (optional)

    Returns:
        Single coaching insight string
    """

    if decision == "TAKE SHOT":

        if contest_level in ["WIDE_OPEN", "OPEN"]:
            return "Great shot selection discipline, taking open looks in rhythm is how efficient offenses operate."
        elif zone in ["Left Corner 3", "Right Corner 3"]:
            return "Emphasize corner three opportunities in offensive schemes, they're the most efficient outside shots."
        elif make_probability >= threshold + 0.15:
            return "This is exactly the type of high-quality shot we want to generate consistently."
        else:
            return "Confident, on-balance shooting in good locations builds offensive rhythm."

    else:


        if contest_level == "TIGHT":
            return "Encourage one more pass against tight closeouts, defenders committed to the ball create passing lanes."

        elif shot_type == "2PT Field Goal" and zone == "Mid-Range":
            return "Work on attacking the rim or creating three-point looks rather than settling for mid-range shots."

        elif shot_type == "3PT Field Goal" and shot_distance >= 27:
            return "Coach players to recognize range limitations, relocating 2-3 feet closer significantly improves efficiency."

        elif recommended_action and "Swing" in recommended_action:
            return "Encourage ball reversal to improve spacing and create higher-quality looks on the weak side."

        elif recommended_action and "Drive" in recommended_action:
            return "Teach players to attack closeouts, driving to the rim or creating kick-out opportunities."

        elif recommended_action and "Reset" in recommended_action:
            return "Emphasize early offense execution to avoid late-clock forced attempts."

        elif contest_level in ["TIGHT", "CONTESTED"]:
            return "Reinforce the principle: when the defense commits, the offense should move the ball."

        else:
            return "Shot selection discipline is the foundation of efficient offense, trust the process."


def format_dual_mode_explanation(
    decision: str,
    make_probability: float,
    threshold: float,
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
    Generate both player and coach explanations with coaching insight.

    This is the main entry point for dual-mode explanations.

    Args:
        All standard prediction context parameters

    Returns:
        Dict with:
            - player: List[str] (1-2 short explanations)
            - coach: List[str] (3-5 detailed explanations)
            - coaching_insight: str (single teaching point)
    """


    player_explanations = format_player_explanation(
        decision=decision,
        make_probability=make_probability,
        threshold=threshold,
        shot_type=shot_type,
        zone=zone,
        shot_distance=shot_distance,
        defender_distance=defender_distance,
        contest_level=contest_level,
        time_remaining=time_remaining
    )


    coach_explanations = format_coach_explanation(
        decision=decision,
        make_probability=make_probability,
        threshold=threshold,
        shot_type=shot_type,
        zone=zone,
        shot_distance=shot_distance,
        defender_distance=defender_distance,
        contest_level=contest_level,
        time_remaining=time_remaining,
        quarter=quarter
    )


    coaching_insight = get_coaching_insight(
        decision=decision,
        make_probability=make_probability,
        threshold=threshold,
        shot_type=shot_type,
        zone=zone,
        shot_distance=shot_distance,
        defender_distance=defender_distance,
        contest_level=contest_level,
        recommended_action=recommended_action
    )

    return {
        "player": player_explanations,
        "coach": coach_explanations,
        "coaching_insight": coaching_insight
    }






if __name__ == "__main__":
    """
    Test cases demonstrating dual-mode explanations
    """

    test_scenarios = [
        {
            "name": "PASS - Tight Contest on Deep Three",
            "params": {
                "decision": "PASS",
                "make_probability": 0.24,
                "threshold": 0.35,
                "shot_type": "3PT Field Goal",
                "zone": "Above the Break 3",
                "shot_distance": 28.0,
                "time_remaining": 14,
                "quarter": 2,
                "defender_distance": 2.2,
                "contest_level": "TIGHT",
                "recommended_action": "Swing Pass"
            }
        },
        {
            "name": "PASS - Contested Mid-Range",
            "params": {
                "decision": "PASS",
                "make_probability": 0.31,
                "threshold": 0.41,
                "shot_type": "2PT Field Goal",
                "zone": "Mid-Range",
                "shot_distance": 17.0,
                "time_remaining": 12,
                "quarter": 3,
                "defender_distance": 5.0,
                "contest_level": "CONTESTED",
                "recommended_action": "Drive or Kick"
            }
        },
        {
            "name": "TAKE - Wide Open Corner Three",
            "params": {
                "decision": "TAKE SHOT",
                "make_probability": 0.47,
                "threshold": 0.35,
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
            "name": "PASS - Late Clock Forced Shot",
            "params": {
                "decision": "PASS",
                "make_probability": 0.32,
                "threshold": 0.38,
                "shot_type": "2PT Field Goal",
                "zone": "Mid-Range",
                "shot_distance": 15.0,
                "time_remaining": 3,
                "quarter": 4,
                "defender_distance": 5.5,
                "contest_level": "CONTESTED",
                "recommended_action": "Take Best Available Shot"
            }
        }
    ]

    print("=" * 80)
    print("DUAL-MODE EXPLANATION FORMATTER - TEST SCENARIOS")
    print("=" * 80)
    print()

    for scenario in test_scenarios:
        print(f"📊 {scenario['name']}")
        print("-" * 80)

        result = format_dual_mode_explanation(**scenario['params'])

        print(f"Decision: {scenario['params']['decision']}")
        print(f"Make Probability: {scenario['params']['make_probability']:.1%}")
        print(f"Threshold: {scenario['params']['threshold']:.1%}")
        if scenario['params']['recommended_action']:
            print(f"Recommended Action: {scenario['params']['recommended_action']}")
        print()

        print("🏀 PLAYER MODE:")
        for exp in result['player']:
            print(f"  • {exp}")
        print()

        print("📋 COACH MODE:")
        for i, exp in enumerate(result['coach'], 1):
            print(f"  {i}. {exp}")
        print()

        print(f"💡 COACHING INSIGHT:")
        print(f"  {result['coaching_insight']}")
        print()
        print()