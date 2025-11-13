# tools/plot_rnd_tool.py

"""Plot RND Tool - Visualization of Risk Neutral Densities."""

import logging
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def plot_rnd_with_scenarios(
    rnd_strikes: List[float],
    rnd_density: List[float],
    scenarios: Dict[str, List[float]],
    forward_rate: float,
    date: str,
    title: str = "Risk Neutral Density"
) -> Dict[str, Any]:
    """
    Creates a visualization of Risk Neutral Density with colored scenario regions.
    
    The chart shows:
    - RND curve (probability density over rate range)
    - Vertical line for implied forward rate
    - Colored shaded regions for each scenario
    - Grid and labels
    
    Use this to visualize a single date's market expectations.
    
    Args:
        rnd_strikes: Array of rate values (x-axis)
        rnd_density: Array of probability densities (y-axis)
        scenarios: Dict of scenario names to [min_rate, max_rate]
        forward_rate: Implied forward rate from futures contract
        date: Date of analysis snapshot
        title: Chart title (optional, default: "Risk Neutral Density")
    
    Returns:
        Dict with base64 encoded PNG image
    """
    try:
        logger.info(f"Creating RND chart for {date}")
        
        x = np.array(rnd_strikes)
        y = np.array(rnd_density)
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Plot RND
        ax.plot(x, y, 'b-', linewidth=2.5, label=f'{date} RND', zorder=3)
        
        # Plot forward rate
        ax.axvline(forward_rate, color='darkblue', linestyle='--', linewidth=2, 
                   alpha=0.8, label=f'Forward Rate: {forward_rate:.2f}%', zorder=4)
        
        # Plot scenario regions
        colors = ['#ff9999', '#ffcc99', '#99ff99', '#99ccff', '#cc99ff']
        for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
            min_r, max_r = rate_range[0], rate_range[1]
            color = colors[idx % len(colors)]
            ax.axvspan(min_r, max_r, alpha=0.25, color=color, 
                      label=scenario_name, zorder=1)
        
        # Formatting
        ax.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
        ax.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
        ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
        ax.grid(True, alpha=0.3, linestyle='--', zorder=0)
        ax.set_xlim(x.min(), x.max())
        
        # Save to bytes
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        buf.seek(0)
        image_bytes = buf.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info("Chart created successfully")
        return {
            "success": True,
            "image_base64": image_base64,
            "image_format": "png"
        }
        
    except Exception as e:
        logger.error(f"Error creating RND chart: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def plot_rnd_comparison(
    rnd_data_1: Dict[str, Any],
    rnd_data_2: Dict[str, Any],
    scenarios: Dict[str, List[float]],
    title: str = "RND Comparison"
) -> Dict[str, Any]:
    """
    Creates a comparison chart of two RNDs (e.g., start date vs end date).
    
    Shows how market expectations evolved between two dates:
    - Two RND curves overlaid
    - Forward rates for both dates
    - Common scenario regions for reference
    
    Use this to compare two analysis snapshots.
    
    Args:
        rnd_data_1: First RND data with keys: strikes, density, forward_rate, date
        rnd_data_2: Second RND data with same structure
        scenarios: Dict of scenario names to [min_rate, max_rate]
        title: Chart title (optional, default: "RND Comparison")
    
    Returns:
        Dict with base64 encoded PNG image
    """
    try:
        logger.info(f"Creating RND comparison chart")
        
        x1 = np.array(rnd_data_1["strikes"])
        y1 = np.array(rnd_data_1["density"])
        fwd1 = rnd_data_1["forward_rate"]
        date1 = rnd_data_1["date"]
        
        x2 = np.array(rnd_data_2["strikes"])
        y2 = np.array(rnd_data_2["density"])
        fwd2 = rnd_data_2["forward_rate"]
        date2 = rnd_data_2["date"]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot RNDs
        ax.plot(x1, y1, 'k--', linewidth=2.5, label=f'{date1} RND', zorder=3)
        ax.plot(x2, y2, 'r-', linewidth=2.5, label=f'{date2} RND', zorder=3)
        
        # Plot forward rates
        ax.axvline(fwd1, color='black', linestyle=':', linewidth=2,
                   alpha=0.7, label=f'{date1} Forward: {fwd1:.2f}%', zorder=4)
        ax.axvline(fwd2, color='red', linestyle=':', linewidth=2,
                   alpha=0.7, label=f'{date2} Forward: {fwd2:.2f}%', zorder=4)
        
        # Plot scenario regions
        colors = ['#ff9999', '#ffcc99', '#99ff99', '#99ccff', '#cc99ff']
        for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
            min_r, max_r = rate_range[0], rate_range[1]
            color = colors[idx % len(colors)]
            ax.axvspan(min_r, max_r, alpha=0.25, color=color,
                      label=scenario_name, zorder=1)
        
        # Formatting
        ax.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
        ax.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
        ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        ax.legend(loc='upper right', fontsize=9, framealpha=0.95, ncol=2)
        ax.grid(True, alpha=0.3, linestyle='--', zorder=0)
        
        # Save to bytes
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        buf.seek(0)
        image_bytes = buf.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info("Comparison chart created successfully")
        return {
            "success": True,
            "image_base64": image_base64,
            "image_format": "png"
        }
        
    except Exception as e:
        logger.error(f"Error creating comparison chart: {e}")
        return {
            "success": False,
            "error": str(e)
        }