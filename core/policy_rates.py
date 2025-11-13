
# core/policy_rates.py
import logging
logger = logging.getLogger(__name__)


"""Policy rate retrieval logic."""

from typing import Dict, Any
from ..infra import (
    BloombergConnection,
    fetch_historical_data,
    POLICY_RATE_MAPPING,
    BBG_HOST,
    BBG_PORT
)


def get_policy_rate_for_currency(currency: str, date: str) -> Dict[str, Any]:
    """
    Retrieves policy rate for a currency on a specific date.
    
    Args:
        currency: USD, EUR, or GBP
        date: Date in YYYYMMDD format
    
    Returns:
        Dict with rate value and metadata
    """
    if currency not in POLICY_RATE_MAPPING:
        raise ValueError(f"Unsupported currency: {currency}")
    
    rate_info = POLICY_RATE_MAPPING[currency]
    logger.info(f"In policy_rates: Retrieving policy rate for {rate_info} on {date}")

    with BloombergConnection(BBG_HOST, BBG_PORT) as conn:
        df = fetch_historical_data(
            conn,
            rate_info["ticker"],
            "PX_LAST",
            date,
            date
        )
    
    if df.empty or df.iloc[0]["PX_LAST"] is None:
        raise ValueError(f"No policy rate data for {currency} on {date}")
    
    return {
        "currency": currency,
        "date": date,
        "policy_rate": float(df.iloc[0]["PX_LAST"]),
        "ticker": rate_info["ticker"],
        "rate_name": rate_info["name"],
        "central_bank": rate_info["central_bank"]
    }