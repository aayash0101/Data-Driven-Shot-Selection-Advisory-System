"""
Coach-like explanation generator for PASS recommendations.
Transforms model signals into natural basketball feedback.

Uses existing model data:
- Defender distance & contest level
- Shot zone & distance
- Shot type (2PT/3PT)
- Time remaining & quarter
- Make probability vs threshold
"""

import random
from typing import Dict, List, Optional
from enum import Enum


class PassReason(Enum):
    """Primary reason categories for PASS recommendation."""
    TIGHT_DEFENSE = "tight_defense"
    POOR_LOCATION = "poor_location"
    CONTESTED_THREE = "contested_three"
    LATE_CLOCK_PRESSURE = "late_clock_pressure"
    EARLY_CLOCK_RUSH = "early_clock_rush"
    LOW_PERCENTAGE_AREA = "low_percentage_area"
    MARGINAL_DECISION = "marginal_decision"


class CoachFeedbackGenerator:
    """
    Generates natural, coach-like explanations for PASS recommendations.
    Uses multiple phrasing variants to avoid repetitive output.
    """

    def __init__(self):
        """Initialize feedback templates organized by reason category."""


        self.tight_defense_templates = [
            "The defender is right on you, making this a tough shot even for elite shooters. {context} Moving the ball gives the offense a better chance.",
            "This is a heavily contested look. {context} Trust your teammates to find better spacing.",
            "With a defender this close, the probability drops significantly. {context} Keep the ball moving.",
            "That's hand-in-face defense. {context} There's a better shot available if we swing it.",
            "The contest is too tight here. {context} Let's create some separation first."
        ]


        self.contested_three_templates = [
            "This three is contested, and the math doesn't favor taking it. {context} An extra pass could open up a cleaner look.",
            "With a defender closing out, this three becomes low percentage. {context} We've got time to find better.",
            "The defense is recovering on this three-point attempt. {context} Another touch or two could get us an open look.",
            "This is the kind of contested three we want to avoid. {context} Let's work for something cleaner.",
            "The closeout makes this three harder than it needs to be. {context} Keep attacking."
        ]


        self.poor_location_templates = [
            "This spot on the floor has a lower success rate than other options. {context} Moving closer or finding a three gives us better math.",
            "The data shows this area isn't high value for us. {context} Let's work for a shot at the rim or from three.",
            "This is one of the tougher zones on the floor. {context} We can create something more efficient.",
            "Shot quality matters here this location puts us at a disadvantage. {context} Another pass improves our chances.",
            "This isn't where we want to live. {context} Get to the rim or kick it out for three."
        ]


        self.late_clock_templates = [
            "The shot clock is running down, but this look isn't worth forcing. {context} Make the smart play.",
            "With time running out, this is still a low-percentage option. {context} Don't settle attack or find the open man.",
            "Even in late clock, we need to be disciplined. {context} A better decision is available.",
            "The pressure is on, but forcing this shot doesn't help us. {context} Stay composed.",
            "Clock's low, but this isn't the answer. {context} Trust your read."
        ]


        self.early_clock_templates = [
            "There's plenty of time left no need to settle for this. {context} Let's work the possession.",
            "We're early in the clock and can get a better look. {context} Be patient with the offense.",
            "With this much time, we should be looking for quality over speed. {context} Keep the ball moving.",
            "No reason to rush into this shot. {context} Let the play develop.",
            "The clock gives us options here. {context} Don't force it early in the possession."
        ]


        self.low_percentage_templates = [
            "This area of the floor doesn't produce for us consistently. {context} Find a better spot.",
            "Historically, this shot type from here has low success rates. {context} Let's create a higher-value attempt.",
            "The numbers don't favor taking this shot. {context} Another action could get us something cleaner.",
            "This is a low-efficiency zone. {context} Work for position or reset the offense.",
            "We don't want to live in this space. {context} Get back to our strengths."
        ]


        self.marginal_templates = [
            "This is close, but the odds are just under where we want them. {context} One more pass could tip the scales.",
            "It's a borderline decision leaning toward passing to improve our chances. {context} Stay aggressive but smart.",
            "The probability is right on the edge. {context} Trust the process and find the extra percent.",
            "This is almost there, but we can do slightly better. {context} Keep the confidence, make the right read.",
            "It's a judgment call, and the data suggests looking off this one. {context} Good recognition."
        ]


        self.context_snippets = {
            "time_plenty": "We've got time to work.",
            "time_some": "There's still time on the clock.",
            "time_low": "Even with the clock winding down,",
            "quarter_early": "It's early in the game stay patient.",
            "quarter_late": "Late in the game, every possession matters.",
            "three_point": "Three-point shots need spacing.",
            "two_point": "Inside the arc, we need a clear path.",
            "distance_far": "That's a long shot to settle for.",
            "distance_mid": "From this range, we need clean looks.",
            "distance_close": "You're close attack the rim instead.",
            "defender_tight": "The defender took away your space.",
            "defender_contest": "The defense is in position.",
            "defender_closing": "They're rotating over.",
        }

    def generate_pass_explanation(
        self,
        make_probability: float,
        threshold: float,
        shot_type: str,
        zone: str,
        shot_distance: float,
        time_remaining: int,
        quarter: int,
        defender_distance: Optional[float] = None,
        contest_level: Optional[str] = None
    ) -> List[str]:
        """
        Generate coach-like explanation for PASS recommendation.

        Args:
            make_probability: Model's predicted make probability (0-1)
            threshold: Decision threshold (0-1)
            shot_type: "2PT Field Goal" or "3PT Field Goal"
            zone: Shot zone string
            shot_distance: Distance from basket in feet
            time_remaining: Seconds remaining in quarter
            quarter: Quarter number (1-4+)
            defender_distance: Distance to nearest defender in feet (optional)
            contest_level: "TIGHT", "CONTESTED", "OPEN", "WIDE_OPEN" (optional)

        Returns:
            List of explanation strings in coach-like language
        """


        reason = self._identify_pass_reason(
            make_probability, threshold, shot_type, zone, shot_distance,
            time_remaining, quarter, defender_distance, contest_level
        )


        context = self._build_context(
            shot_type, shot_distance, time_remaining, quarter,
            defender_distance, contest_level
        )


        template = self._select_template(reason)


        main_explanation = template.format(context=context)


        explanations = []


        if defender_distance is not None and contest_level:
            defender_insight = self._get_defender_insight(
                defender_distance, contest_level
            )
            if defender_insight:
                explanations.append(defender_insight)


        explanations.append(main_explanation)


        quality_insight = self._get_quality_insight(
            make_probability, threshold, shot_type, zone
        )
        explanations.append(quality_insight)


        margin = threshold - make_probability
        explanations.append(
            f"Shot probability: {make_probability:.1%} (threshold: {threshold:.1%}, "
            f"margin: {margin:.1%})"
        )

        return explanations

    def _identify_pass_reason(
        self,
        make_probability: float,
        threshold: float,
        shot_type: str,
        zone: str,
        shot_distance: float,
        time_remaining: int,
        quarter: int,
        defender_distance: Optional[float],
        contest_level: Optional[str]
    ) -> PassReason:
        """Determine the primary reason for PASS recommendation."""


        if contest_level == "TIGHT" or (defender_distance and defender_distance <= 3):
            return PassReason.TIGHT_DEFENSE


        if (contest_level in ["CONTESTED", "TIGHT"] and
            shot_type == "3PT Field Goal" and
            defender_distance and defender_distance <= 6):
            return PassReason.CONTESTED_THREE


        if time_remaining <= 4:
            return PassReason.LATE_CLOCK_PRESSURE


        poor_zones = ["Mid-Range", "In The Paint (Non-RA)"]
        if zone in poor_zones and shot_distance > 8:
            return PassReason.POOR_LOCATION


        if make_probability < threshold - 0.08:
            return PassReason.LOW_PERCENTAGE_AREA


        if time_remaining > 20 and quarter <= 3:
            return PassReason.EARLY_CLOCK_RUSH


        return PassReason.MARGINAL_DECISION

    def _build_context(
        self,
        shot_type: str,
        shot_distance: float,
        time_remaining: int,
        quarter: int,
        defender_distance: Optional[float],
        contest_level: Optional[str]
    ) -> str:
        """Build supporting context snippet."""

        context_parts = []


        if time_remaining > 20:
            context_parts.append(self.context_snippets["time_plenty"])
        elif time_remaining > 8:
            context_parts.append(self.context_snippets["time_some"])
        elif time_remaining <= 4:
            context_parts.append(self.context_snippets["time_low"])


        if quarter >= 4:
            context_parts.append(self.context_snippets["quarter_late"])
        elif quarter <= 2:
            context_parts.append(self.context_snippets["quarter_early"])


        if defender_distance is not None and contest_level:
            if contest_level == "CONTESTED":
                context_parts.append(self.context_snippets["defender_contest"])
            elif contest_level == "TIGHT":
                context_parts.append(self.context_snippets["defender_tight"])


        if shot_distance >= 20:
            context_parts.append(self.context_snippets["distance_far"])
        elif shot_distance <= 8:
            context_parts.append(self.context_snippets["distance_close"])


        if len(context_parts) > 2:
            context_parts = random.sample(context_parts, 2)

        return " ".join(context_parts) if context_parts else ""

    def _select_template(self, reason: PassReason) -> str:
        """Select a random template for the given reason."""

        template_map = {
            PassReason.TIGHT_DEFENSE: self.tight_defense_templates,
            PassReason.CONTESTED_THREE: self.contested_three_templates,
            PassReason.POOR_LOCATION: self.poor_location_templates,
            PassReason.LATE_CLOCK_PRESSURE: self.late_clock_templates,
            PassReason.EARLY_CLOCK_RUSH: self.early_clock_templates,
            PassReason.LOW_PERCENTAGE_AREA: self.low_percentage_templates,
            PassReason.MARGINAL_DECISION: self.marginal_templates,
        }

        templates = template_map.get(reason, self.marginal_templates)
        return random.choice(templates)

    def _get_defender_insight(
        self,
        defender_distance: float,
        contest_level: str
    ) -> Optional[str]:
        """Generate defender-specific insight."""

        if contest_level == "TIGHT" and defender_distance <= 2:
            insights = [
                f"With the defender only {defender_distance:.1f} feet away, you're looking at hand-in-face defense.",
                f"Defender is at {defender_distance:.1f} feet, that's elite closeout position.",
                f"At {defender_distance:.1f} feet, the defender has taken away your shooting window.",
            ]
            return random.choice(insights)

        elif contest_level == "CONTESTED" and defender_distance <= 5:
            insights = [
                f"The defender at {defender_distance:.1f} feet is in active contest range.",
                f"With {defender_distance:.1f} feet of separation, they can still challenge the shot effectively.",
            ]
            return random.choice(insights)

        return None

    def _get_quality_insight(
        self,
        make_probability: float,
        threshold: float,
        shot_type: str,
        zone: str
    ) -> str:
        """Generate shot quality insight."""

        margin = threshold - make_probability


        if margin >= 0.08:
            insights = [
                "This shot grades significantly below our quality standards.",
                "The combination of factors makes this a low-value attempt.",
                "Multiple indicators suggest this isn't the right play.",
            ]
            return random.choice(insights)


        elif margin >= 0.04:
            insights = [
                "This shot is below our target efficiency range.",
                "The situation calls for a better option.",
                "We can improve our chances with an extra pass or action.",
            ]
            return random.choice(insights)


        else:
            insights = [
                "This is close, but we're looking for that extra edge.",
                "It's a borderline decision, let's focus on the side of quality.",
                "Trust the read and find the incremental improvement.",
            ]
            return random.choice(insights)


