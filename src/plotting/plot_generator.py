# f1_analysis_dashboard/src/plotting/plot_generator.py
import pandas as pd
import matplotlib.pyplot as plt
import fastf1 as ff1
import fastf1.plotting
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any

from f1_analysis_dashboard.src.utils import formatting
from f1_analysis_dashboard import config

logger = logging.getLogger(__name__)

# Ensure correct timedelta formatting is enabled for plots
try:
    pd.plotting.register_matplotlib_converters()
except Exception as e: # Might be deprecated/changed in future pandas/mpl
    logger.warning(f"Could not register matplotlib converters: {e}")


def setup_plotting_style():
    """Sets up the matplotlib style using FastF1's helper."""
    try:
        # Pass mpl_timedelta_support=True only if needed and supported
        # Pass color_scheme=None to use default matplotlib colors if FastF1 scheme fails
        fastf1.plotting.setup_mpl(
             misc_mpl_mods=False, # Avoids potential conflicts
             mpl_timedelta_support=False, # Handle timedelta formatting manually for more control
             color_scheme=config.COLOR_SCHEME
        )
        logger.info(f"Set up matplotlib plotting style with scheme: '{config.COLOR_SCHEME}'.")
    except Exception as e:
        logger.error(f"Could not set up FastF1 plotting styles: {e}. Using default matplotlib styles.", exc_info=True)


def _save_plot(fig: plt.Figure, filename: Union[str, Path]):
    """Helper function to save a matplotlib figure."""
    if not config.PLOT_SAVE:
        logger.debug(f"Plot saving disabled. Skipping save for '{filename}'.")
        return

    try:
        # Ensure output directory exists
        output_path = Path(config.OUTPUT_DIR)
        output_path.mkdir(parents=True, exist_ok=True)

        full_path = output_path / f"{filename}.{config.PLOT_FORMAT}"

        # Check if figure has axes with data before saving
        if not fig.get_axes() or all(not ax.has_data() for ax in fig.get_axes()):
             logger.warning(f"Attempted to save plot '{full_path}' but it appears empty. Skipping.")
             return

        # Add a background color to ensure non-transparent saving if needed
        # fig.patch.set_facecolor('white') # Optional: forces white background

        fig.savefig(full_path, dpi=config.PLOT_DPI, bbox_inches='tight')
        logger.info(f"Plot saved successfully: {full_path}")

    except Exception as e:
        logger.error(f"Failed to save plot '{filename}': {e}", exc_info=True)


def plot_constructor_pace_deltas(pace_data: pd.Series, session_info: Dict[str, Any], session: ff1.core.Session):
    """
    Generates and saves a bar plot comparing constructor median race pace
    as deltas relative to the fastest constructor.

    Args:
        pace_data: Series with Team as index and median lap time (seconds) as values.
        session_info: Dict containing 'EventName', 'SessionName', 'Year'.
        session: The FastF1 session object for context (e.g., colors).
    """
    if pace_data is None or pace_data.empty:
        logger.warning("No constructor pace data provided for plotting.")
        return

    logger.info("Generating constructor pace delta comparison plot...")
    fig, ax = plt.subplots(figsize=(10, 6))

    pace_df = pace_data.reset_index()
    pace_df.columns = [config.COL_TEAM, config.COL_LAP_TIME_SECONDS] # Rename for clarity

    # --- Calculate Deltas ---
    min_pace = pace_df[config.COL_LAP_TIME_SECONDS].min()
    pace_df['DeltaSeconds'] = pace_df[config.COL_LAP_TIME_SECONDS] - min_pace
    # ----------------------

    # Get team colors, defaulting to grey if not found
    team_colors = [fastf1.plotting.get_team_color(team, session=session) or '#808080'
                   for team in pace_df[config.COL_TEAM]]

    bars = ax.barh(pace_df[config.COL_TEAM], pace_df['DeltaSeconds'], color=team_colors) # Plot Deltas

    ax.set_xlabel("Median Lap Time Delta to Fastest (seconds)") # Update Label
    ax.set_ylabel("Constructor")
    title = f"{session_info.get('EventName', 'Event')} {session_info.get('SessionName', 'Session')} ({session_info.get('Year', '')})\nConstructor Median Race Pace Delta" # Update Title
    ax.set_title(title)
    ax.invert_yaxis()  # Fastest (0.0 delta) at the top

    # Add labels to bars showing the delta
    for bar in bars:
        width = bar.get_width()
        # Format delta time - handle potential floating point inaccuracies near zero
        label = f"+{width:.3f}s" if width > 0.0001 else "0.000s"
        ax.text(width + 0.01, bar.get_y() + bar.get_height()/2., # Adjust text position slightly
                 label, va='center', ha='left', fontsize=8)

    plt.tight_layout()
    plt.subplots_adjust(left=0.25) # Adjust for long team names

    # Update filename
    filename = f"{session_info.get('Year', 'YYYY')}_{session_info.get('EventName', 'Event').replace(' ', '')}_{session_info.get('SessionName', 'Session')}_ConstructorPaceDelta"
    _save_plot(fig, filename)

    if config.PLOT_SHOW:
        plt.show()
    else:
        plt.close(fig)

