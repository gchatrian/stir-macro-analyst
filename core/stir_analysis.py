# core/stir_analysis.py

"""Complete STIR analysis orchestration."""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Any
from .contracts import normalize_ticker, infer_currency
from .market_data import (
    get_futures_settlement,
    get_option_chain_filtered,
    get_option_settlements,
    get_discount_curve
)
from .rates_engine import interpolate_discount_rate
from .sabr_calibration import calculate_implied_vol, calibrate_sabr
from .rnd_engine import generate_rnd
from .scenarios import compute_scenario_probabilities
from ..infra import (
    BloombergConnection,
    fetch_reference_data,
    BBG_HOST,
    BBG_PORT
)


def analyze_stir_contract(
    contract: str,
    date: str,
    scenarios: Dict[str, Tuple[float, float]],
    min_settlement_price: float = 0.02
) -> Dict[str, Any]:
    """
    Complete STIR analysis: calibrates SABR, generates RND, computes scenario probabilities.
    
    Args:
        contract: Futures ticker (e.g., 'SFRZ6', 'ERH5')
        date: Analysis date in YYYYMMDD format
        scenarios: Dict of {scenario_name: (min_rate, max_rate)}
        min_settlement_price: Minimum option settlement to include
    
    Returns:
        Dict with complete analysis results
    """
    # Normalize and infer currency
    normalized_ticker = normalize_ticker(contract)
    currency = infer_currency(normalized_ticker)
    
    # Get futures settlement
    fut_data = get_futures_settlement(normalized_ticker, date)
    fut_settle = fut_data["settlement_price"]
    forward_rate = 100 - fut_settle
    
    # Get option chain (OTM only)
    option_tickers = get_option_chain_filtered(normalized_ticker, fut_settle, min_settlement_price)
    
    if len(option_tickers) == 0:
        raise ValueError(f"No options found for {contract} on {date}")
    
    # Get option settlements
    opt_df = get_option_settlements(option_tickers, date)
    opt_df = opt_df[opt_df['SETTLEMENT'] >= min_settlement_price]
    
    if len(opt_df) < 5:
        raise ValueError(f"Insufficient options: only {len(opt_df)} with settlement >= {min_settlement_price}")
    
    # Get discount curve
    curve_df = get_discount_curve(currency, date)
    
    # Get option expiry
    with BloombergConnection(BBG_HOST, BBG_PORT) as conn:
        exp_df = fetch_reference_data(conn, [option_tickers[0]], ["OPT_EXPIRE_DT"])
    
    expiry_str = exp_df.iloc[0]["OPT_EXPIRE_DT"]
    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
    date_obj = datetime.strptime(date, "%Y%m%d").date()
    dte = (expiry_date - date_obj).days
    tau = dte / 365.0
    
    # Interpolate discount rate
    rfr = interpolate_discount_rate(curve_df, dte) / 100
    
    # Calculate implied volatilities
    implied_vols = []
    for _, row in opt_df.iterrows():
        iv = calculate_implied_vol(
            row['SETTLEMENT'],
            fut_settle,
            row['STRIKE'],
            tau,
            rfr,
            row['OPTION_TYPE']
        )
        implied_vols.append(iv)
    
    opt_df['IVOL'] = implied_vols
    opt_df = opt_df[opt_df['IVOL'] > 0]
    
    if len(opt_df) < 5:
        raise ValueError("Insufficient options after IV calculation")
    
    # Calibrate SABR
    sabr_params = calibrate_sabr(
        fut_settle,
        opt_df['STRIKE'].tolist(),
        opt_df['IVOL'].tolist(),
        tau,
        rfr
    )
    
    # Generate RND in price space
    all_rates = [r for scenario_range in scenarios.values() for r in scenario_range]
    min_rate = min(all_rates)
    max_rate = max(all_rates)
    
    min_price_strike = 100 - max_rate
    max_price_strike = 100 - min_rate
    
    strikes_price, density = generate_rnd(sabr_params, min_price_strike, max_price_strike)
    
    # Convert strikes from price space to rate space
    strikes_rate = 100 - strikes_price
    strikes_rate = np.flip(strikes_rate)
    density = np.flip(density)
    
    # Compute scenario probabilities
    probabilities = compute_scenario_probabilities(strikes_rate, density, scenarios)
    probabilities_pct = {k: v * 100 for k, v in probabilities.items()}
    
    return {
        "success": True,
        "contract": normalized_ticker,
        "currency": currency,
        "date": date,
        "futures_settlement": fut_settle,
        "forward_rate": forward_rate,
        "sabr_parameters": {
            "alpha": sabr_params.alpha,
            "rho": sabr_params.rho,
            "volvol": sabr_params.volvol,
            "beta": sabr_params.beta,
            "atm_vol": sabr_params.atm_vol,
            "tau": sabr_params.tau,
            "rfr": sabr_params.rfr
        },
        "rnd_data": {
            "strikes": strikes_rate.tolist(),
            "density": density.tolist()
        },
        "scenarios": scenarios,
        "scenario_probabilities": probabilities,
        "scenario_probabilities_pct": probabilities_pct,
        "num_options_used": len(opt_df)
    }