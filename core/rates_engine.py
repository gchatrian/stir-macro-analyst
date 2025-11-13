# core/rates_engine.py

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import holidays
import pandas as pd
from scipy.interpolate import CubicSpline


def calculate_time_to_expiry(start_date, expiry_date):
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
    
    curve_df = curve_df.sort_values('DTE')
    
    if target_dte <= curve_df['DTE'].min():
        return curve_df.iloc[0]['RATE']
    if target_dte >= curve_df['DTE'].max():
        return curve_df.iloc[-1]['RATE']
    
    spl = CubicSpline(curve_df['DTE'].values, curve_df['RATE'].values)
    return float(spl(target_dte))


def add_months_and_ensure_business_day(start_date, months, country_code):
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


def add_weeks_and_ensure_business_day(start_date, weeks, country_code):
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


def get_rate_tenor(ccy: str, curve_ticker: str, date_ref):
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