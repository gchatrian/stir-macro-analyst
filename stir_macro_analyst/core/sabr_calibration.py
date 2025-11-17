# core/sabr_calibration.py

import numpy as np
from py_vollib.black.implied_volatility import implied_volatility
from pysabr import Hagan2002LognormalSABR
from pysabr import black
from scipy.interpolate import CubicSpline
from dataclasses import dataclass
from typing import List


@dataclass
class SABRParameters:
    alpha: float
    rho: float
    volvol: float
    beta: float
    atm_vol: float
    tau: float
    rfr: float
    forward: float


def calculate_implied_vol(
    option_price: float,
    underlying_price: float,
    strike: float,
    tau: float,
    rfr: float,
    option_type: str
) -> float:
    flag = 'c' if option_type == 'call' else 'p'
    
    try:
        iv = implied_volatility(option_price, underlying_price, strike, rfr, tau, flag)
        return iv * 100
    except Exception:
        return 0.0


def calibrate_sabr(
    forward: float,
    strikes: List[float],
    market_vols: List[float],
    tau: float,
    rfr: float,
    beta: float = 0.5
) -> SABRParameters:
    
    strikes_arr = np.array(strikes)
    market_vols_arr = np.array(market_vols)
    
    spl = CubicSpline(strikes_arr, market_vols_arr)
    atm_ln_vol = spl(forward) / 100
    
    atm_n_vol = black.shifted_lognormal_to_normal(
        forward, forward, 0.0, tau, atm_ln_vol
    )
    
    sabr_model = Hagan2002LognormalSABR(f=forward, t=tau, beta=beta)
    alpha, rho, volvol = sabr_model.fit(strikes_arr, market_vols_arr)
    
    return SABRParameters(
        alpha=alpha,
        rho=rho,
        volvol=volvol,
        beta=beta,
        atm_vol=atm_n_vol,
        tau=tau,
        rfr=rfr,
        forward=forward
    )