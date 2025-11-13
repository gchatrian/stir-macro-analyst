# tools/policy_rate_tool.py

"""Policy Rate Tool - Retrieves central bank policy rates."""

import logging
from datetime import datetime
from ..core import get_policy_rate_for_currency

logger = logging.getLogger(__name__)


def get_policy_rate(currency: str) -> dict:
    """
    Retrieves the official central bank policy rate for a currency.
    
    Returns the current policy rate set by:
    - USD: Federal Reserve (FDTR - Federal Funds Target Rate)
    - EUR: European Central Bank (ECB Deposit Facility Rate)
    - GBP: Bank of England (BoE Base Rate)
    
    Use this to understand the current monetary policy stance before analyzing STIR contracts.
    
    Args:
        currency: Currency code (USD, EUR, or GBP)
    
    Returns:
        Dict with policy rate value and metadata
    """
    try:
        logger.info(f"Retrieving policy rate for {currency}")
        
        # Use latest available date (today or most recent business day)
        today = datetime.now().strftime("%Y%m%d")
        
        result = get_policy_rate_for_currency(currency, today)
        result["success"] = True
        
        logger.info(f"Policy rate for {currency}: {result['policy_rate']}%")
        return result
        
    except Exception as e:
        logger.error(f"Error getting policy rate for {currency}: {e}")
        return {
            "success": False,
            "error": str(e)
        }