def plot_driver_fastest_lap_deltas(fastest_laps_df: pd.DataFrame, session_info: Dict[str, Any], session: ff1.core.Session):
    """
    Generates and saves a bar plot comparing driver fastest laps
    as deltas relative to the overall fastest lap.

    Args:
        fastest_laps_df: DataFrame containing fastest lap per driver.
        session_info: Dict containing 'EventName', 'SessionName', 'Year'.
        session: The FastF1 session object for context (e.g., colors).
    """
    if fastest_laps_df is None or fastest_laps_df.empty:
        logger.warning("No driver fastest lap data provided for plotting.")
        return

    logger.info("Generating driver fastest lap delta comparison plot...")
    fig, ax = plt.subplots(figsize=(10, max(6, len(fastest_laps_df) * 0.35))) # Adjust height

    # Ensure LapTime column exists
    if config.COL_LAP_TIME not in fastest_laps_df.columns:
         logger.error(f"Cannot plot driver laps: '{config.COL_LAP_TIME}' column missing.")
         plt.close(fig)
         return

    # --- Calculate Deltas ---
    # Convert to seconds first if necessary
    if pd.api.types.is_timedelta64_dtype(fastest_laps_df[config.COL_LAP_TIME]):
        fastest_laps_df['LapTimeSeconds'] = fastest_laps_df[config.COL_LAP_TIME].dt.total_seconds()
    elif pd.api.types.is_numeric_dtype(fastest_laps_df[config.COL_LAP_TIME]):
        fastest_laps_df['LapTimeSeconds'] = fastest_laps_df[config.COL_LAP_TIME] # Assume already seconds
    else:
         logger.error(f"Cannot calculate delta: '{config.COL_LAP_TIME}' is not numeric or timedelta.")
         plt.close(fig)
         return

    min_lap_time_sec = fastest_laps_df['LapTimeSeconds'].min()
    fastest_laps_df['DeltaSeconds'] = fastest_laps_df['LapTimeSeconds'] - min_lap_time_sec
    # ----------------------

    # Get driver colors
    driver_colors = []
    team_col = config.COL_TEAM
    driver_col = config.COL_DRIVER # Assuming this holds abbreviation

    teams = fastest_laps_df[team_col] if team_col in fastest_laps_df else pd.Series(['N/A'] * len(fastest_laps_df))

    for driver, team in zip(fastest_laps_df[driver_col], teams):
        # Use session context for colors
        color = fastf1.plotting.get_driver_color(driver, session=session)
        if color is None or color == '#ffffff': # White often means not found
             color = fastf1.plotting.get_team_color(team, session=session) or '#808080' # Fallback grey
        driver_colors.append(color)

    bars = ax.barh(fastest_laps_df[config.COL_DRIVER], fastest_laps_df['DeltaSeconds'], color=driver_colors) # Plot Deltas

    ax.set_xlabel("Fastest Lap Delta to Overall Fastest (seconds)") # Update Label
    ax.set_ylabel("Driver")
    title = f"{session_info.get('EventName', 'Event')} {session_info.get('SessionName', 'Session')} ({session_info.get('Year', '')})\nDriver Fastest Lap Delta" # Update Title
    ax.set_title(title)
    ax.invert_yaxis() # Fastest (0.0 delta) at the top

    # Add labels showing delta
    for bar in bars:
        width = bar.get_width()
        label = f"+{width:.3f}s" if width > 0.0001 else "0.000s"
        ax.text(width + 0.01, bar.get_y() + bar.get_height()/2., # Adjust text position
                 label, va='center', ha='left', fontsize=8)

    plt.tight_layout()
    plt.subplots_adjust(left=0.18) # Adjust for driver names

    # Update filename
    filename = f"{session_info.get('Year', 'YYYY')}_{session_info.get('EventName', 'Event').replace(' ', '')}_{session_info.get('SessionName', 'Session')}_DriverFastestLapDelta"
    _save_plot(fig, filename)

    if config.PLOT_SHOW:
        plt.show()
    else:
        plt.close(fig)

