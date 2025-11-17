# tools/meeting_dates_tool.py

"""Meeting Dates Tool - Counts central bank meetings in a date range."""

import logging
from typing import Dict, Any
from ..core import count_meetings_in_range

logger = logging.getLogger(__name__)


def count_central_bank_meetings(
    currency: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Counts how many central bank policy meetings occur between two dates.
    
    This tool helps contextualize STIR analysis by showing how many rate decision
    opportunities exist in the analysis period. More meetings = more opportunities
    for rate changes.
    
    Use this when:
    - Analyzing STIR contracts to understand the timeline for potential rate changes
    - Comparing different time horizons (more meetings = higher uncertainty)
    - Assessing whether market expectations are realistic given meeting schedule
    
    Example: If analyzing SFRZ6 (SOFR Dec 2026) from Oct 2024 to Dec 2026,
    this tool tells you how many FOMC meetings will occur in that period.
    
    Args:
        currency: Currency code (USD for FOMC, EUR for ECB, GBP for BoE)
        start_date: Start date in YYYYMMDD format (e.g., '20241018')
        end_date: End date in YYYYMMDD format (e.g., '20261218')
    
    Returns:
        Dict with:
        - num_meetings: Count of meetings in range
        - central_bank: Name of central bank
        - meetings: List of meeting dates (YYYY-MM-DD format)
        - Other metadata
    
    Raises:
        Returns error dict if currency unsupported, dates invalid, or file missing
    """
    try:
        logger.info(
            f"Counting {currency} central bank meetings "
            f"between {start_date} and {end_date}"
        )
        
        result = count_meetings_in_range(currency, start_date, end_date)
        result["success"] = True
        
        logger.info(
            f"Found {result['num_meetings']} meetings for {currency}"
        )
        
        return result
        
    except FileNotFoundError as e:
        logger.error(f"Meeting dates file not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "currency": currency,
            "start_date": start_date,
            "end_date": end_date,
            "suggestion": (
                "Ensure the meeting dates CSV file exists in the data/ directory. "
                f"Expected file: data/{currency.lower()}_meetings.csv"
            )
        }
    
    except ValueError as e:
        logger.error(f"Invalid input for meeting dates: {e}")
        return {
            "success": False,
            "error": str(e),
            "currency": currency,
            "start_date": start_date,
            "end_date": end_date,
            "suggestion": (
                "Check that: (1) currency is USD/EUR/GBP, "
                "(2) dates are in YYYYMMDD format, "
                "(3) start_date <= end_date"
            )
        }
    
    except Exception as e:
        logger.error(f"Unexpected error counting meetings: {e}")
        return {
            "success": False,
            "error": str(e),
            "currency": currency,
            "start_date": start_date,
            "end_date": end_date,
            "suggestion": (
                "Check CSV file format (must have 'date' column with YYYY-MM-DD dates). "
                "If problem persists, verify file integrity."
            )
        }
