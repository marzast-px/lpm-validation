"""Comparison plot implementation for simulator correlation analysis."""

import logging
from typing import Optional, List, Dict
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

# Car-specific colors (Sedans: blue variants, SUVs: red variants)
CAR_SPECIFIC_COLORS = {
    'Audi_RS7_Sportback_Symmetric': '#1f77b4',  # Blue
    'BMW_IX': '#d62728',                         # Red
    'Mitsubishi_Eclipse': '#e377c2',             # Pink-Red
}

# Morph type symbols
MORPH_TYPE_SYMBOLS = {
    'Front Fascia Curvature': 'circle',
    'Front Overhang': 'square',
    'Rear Overhang': 'diamond',
    'Ride Height': 'triangle-up',
    'Wheel Size': 'triangle-down',
    'Spoiler Angle': 'star',
    'Baseline': 'x',  # For baseline variants
}


# ============================================================================
# SIMULATOR COMPARISON PLOT CLASS
# ============================================================================

class SimulatorComparisonPlot:
    """Correlation plot comparing two simulators.
    
    Creates scatter plots showing how two simulators compare for the same variants.
    Points near the diagonal line indicate good agreement between simulators.
    
    Example:
        >>> plot = SimulatorComparisonPlot.create_plot(
        ...     datasets=datasets,
        ...     simulator1='JakubNet',
        ...     simulator2='SiemensSolve',
        ...     cars=['Audi_RS7_Sportback_Symmetric', 'BMW_IX'],
        ...     metric='Cd'
        ... )
        >>> plot.show()
    """
    
    def __init__(
        self,
        datasets: Dict[str, pd.DataFrame],
        simulator1: str,
        simulator2: str,
        cars: List[str],
        metric: str = 'Cd',
        title: Optional[str] = None,
        marker_size: int = 10,
        show_diagonal: bool = True
    ):
        """Initialize the comparison plot.
        
        Args:
            datasets: Dictionary of DataFrames keyed by '{simulator}_{car}'
            simulator1: First simulator name (x-axis)
            simulator2: Second simulator name (y-axis)
            cars: List of car names to include
            metric: Metric to compare (default: 'Cd')
            title: Plot title (auto-generated if None)
            marker_size: Size of markers (default: 10)
            show_diagonal: Show diagonal reference line (default: True)
        """
        self.datasets = datasets
        self.sim1 = simulator1
        self.sim2 = simulator2
        self.cars = cars
        self.metric = metric
        self.title = title or f'{metric} Comparison: {simulator1} vs {simulator2}'
        self.marker_size = marker_size
        self.show_diagonal = show_diagonal
        self._fig: Optional[go.Figure] = None
    
    @classmethod
    def create_plot(
        cls,
        datasets: Dict[str, pd.DataFrame],
        simulator1: str,
        simulator2: str,
        cars: List[str],
        metric: str = 'Cd',
        **kwargs
    ) -> 'SimulatorComparisonPlot':
        """Create a new simulator comparison plot.
        
        Args:
            datasets: Dictionary of DataFrames keyed by '{simulator}_{car}'
            simulator1: First simulator name (x-axis)
            simulator2: Second simulator name (y-axis)
            cars: List of car names to include
            metric: Metric to compare (default: 'Cd')
            **kwargs: Additional arguments:
                - title: Custom title
                - marker_size: Marker size (default: 10)
                - show_diagonal: Show diagonal line (default: True)
        
        Returns:
            SimulatorComparisonPlot instance
        
        Example:
            >>> plot = SimulatorComparisonPlot.create_plot(
            ...     datasets, 'JakubNet', 'SiemensSolve',
            ...     ['Audi_RS7_Sportback_Symmetric'], metric='Cd'
            ... )
        """
        return cls(datasets, simulator1, simulator2, cars, metric, **kwargs)
    
    def _get_color_for_car(self, car: str) -> str:
        """Get color for a car."""
        return CAR_SPECIFIC_COLORS.get(car, '#999999')
    
    def _get_symbol_for_morph(self, morph_type: str) -> str:
        """Get symbol for a morph type."""
        if pd.isna(morph_type) or morph_type == '':
            return MORPH_TYPE_SYMBOLS.get('Baseline', 'x')
        return MORPH_TYPE_SYMBOLS.get(morph_type, 'circle')
    
    def _create_figure(self) -> go.Figure:
        """Create comparison plot figure."""
        fig = go.Figure()
        
        all_values = []  # For determining axis ranges
        
        for car in self.cars:
            key1 = f"{self.sim1}_{car}"
            key2 = f"{self.sim2}_{car}"
            
            if key1 not in self.datasets or key2 not in self.datasets:
                logger.warning(f"Skipping {car}: missing data for {self.sim1} or {self.sim2}")
                continue
            
            df1 = self.datasets[key1]
            df2 = self.datasets[key2]
            
            # Filter out rows with NaN values in the metric
            df1_clean = df1[df1[self.metric].notna()].copy()
            df2_clean = df2[df2[self.metric].notna()].copy()
            
            if len(df1_clean) == 0 or len(df2_clean) == 0:
                logger.warning(f"Skipping {car}: no valid {self.metric} data")
                continue
            
            # Merge on Unique_ID to match corresponding variants
            merged = df1_clean.merge(
                df2_clean,
                on='Unique_ID',
                suffixes=(f'_{self.sim1}', f'_{self.sim2}')
            )
            
            if len(merged) == 0:
                logger.warning(f"Skipping {car}: no matching variants between {self.sim1} and {self.sim2}")
                continue
            
            # Get values
            x_values = merged[f'{self.metric}_{self.sim1}']
            y_values = merged[f'{self.metric}_{self.sim2}']
            
            all_values.extend(x_values.tolist())
            all_values.extend(y_values.tolist())
            
            # Group by morph type to create separate traces with different symbols
            morph_col_sim1 = f'Morph_Type_{self.sim1}'
            morph_col_sim2 = f'Morph_Type_{self.sim2}'
            
            # Use morph type from either simulator (should be the same)
            if morph_col_sim1 in merged.columns:
                merged['Morph_Type'] = merged[morph_col_sim1]
            elif morph_col_sim2 in merged.columns:
                merged['Morph_Type'] = merged[morph_col_sim2]
            else:
                merged['Morph_Type'] = None
            
            # Group by morph type
            for morph_type, group in merged.groupby('Morph_Type', dropna=False):
                # Create hover text
                hover_text = []
                for _, row in group.iterrows():
                    morph_str = morph_type if pd.notna(morph_type) and morph_type != '' else 'Baseline'
                    text = (
                        f"<b>{row['Unique_ID']}</b><br>"
                        f"Car: {car}<br>"
                        f"Morph: {morph_str}<br>"
                        f"{self.sim1}: {row[f'{self.metric}_{self.sim1}']:.6f}<br>"
                        f"{self.sim2}: {row[f'{self.metric}_{self.sim2}']:.6f}<br>"
                        f"Difference: {row[f'{self.metric}_{self.sim2}'] - row[f'{self.metric}_{self.sim1}']:.6f}"
                    )
                    hover_text.append(text)
                
                # Determine symbol based on morph type
                symbol = self._get_symbol_for_morph(morph_type)
                
                # Create legend label
                morph_label = morph_type if pd.notna(morph_type) and morph_type != '' else 'Baseline'
                legend_label = f"{car} - {morph_label}"
                
                # Add scatter trace
                fig.add_trace(go.Scatter(
                    x=group[f'{self.metric}_{self.sim1}'],
                    y=group[f'{self.metric}_{self.sim2}'],
                    mode='markers',
                    name=legend_label,
                    marker=dict(
                        symbol=symbol,
                        size=self.marker_size,
                        color=self._get_color_for_car(car),
                        line=dict(width=1, color='white')
                    ),
                    text=hover_text,
                    hovertemplate='%{text}<extra></extra>',
                    legendgroup=car,
                ))
        
        # Add diagonal reference line (perfect correlation)
        if self.show_diagonal and all_values:
            min_val = min(all_values)
            max_val = max(all_values)
            margin = (max_val - min_val) * 0.05
            
            fig.add_trace(go.Scatter(
                x=[min_val - margin, max_val + margin],
                y=[min_val - margin, max_val + margin],
                mode='lines',
                name='Perfect Correlation (y=x)',
                line=dict(color='gray', dash='dash', width=2),
                showlegend=True,
                hoverinfo='skip'
            ))
            
            # Set equal axis ranges for proper diagonal
            fig.update_xaxes(range=[min_val - margin, max_val + margin])
            fig.update_yaxes(range=[min_val - margin, max_val + margin])
        
        # Update layout
        fig.update_layout(
            title=self.title,
            xaxis_title=f'{self.metric} - {self.sim1}',
            yaxis_title=f'{self.metric} - {self.sim2}',
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
                scaleanchor='x',
                scaleratio=1,
            ),
            legend=dict(
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#333',
                borderwidth=1,
            ),
        )
        
        return fig
    
    @property
    def fig(self) -> go.Figure:
        """Get or create the plotly Figure."""
        if self._fig is None:
            self._fig = self._create_figure()
        return self._fig
    
    def show(self) -> None:
        """Display the plot."""
        self.fig.show()
    
    def save(self, filepath: str, format: str = 'html') -> None:
        """Save plot to file.
        
        Args:
            filepath: Output file path
            format: Output format ('html', 'png', 'svg', 'pdf')
        """
        if format == 'html':
            self.fig.write_html(filepath)
        else:
            self.fig.write_image(filepath, format=format)
        logger.info(f"Saved plot to {filepath}")
