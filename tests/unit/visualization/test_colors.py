"""Unit tests for visualization colors module."""

import pytest
import pandas as pd
from lpm_validation.visualization.colors import ColorScheme


class TestColorScheme:
    """Test ColorScheme class."""
    
    def test_simulator_colors_defined(self):
        """Test that simulator colors are predefined."""
        assert 'JakubNet' in ColorScheme.SIMULATOR_COLORS
        assert 'DES' in ColorScheme.SIMULATOR_COLORS
        assert 'OpenFOAM' in ColorScheme.SIMULATOR_COLORS
        
        # All colors should be hex codes
        for color in ColorScheme.SIMULATOR_COLORS.values():
            assert color.startswith('#')
            assert len(color) == 7
    
    def test_car_group_colors_defined(self):
        """Test that car group colors are predefined."""
        assert 'Sedan' in ColorScheme.CAR_GROUP_COLORS
        assert 'SUV' in ColorScheme.CAR_GROUP_COLORS
        
        # All colors should be hex codes
        for color in ColorScheme.CAR_GROUP_COLORS.values():
            assert color.startswith('#')
            assert len(color) == 7
    
    def test_extended_palette_exists(self):
        """Test that extended palette is available."""
        assert len(ColorScheme.EXTENDED_PALETTE) > 0
        
        for color in ColorScheme.EXTENDED_PALETTE:
            assert color.startswith('#')
    
    def test_marker_symbols_available(self):
        """Test that marker symbols are defined."""
        assert len(ColorScheme.MARKER_SYMBOLS) > 0
        
        # Check some common symbols
        assert 'circle' in ColorScheme.MARKER_SYMBOLS
        assert 'square' in ColorScheme.MARKER_SYMBOLS
        assert 'diamond' in ColorScheme.MARKER_SYMBOLS


class TestGetColorMap:
    """Test get_color_map method."""
    
    def test_get_color_map_simulator(self, sample_dataframe):
        """Test getting color map for simulators."""
        color_map = ColorScheme.get_color_map(sample_dataframe, 'Simulator')
        
        assert isinstance(color_map, dict)
        
        # Check that known simulators get predefined colors
        if 'JakubNet' in color_map:
            assert color_map['JakubNet'] == ColorScheme.SIMULATOR_COLORS['JakubNet']
    
    def test_get_color_map_car_group(self, sample_dataframe):
        """Test getting color map for car groups."""
        color_map = ColorScheme.get_color_map(sample_dataframe, 'Car_Group')
        
        assert isinstance(color_map, dict)
        
        # Check that known car groups get predefined colors
        if 'Sedan' in color_map:
            assert color_map['Sedan'] == ColorScheme.CAR_GROUP_COLORS['Sedan']
    
    def test_get_color_map_baseline_id(self, sample_dataframe):
        """Test getting color map for baseline IDs."""
        color_map = ColorScheme.get_color_map(sample_dataframe, 'Baseline_ID')
        
        assert isinstance(color_map, dict)
        
        # Should have colors for all unique baseline IDs
        unique_baselines = sample_dataframe['Baseline_ID'].dropna().unique()
        assert len(color_map) == len(unique_baselines)
        
        # All colors should be valid hex codes
        for color in color_map.values():
            assert color.startswith('#')
    
    def test_get_color_map_nonexistent_column(self, sample_dataframe):
        """Test handling of non-existent column."""
        color_map = ColorScheme.get_color_map(sample_dataframe, 'NonExistentColumn')
        
        assert color_map == {}
    
    def test_get_color_map_consistency(self, sample_dataframe):
        """Test that color map is consistent across calls."""
        color_map1 = ColorScheme.get_color_map(sample_dataframe, 'Simulator')
        color_map2 = ColorScheme.get_color_map(sample_dataframe, 'Simulator')
        
        assert color_map1 == color_map2
    
    def test_get_color_map_handles_na(self):
        """Test that NA values are excluded from color map."""
        df = pd.DataFrame({
            'Simulator': ['JakubNet', 'DES', None, pd.NA]
        })
        
        color_map = ColorScheme.get_color_map(df, 'Simulator')
        
        # Should only have 2 entries (excluding NAs)
        assert len(color_map) == 2
        assert None not in color_map


class TestGetSymbolMap:
    """Test get_symbol_map method."""
    
    def test_get_symbol_map_basic(self):
        """Test getting symbol map for dataset labels."""
        labels = ['Dataset 1', 'Dataset 2', 'Dataset 3']
        symbol_map = ColorScheme.get_symbol_map(labels)
        
        assert isinstance(symbol_map, dict)
        assert len(symbol_map) == 3
        
        # Each label should have a symbol
        for label in labels:
            assert label in symbol_map
            assert symbol_map[label] in ColorScheme.MARKER_SYMBOLS
    
    def test_get_symbol_map_cycling(self):
        """Test that symbols cycle when more labels than symbols."""
        # Create more labels than available symbols
        labels = [f'Dataset {i}' for i in range(len(ColorScheme.MARKER_SYMBOLS) + 5)]
        symbol_map = ColorScheme.get_symbol_map(labels)
        
        assert len(symbol_map) == len(labels)
        
        # First label should match first symbol
        assert symbol_map[labels[0]] == ColorScheme.MARKER_SYMBOLS[0]
        
        # After cycling, should repeat
        assert symbol_map[labels[len(ColorScheme.MARKER_SYMBOLS)]] == ColorScheme.MARKER_SYMBOLS[0]
    
    def test_get_symbol_map_empty_list(self):
        """Test symbol map with empty list."""
        symbol_map = ColorScheme.get_symbol_map([])
        
        assert symbol_map == {}


class TestGetDefaultTheme:
    """Test get_default_theme method."""
    
    def test_get_default_theme_structure(self):
        """Test that default theme has required keys."""
        theme = ColorScheme.get_default_theme()
        
        assert isinstance(theme, dict)
        assert 'plot_bgcolor' in theme
        assert 'paper_bgcolor' in theme
        assert 'font' in theme
        assert 'xaxis' in theme
        assert 'yaxis' in theme
        assert 'legend' in theme
    
    def test_get_default_theme_colors(self):
        """Test that theme colors are valid."""
        theme = ColorScheme.get_default_theme()
        
        # Background colors should be valid CSS colors
        assert theme['plot_bgcolor'] in ['white', '#FFFFFF', '#ffffff', 'rgba(255,255,255,1)'] or \
               theme['plot_bgcolor'].startswith('#') or \
               theme['plot_bgcolor'] == 'white'
    
    def test_get_default_theme_nested_structure(self):
        """Test nested structure of theme."""
        theme = ColorScheme.get_default_theme()
        
        # Font should be a dict
        assert isinstance(theme['font'], dict)
        assert 'family' in theme['font']
        assert 'size' in theme['font']
        
        # Axes should have grid settings
        assert isinstance(theme['xaxis'], dict)
        assert 'showgrid' in theme['xaxis']
        
        assert isinstance(theme['yaxis'], dict)
        assert 'showgrid' in theme['yaxis']
