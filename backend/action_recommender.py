"""
Action Recommendation System for Shot Selection Advisory
Provides basketball-intelligent next actions when the model suggests PASS.

Version 1.0 - Rule-based action selection from shot context
"""

from typing import Dict, Optional, Tuple
from enum import Enum


class RecommendedAction(Enum):
    """Possible recommended actions when passing on a shot."""
    SWING_PASS = "Swing Pass"
    ATTACK_CLOSEOUT = "Attack the Closeout"
    RESET_OFFENSE = "Reset the Offense"
    LOOK_INSIDE = "Look Inside"
    DRIVE_AND_KICK = "Drive and Kick"
    BEST_AVAILABLE = "Take Best Available Shot"
    RELOCATE = "Relocate for Better Look"


class ActionRecommender:
    """
    Generates basketball-intelligent action recommendations for PASS decisions.
    Uses rule-based logic derived from shot context and defender pressure.
    """


    TIGHT_THRESHOLD = 3.0
    CONTESTED_THRESHOLD = 6.0
    OPEN_THRESHOLD = 10.0


    LOW_QUALITY_THRESHOLD = 0.30
    MEDIUM_QUALITY_THRESHOLD = 0.35


    LATE_CLOCK_THRESHOLD = 5
    EARLY_CLOCK_THRESHOLD = 15


    THREE_POINT_ZONES = {
        'Above the Break 3',
        'Left Corner 3',
        'Right Corner 3',
        'Left Side 3',
        'Right Side 3'
    }

    PAINT_ZONES = {
        'Restricted Area',
        'In The Paint (Non-RA)'
    }

    @classmethod
    def get_recommendation(
        cls,
        make_probability: float,
        shot_type: str,
        zone: str,
        shot_distance: float,
        time_remaining: int,
        quarter: int,
        defender_distance: Optional[float] = None,
        contest_level: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate action recommendation based on shot context.

        Args:
            make_probability: Adjusted shot make probability (0-1)
            shot_type: '2PT Field Goal' or '3PT Field Goal'
            zone: Shot zone (e.g., 'Above the Break 3', 'Mid-Range')
            shot_distance: Distance from basket in feet
            time_remaining: Total seconds left in quarter
            quarter: Current quarter (1-5)
            defender_distance: Distance to closest defender in feet
            contest_level: 'TIGHT', 'CONTESTED', 'OPEN', or 'WIDE_OPEN'

        Returns:
            Dict with 'action' and 'reasoning' keys
        """


        primary_reason = cls._identify_primary_reason(
            make_probability=make_probability,
            defender_distance=defender_distance,
            contest_level=contest_level,
            zone=zone,
            shot_distance=shot_distance,
            time_remaining=time_remaining,
            shot_type=shot_type
        )


        action, reasoning = cls._select_action(
            primary_reason=primary_reason,
            make_probability=make_probability,
            shot_type=shot_type,
            zone=zone,
            shot_distance=shot_distance,
            time_remaining=time_remaining,
            quarter=quarter,
            defender_distance=defender_distance,
            contest_level=contest_level
        )

        return {
            'action': action.value,
            'reasoning': reasoning,
            'primary_reason': primary_reason
        }

    @classmethod
    def _identify_primary_reason(
        cls,
        make_probability: float,
        defender_distance: Optional[float],
        contest_level: Optional[str],
        zone: str,
        shot_distance: float,
        time_remaining: int,
        shot_type: str
    ) -> str:
        """
        Identify the primary reason for the PASS decision.
        This drives action selection logic.
        """


        if time_remaining <= cls.LATE_CLOCK_THRESHOLD:
            return "late_clock"


        if contest_level == "TIGHT" or (defender_distance and defender_distance <= cls.TIGHT_THRESHOLD):

            if zone in cls.THREE_POINT_ZONES and shot_type == '3PT Field Goal':
                return "tight_contest_good_zone"
            return "tight_contest"


        if contest_level == "CONTESTED" or (defender_distance and defender_distance <= cls.CONTESTED_THRESHOLD):
            if zone in cls.THREE_POINT_ZONES:
                return "contested_perimeter"
            return "contested_shot"


        if make_probability < cls.LOW_QUALITY_THRESHOLD:
            if shot_distance > 20:
                return "poor_location_perimeter"
            return "poor_location_general"


        if make_probability < cls.MEDIUM_QUALITY_THRESHOLD and time_remaining >= cls.EARLY_CLOCK_THRESHOLD:
            return "marginal_quality_time_available"


        return "low_quality_general"

    @classmethod
    def _select_action(
        cls,
        primary_reason: str,
        make_probability: float,
        shot_type: str,
        zone: str,
        shot_distance: float,
        time_remaining: int,
        quarter: int,
        defender_distance: Optional[float],
        contest_level: Optional[str]
    ) -> Tuple[RecommendedAction, str]:
        """
        Select the best action recommendation based on primary reason and context.
        Returns (action, reasoning) tuple.
        """




        if primary_reason == "late_clock":

            if quarter == 4 and time_remaining <= 3:
                return (
                    RecommendedAction.BEST_AVAILABLE,
                    "Clock is critical in the 4th quarter. If no better option emerges "
                    "in the next second, this might be your best available shot despite the low probability."
                )

            return (
                RecommendedAction.BEST_AVAILABLE,
                f"With only {time_remaining} seconds left, limited options remain. "
                "Look for a quick drive or immediate kick-out, but be ready to shoot if nothing develops."
            )




        if primary_reason == "tight_contest_good_zone":


            if shot_distance >= 22:
                return (
                    RecommendedAction.ATTACK_CLOSEOUT,
                    f"The defender is flying at you ({defender_distance:.1f} ft away) but you're in "
                    f"a quality {zone} spot. Attack the closeout with a hard drive to force help defense, "
                    "then kick to an open teammate or finish at the rim."
                )
            else:
                return (
                    RecommendedAction.DRIVE_AND_KICK,
                    "The defender is tight on you in a decent mid-range area. "
                    "Use your dribble to collapse the defense and create an open perimeter look."
                )

        if primary_reason == "tight_contest":

            return (
                RecommendedAction.SWING_PASS,
                f"The defender is locked in tight ({defender_distance:.1f} ft away), limiting your shooting space. "
                "A quick swing pass forces defensive rotation and should create an open look on the weak side."
            )




        if primary_reason == "contested_perimeter":

            if time_remaining >= cls.EARLY_CLOCK_THRESHOLD:
                return (
                    RecommendedAction.SWING_PASS,
                    f"The defender is contesting actively ({defender_distance:.1f} ft) on a three-point attempt. "
                    "With time on the clock, swing the ball to find a cleaner look or better spacing."
                )
            else:

                return (
                    RecommendedAction.RELOCATE,
                    "The defender has you contested on the perimeter. "
                    "Relocate to another spot along the arc to create separation, or look for a backdoor cut."
                )

        if primary_reason == "contested_shot":

            return (
                RecommendedAction.LOOK_INSIDE,
                "The defender is contesting your mid-range look. "
                "Scan for a cutting teammate or post entry paint touches often lead to better shots or free throws."
            )




        if primary_reason == "poor_location_perimeter":

            return (
                RecommendedAction.RESET_OFFENSE,
                f"This {shot_distance:.1f}-foot shot is outside optimal range ({make_probability:.1%} probability). "
                "Reset the offense to generate a higher-quality look through ball movement or a designed play."
            )

        if primary_reason == "poor_location_general":

            if zone in cls.PAINT_ZONES:

                return (
                    RecommendedAction.DRIVE_AND_KICK,
                    "You're in traffic in the paint. "
                    "Kick out to a perimeter shooter to force the defense to recover and create better spacing."
                )
            else:
                return (
                    RecommendedAction.LOOK_INSIDE,
                    f"The {zone} is not yielding quality looks right now. "
                    "Feed the post or drive to collapse the defense, then kick out for an open three."
                )




        if primary_reason == "marginal_quality_time_available":
            if shot_type == "3PT Field Goal":
                return (
                    RecommendedAction.RESET_OFFENSE,
                    f"This three-pointer shows {make_probability:.1%} probability with {time_remaining}s remaining. "
                    "Run another action to create a better look penetrate and kick, or set a ball screen."
                )
            else:
                return (
                    RecommendedAction.LOOK_INSIDE,
                    f"This two-pointer is marginal ({make_probability:.1%}) with time on the clock. "
                    "Probe the paint for a higher-percentage shot or drawing help to kick out."
                )





        if time_remaining >= 10:
            return (
                RecommendedAction.RESET_OFFENSE,
                f"This shot has a {make_probability:.1%} make probability. "
                "With time available, reset and run an action to generate a better opportunity."
            )
        else:
            return (
                RecommendedAction.SWING_PASS,
                "The shot quality is below threshold. Make a quick pass to find a better look before the clock expires."
            )






def get_action_recommendation(
    make_probability: float,
    shot_type: str,
    zone: str,
    shot_distance: float,
    time_remaining: int,
    quarter: int,
    defender_distance: Optional[float] = None,
    contest_level: Optional[str] = None
) -> Dict[str, str]:
    """
    Convenience wrapper for ActionRecommender.get_recommendation().

    Returns dict with:
        - action: Short action label (e.g., "Swing Pass")
        - reasoning: 1-2 sentence basketball explanation
        - primary_reason: Internal classification of why shot was passed
    """
    return ActionRecommender.get_recommendation(
        make_probability=make_probability,
        shot_type=shot_type,
        zone=zone,
        shot_distance=shot_distance,
        time_remaining=time_remaining,
        quarter=quarter,
        defender_distance=defender_distance,
        contest_level=contest_level
    )