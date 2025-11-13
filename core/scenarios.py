# core/scenarios.py

import numpy as np
from scipy import integrate
from typing import Dict, Tuple


def integrate_rnd_over_range(
    strikes: np.ndarray,
    density: np.ndarray,
    min_rate: float,
    max_rate: float
) -> float:
    
    mask = (strikes >= min_rate) & (strikes <= max_rate)
    filtered_strikes = strikes[mask]
    filtered_density = density[mask]
    
    if len(filtered_strikes) > 1:
        prob = integrate.simpson(filtered_density, x=filtered_strikes)
    else:
        prob = 0.0
    
    return float(prob)


def compute_scenario_probabilities(
    strikes: np.ndarray,
    density: np.ndarray,
    scenarios: Dict[str, Tuple[float, float]]
) -> Dict[str, float]:
    
    probabilities = {}
    
    for scenario_name, (min_rate, max_rate) in scenarios.items():
        prob = integrate_rnd_over_range(strikes, density, min_rate, max_rate)
        probabilities[scenario_name] = prob
    
    return probabilities


def calculate_probability_shifts(
    probs1: Dict[str, float], 
    probs2: Dict[str, float]
) -> Dict[str, float]:
    shifts = {}
    
    for scenario in probs1.keys():
        if scenario in probs2:
            shift = probs2[scenario] - probs1[scenario]
            shifts[scenario] = shift
    
    return shifts