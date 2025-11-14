# tools/plot_rnd_tool.py

"""Plot RND Tool - Visualization of Risk Neutral Densities."""

import logging
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from typing import Dict, List, Any
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


async def plot_rnd_analysis(
    rnd_data_1: Dict[str, Any],
    rnd_data_2: Dict[str, Any],
    scenarios: Dict[str, List[float]],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Creates comprehensive RND visualization with 3 charts:
    1. First date RND with colored scenario regions
    2. Second date RND with colored scenario regions  
    3. Comparison chart with both RNDs overlaid
    
    All charts are saved as artifacts in ADK and will be displayed automatically in the UI.
    
    Use this tool when analyzing STIR contracts across two dates to visualize:
    - How market expectations (RND shape) evolved between dates
    - Which rate scenarios gained/lost probability
    - Changes in implied forward rates
    
    Args:
        rnd_data_1: First RND with keys:
            - strikes: List[float] (rate values)
            - density: List[float] (probability densities)
            - forward_rate: float (implied forward rate)
            - date: str (YYYYMMDD)
        rnd_data_2: Second RND with same structure
        scenarios: Dict of scenario names to [min_rate, max_rate]
            Example: {"Deep Cut": [0.0, 2.5], "Neutral": [3.5, 4.5]}
        tool_context: ADK context for saving artifacts (automatically provided)
    
    Returns:
        Dict with:
        - success: bool
        - artifacts_saved: List[str] (filenames of saved charts)
        - message: str (summary)
    
    Example:
        result = await plot_rnd_analysis(
            rnd_data_1={"strikes": [...], "density": [...], "forward_rate": 4.12, "date": "20241018"},
            rnd_data_2={"strikes": [...], "density": [...], "forward_rate": 3.45, "date": "20250212"},
            scenarios={"Cut": [0, 3.5], "Neutral": [3.5, 4.5], "Hike": [4.5, 8]},
            tool_context=tool_context
        )
    """
    try:
        logger.info(f"Creating RND analysis charts for {rnd_data_1['date']} vs {rnd_data_2['date']}")
        
        # Extract data
        x1 = np.array(rnd_data_1["strikes"])
        y1 = np.array(rnd_data_1["density"])
        fwd1 = rnd_data_1["forward_rate"]
        date1 = rnd_data_1["date"]
        
        x2 = np.array(rnd_data_2["strikes"])
        y2 = np.array(rnd_data_2["density"])
        fwd2 = rnd_data_2["forward_rate"]
        date2 = rnd_data_2["date"]
        
        # Scenario colors
        colors = ['#ff9999', '#ffcc99', '#99ff99', '#99ccff', '#cc99ff']
        
        artifacts_saved = []
        
        # ===== CHART 1: First Date RND =====
        fig1, ax1 = plt.subplots(figsize=(12, 7))
        
        # Plot RND
        ax1.plot(x1, y1, 'b-', linewidth=2.5, label=f'{date1} RND', zorder=3)
        
        # Plot forward rate
        ax1.axvline(fwd1, color='darkblue', linestyle='--', linewidth=2, 
                   alpha=0.8, label=f'Forward Rate: {fwd1:.2f}%', zorder=4)
        
        # Plot scenario regions
        for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
            min_r, max_r = rate_range[0], rate_range[1]
            color = colors[idx % len(colors)]
            ax1.axvspan(min_r, max_r, alpha=0.25, color=color, 
                       label=scenario_name, zorder=1)
        
        # Formatting
        ax1.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
        ax1.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
        ax1.set_title(f'Risk Neutral Density - {date1}', fontsize=15, fontweight='bold', pad=20)
        ax1.legend(loc='upper right', fontsize=10, framealpha=0.95)
        ax1.grid(True, alpha=0.3, linestyle='--', zorder=0)
        ax1.set_xlim(x1.min(), x1.max())
        
        # Save to bytes
        buf1 = BytesIO()
        plt.tight_layout()
        plt.savefig(buf1, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Save as artifact
        buf1.seek(0)
        image_bytes_1 = buf1.read()
        filename1 = f"rnd_{date1}.png"
        await tool_context.save_artifact(filename1, image_bytes_1)
        artifacts_saved.append(filename1)
        logger.info(f"Saved artifact: {filename1}")
        
        
        # ===== CHART 2: Second Date RND =====
        fig2, ax2 = plt.subplots(figsize=(12, 7))
        
        # Plot RND
        ax2.plot(x2, y2, 'r-', linewidth=2.5, label=f'{date2} RND', zorder=3)
        
        # Plot forward rate
        ax2.axvline(fwd2, color='darkred', linestyle='--', linewidth=2, 
                   alpha=0.8, label=f'Forward Rate: {fwd2:.2f}%', zorder=4)
        
        # Plot scenario regions
        for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
            min_r, max_r = rate_range[0], rate_range[1]
            color = colors[idx % len(colors)]
            ax2.axvspan(min_r, max_r, alpha=0.25, color=color, 
                       label=scenario_name, zorder=1)
        
        # Formatting
        ax2.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
        ax2.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
        ax2.set_title(f'Risk Neutral Density - {date2}', fontsize=15, fontweight='bold', pad=20)
        ax2.legend(loc='upper right', fontsize=10, framealpha=0.95)
        ax2.grid(True, alpha=0.3, linestyle='--', zorder=0)
        ax2.set_xlim(x2.min(), x2.max())
        
        # Save to bytes
        buf2 = BytesIO()
        plt.tight_layout()
        plt.savefig(buf2, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Save as artifact
        buf2.seek(0)
        image_bytes_2 = buf2.read()
        filename2 = f"rnd_{date2}.png"
        await tool_context.save_artifact(filename2, image_bytes_2)
        artifacts_saved.append(filename2)
        logger.info(f"Saved artifact: {filename2}")
        
        
        # ===== CHART 3: Comparison =====
        fig3, ax3 = plt.subplots(figsize=(14, 8))
        
        # Plot RNDs
        ax3.plot(x1, y1, 'k--', linewidth=2.5, label=f'{date1} RND', zorder=3)
        ax3.plot(x2, y2, 'r-', linewidth=2.5, label=f'{date2} RND', zorder=3)
        
        # Plot forward rates
        ax3.axvline(fwd1, color='black', linestyle=':', linewidth=2,
                   alpha=0.7, label=f'{date1} Forward: {fwd1:.2f}%', zorder=4)
        ax3.axvline(fwd2, color='red', linestyle=':', linewidth=2,
                   alpha=0.7, label=f'{date2} Forward: {fwd2:.2f}%', zorder=4)
        
        # Plot scenario regions
        for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
            min_r, max_r = rate_range[0], rate_range[1]
            color = colors[idx % len(colors)]
            ax3.axvspan(min_r, max_r, alpha=0.25, color=color,
                       label=scenario_name, zorder=1)
        
        # Formatting
        ax3.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
        ax3.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
        ax3.set_title(f'RND Comparison: {date1} vs {date2}', fontsize=15, fontweight='bold', pad=20)
        ax3.legend(loc='upper right', fontsize=9, framealpha=0.95, ncol=2)
        ax3.grid(True, alpha=0.3, linestyle='--', zorder=0)
        
        # Save to bytes
        buf3 = BytesIO()
        plt.tight_layout()
        plt.savefig(buf3, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Save as artifact
        buf3.seek(0)
        image_bytes_3 = buf3.read()
        filename3 = f"rnd_comparison_{date1}_vs_{date2}.png"
        await tool_context.save_artifact(filename3, image_bytes_3)
        artifacts_saved.append(filename3)
        logger.info(f"Saved artifact: {filename3}")
        
        
        logger.info("All RND charts created successfully")
        return {
            "success": True,
            "artifacts_saved": artifacts_saved,
            "message": f"Generated 3 charts: individual RNDs for {date1} and {date2}, plus comparison chart",
            "chart_1": filename1,
            "chart_2": filename2,
            "chart_3": filename3
        }
        
    except Exception as e:
        logger.error(f"Error creating RND charts: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate RND visualization charts"
        }
