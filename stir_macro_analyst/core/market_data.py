# core/market_data.py

"""High-level market data retrieval."""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from ..infra import (
    BloombergConnection,
    fetch_reference_data,
    fetch_historical_data,
    fetch_option_chain,
    DISCOUNT_CURVE_MAPPING,
    BBG_HOST,
    BBG_PORT
)
from .rates_engine import get_rate_tenor


def get_futures_settlement(ticker: str, date: str) -> Dict[str, Any]:
    """Get futures settlement price for a specific date."""
    with BloombergConnection(BBG_HOST, BBG_PORT) as conn:
        df = fetch_historical_data(conn, ticker, "PX_SETTLE", date, date, "DAILY")
        
        if df.empty:
            raise ValueError(f"No settlement data for {ticker} on {date}")
        
        settlement = float(df.iloc[0]["PX_SETTLE"])
        
        return {
            "ticker": ticker,
            "date": date,
            "settlement_price": settlement,
            "implied_rate": 100 - settlement
        }


def get_option_chain_filtered(
    futures_code: str,
    fut_settlement: float,
    min_settlement: float = 0.02
) -> List[str]:
    """Get filtered OTM option chain."""
    with BloombergConnection(BBG_HOST, BBG_PORT) as conn:
        option_tickers = fetch_option_chain(conn, futures_code)
    
    fcode = futures_code.split()[0]
    asset_class = futures_code.split()[1] if len(futures_code.split()) > 1 else "Comdty"
    
    strike_list = []
    for opt in option_tickers:
        parts = opt.split()
        if len(parts) >= 2:
            try:
                strike = float(parts[1])
                strike_list.append(strike)
            except ValueError:
                continue
    
    strikes = sorted(set(strike_list))
    
    filtered_tickers = []
    for strike in strikes:
        if fut_settlement >= strike:
            filtered_tickers.append(f"{fcode}P {strike} COMB {asset_class}")
        else:
            filtered_tickers.append(f"{fcode}C {strike} COMB {asset_class}")
    
    return filtered_tickers


def get_option_settlements(option_tickers: List[str], date: str) -> pd.DataFrame:
    """Get settlement prices for multiple options."""
    with BloombergConnection(BBG_HOST, BBG_PORT) as conn:
        data = {
            'CODE': [],
            'OPTION_TYPE': [],
            'STRIKE': [],
            'SETTLEMENT': []
        }
        
        for ticker in option_tickers:
            df = fetch_historical_data(conn, ticker, "PX_SETTLE", date, date, "DAILY")
            
            if not df.empty:
                parts = ticker.split()
                option_type = 'call' if parts[0][-1] == 'C' else 'put'
                strike = float(parts[1])
                settlement = float(df.iloc[0]["PX_SETTLE"])
                
                data['CODE'].append(ticker)
                data['OPTION_TYPE'].append(option_type)
                data['STRIKE'].append(strike)
                data['SETTLEMENT'].append(settlement)
        
        return pd.DataFrame(data)


def get_discount_curve(currency: str, date: str) -> pd.DataFrame:
    """Get discount curve for a currency."""
    if currency not in DISCOUNT_CURVE_MAPPING:
        raise ValueError(f"Unsupported currency: {currency}")
    
    curve_tickers = DISCOUNT_CURVE_MAPPING[currency]
    
    with BloombergConnection(BBG_HOST, BBG_PORT) as conn:
        data = {
            'CODE': [],
            'RATE': [],
            'TENOR': [],
            'DTE': []
        }
        
        date_obj = datetime.strptime(date, "%Y%m%d").date()
        
        for ticker in curve_tickers:
            df = fetch_historical_data(conn, ticker, "PX_LAST", date, date, "DAILY")
            
            if not df.empty:
                rate = float(df.iloc[0]["PX_LAST"])
                tenor_date = get_rate_tenor(currency, ticker, date_obj)
                dte = (tenor_date - date_obj).days
                
                data['CODE'].append(ticker)
                data['RATE'].append(rate)
                data['TENOR'].append(tenor_date)
                data['DTE'].append(dte)
        
        return pd.DataFrame(data)