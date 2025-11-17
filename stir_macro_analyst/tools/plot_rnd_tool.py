# tools/plot_rnd_tool.py

import logging
from io import BytesIO
from typing import Dict, List, Any, Optional

import matplotlib.pyplot as plt
import numpy as np
from google.adk.tools import ToolContext
from google.genai.types import Part, Blob

logger = logging.getLogger(__name__)


def _extract_rnd_components(rnd_analysis: Dict[str, Any], label: str):
    """
    Extract strikes, density, forward_rate and date from a full STIR analysis result.

    Expected structure (output of analyze_stir_scenarios / analyze_stir_contract):
        {
            "success": True,
            "date": "YYYYMMDD",
            "forward_rate": float,
            "rnd_data": {
                "strikes": [...],
                "density": [...]
            },
            ...
        }
    """
    if not rnd_analysis.get("success", True):
        raise ValueError(f"{label}: analysis success flag is False: {rnd_analysis.get('error')}")

    # Log keys to help debugging if things go wrong
    logger.debug(f"{label} keys: {list(rnd_analysis.keys())}")

    required_top = {"date", "forward_rate", "rnd_data"}
    missing_top = required_top - set(rnd_analysis.keys())
    if missing_top:
        raise KeyError(f"{label}: missing top-level keys {missing_top}")

    rnd_block = rnd_analysis["rnd_data"]
    if not isinstance(rnd_block, dict):
        raise TypeError(f"{label}: 'rnd_data' must be a dict, got {type(rnd_block)}")

    required_rnd = {"strikes", "density"}
    missing_rnd = required_rnd - set(rnd_block.keys())
    if missing_rnd:
        raise KeyError(f"{label}: 'rnd_data' missing keys {missing_rnd}")

    x = np.array(rnd_block["strikes"], dtype=float)
    y = np.array(rnd_block["density"], dtype=float)
    fwd = float(rnd_analysis["forward_rate"])
    date = str(rnd_analysis["date"])

    return x, y, fwd, date


