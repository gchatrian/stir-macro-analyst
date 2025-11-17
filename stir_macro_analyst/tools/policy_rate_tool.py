# tools/policy_rate_tool.py
"""Policy Rate Tool - Retrieves central bank policy rates."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..core import get_policy_rate_for_currency

logger = logging.getLogger(__name__)


def _normalize_date(date_str: str) -> str:
    """
    Normalizza varie forme di data in formato YYYYMMDD.

    Accetta cose come:
    - "2025-06-03"
    - "2025/06/03"
    - "June 3rd 2025"
    - "3 Jun 2025"
    """
    from dateutil import parser

    # Già nel formato giusto
    if len(date_str) == 8 and date_str.isdigit():
        return date_str

    dt = parser.parse(date_str)
    return dt.strftime("%Y%m%d")


def get_policy_rate(currency: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Recupera il tasso ufficiale di policy per una valuta.

    - Se `date` è None → usa la data odierna (ultimo dato disponibile).
    - Se `date` è valorizzata → usa quella data (storico).

    Args:
        currency: Codice valuta (USD, EUR, GBP).
        date: Data opzionale in formato YYYYMMDD oppure in formato naturale
              (es. "2025-06-03", "June 3rd 2025").

    Returns:
        Dict con valore del policy rate e metadati.
    """
    try:
        if date is None:
            normalized_date = datetime.now().strftime("%Y%m%d")
            
        else:
            normalized_date = _normalize_date(date)

        logger.info(f"Retrieving policy rate for {currency} on {normalized_date}")

        result = get_policy_rate_for_currency(currency, normalized_date)
        result["success"] = True

        logger.info(
            f"Policy rate for {currency} on {normalized_date}: {result['policy_rate']}%"
        )
        return result

    except Exception as e:
        logger.error(f"Error getting policy rate for {currency} on {date}: {e}")
        return {
            "success": False,
            "error": str(e),
            "currency": currency,
            "date": date,
        }
