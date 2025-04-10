# f1_analysis_dashboard/config.py
import os
from pathlib import Path

# --- Core Settings ---
# Default values, can be overridden by command-line arguments in main.py
DEFAULT_YEAR: int = 2023
DEFAULT_EVENT: str = 'Jeddah' # Use GP name or Round Number or City

# --- Cache Settings ---
# Use a directory within the project or a system temp dir
# Using Path for better cross-platform compatibility
# CACHE_DIR: Path = Path(os.getenv('FF1_CACHE_PATH', '/tmp/ff1_cache')) # Example using env var or default tmp
CACHE_DIR: Path = Path(__file__).parent.parent / '.ff1_cache' # Cache inside project dir
CACHE_ENABLED: bool = True

# --- Data Loading Settings ---
# What data aspects to load by default. Can be memory intensive.
LOAD_CONFIG = {
    'laps': True,
    'telemetry': False, # Telemetry is very large, keep False unless needed
    'weather': False,
    'messages': False
}

# --- Analysis Settings ---
# Threshold for filtering outlier laps (e.g., 1.15 means keep laps within 115% of median)
PACE_FILTER_THRESHOLD: float = 1.15
# Minimum lap number to consider for pace analysis (ignores formation/first lap)
MIN_LAP_NUMBER_PACE: int = 2

# --- Plotting Settings ---
OUTPUT_DIR: Path = Path(__file__).parent.parent / 'output'
PLOT_FORMAT: str = 'png'
PLOT_DPI: int = 150
PLOT_SHOW: bool = False # Set to True to display plots interactively
PLOT_SAVE: bool = True # Set to True to save plots to OUTPUT_DIR

# --- FastF1 Plotting Style ---
# Options: 'fastf1', None, etc.
COLOR_SCHEME = 'fastf1' # Use fastf1 default color scheme

# --- Session Types Mapping ---
# Common identifiers used by FastF1
SESSION_TYPES = {
    'FP1': 'FP1', 'FP2': 'FP2', 'FP3': 'FP3',
    'Q': 'Q', 'SQ': 'SQ', # Qualifying, Sprint Qualifying
    'R': 'R', 'S': 'S'   # Race, Sprint Race
}

# --- Constants ---
# For safer column access
COL_DRIVER = 'Driver'
COL_TEAM = 'Team'
COL_LAP_TIME = 'LapTime'
COL_LAP_NUMBER = 'LapNumber'
COL_COMPOUND = 'Compound'
COL_TYRE_LIFE = 'TyreLife'
COL_SECTOR1 = 'Sector1Time'
COL_SECTOR2 = 'Sector2Time'
COL_SECTOR3 = 'Sector3Time'
COL_LAP_TIME_SECONDS = 'LapTimeSeconds'
COL_IS_ACCURATE = 'IsAccurate'
COL_ABBREVIATION = 'Abbreviation'
COL_TEAM_NAME = 'TeamName' # From results
COL_POSITION = 'Position'
COL_FULL_NAME = 'FullName'
COL_STATUS = 'Status'
COL_TIME = 'Time'
COL_POINTS = 'Points'

print(f"Config loaded. Cache directory set to: {CACHE_DIR.resolve()}")
print(f"Output directory set to: {OUTPUT_DIR.resolve()}")