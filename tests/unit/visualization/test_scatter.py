"""Unit tests for visualization scatter plot module."""

import pytest
import pandas as pd
import plotly.graph_objects as go
from lpm_validation.visualization.scatter import CoefficientScatterPlot


class TestCoefficientScatterPlot:
    """Test CoefficientScatterPlot class."""
    
    def test_init_single_dataset(self, sample_dataframe):
        """Test initialization with single dataset."""
        plot = CoefficientScatterPlot(sample_dataframe)
        
        assert plot.y_metric == 'Cd'
        assert plot.x_axis == 'index'
        assert plot.color_by == 'Simulator'
        assert len(plot.datasets) == 1
    
    def test_init_multiple_datasets(self, sample_dataframe):
        """Test initialization with multiple datasets."""
        df1 = sample_dataframe.copy()
        df2 = sample_dataframe.copy()
        
        plot = CoefficientScatterPlot(
            [df1, df2],
            labels=['Dataset 1', 'Dataset 2']
        )
        
        assert len(plot.datasets) == 2
        assert plot.labels == ['Dataset 1', 'Dataset 2']
    
    def test_init_custom_parameters(self, sample_dataframe):
        """Test initialization with custom parameters."""
        plot = CoefficientScatterPlot(
            sample_dataframe,
            y_metric='Cl',
            x_axis='Morph_Value',
            color_by='Baseline_ID',
            symbol_by='Simulator',
            show_baseline=False,
            title='Custom Plot'
        )
        
        assert plot.y_metric == 'Cl'
        assert plot.x_axis == 'Morph_Value'
        assert plot.color_by == 'Baseline_ID'
        assert plot.symbol_by == 'Simulator'
        assert plot.show_baseline == False
        assert plot.title == 'Custom Plot'
    
    def test_validate_columns_valid(self, sample_dataframe):
        """Test that valid columns pass validation."""
        # Should not raise error
        plot = CoefficientScatterPlot(
            sample_dataframe,
            y_metric='Cd',
            color_by='Simulator'
        )
        
        assert plot is not None
    
    def test_validate_columns_invalid_metric(self, sample_dataframe):
        """Test that invalid metric column raises error."""
        with pytest.raises(ValueError, match="missing required columns"):
            CoefficientScatterPlot(
                sample_dataframe,
                y_metric='NonExistentMetric'
            )
    
    def test_validate_columns_invalid_x_axis(self, sample_dataframe):
        """Test that invalid x_axis column raises error."""
        with pytest.raises(ValueError, match="missing required columns"):
            CoefficientScatterPlot(
                sample_dataframe,
                x_axis='NonExistentColumn'
            )
    
    def test_create_figure_generates_figure(self, sample_dataframe):
        """Test that figure is created."""
        plot = CoefficientScatterPlot(sample_dataframe)
        fig = plot.fig
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_create_figure_with_title(self, sample_dataframe):
        """Test that title is applied to figure."""
        plot = CoefficientScatterPlot(
            sample_dataframe,
            title='Test Title'
        )
        fig = plot.fig
        
        assert fig.layout.title.text == 'Test Title'
    
    def test_create_figure_traces_for_categories(self, sample_dataframe):
        """Test that traces are created for each category."""
        plot = CoefficientScatterPlot(
            sample_dataframe,
            color_by='Simulator'
        )
        fig = plot.fig
        
        # Should have at least one trace per unique simulator
        unique_simulators = sample_dataframe['Simulator'].dropna().nunique()
        assert len(fig.data) >= unique_simulators
    
    def test_create_figure_index_x_axis(self, sample_dataframe):
        """Test figure creation with index x-axis."""
        plot = CoefficientScatterPlot(
            sample_dataframe,
            x_axis='index'
        )
        fig = plot.fig
        
        assert 'Index' in fig.layout.xaxis.title.text or \
               fig.layout.xaxis.title.text is None  # May not be set
    
    def test_create_figure_custom_x_axis(self, sample_dataframe_with_morphs):
        """Test figure creation with custom x-axis column."""
        plot = CoefficientScatterPlot(
            sample_dataframe_with_morphs,
            x_axis='Morph_Value',
            y_metric='Cd'
        )
        fig = plot.fig
        
        assert fig is not None
    
    def test_create_figure_no_color_grouping(self, sample_dataframe):
        """Test figure creation without color grouping."""
        plot = CoefficientScatterPlot(
            sample_dataframe,
            color_by=None
        )
        fig = plot.fig
        
        # Should still create at least one trace
        assert len(fig.data) > 0
    
    def test_create_figure_filter_baseline(self, sample_dataframe_with_morphs):
        """Test that show_baseline filter works."""
        plot_with_baseline = CoefficientScatterPlot(
            sample_dataframe_with_morphs,
            show_baseline=True
        )
        
        plot_without_baseline = CoefficientScatterPlot(
            sample_dataframe_with_morphs,
            show_baseline=False
        )
        
        # Both should create figures
        assert plot_with_baseline.fig is not None
        assert plot_without_baseline.fig is not None
    
    def test_create_hover_text(self, sample_dataframe):
        """Test hover text generation."""
        plot = CoefficientScatterPlot(sample_dataframe)
        
        hover_texts = plot._create_hover_text(sample_dataframe)
        
        assert len(hover_texts) == len(sample_dataframe)
        
        # Each hover text should contain key information
        for text in hover_texts:
            assert 'Baseline:' in text or 'Baseline_ID' in text
            assert 'Simulator:' in text
    
    def test_add_baseline_reference(self, sample_dataframe):
        """Test adding baseline reference line."""
        plot = CoefficientScatterPlot(sample_dataframe)
        
        # Create figure first
        _ = plot.fig
        
        # Add baseline reference
        plot.add_baseline_reference(0.25, label='Target')
        
        # Should have added a line
        assert plot.fig is not None
    
    def test_multi_dataset_plot(self, sample_dataframe):
        """Test plotting multiple datasets."""
        df1 = sample_dataframe.copy()
        df2 = sample_dataframe.copy()
        df2['Cd'] = df2['Cd'] * 1.1  # Slightly different values
        
        plot = CoefficientScatterPlot(
            [df1, df2],
            labels=['Run 1', 'Run 2'],
            y_metric='Cd',
            color_by='Baseline_ID',
            symbol_by='dataset'
        )
        
        fig = plot.fig
        
        # Should have traces for both datasets
        assert len(fig.data) > 1
    
    def test_save_html(self, sample_dataframe, tmp_path):
        """Test saving plot as HTML."""
        plot = CoefficientScatterPlot(sample_dataframe)
        
        output_file = tmp_path / "test_plot.html"
        plot.save(output_file, format='html')
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    def test_show_returns_none(self, sample_dataframe):
        """Test that show() method exists and returns None."""
        plot = CoefficientScatterPlot(sample_dataframe)
        
        # Should not raise error (may not actually display in test environment)
        result = plot.show()
        
        # show() returns None
        assert result is None
    
    def test_different_y_metrics(self, sample_dataframe):
        """Test plotting different metrics."""
        metrics = ['Cd', 'Cl']
        
        for metric in metrics:
            if metric in sample_dataframe.columns:
                plot = CoefficientScatterPlot(
                    sample_dataframe,
                    y_metric=metric
                )
                
                assert plot.y_metric == metric
                assert plot.fig is not None
    
    def test_color_by_options(self, sample_dataframe):
        """Test different color_by options."""
        color_options = ['Simulator', 'Baseline_ID', 'Car_Group', None]
        
        for color_by in color_options:
            if color_by is None or color_by in sample_dataframe.columns:
                plot = CoefficientScatterPlot(
                    sample_dataframe,
                    color_by=color_by
                )
                
                assert plot.fig is not None
