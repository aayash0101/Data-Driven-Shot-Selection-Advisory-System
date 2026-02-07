"""
Shot quality breakdown analyzer.
Provides interpretable components showing how different factors
contribute to shot make probability.

Updated to include defensive pressure modeling.
"""

from typing import Dict, Optional


class ShotQualityAnalyzer:
    """
    Decomposes shot probability into interpretable components.

    Components:
    - baseline: Player's base shooting ability
    - location_quality: Shot location efficiency
    - shot_type_value: 2PT vs 3PT value
    - time_context: Game situation timing
    - defensive_pressure: Defender impact (NEW)
    """

    def compute_breakdown(
        self,
        make_probability: float,
        shot_type: str,
        zone: str,
        shot_distance: float,
        time_remaining: int,
        quarter: int,

        defender_distance: Optional[float] = None,
        contest_level: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Compute interpretable shot quality breakdown.

        Each component represents an additive contribution to the
        final make probability (displayed as percentage adjustments).

        Args:
            make_probability: Final adjusted probability
            shot_type: '2PT Field Goal' or '3PT Field Goal'
            zone: Shot zone (e.g., 'Restricted Area', 'Corner 3')
            shot_distance: Distance from basket in feet
            time_remaining: Seconds left in quarter
            quarter: Current quarter (1-4, 5 for OT)
            defender_distance: Distance to nearest defender in feet (NEW)
            contest_level: Contest classification (NEW)

        Returns:
            Dictionary of component contributions as decimals
            (e.g., 0.05 = +5%, -0.12 = -12%)
        """

        baseline = self._baseline_ability()
        location = self._location_quality(zone, shot_distance)
        shot_value = self._shot_type_value(shot_type)
        time_ctx = self._time_context(time_remaining, quarter)


        defensive_pressure = self._defensive_pressure(
            defender_distance,
            contest_level
        )

        return {
            'baseline': baseline,
            'location_quality': location,
            'shot_type_value': shot_value,
            'time_context': time_ctx,
            'defensive_pressure': defensive_pressure
        }

    def _baseline_ability(self) -> float:
        """
        Base shooting ability component.

        Represents the player's fundamental shooting skill level.
        For point guards, this is typically +5% above league average.
        """
        return 0.05

    def _location_quality(self, zone: str, shot_distance: float) -> float:
        """
        Shot location efficiency component.

        Different court locations have different efficiency values
        based on NBA shooting data.

        Args:
            zone: Court zone name
            shot_distance: Distance from basket

        Returns:
            Location quality adjustment (-0.15 to +0.12)
        """

        if zone == 'Restricted Area':
            return 0.12
        elif zone in ['Left Corner 3', 'Right Corner 3']:
            return 0.08


        elif zone == 'In The Paint (Non-RA)':
            return 0.03
        elif zone == 'Above the Break 3':
            return 0.00


        elif zone == 'Mid-Range':
            if shot_distance < 16:
                return -0.05
            else:
                return -0.10

        return 0.00

    def _shot_type_value(self, shot_type: str) -> float:
        """
        Shot type value component.

        3-pointers have higher expected value (1.05 vs 1.00 points per attempt)
        but are harder to make.

        Args:
            shot_type: '2PT Field Goal' or '3PT Field Goal'

        Returns:
            Shot type value adjustment
        """
        if '3PT' in shot_type:
            return 0.08
        else:
            return -0.02

    def _time_context(self, time_remaining: int, quarter: int) -> float:
        """
        Game situation timing component.

        Accounts for pressure and fatigue based on game clock.

        Args:
            time_remaining: Seconds left in quarter
            quarter: Current quarter

        Returns:
            Time context adjustment (-0.08 to +0.03)
        """

        if quarter >= 4 and time_remaining < 120:
            return -0.08


        if time_remaining < 60:
            return -0.05


        if quarter <= 2 and time_remaining > 360:
            return 0.03

        return 0.00

    def _defensive_pressure(
        self,
        defender_distance: Optional[float],
        contest_level: Optional[str]
    ) -> float:
        """
        Defensive pressure component (NEW).

        Converts the multiplicative defender impact into an additive
        component for the breakdown display.

        Args:
            defender_distance: Distance to defender in feet
            contest_level: Contest classification string

        Returns:
            Defensive pressure adjustment (typically -0.35 to 0.00)
        """
        if defender_distance is None:
            return 0.0

        try:

            from defender_impact import DefenderImpactModel, ContestLevel


            contest_enum = None
            if contest_level:
                try:
                    contest_enum = ContestLevel(contest_level)
                except (ValueError, KeyError):
                    contest_enum = ContestLevel.OPEN


            impact = DefenderImpactModel.compute_defender_impact(
                defender_distance,
                contest_enum
            )



            defensive_pressure = impact['impact_factor'] - 1.0

            return defensive_pressure

        except ImportError:

            print("Warning: defender_impact module not found, using neutral defense")
            return 0.0

    def format_breakdown_for_display(self, breakdown: Dict[str, float]) -> Dict[str, str]:
        """
        Format breakdown components for user-friendly display.

        Args:
            breakdown: Raw breakdown dictionary

        Returns:
            Dictionary with formatted percentage strings
        """
        formatted = {}

        component_names = {
            'baseline': 'Base Ability',
            'location_quality': 'Location Quality',
            'shot_type_value': 'Shot Type Value',
            'time_context': 'Time Context',
            'defensive_pressure': 'Defensive Pressure'
        }

        for key, value in breakdown.items():
            name = component_names.get(key, key)
            percentage = value * 100
            sign = '+' if value >= 0 else ''
            formatted[name] = f"{sign}{percentage:.1f}%"

        return formatted



def test_breakdown():
    """Test shot quality breakdown with various scenarios."""
    analyzer = ShotQualityAnalyzer()

    test_cases = [
        {
            'name': 'Open corner 3',
            'make_probability': 0.42,
            'shot_type': '3PT Field Goal',
            'zone': 'Left Corner 3',
            'shot_distance': 23.5,
            'time_remaining': 420,
            'quarter': 2,
            'defender_distance': 12.0,
            'contest_level': 'WIDE_OPEN'
        },
        {
            'name': 'Contested layup',
            'make_probability': 0.58,
            'shot_type': '2PT Field Goal',
            'zone': 'Restricted Area',
            'shot_distance': 2.5,
            'time_remaining': 85,
            'quarter': 4,
            'defender_distance': 3.5,
            'contest_level': 'CONTESTED'
        }
    ]

    print("Shot Quality Breakdown Test Cases")
    print("=" * 70)

    for case in test_cases:
        name = case.pop('name')
        breakdown = analyzer.compute_breakdown(**case)
        formatted = analyzer.format_breakdown_for_display(breakdown)

        print(f"\n{name}:")
        for component, value in formatted.items():
            print(f"  {component:.<30} {value:>8}")
        print(f"  {'Final Probability':.<30} {case['make_probability']*100:>7.1f}%")


if __name__ == "__main__":
    test_breakdown()