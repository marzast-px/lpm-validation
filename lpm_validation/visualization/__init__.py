"""Visualization module for LPM validation data analysis.

This module provides tools for loading, processing, and visualizing
simulation validation data in Jupyter notebooks.
"""

from .loaders import (
    load_csv,
    load_dataset,
    load_multiple_datasets,
    identify_baseline_rows,
    filter_morphs_only,
    filter_converged_results,
)
from .scatter import CoefficientScatterPlot
from .comparison import SimulatorComparisonPlot

__version__ = "0.1.0"

__all__ = [
    'load_csv',
    'load_dataset',
    'load_multiple_datasets',
    'identify_baseline_rows',
    'filter_morphs_only',
    'filter_converged_results',
    'CoefficientScatterPlot',
    'SimulatorComparisonPlot',
]
