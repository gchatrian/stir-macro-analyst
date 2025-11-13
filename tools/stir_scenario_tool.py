# tools/stir_scenario_tool.py

"""STIR Scenario Tool - Complete STIR analysis with scenario probabilities."""

import logging
from typing import Dict, List, Any
from ..core import analyze_stir_contract

logger = logging.getLogger(__name__)


def analyze_stir_scenarios(
    contract: str, 
    date: str, 
    scenarios: Dict[str, List[float]]
) -> Dict[str, Any]:
    """
    Performs complete STIR futures analysis for a specific date.
    
    This tool:
    1. Automatically infers currency from contract ticker
    2. Downloads futures and options market data from Bloomberg
    3. Calibrates SABR volatility model to market prices
    4. Generates Risk Neutral Density (RND)
    5. Computes probability for each scenario by integrating RND
    
    Input scenarios should cover the full rate spectrum and be mutually exclusive.
    Typical scenarios: Deep Cut (0-1.5%), Moderate Cut (1.5-3%), Neutral (3-4.5%), Hike (4.5-8%)
    
    The RND represents market-implied probability distribution of rates at contract expiry.
    
    Args:
        contract: STIR futures ticker (e.g., SFRZ6 for SOFR Dec 2026, ERH5 for Euribor Mar 2025)
        date: Analysis snapshot date in YYYYMMDD format (e.g., 20241018)
        scenarios: Dict mapping scenario names to [min_rate, max_rate] in percentage terms.
                   Example: {'Deep Cut': [0.0, 1.5], 'Neutral': [3.0, 4.5]}
    
    Returns:
        Complete analysis with RND data and scenario probabilities
    """
    try:
        logger.info(f"Analyzing {contract} on {date}")
        
        # Convert scenarios from list format to tuple format
        scenarios_tuples = {
            name: tuple(range_list) 
            for name, range_list in scenarios.items()
        }
        
        result = analyze_stir_contract(contract, date, scenarios_tuples)
        
        logger.info(f"Analysis complete: {len(result['scenario_probabilities'])} scenarios computed")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing {contract} on {date}: {e}")
        return {
            "success": False,
            "error": str(e),
            "contract": contract,
            "date": date
        }