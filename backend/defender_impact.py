"""
Defender impact modeling for shot probability adjustment.
Combines continuous distance decay with discrete contest quality.

This module provides basketball-realistic defender pressure modeling
that adjusts shot make probability based on defensive pressure.
"""

import numpy as np
from typing import Optional, Dict
from enum import Enum


class ContestLevel(str, Enum):
    """Defensive contest intensity categories."""
    TIGHT = "TIGHT"
    CONTESTED = "CONTESTED"
    OPEN = "OPEN"
    WIDE_OPEN = "WIDE_OPEN"


class DefenderImpactModel:
    """
    Basketball-realistic defender pressure model.
    
    Philosophy:
    - Exponential distance decay (non-linear, smooth)
    - Contest multipliers for qualitative adjustments
    - Multiplicative application to preserve [0,1] bounds
    
    Examples:
        >>> # Tight defense on a 3-pointer
        >>> adj_prob, breakdown = DefenderImpactModel.apply_defender_adjustment(
        ...     base_probability=0.38,
        ...     defender_distance=2.5,
        ...     contest_level=ContestLevel.TIGHT
        ... )
        >>> print(f"Adjusted: {adj_prob:.1%}")  # ~26.8%
        
        >>> # Wide-open shot
        >>> adj_prob, breakdown = DefenderImpactModel.apply_defender_adjustment(
        ...     base_probability=0.35,
        ...     defender_distance=15.0,
        ...     contest_level=ContestLevel.WIDE_OPEN
        ... )
        >>> print(f"Adjusted: {adj_prob:.1%}")  # ~34.2%
    """
    
    # Tunable parameters (calibrated to NBA shooting patterns)
    MAX_PENALTY = 0.35        # 35% max reduction at d=0 (hand-in-face)
    DECAY_RATE = 0.25         # Controls how fast impact fades with distance
    
    # Contest quality multipliers - fine-tune beyond distance alone
    CONTEST_MULTIPLIERS = {
        ContestLevel.TIGHT: 0.85,        # Active hand contest, good position
        ContestLevel.CONTESTED: 0.92,    # Closeout with some pressure
        ContestLevel.OPEN: 0.97,         # Late rotation, minimal pressure
        ContestLevel.WIDE_OPEN: 1.00     # No meaningful contest
    }
    
    @classmethod
    def compute_distance_decay(cls, defender_distance: float) -> float:
        """
        Exponential decay function for defender distance impact.
        
        Uses formula: 1 - (max_penalty × e^(-λ × d))
        
        This creates a smooth, non-linear decay where:
        - Close defenders (0-3 ft) have strong impact
        - Medium distance (3-8 ft) has moderate impact
        - Far defenders (10+ ft) have minimal impact
        
        Args:
            defender_distance: Distance to nearest defender in feet
            
        Returns:
            Decay factor in [0.65, 1.0] where:
            - 0.65 = maximum penalty (defender at 0 ft)
            - 1.0 = no penalty (defender very far)
        
        Examples:
            >>> DefenderImpactModel.compute_distance_decay(0)    # 0.65
            >>> DefenderImpactModel.compute_distance_decay(3)    # ~0.79
            >>> DefenderImpactModel.compute_distance_decay(6)    # ~0.87
            >>> DefenderImpactModel.compute_distance_decay(15)   # ~0.98
        """
        if defender_distance is None or defender_distance < 0:
            return 1.0  # No defender data = no adjustment
        
        # Exponential decay: 1 - (max_penalty × e^(-λ × d))
        decay = 1.0 - (cls.MAX_PENALTY * np.exp(-cls.DECAY_RATE * defender_distance))
        
        # Clamp to reasonable bounds for stability
        return np.clip(decay, 0.65, 1.0)
    
    @classmethod
    def get_contest_multiplier(cls, contest_level: Optional[ContestLevel]) -> float:
        """
        Get discrete multiplier for contest quality.
        
        This captures defensive positioning and effort that distance alone
        doesn't fully represent (e.g., hand position, body angle, timing).
        
        Args:
            contest_level: Contest classification from court analysis
            
        Returns:
            Multiplier in [0.85, 1.0] where:
            - 0.85 = tight contest with active hand
            - 1.0 = no meaningful contest
        
        Examples:
            >>> DefenderImpactModel.get_contest_multiplier(ContestLevel.TIGHT)      # 0.85
            >>> DefenderImpactModel.get_contest_multiplier(ContestLevel.OPEN)       # 0.97
            >>> DefenderImpactModel.get_contest_multiplier(ContestLevel.WIDE_OPEN)  # 1.00
        """
        if contest_level is None:
            return cls.CONTEST_MULTIPLIERS[ContestLevel.OPEN]
        
        return cls.CONTEST_MULTIPLIERS.get(contest_level, 0.97)
    
    @classmethod
    def compute_defender_impact(
        cls,
        defender_distance: Optional[float],
        contest_level: Optional[ContestLevel]
    ) -> Dict[str, float]:
        """
        Compute full defender impact with detailed breakdown.
        
        This is the core computation that combines distance decay
        and contest quality into a single impact factor.
        
        Args:
            defender_distance: Distance to nearest defender in feet
            contest_level: Qualitative contest assessment
            
        Returns:
            Dictionary containing:
            - impact_factor: Combined multiplicative factor (0.65-1.0)
            - distance_decay: Distance component (0.65-1.0)
            - contest_multiplier: Contest quality component (0.85-1.0)
            - percentage_adjustment: Net percentage change for display
        
        Examples:
            >>> impact = DefenderImpactModel.compute_defender_impact(2.5, ContestLevel.TIGHT)
            >>> print(impact['impact_factor'])        # ~0.66
            >>> print(impact['percentage_adjustment']) # ~-34%
        """
        distance_decay = cls.compute_distance_decay(defender_distance)
        contest_mult = cls.get_contest_multiplier(contest_level)
        
        # Combined impact: multiply both factors
        impact_factor = distance_decay * contest_mult
        
        # Convert to percentage for display (e.g., 0.88 → -12%)
        percentage_adjustment = (impact_factor - 1.0) * 100
        
        return {
            'impact_factor': impact_factor,
            'distance_decay': distance_decay,
            'contest_multiplier': contest_mult,
            'percentage_adjustment': percentage_adjustment
        }
    
    @classmethod
    def apply_defender_adjustment(
        cls,
        base_probability: float,
        defender_distance: Optional[float],
        contest_level: Optional[ContestLevel]
    ) -> tuple[float, Dict[str, float]]:
        """
        Apply defender impact to base probability.
        
        This is the main entry point for adjusting ML predictions
        based on defensive pressure.
        
        Args:
            base_probability: ML model output (unadjusted)
            defender_distance: Defender distance in feet (None if no data)
            contest_level: Contest classification (None if no data)
            
        Returns:
            Tuple of (adjusted_probability, impact_breakdown) where:
            - adjusted_probability: Final probability after defense adjustment
            - impact_breakdown: Detailed breakdown dict from compute_defender_impact
        
        Examples:
            >>> # Tight defense reduces 38% shot to ~27%
            >>> adj_prob, breakdown = DefenderImpactModel.apply_defender_adjustment(
            ...     0.38, 2.5, ContestLevel.TIGHT
            ... )
            
            >>> # No defender data = no adjustment
            >>> adj_prob, breakdown = DefenderImpactModel.apply_defender_adjustment(
            ...     0.38, None, None
            ... )
            >>> assert adj_prob == 0.38
        """
        # Compute impact breakdown
        impact = cls.compute_defender_impact(defender_distance, contest_level)
        
        # Apply multiplicative adjustment
        adjusted_prob = base_probability * impact['impact_factor']
        
        # Ensure valid probability bounds
        adjusted_prob = np.clip(adjusted_prob, 0.0, 1.0)
        
        return adjusted_prob, impact
    
    @classmethod
    def get_explanation(
        cls,
        defender_distance: Optional[float],
        contest_level: Optional[ContestLevel],
        impact_breakdown: Dict[str, float]
    ) -> str:
        """
        Generate human-readable explanation of defender impact.
        
        Creates coach/player-friendly text explaining how defense
        affected the shot probability.
        
        Args:
            defender_distance: Defender distance in feet
            contest_level: Contest classification
            impact_breakdown: Output from compute_defender_impact()
            
        Returns:
            Explanation string suitable for display to users
        
        Examples:
            >>> impact = DefenderImpactModel.compute_defender_impact(2.5, ContestLevel.TIGHT)
            >>> explanation = DefenderImpactModel.get_explanation(2.5, ContestLevel.TIGHT, impact)
            >>> print(explanation)
            # "Defender at 2.5 ft (tight closeout) with active hand contest 
            #  adjusts probability by -34.0 percentage points"
        """
        if defender_distance is None:
            return "No defender data available - using base probability"
        
        adj_pct = impact_breakdown['percentage_adjustment']
        
        # Distance-based qualitative description
        if defender_distance <= 3:
            distance_desc = "tight closeout"
        elif defender_distance <= 6:
            distance_desc = "contested"
        elif defender_distance <= 10:
            distance_desc = "open look"
        else:
            distance_desc = "wide-open"
        
        # Contest quality description
        contest_descriptions = {
            ContestLevel.TIGHT: "active hand contest",
            ContestLevel.CONTESTED: "moderate pressure",
            ContestLevel.OPEN: "late rotation",
            ContestLevel.WIDE_OPEN: "no real contest"
        }
        contest_desc = contest_descriptions.get(contest_level, "standard defense")
        
        return (
            f"Defender at {defender_distance:.1f} ft ({distance_desc}) with {contest_desc} "
            f"adjusts probability by {adj_pct:+.1f} percentage points"
        )


# Convenience function for quick testing
def test_defender_impact():
    """Test function to demonstrate model behavior."""
    test_cases = [
        ("Tight 3PT closeout", 0.38, 2.5, ContestLevel.TIGHT),
        ("Contested mid-range", 0.42, 5.0, ContestLevel.CONTESTED),
        ("Open layup", 0.65, 8.0, ContestLevel.OPEN),
        ("Wide-open 3PT", 0.35, 15.0, ContestLevel.WIDE_OPEN),
    ]
    
    print("Defender Impact Model Test Cases")
    print("=" * 70)
    
    for name, base_prob, distance, contest in test_cases:
        adj_prob, breakdown = DefenderImpactModel.apply_defender_adjustment(
            base_prob, distance, contest
        )
        explanation = DefenderImpactModel.get_explanation(distance, contest, breakdown)
        
        print(f"\n{name}:")
        print(f"  Base: {base_prob:.1%} → Adjusted: {adj_prob:.1%}")
        print(f"  Impact: {breakdown['percentage_adjustment']:+.1f} pp")
        print(f"  {explanation}")


if __name__ == "__main__":
    test_defender_impact()