# --- NEW FUNCTION for Violin Plot ---
def plot_driver_pace_distribution(laps_df: pd.DataFrame, session_info: Dict[str, Any], session: ff1.core.Session):
    """
    Generates and saves a violin plot showing the distribution of lap times
    for each driver during a race session.

    Args:
        laps_df: DataFrame containing cleaned lap data per driver (needs Driver, Team, LapTimeSeconds).
        session_info: Dict containing 'EventName', 'SessionName', 'Year'.
        session: The FastF1 session object for context (e.g., colors).
    """
    if laps_df is None or laps_df.empty or config.COL_LAP_TIME_SECONDS not in laps_df.columns:
        logger.warning("No valid driver lap data provided for pace distribution plot.")
        return

    logger.info("Generating driver race pace distribution plot (violin)...")

    # --- Prepare data for plotting ---
    # Calculate median pace per driver to order the plot
    median_pace = laps_df.groupby(config.COL_DRIVER)[config.COL_LAP_TIME_SECONDS].median()
    # Sort drivers by median pace (fastest first)
    driver_order = median_pace.sort_values().index.tolist()

    # Get driver colors
    driver_colors_map = {}
    team_col = config.COL_TEAM
    driver_col = config.COL_DRIVER

    # Create a mapping from driver abbreviation to team (handle potential missing teams)
    driver_team_map = laps_df.set_index(driver_col)[team_col].to_dict() if team_col in laps_df else {}

    for driver in driver_order:
        team = driver_team_map.get(driver, 'N/A')
        color = fastf1.plotting.get_driver_color(driver, session=session)
        if color is None or color == '#ffffff': # White often means not found
             color = fastf1.plotting.get_team_color(team, session=session) or '#808080' # Fallback grey
        driver_colors_map[driver] = color

    # --- Create Plot ---
    fig, ax = plt.subplots(figsize=(14, 7)) # Wider figure for many drivers

    sns.violinplot(data=laps_df,
                   x=config.COL_DRIVER,
                   y=config.COL_LAP_TIME_SECONDS,
                   order=driver_order, # Order drivers by median pace
                   palette=driver_colors_map, # Use mapped driver/team colors
                   inner='box', # Show boxplot inside violins (can use 'quartile', 'point', None)
                   ax=ax)

    ax.set_xlabel("Driver")
    ax.set_ylabel("Race Lap Time (seconds)")
    title = f"{session_info.get('EventName', 'Event')} {session_info.get('SessionName', 'Session')} ({session_info.get('Year', '')})\nDriver Race Pace Distribution"
    ax.set_title(title)

    # Improve readability
    ax.tick_params(axis='x', rotation=70) # Rotate driver names if needed
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15) # Adjust for rotated labels

    filename = f"{session_info.get('Year', 'YYYY')}_{session_info.get('EventName', 'Event').replace(' ', '')}_{session_info.get('SessionName', 'Session')}_DriverPaceDistribution"
    _save_plot(fig, filename)

    if config.PLOT_SHOW:
        plt.show()
    else:
        plt.close(fig)