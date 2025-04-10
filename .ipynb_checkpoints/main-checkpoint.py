# f1_analysis_dashboard/main.py
import argparse
import logging
import sys
import pandas as pd
from fastf1.ergast.interface import ErgastError
from typing import List, Union, Optional, Dict, Any

# Set up project structure for imports
# Ensure the project root is discoverable if running main.py directly
import os
# project_root = os.path.dirname(os.path.abspath(__file__))
# if project_root not in sys.path:
#      sys.path.insert(0, project_root)
# --> Better approach: Run as a module `python -m f1_analysis_dashboard.main` from parent dir
# Or install the package in editable mode `pip install -e .`

from f1_analysis_dashboard import config
from f1_analysis_dashboard.src import data_loader
from f1_analysis_dashboard.src.analysis import lap_analysis, pace_analysis, results_analysis
from f1_analysis_dashboard.src.plotting import plot_generator
from f1_analysis_dashboard.src.utils import formatting # For printing summaries

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout) # Output logs to console
        # Optionally add FileHandler here
        # logging.FileHandler("f1_analysis.log")
    ]
)
# Silence excessive matplotlib/fastf1 logs if desired
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('fastf1').setLevel(logging.INFO) # Keep FastF1 INFO for loading status

logger = logging.getLogger(__name__) # Get logger for this module

# --- Argument Parsing ---
def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Run F1 Analysis Dashboard tasks.")
    parser.add_argument(
        "-y", "--year", type=int, default=config.DEFAULT_YEAR,
        help=f"Championship year (default: {config.DEFAULT_YEAR})"
    )
    parser.add_argument(
        "-e", "--event", type=str, default=config.DEFAULT_EVENT,
        help=f"Event name, city, or round number (default: '{config.DEFAULT_EVENT}')"
    )
    parser.add_argument(
        "-s", "--sessions", nargs='+', default=['R'], # Default to Race only
        choices=config.SESSION_TYPES.keys(),
        help=f"Session types to analyze (e.g., R Q FP1 FP2 FP3). Default: R"
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Disable FastF1 caching for this run."
    )
    parser.add_argument(
        "--show-plots", action="store_true",
        help="Show plots interactively after generation (default: save only)."
    )
    return parser.parse_args()

# --- Main Analysis Orchestration ---
def run_session_analysis(year: int, event: Union[str, int], session_type: str):
    # ... (session loading and info setup) ...

    # --- Run Analyses ---
    # ... (Overall Fastest, Driver Fastest Laps analysis and plotting) ...

    # 3. Race Session Specific Analysis
    if session_identifier == config.SESSION_TYPES['R']:
        # 3a. Constructor Pace
        # --- GET STATS DATAFRAME ---
        constructor_stats = pace_analysis.get_constructor_race_pace(session)
        if constructor_stats is not None:
            print("\n--- Constructor Race Pace (Median Lap Time) ---")
            print("Median Lap Time per Constructor (Lower is better):")
            # --- ACCESS 'median' COLUMN FOR PRINTING ---
            for team, stats_row in constructor_stats.iterrows():
                pace_seconds = stats_row['median'] # Access median value
                lap_count = stats_row['count'] # Get count for potential logging/printing
                pace_str = formatting.format_timedelta(pd.Timedelta(seconds=pace_seconds))
                # Optional: Add count to print statement
                print(f"  {team}: {pace_str} (from {lap_count} laps)")
            # --- PASS THE WHOLE DATAFRAME TO PLOTTING ---
            plot_generator.plot_constructor_pace_deltas(constructor_stats, session_info, session)

        # 3b. Driver Pace Distribution (remains the same)
        driver_laps = pace_analysis.get_driver_race_laps(session)
        # ... (rest of driver pace plotting) ...

    # 4. Official Results (remains the same)
    official_results = results_analysis.get_official_results(session)
    # ... (rest of results printing) ...

    logger.info(f"===== Finished Analysis for {year} {event} - {session_type} =====")


def main():
    """Main entry point for the F1 Analysis script."""
    args = parse_arguments()
    logger.info("Starting F1 Analysis Dashboard script...")
    logger.info(f"Arguments: Year={args.year}, Event='{args.event}', Sessions={args.sessions}")

    # --- Apply settings from arguments ---
    if args.no_cache:
        config.CACHE_ENABLED = False
        logger.info("Cache explicitly disabled via command line.")
    config.PLOT_SHOW = args.show_plots
    if config.PLOT_SHOW:
         logger.info("Interactive plot display enabled.")

    # --- Setup ---
    plot_generator.setup_plotting_style()

    # --- Run Analysis for each requested session ---
    for session_type in args.sessions:
        run_session_analysis(args.year, args.event, session_type)

    logger.info("--- Analysis Complete ---")
    if config.PLOT_SAVE:
        logger.info(f"Plots saved to: {config.OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    # This allows running the script directly using `python main.py`
    # For proper package structure, it's better to run as module:
    # `python -m f1_analysis_dashboard.main -y 2023 -e Jeddah -s R Q FP1`
    main()