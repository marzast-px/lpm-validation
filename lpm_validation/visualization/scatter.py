"""Scatter plot implementation for coefficient visualization."""

import logging
from pathlib import Path
from typing import Optional, List, Union, Dict, Tuple, cast
import pandas as pd
import numpy as np

try:
    import plotly.graph_objects as go
except ImportError:
    raise ImportError("plotly not installed. Install with: pip install plotly")

logger = logging.getLogger(__name__)


# ============================================================================
# COLOR AND SYMBOL SCHEMES
# ============================================================================

# Car group colors
CAR_GROUP_COLORS = {
    'Sedan': '#e41a1c',
    'SUV': '#377eb8',
    'Estate': '#4daf4a',
    'Truck': '#984ea3',
    'Van': '#ff7f00',
}

# Car-specific colors (Sedans: blue variants, SUVs: red variants)
CAR_SPECIFIC_COLORS = {
    'Audi_RS7_Sportback_Symmetric': '#1f77b4',  # Blue
    'BMW_IX': '#d62728',                         # Red
    'Mitsubishi_Eclipse': '#e377c2',             # Pink-Red
}

# Simulator-specific symbols (constant for all analyses)
SIMULATOR_SYMBOLS = {
    'JakubNet': 'circle',
    'DES': 'square',
    'SiemensMesh': 'diamond',
    'SiemensSolve': 'triangle-up',
}


# ============================================================================
# SCATTER PLOT CLASS
# ============================================================================

