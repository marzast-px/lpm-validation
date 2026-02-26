"""Base class for all plot types."""

import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Union, Optional
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import plotly.graph_objects as go
except ImportError:
    logger.error("plotly not installed. Install with: pip install plotly")
    raise


class BasePlot(ABC):
    """Abstract base class for all plot types.
    
    Provides common functionality for dataset handling, validation,
    figure creation, display, and export.
    
    Subclasses must implement:
        - _create_figure(): Create and return plotly Figure object
    
    Example:
        >>> class MyPlot(BasePlot):
        ...     def _create_figure(self):
        ...         fig = go.Figure()
        ...         # ... create plot ...
        ...         return fig
        >>> plot = MyPlot(df, title="My Plot")
        >>> plot.show()
    """
    
    def __init__(
        self,
        datasets: Union[pd.DataFrame, List[pd.DataFrame]],
        labels: Optional[List[str]] = None,
        title: Optional[str] = None,
        **kwargs
    ):
        """Initialize plot with datasets.
        
        Args:
            datasets: Single DataFrame or list of DataFrames
            labels: List of dataset labels (required if multiple datasets)
            title: Plot title
            **kwargs: Additional arguments passed to subclasses
        """
        self.datasets_raw = datasets
        self.labels = labels
        self.title = title
        self.kwargs = kwargs
        self._fig = None
        
        # Prepare datasets
        self.datasets = self._prepare_datasets()
        
        logger.info(f"Initialized {self.__class__.__name__} with {len(self.datasets)} dataset(s)")
    
    def _prepare_datasets(self) -> List[Tuple[pd.DataFrame, str]]:
        """Normalize datasets to list of (DataFrame, label) tuples.
        
        Returns:
            List of (DataFrame, label) tuples
        """
        # Handle single DataFrame
        if isinstance(self.datasets_raw, pd.DataFrame):
            label = self.labels[0] if self.labels else "Dataset"
            return [(self.datasets_raw, label)]
        
        # Handle list of DataFrames
        if isinstance(self.datasets_raw, list):
            if not self.labels:
                # Auto-generate labels
                self.labels = [f"Dataset {i+1}" for i in range(len(self.datasets_raw))]
            
            if len(self.labels) != len(self.datasets_raw):
                raise ValueError(
                    f"Number of labels ({len(self.labels)}) must match "
                    f"number of datasets ({len(self.datasets_raw)})"
                )
            
            return list(zip(self.datasets_raw, self.labels))
        
        raise TypeError(f"datasets must be DataFrame or list of DataFrames, got {type(self.datasets_raw)}")
    
    def _validate_columns(self, required_columns: List[str]) -> None:
        """Check that all datasets have required columns.
        
        Args:
            required_columns: List of required column names
        
        Raises:
            ValueError: If required columns are missing
        """
        for df, label in self.datasets:
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                raise ValueError(
                    f"Dataset '{label}' missing required columns: {missing}. "
                    f"Available columns: {list(df.columns)}"
                )
    
    @abstractmethod
    def _create_figure(self) -> go.Figure:
        """Create and return plotly Figure.
        
        Must be implemented by subclasses.
        
        Returns:
            Plotly Figure object
        """
        pass
    
    @property
    def fig(self) -> go.Figure:
        """Get or create the plotly Figure.
        
        Returns:
            Plotly Figure object
        """
        if self._fig is None:
            self._fig = self._create_figure()
        return self._fig
    
    def show(self) -> None:
        """Display the plot in Jupyter notebook or browser.
        
        Example:
            >>> plot.show()
        """
        self.fig.show()
    
    def save(
        self,
        filepath: Union[str, Path],
        format: str = 'html',
        width: Optional[int] = None,
        height: Optional[int] = None,
        scale: float = 1.0
    ) -> None:
        """Save plot to file.
        
        Args:
            filepath: Output file path
            format: Output format ('html', 'png', 'svg', 'pdf', 'jpeg')
            width: Image width in pixels (for static formats)
            height: Image height in pixels (for static formats)
            scale: Scale factor for static images (default: 1.0)
        
        Example:
            >>> plot.save('output.html')
            >>> plot.save('output.png', format='png', width=1200, height=800)
        """
        filepath = Path(filepath)
        
        if format == 'html':
            self.fig.write_html(str(filepath))
            logger.info(f"Saved plot to {filepath}")
        else:
            # For static formats, need kaleido
            try:
                self.fig.write_image(
                    str(filepath),
                    format=format,
                    width=width,
                    height=height,
                    scale=scale
                )
                logger.info(f"Saved plot to {filepath}")
            except Exception as e:
                logger.error(
                    f"Error saving static image: {e}. "
                    "Install kaleido: pip install kaleido"
                )
                raise
    
    def _apply_theme(self, fig: go.Figure) -> go.Figure:
        """Apply consistent theme to figure.
        
        Args:
            fig: Plotly Figure object
        
        Returns:
            Figure with theme applied
        """
        # Default theme
        fig.update_layout(
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
        
        if self.title:
            fig.update_layout(title=self.title)
        
        return fig