def generate_coach_feedback(
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
    **kwargs
) -> List[str]:
    """
    Main entry point for generating explanations.

    For TAKE SHOT: Returns concise positive feedback
    For PASS: Returns detailed coach-like reasoning

    Args:
        decision: "TAKE SHOT" or "PASS"
        make_probability: Predicted make probability (0-1)
        threshold: Decision threshold (0-1)
        shot_type: "2PT Field Goal" or "3PT Field Goal"
        zone: Shot zone description
        shot_distance: Distance from basket in feet
        time_remaining: Seconds left in quarter
        quarter: Quarter number
        defender_distance: Distance to defender in feet (optional)
        contest_level: Contest level string (optional)
        **kwargs: Additional arguments (ignored)

    Returns:
        List of explanation strings
    """

    if decision == "TAKE SHOT":

        explanations = []

        margin = make_probability - threshold

        if defender_distance is not None and contest_level == "WIDE_OPEN":
            explanations.append("You're wide open this is a great look.")
        elif margin >= 0.10:
            explanations.append("High-quality shot. Take it with confidence.")
        else:
            explanations.append("Good look. Let it fly.")

        if shot_type == "3PT Field Goal" and zone in ["Left Corner 3", "Right Corner 3"]:
            explanations.append("Corner three is one of our best shots.")
        elif shot_distance <= 5:
            explanations.append("You're at the rim finish strong.")

        explanations.append(
            f"Shot probability: {make_probability:.1%} (threshold: {threshold:.1%}, "
            f"margin: +{margin:.1%})"
        )

        return explanations

    else:
        generator = CoachFeedbackGenerator()
        return generator.generate_pass_explanation(
            make_probability=make_probability,
            threshold=threshold,
            shot_type=shot_type,
            zone=zone,
            shot_distance=shot_distance,
            time_remaining=time_remaining,
            quarter=quarter,
            defender_distance=defender_distance,
            contest_level=contest_level
        )



