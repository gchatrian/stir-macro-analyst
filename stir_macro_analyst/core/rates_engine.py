# core/rates_engine.py

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import holidays
import pandas as pd
from scipy.interpolate import CubicSpline
from typing import Union, Tuple

import logging

logger = logging.getLogger(__name__)

def calculate_time_to_expiry(
    start_date: Union[str, date], 
    expiry_date: Union[str, date]
) -> Tuple[int, float]:
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y%m%d").date()
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, "%Y%m%d").date()
    
    delta = expiry_date - start_date
    days = delta.days
    years = days / 365.0
    
    return days, years


def interpolate_discount_rate(curve_df: pd.DataFrame, target_dte: int) -> float:
    if 'DTE' not in curve_df.columns or 'RATE' not in curve_df.columns:
        raise ValueError("curve_df must contain 'DTE' and 'RATE' columns")

    # Pulisci i dati
    df = curve_df.copy()

    # Tieni solo righe con DTE e RATE validi
    df = df.dropna(subset=['DTE', 'RATE'])

    # Converte in numerico (se arrivano come stringhe)
    df['DTE'] = pd.to_numeric(df['DTE'], errors='coerce')
    df['RATE'] = pd.to_numeric(df['RATE'], errors='coerce')
    df = df.dropna(subset=['DTE', 'RATE'])

    # Tieni solo DTE strettamente positivi (o >=0 se vuoi includere oggi)
    df = df[df['DTE'] > 0]

    # Aggrega eventuali duplicati sulla stessa DTE (media dei RATE o first, scegli tu)
    df = (
        df.groupby('DTE', as_index=False)['RATE']
        .mean()             # puoi usare .first() se preferisci
        .sort_values('DTE')
    )

    # Serve almeno 2 punti per una spline sensata
    if len(df) < 2:
        raise ValueError(f"Not enough points to build curve after cleaning: {len(df)} rows")

    # Boundaries: se target fuori range, clamp ai bordi
    dte_min = df['DTE'].min()
    dte_max = df['DTE'].max()

    if target_dte <= dte_min:
        return float(df.iloc[0]['RATE'])
    if target_dte >= dte_max:
        return float(df.iloc[-1]['RATE'])

    logger.info("Siamo in interpolate_discount_rate (clean curve)")
    x = df['DTE'].values
    y = df['RATE'].values

    # Ora x è strettamente crescente e senza duplicati
    spl = CubicSpline(x, y)

    return float(spl(target_dte))



def add_months_and_ensure_business_day(
    start_date: date, 
    months: int, 
    country_code: str
) -> date:
    country_holidays = holidays.country_holidays(country_code)
    new_date = start_date + relativedelta(months=months)
    
    while new_date.weekday() >= 5 or new_date in country_holidays:
        if new_date.weekday() == 5:
            new_date += relativedelta(days=2)
        elif new_date.weekday() == 6:
            new_date += relativedelta(days=1)
        else:
            new_date += relativedelta(days=1)
    
    return new_date


def add_weeks_and_ensure_business_day(
    start_date: date, 
    weeks: int, 
    country_code: str
) -> date:
    country_holidays = holidays.country_holidays(country_code)
    new_date = start_date + relativedelta(weeks=weeks)
    
    while new_date.weekday() >= 5 or new_date in country_holidays:
        if new_date.weekday() == 5:
            new_date += relativedelta(days=2)
        elif new_date.weekday() == 6:
            new_date += relativedelta(days=1)
        else:
            new_date += relativedelta(days=1)
    
    return new_date


def get_rate_tenor(ccy: str, curve_ticker: str, date_ref: date) -> date:
    country_map = {"USD": "US", "EUR": "DE", "GBP": "GB"}
    country = country_map.get(ccy)
    
    if not country:
        raise ValueError(f"Unsupported currency: {ccy}")
    
    tenor_map = {
        "1Z": ("weeks", 1), "2Z": ("weeks", 2), "3Z": ("weeks", 3),
        "A": ("months", 1), "B": ("months", 2), "C": ("months", 3),
        "D": ("months", 4), "E": ("months", 5), "F": ("months", 6),
        "G": ("months", 7), "H": ("months", 8), "I": ("months", 9),
        "J": ("months", 10), "K": ("months", 11), "1": ("months", 12),
        "1F": ("months", 18), "2": ("months", 24), "3": ("months", 36)
    }
    
    for suffix, (period_type, period_value) in tenor_map.items():
        if curve_ticker.endswith(f"{suffix} BGN CURNCY"):
            if period_type == "weeks":
                return add_weeks_and_ensure_business_day(date_ref, period_value, country)
            else:
                return add_months_and_ensure_business_day(date_ref, period_value, country)
    
    raise ValueError(f"Cannot parse tenor from {curve_ticker}")