# core/meeting_dates.py

"""Central bank meeting dates retrieval and analysis."""

import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Mapping currency to CSV file
MEETING_FILES = {
    "USD": {
        "file": "../data/fomc_meetings.csv",
        "central_bank": "Federal Reserve",
        "meeting_type": "FOMC"
    },
    "EUR": {
        "file": "../data/ecb_meetings.csv",
        "central_bank": "European Central Bank",
        "meeting_type": "ECB Governing Council"
    },
    "GBP": {
        "file": "../data/boe_meetings.csv",
        "central_bank": "Bank of England",
        "meeting_type": "MPC"
    }
}


def count_meetings_in_range(
    currency: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Counts central bank meetings between two dates.
    
    Args:
        currency: USD, EUR, or GBP
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
    
    Returns:
        Dict with meeting count and metadata
    
    Raises:
        ValueError: If currency unsupported, file missing, or invalid dates
    """
    # Validate currency
    if currency not in MEETING_FILES:
        raise ValueError(
            f"Unsupported currency: {currency}. "
            f"Supported currencies: {', '.join(MEETING_FILES.keys())}"
        )
    
    meeting_info = MEETING_FILES[currency]
    csv_path = meeting_info["file"]
    
    # Check if file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Meeting dates file not found: {csv_path}. "
            f"Please ensure the CSV file exists with meeting dates."
        )
    
    # Parse dates
    try:
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")
    except ValueError as e:
        raise ValueError(
            f"Invalid date format. Expected YYYYMMDD, got start={start_date}, end={end_date}. "
            f"Error: {e}"
        )
    
    # Validate date range
    if start_dt > end_dt:
        raise ValueError(
            f"Start date ({start_date}) must be before or equal to end date ({end_date})"
        )
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise IOError(
            f"Error reading meeting dates file {csv_path}: {e}. "
            f"Please check file format (expected: CSV with 'date' column)."
        )
    
    # Validate CSV structure
    if 'date' not in df.columns:
        raise ValueError(
            f"Invalid CSV format in {csv_path}. "
            f"Expected column 'date', found columns: {df.columns.tolist()}"
        )
    
    # Parse meeting dates
    try:
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        raise ValueError(
            f"Error parsing dates in {csv_path}: {e}. "
            f"Expected date format: YYYY-MM-DD"
        )
    
    # Filter meetings in range
    mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
    meetings_in_range = df[mask].sort_values('date')
    
    num_meetings = len(meetings_in_range)
    
    # Format meeting dates for output
    meeting_dates = [
        dt.strftime("%Y-%m-%d") for dt in meetings_in_range['date']
    ]
    
    logger.info(
        f"Found {num_meetings} {meeting_info['meeting_type']} meetings "
        f"between {start_date} and {end_date}"
    )
    
    return {
        "currency": currency,
        "start_date": start_date,
        "end_date": end_date,
        "num_meetings": num_meetings,
        "central_bank": meeting_info["central_bank"],
        "meeting_type": meeting_info["meeting_type"],
        "meetings": meeting_dates
    }