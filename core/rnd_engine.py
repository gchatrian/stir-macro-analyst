# core/rnd_engine.py

import numpy as np
from pysabr import Hagan2002LognormalSABR, black
from typing import Tuple
from .sabr_calibration import SABRParameters


def generate_rnd(
    sabr_params: SABRParameters,
    min_strike: float,
    max_strike: float,
    grid_points: int = 500
) -> Tuple[np.ndarray, np.ndarray]:
    
    strikes = np.linspace(min_strike, max_strike, grid_points)
    
    bs_calls = []
    for strike in strikes:
        vola = Hagan2002LognormalSABR(
            f=sabr_params.forward,
            shift=0,
            t=sabr_params.tau,
            v_atm_n=sabr_params.atm_vol,
            beta=sabr_params.beta,
            rho=sabr_params.rho,
            volvol=sabr_params.volvol
        ).lognormal_vol(strike)
        
        call_price = black.lognormal_call(
            k=strike,
            f=sabr_params.forward,
            t=sabr_params.tau,
            v=vola,
            r=sabr_params.rfr,
            cp='call'
        )
        bs_calls.append(call_price)
    
    first_grad = np.gradient(bs_calls, strikes)
    second_grad = np.gradient(first_grad, strikes)
    
    rnd = second_grad * np.exp(sabr_params.tau * sabr_params.rfr)
    
    return strikes, rnd