class CoefficientScatterPlot:
    """Scatter plot for visualizing coefficients across datasets.
    
    Creates interactive scatter plots with customizable settings and supports
    adding multiple datasets dynamically.
    
    Example:
        >>> plot = CoefficientScatterPlot(
        ...     df,
        ...     y_metric='Cd',
        ...     color_by='Simulator',
        ...     title='Drag Coefficient Comparison'
        ... )
        >>> plot.show()
    """
    
    def __init__(
        self,
        data: Union[pd.DataFrame, List[pd.DataFrame]],
        y_metric: str = 'Cd',
        x_axis: str = 'index',
        color_by: Optional[str] = 'Simulator',
        symbol_by: Optional[str] = None,
        show_baseline: bool = True,
        title: Optional[str] = None,
        labels: Optional[Union[str, List[str]]] = None,
        marker_size: int = 12
    ):
        """Initialize the scatter plot.
        
        Args:
            data: Single DataFrame or list of DataFrames
            y_metric: Column for Y-axis (default: 'Cd')
            x_axis: Column for X-axis (default: 'index')
            color_by: Column for color grouping (default: 'Simulator')
            symbol_by: Column for symbol grouping (default: None)
            show_baseline: Include baseline rows (default: True)
            title: Plot title
            labels: Single label or list of labels for the datasets
            marker_size: Size of markers (default: 12)
        """
        self.y_metric = y_metric
        self.x_axis = x_axis
        self.color_by = color_by
        self.symbol_by = symbol_by
        self.show_baseline = show_baseline
        self.title = title
        self.marker_size = marker_size
        self.labels = labels
        self.datasets: List[Tuple[pd.DataFrame, str]] = []
        self._fig: Optional[go.Figure] = None
        
        # Normalize data to list
        if isinstance(data, pd.DataFrame):
            dataset_list = [data]
            if labels is None:
                label_list = ['Dataset']
            elif isinstance(labels, str):
                label_list = [labels]
            else:
                label_list = list(labels) if labels else ['Dataset']
        else:
            dataset_list = data
            if labels is None:
                label_list = [f'Dataset {i+1}' for i in range(len(data))]
            elif isinstance(labels, str):
                label_list = [labels]
            else:
                label_list = list(labels)
        
        # Store labels properly
        self.labels = label_list
        
        # Validate columns for each dataset
        for df in dataset_list:
            if df is not None and len(df) > 0:
                self._validate_columns(df)
        
        # Add datasets
        for df, label in zip(dataset_list, label_list):
            if df is not None and len(df) > 0:
                self.datasets.append((df, label))
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist in the DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If required columns are missing
        """
        required_cols = [self.y_metric]
        if self.x_axis != 'index':
            required_cols.append(self.x_axis)
        
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(
                f"Dataset missing required columns: {missing}. "
                f"Available columns: {list(df.columns)}"
            )
    
    def add_data(
        self,
        datasets: Union[pd.DataFrame, List[pd.DataFrame]],
        labels: Optional[Union[str, List[str]]] = None
    ) -> 'CoefficientScatterPlot':
        """Add data to the plot.
        
        Args:
            datasets: Single DataFrame or list of DataFrames
            labels: Single label or list of labels for the datasets
        
        Returns:
            Self for method chaining
        
        Example:
            >>> plot.add_data(df1, 'Dataset 1')
            >>> plot.add_data([df2, df3], ['Dataset 2', 'Dataset 3'])
        """
        # Normalize to list
        if isinstance(datasets, pd.DataFrame):
            dataset_list = [datasets]
            label_list: List[str] = [labels if isinstance(labels, str) else 'Dataset']
        else:
            dataset_list = datasets
            if labels is None:
                label_list = [f'Dataset {i+1}' for i in range(len(datasets))]
            elif isinstance(labels, str):
                label_list = [labels]
            else:
                label_list = list(labels)  # Ensure it's a list of strings
        
        # Add datasets, skipping empty ones
        for df, label in zip(dataset_list, label_list):
            if df is None:
                print(f"⚠ Skipping '{label}': Data is None")
                continue
            
            if len(df) == 0:
                print(f"⚠ Skipping '{label}': DataFrame is empty (0 rows)")
                continue
            
            self.datasets.append((df, label))
        
        # Reset figure to force recreation
        self._fig = None
        
        return self
    
    def _get_color_for_value(self, value: str, category: str) -> str:
        """Get color for a category value."""
        if category == 'Baseline_ID' and value in CAR_SPECIFIC_COLORS:
            return CAR_SPECIFIC_COLORS[value]
        elif category == 'Car_Group' and value in CAR_GROUP_COLORS:
            return CAR_GROUP_COLORS[value]
        return '#999999'  # Default gray
    
    def _get_symbol_for_simulator(self, simulator: str) -> str:
        """Get symbol for a simulator."""
        return SIMULATOR_SYMBOLS.get(simulator, 'circle')
    
    def _create_figure(self) -> go.Figure:
        """Create scatter plot figure."""
        fig = go.Figure()
        
        # Use instance attributes
        y_metric = self.y_metric
        x_axis = self.x_axis
        color_by = self.color_by
        marker_size = self.marker_size
        show_baseline = self.show_baseline
        
        # Determine x_label based on x_axis setting
        x_label = 'Index' if x_axis == 'index' else x_axis
        
        # Track which legend entries we've already added
        seen_labels = set()
        
        for df, dataset_label in self.datasets:
            # Skip empty dataframes
            if df is None or len(df) == 0:
                continue
            
            # Filter baseline rows if needed
            if not show_baseline:
                df = df[~(df['Morph_Type'].isna() | (df['Morph_Type'] == ''))].copy()
            
            # Check again after filtering
            if len(df) == 0:
                continue
            
            # Filter out rows where y_metric is NaN
            if y_metric in df.columns:
                df = df[df[y_metric].notna()].copy()
            
            # Check again after filtering NaN values
            if len(df) == 0:
                continue
            
            # Group by color_by column if specified
            if color_by and color_by in df.columns:
                grouped = df.groupby(color_by, dropna=False)
            else:
                # Create a single group with entire dataframe
                grouped = [(None, df)]
            
            for category_value, group_df in grouped:
                if len(group_df) == 0:
                    continue
                
                # Get axis values
                if x_axis == 'index':
                    x_values = pd.Series(range(len(group_df)), index=group_df.index)
                else:
                    x_values = group_df[x_axis]
                
                y_values = group_df[y_metric]
                
                # Determine color from color_by column
                color = '#1f77b4'  # Default blue
                if color_by and category_value is not None:
                    color = self._get_color_for_value(str(category_value), color_by)
                
                # Determine symbol from Simulator column (if it exists)
                symbol = 'circle'
                if 'Simulator' in group_df.columns and len(group_df) > 0:
                    simulator = group_df['Simulator'].iloc[0]
                    symbol = self._get_symbol_for_simulator(str(simulator))
                
                # Create trace label
                if category_value is not None:
                    trace_label = str(category_value)
                else:
                    trace_label = dataset_label
                
                # Only show legend entry for first occurrence of each label
                show_in_legend = trace_label not in seen_labels
                seen_labels.add(trace_label)
                
                # Use the category value or dataset label for legend
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='markers',
                    name=trace_label,
                    marker=dict(
                        symbol=symbol,
                        size=marker_size,
                        color=color,
                        line=dict(width=1, color='white')
                    ),
                    text=self._create_hover_text(group_df),
                    hovertemplate='%{text}<extra></extra>',
                    legendgroup=trace_label,
                    showlegend=show_in_legend,
                ))
        
        # Update layout
        fig.update_layout(
            title=self.title,
            xaxis_title=x_label,
            yaxis_title=y_metric,
            hovermode='closest',
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'family': 'Arial, sans-serif', 'size': 14, 'color': '#333'},
            xaxis=dict(
                showgrid=True,
                gridwidth=2,
                gridcolor='#E5E5E5',
                showline=True,
                linewidth=2,
                linecolor='#333',
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=2,
                gridcolor='#E5E5E5',
                showline=True,
                linewidth=2,
                linecolor='#333',
            ),
            legend=dict(
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#333',
                borderwidth=1,
            ),
        )
        
        return fig
    
    def _create_hover_text(self, df: pd.DataFrame) -> List[str]:
        """Create hover text for data points."""
        hover_texts = []
        
        for _, row in df.iterrows():
            text_parts = [
                f"<b>{row.get('Unique_ID', 'N/A')}</b>",
                f"Baseline: {row.get('Baseline_ID', 'N/A')}",
                f"Simulator: {row.get('Simulator', 'N/A')}",
            ]
            
            # Add morph info
            morph_type = row.get('Morph_Type')
            if pd.notna(morph_type) and morph_type != '':
                text_parts.append(f"Morph: {morph_type} = {row.get('Morph_Value', 'N/A')}")
            else:
                text_parts.append("Type: Baseline")
            
            # Add metric value
            metric_value = row.get(self.y_metric, np.nan)
            metric_str = f"{metric_value:.6f}" if pd.notna(metric_value) else "N/A"
            text_parts.append(f"{self.y_metric}: {metric_str}")
            
            hover_texts.append("<br>".join(text_parts))
        
        return hover_texts
    
    @property
    def fig(self) -> go.Figure:
        """Get or create the plotly Figure."""
        if self._fig is None:
            self._fig = self._create_figure()
        return self._fig
    
    def show(self) -> None:
        """Display the plot."""
        if len(self.datasets) == 0:
            print("⚠ No data to display. All datasets were empty or not added.")
            return
        self.fig.show()
    
    def add_baseline_reference(self, baseline_value: float, label: str = "Baseline") -> None:
        """Add horizontal reference line at baseline value."""
        self.fig.add_hline(
            y=baseline_value,
            line_dash="dash",
            line_color="gray",
            annotation_text=label,
            annotation_position="right"
        )
    
    def save(self, filepath: Union[str, Path], format: str = 'html') -> None:
        """Save the plot to a file.
        
        Args:
            filepath: Path to save the file
            format: File format ('html', 'png', 'svg', 'pdf')
        """
        if format == 'html':
            self.fig.write_html(str(filepath))
        else:
            self.fig.write_image(str(filepath), format=format)