if __name__ == "__main__":
    print("Coach Feedback Generator - Test Cases\n")
    print("=" * 70)

    test_cases = [
        {
            "name": "Tight Defense",
            "decision": "PASS",
            "make_probability": 0.28,
            "threshold": 0.35,
            "shot_type": "3PT Field Goal",
            "zone": "Above the Break 3",
            "shot_distance": 24.0,
            "time_remaining": 12,
            "quarter": 2,
            "defender_distance": 1.5,
            "contest_level": "TIGHT"
        },
        {
            "name": "Contested Three",
            "decision": "PASS",
            "make_probability": 0.30,
            "threshold": 0.38,
            "shot_type": "3PT Field Goal",
            "zone": "Right Corner 3",
            "shot_distance": 23.0,
            "time_remaining": 18,
            "quarter": 3,
            "defender_distance": 4.5,
            "contest_level": "CONTESTED"
        },
        {
            "name": "Poor Mid-Range",
            "decision": "PASS",
            "make_probability": 0.32,
            "threshold": 0.40,
            "shot_type": "2PT Field Goal",
            "zone": "Mid-Range",
            "shot_distance": 16.0,
            "time_remaining": 22,
            "quarter": 1,
            "defender_distance": 8.0,
            "contest_level": "OPEN"
        },
        {
            "name": "Good Look (TAKE)",
            "decision": "TAKE SHOT",
            "make_probability": 0.48,
            "threshold": 0.35,
            "shot_type": "3PT Field Goal",
            "zone": "Left Corner 3",
            "shot_distance": 23.0,
            "time_remaining": 15,
            "quarter": 4,
            "defender_distance": 12.0,
            "contest_level": "WIDE_OPEN"
        }
    ]

    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"Decision: {case['decision']}")
        print(f"Context: {case['shot_type']} from {case['zone']}, "
              f"{case['defender_distance']:.1f}ft defender ({case['contest_level']})")
        print("\nExplanation:")

        explanations = generate_coach_feedback(**case)
        for i, exp in enumerate(explanations, 1):
            print(f"  {i}. {exp}")

        print("-" * 70)