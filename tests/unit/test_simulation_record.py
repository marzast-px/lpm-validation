"""Unit tests for simulation_record module."""

import pytest
from lpm_validation.simulation_record import SimulationRecord


class TestSimulationRecord:
    """Test SimulationRecord dataclass."""
    
    def test_init_baseline(self):
        """Test creating a baseline record."""
        record = SimulationRecord(
            geometry_name="Polestar3_baseline_001",
            unique_id="Polestar3_baseline_001",
            car_name="Polestar3",
            car_group="Polestar3",
            baseline_id="Polestar3_baseline",
            morph_type=None,
            morph_value=None
        )
        
        assert record.geometry_name == "Polestar3_baseline_001"
        assert record.car_name == "Polestar3"
        assert record.morph_type is None
        assert record.has_results is False
    
    def test_init_with_morph(self):
        """Test creating a record with morph parameters."""
        record = SimulationRecord(
            geometry_name="Polestar3_morph_001",
            unique_id="Polestar3_morph_001",
            car_name="Polestar3",
            car_group="Polestar3",
            baseline_id="Polestar3_baseline",
            morph_type="ride_height",
            morph_value=10.0
        )
        
        assert record.morph_type == "ride_height"
        assert record.morph_value == 10.0
    
    def test_get_status_no_results(self, sample_simulation_record):
        """Test status when no results available."""
        status = sample_simulation_record.get_status()
        assert status == "No Results"
    
    def test_get_status_converged(self):
        """Test status when converged."""
        record = SimulationRecord(
            geometry_name="test",
            unique_id="test",
            car_name="Test",
            car_group="Test",
            baseline_id="test_baseline",
            has_results=True,
            converged=True
        )
        
        status = record.get_status()
        assert status == "Converged"
    
    def test_get_status_not_converged(self):
        """Test status when not converged."""
        record = SimulationRecord(
            geometry_name="test",
            unique_id="test",
            car_name="Test",
            car_group="Test",
            baseline_id="test_baseline",
            has_results=True,
            converged=False
        )
        
        status = record.get_status()
        assert status == "Not Converged"
    
    def test_get_status_unknown_convergence(self):
        """Test status when convergence is unknown."""
        record = SimulationRecord(
            geometry_name="test",
            unique_id="test",
            car_name="Test",
            car_group="Test",
            baseline_id="test_baseline",
            has_results=True,
            converged=None
        )
        
        status = record.get_status()
        assert status == "Unknown"
    
    def test_has_results_flag(self, sample_simulation_record_with_results):
        """Test that has_results flag is set correctly."""
        assert sample_simulation_record_with_results.has_results is True
        assert sample_simulation_record_with_results.simulator == "JakubNet"
        assert sample_simulation_record_with_results.cd == 0.342
