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
    """Loads data and runs all analyses for a single session."""
    logger.info(f"===== Starting Analysis for {year} {event} - {session_type} =====")

    session_identifier = config.SESSION_TYPES.get(session_type, session_type) # Get 'R', 'Q' etc.
    session = data_loader.load_session_data(year, event, session_identifier)

    if session is None:
        logger.error(f"Failed to load data for {session_type}. Skipping analysis.")
        return # Stop analysis for this session

    # Prepare session metadata for reporting and plotting
    session_info = {
        "Year": getattr(session.event, 'year', year),
        "EventName": session.event.get('EventName', str(event)), # Use dict.get for safety
        "SessionName": getattr(session, 'name', session_type)
    }
    print(f"\n--- Analysis for {session_info['EventName']} {session_info['SessionName']} ({session_info['Year']}) ---")


    # --- Run Analyses ---
    # 1. Overall Fastest Lap
    overall_fastest = lap_analysis.get_overall_fastest_lap(session)
    if overall_fastest is not None:
        print("\n--- Overall Fastest Lap ---")
        print(f"Driver: {overall_fastest.get(config.COL_DRIVER, 'N/A')} ({overall_fastest.get(config.COL_TEAM, 'N/A')})")
        print(f"Lap Time: {overall_fastest.get('LapTimeStr', 'N/A')}")
        print(f"Lap Number: {int(overall_fastest.get(config.COL_LAP_NUMBER, 0))}")
        print(f"  Sector 1: {overall_fastest.get('Sector1Str', 'N/A')}")
        print(f"  Sector 2: {overall_fastest.get('Sector2Str', 'N/A')}")
        print(f"  Sector 3: {overall_fastest.get('Sector3Str', 'N/A')}")
        print(f"  Compound: {overall_fastest.get(config.COL_COMPOUND, 'N/A')} (Tyre Life: {overall_fastest.get('TyreLifeStr', 'N/A')} laps)")


    # 2. Driver Fastest Laps
    driver_fastest = lap_analysis.get_driver_fastest_laps(session)
    if driver_fastest is not None:
        print(f"\n--- Driver Fastest Laps ({session_info['SessionName']}) ---")
        # Limit printing to top N or use pandas string representation for console
        with pd.option_context('display.max_rows', 10, 'display.width', 100): # Show top 10
             print(driver_fastest[[config.COL_DRIVER, config.COL_TEAM, 'LapTimeStr', config.COL_COMPOUND]].to_string(index=False))
        # Plotting for driver fastest laps
        plot_generator.plot_driver_fastest_lap_deltas(driver_fastest, session_info, session)
    else:
         # Still try plotting if get_practice_pace_comparison is called, as it uses the same func
         if session_identifier in ['FP1', 'FP2', 'FP3']: # Check if it was a practice session
              logger.info(f"No individual driver fastest laps computed, but attempting Practice Pace plot if applicable.")
              # Plotting might still work if the issue was just returning the df but the calc worked internally? Unlikely but possible.
              # Consider calling plot separately based on session type maybe?
              # For now, if df is None, we don't plot.

    # 3. Constructor Race Pace (Only for Race Sessions ideally)
    if session_identifier == config.SESSION_TYPES['R']:
        constructor_pace = pace_analysis.get_constructor_race_pace(session)
        if constructor_pace is not None:
            print("\n--- Constructor Race Pace (Median Lap Time) ---")
            print("Median Lap Time per Constructor (Lower is better):")
            for team, pace_seconds in constructor_pace.items():
                pace_str = formatting.format_timedelta(pd.Timedelta(seconds=pace_seconds))
                print(f"  {team}: {pace_str}")
            # Plotting for constructor pace
            plot_generator.plot_constructor_pace_deltas(constructor_pace, session_info, session)

    # 4. Official Results
    official_results = results_analysis.get_official_results(session)
    if official_results is not None:
         print(f"\n--- Official Results ({session_info['SessionName']}) ---")
         # Use pandas string representation for clean console output
         with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 120):
             print(official_results.to_string(index=False))
    
    # --- Add other analyses as needed ---
    # Example: If it's a practice session, maybe call a specific practice summary
    # if session_identifier in ['FP1', 'FP2', 'FP3']:
    #     get_practice_summary(session) # Assuming such a function exists


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