async def plot_rnd_analysis(
    state_key_1: str,
    scenarios: Dict[str, List[float]],
    tool_context: ToolContext,
    state_key_2: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates RND visualization with 1 or 3 charts depending on whether comparison is requested.

    This tool expects that analyze_stir_scenarios has been called at least once and the results
    are stored in session state. The state keys are returned by analyze_stir_scenarios
    in the format: "stir_analysis_<contract>_<date>"

    **Single-Date Mode (state_key_2 = None):**
    - Generates 1 chart showing RND for the specified date with scenario bands
    
    **Two-Date Comparison Mode (state_key_2 provided):**
    - Generates 3 charts:
      1. RND for first date with scenario bands
      2. RND for second date with scenario bands  
      3. Comparison overlay of both RNDs

    Args:
        state_key_1: Session state key for first/only analysis (e.g., "stir_analysis_SFRZ6_20241018")
        scenarios: Dict mapping scenario names to [min_rate, max_rate] ranges
        tool_context: ADK context (auto-injected, provides access to session state)
        state_key_2: Optional session state key for second analysis (for comparisons)

    Returns:
        Dict with success status, artifact filenames, and message

    Example workflows:
        
        Single-date analysis:
        1. User asks for one date
        2. Agent calls analyze_stir_scenarios for that date → receives result with state_key
        3. Agent calls plot_rnd_analysis(state_key, scenarios, tool_context)
        4. One chart is generated
        
        Two-date comparison:
        1. User asks to compare two dates
        2. Agent calls analyze_stir_scenarios for date1 → receives result with state_key_1
        3. Agent calls analyze_stir_scenarios for date2 → receives result with state_key_2
        4. Agent calls plot_rnd_analysis(state_key_1, scenarios, tool_context, state_key_2)
        5. Three charts are generated
    """
    try:
        # Retrieve first analysis from session state
        logger.info(f"Retrieving analysis from state key: {state_key_1}")
        
        rnd_data_1 = tool_context.state.get(state_key_1)
        
        if rnd_data_1 is None:
            return {
                "success": False,
                "error": f"No analysis found in session state for key: {state_key_1}",
                "suggestion": "Ensure analyze_stir_scenarios was called first for this date"
            }
        
        # Extract RND components for first date
        x1, y1, fwd1, date1 = _extract_rnd_components(rnd_data_1, label="rnd_data_1")
        
        # Determine mode: single-date or comparison
        is_comparison = (state_key_2 is not None)
        
        colors = ['#ff9999', '#ffcc99', '#99ff99', '#99ccff', '#cc99ff']
        artifacts_saved: List[str] = []

        if is_comparison:
            # ============= TWO-DATE COMPARISON MODE =============
            logger.info(f"Retrieving second analysis from state key: {state_key_2}")
            
            rnd_data_2 = tool_context.state.get(state_key_2)
            
            if rnd_data_2 is None:
                return {
                    "success": False,
                    "error": f"No analysis found in session state for key: {state_key_2}",
                    "suggestion": "Ensure analyze_stir_scenarios was called first for this date"
                }
            
            # Extract RND components for second date
            x2, y2, fwd2, date2 = _extract_rnd_components(rnd_data_2, label="rnd_data_2")
            
            logger.info(f"Creating RND comparison charts for {date1} vs {date2}")

            # ===== CHART 1: First Date RND =====
            fig1, ax1 = plt.subplots(figsize=(12, 7))
            ax1.plot(x1, y1, 'b-', linewidth=2.5, label=f'{date1} RND', zorder=3)
            ax1.axvline(
                fwd1,
                color='darkblue',
                linestyle='--',
                linewidth=2,
                alpha=0.8,
                label=f'Forward Rate: {fwd1:.2f}%',
                zorder=4,
            )
            for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
                min_r, max_r = rate_range
                color = colors[idx % len(colors)]
                ax1.axvspan(
                    min_r,
                    max_r,
                    alpha=0.25,
                    color=color,
                    label=scenario_name,
                    zorder=1,
                )
            ax1.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
            ax1.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
            ax1.set_title(
                f'Risk Neutral Density - {date1}',
                fontsize=15,
                fontweight='bold',
                pad=20,
            )
            ax1.legend(loc='upper right', fontsize=10, framealpha=0.95)
            ax1.grid(True, alpha=0.3, linestyle='--', zorder=0)
            ax1.set_xlim(x1.min(), x1.max())

            buf1 = BytesIO()
            plt.tight_layout()
            fig1.savefig(buf1, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig1)
            buf1.seek(0)
            artifact1 = Part(
                inline_data=Blob(
                    data=buf1.read(),
                    mime_type="image/png",
                )
            )
            filename1 = f"rnd_{date1}.png"
            await tool_context.save_artifact(filename1, artifact1)
            artifacts_saved.append(filename1)
            logger.info(f"Saved artifact: {filename1}")

            # ===== CHART 2: Second Date RND =====
            fig2, ax2 = plt.subplots(figsize=(12, 7))
            ax2.plot(x2, y2, 'r-', linewidth=2.5, label=f'{date2} RND', zorder=3)
            ax2.axvline(
                fwd2,
                color='darkred',
                linestyle='--',
                linewidth=2,
                alpha=0.8,
                label=f'Forward Rate: {fwd2:.2f}%',
                zorder=4,
            )
            for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
                min_r, max_r = rate_range
                color = colors[idx % len(colors)]
                ax2.axvspan(
                    min_r,
                    max_r,
                    alpha=0.25,
                    color=color,
                    label=scenario_name,
                    zorder=1,
                )
            ax2.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
            ax2.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
            ax2.set_title(
                f'Risk Neutral Density - {date2}',
                fontsize=15,
                fontweight='bold',
                pad=20,
            )
            ax2.legend(loc='upper right', fontsize=10, framealpha=0.95)
            ax2.grid(True, alpha=0.3, linestyle='--', zorder=0)
            ax2.set_xlim(x2.min(), x2.max())

            buf2 = BytesIO()
            plt.tight_layout()
            fig2.savefig(buf2, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig2)
            buf2.seek(0)
            artifact2 = Part(
                inline_data=Blob(
                    data=buf2.read(),
                    mime_type="image/png",
                )
            )
            filename2 = f"rnd_{date2}.png"
            await tool_context.save_artifact(filename2, artifact2)
            artifacts_saved.append(filename2)
            logger.info(f"Saved artifact: {filename2}")

            # ===== CHART 3: Comparison =====
            fig3, ax3 = plt.subplots(figsize=(14, 8))
            ax3.plot(x1, y1, 'k--', linewidth=2.5, label=f'{date1} RND', zorder=3)
            ax3.plot(x2, y2, 'r-', linewidth=2.5, label=f'{date2} RND', zorder=3)
            ax3.axvline(
                fwd1,
                color='black',
                linestyle=':',
                linewidth=2,
                alpha=0.7,
                label=f'{date1} Forward: {fwd1:.2f}%',
                zorder=4,
            )
            ax3.axvline(
                fwd2,
                color='red',
                linestyle=':',
                linewidth=2,
                alpha=0.7,
                label=f'{date2} Forward: {fwd2:.2f}%',
                zorder=4,
            )
            for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
                min_r, max_r = rate_range
                color = colors[idx % len(colors)]
                ax3.axvspan(
                    min_r,
                    max_r,
                    alpha=0.25,
                    color=color,
                    label=scenario_name,
                    zorder=1,
                )
            ax3.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
            ax3.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
            ax3.set_title(
                f'RND Comparison: {date1} vs {date2}',
                fontsize=15,
                fontweight='bold',
                pad=20,
            )
            ax3.legend(loc='upper right', fontsize=9, framealpha=0.95, ncol=2)
            ax3.grid(True, alpha=0.3, linestyle='--', zorder=0)

            buf3 = BytesIO()
            plt.tight_layout()
            fig3.savefig(buf3, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig3)
            buf3.seek(0)
            artifact3 = Part(
                inline_data=Blob(
                    data=buf3.read(),
                    mime_type="image/png",
                )
            )
            filename3 = f"rnd_comparison_{date1}_vs_{date2}.png"
            await tool_context.save_artifact(filename3, artifact3)
            artifacts_saved.append(filename3)
            logger.info(f"Saved artifact: {filename3}")

            logger.info("All RND charts created successfully")
            return {
                "success": True,
                "mode": "comparison",
                "artifacts_saved": artifacts_saved,
                "message": (
                    f"Generated 3 charts: individual RNDs for {date1} and {date2}, "
                    f"plus comparison chart"
                ),
                "chart_1": filename1,
                "chart_2": filename2,
                "chart_3": filename3,
            }
        
        else:
            # ============= SINGLE-DATE MODE =============
            logger.info(f"Creating single-date RND chart for {date1}")
            
            # ===== SINGLE CHART: RND with Scenarios =====
            fig, ax = plt.subplots(figsize=(12, 7))
            ax.plot(x1, y1, 'b-', linewidth=2.5, label=f'{date1} RND', zorder=3)
            ax.axvline(
                fwd1,
                color='darkblue',
                linestyle='--',
                linewidth=2,
                alpha=0.8,
                label=f'Forward Rate: {fwd1:.2f}%',
                zorder=4,
            )
            for idx, (scenario_name, rate_range) in enumerate(scenarios.items()):
                min_r, max_r = rate_range
                color = colors[idx % len(colors)]
                ax.axvspan(
                    min_r,
                    max_r,
                    alpha=0.25,
                    color=color,
                    label=scenario_name,
                    zorder=1,
                )
            ax.set_xlabel('Rate (%)', fontsize=13, fontweight='bold')
            ax.set_ylabel('Probability Density', fontsize=13, fontweight='bold')
            ax.set_title(
                f'Risk Neutral Density - {date1}',
                fontsize=15,
                fontweight='bold',
                pad=20,
            )
            ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
            ax.grid(True, alpha=0.3, linestyle='--', zorder=0)
            ax.set_xlim(x1.min(), x1.max())

            buf = BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            buf.seek(0)
            artifact = Part(
                inline_data=Blob(
                    data=buf.read(),
                    mime_type="image/png",
                )
            )
            filename = f"rnd_{date1}.png"
            await tool_context.save_artifact(filename, artifact)
            artifacts_saved.append(filename)
            logger.info(f"Saved artifact: {filename}")

            logger.info("Single-date RND chart created successfully")
            return {
                "success": True,
                "mode": "single_date",
                "artifacts_saved": artifacts_saved,
                "message": f"Generated RND visualization for {date1}",
                "chart": filename,
            }

    except KeyError as e:
        logger.error(f"Missing data in analysis results: {e}")
        return {
            "success": False,
            "error": f"Missing required data: {str(e)}",
            "message": "Analysis results incomplete. Ensure analyze_stir_scenarios completed successfully."
        }
    
    except Exception as e:
        logger.error(f"Error creating RND charts: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate RND visualization charts",
        }