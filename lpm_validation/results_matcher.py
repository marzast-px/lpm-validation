"""Results matcher module."""

import logging
from typing import Optional
from lpm_validation.s3_data_source import S3DataSource
from lpm_validation.results_extractor import ResultsExtractor
from lpm_validation.simulation_record import SimulationRecord

logger = logging.getLogger(__name__)


class ResultsMatcher:
    """Matches simulation records with their corresponding results folders."""
    
    def __init__(self, data_source: S3DataSource, results_extractor: ResultsExtractor, 
                 results_prefix: str):
        """
        Initialize results matcher.
        
        Args:
            data_source: S3DataSource instance
            results_extractor: ResultsExtractor instance
            results_prefix: S3 prefix for results
        """
        self.data_source = data_source
        self.results_extractor = results_extractor
        self.results_prefix = results_prefix
    
    def match_and_extract(self, simulation_record: SimulationRecord) -> SimulationRecord:
        """
        Find and extract results for a simulation record.
        
        Args:
            simulation_record: SimulationRecord to update
            
        Returns:
            Updated SimulationRecord
        """
        # Find matching results folder
        results_folder, simulator = self.find_results_folder(simulation_record.unique_id)
        
        if not results_folder:
            logger.debug(f"No results found for {simulation_record.unique_id}")
            simulation_record.has_results = False
            return simulation_record
        
        logger.debug(f"Found results for {simulation_record.unique_id} in {results_folder}")
        
        # Extract results data
        results = self.results_extractor.extract_from_folder(results_folder, simulator)
        
        if not results:
            logger.warning(f"Failed to extract results from {results_folder}")
            simulation_record.has_results = False
            return simulation_record
        
        # Update simulation record with results
        simulation_record.set_results(
            converged=results.get('converged', False),
            simulator=simulator,
            cd=results.get('cd'),
            cl=results.get('cl'),
            drag_n=results.get('drag_n'),
            lift_n=results.get('lift_n'),
            avg_cd=results.get('avg_cd'),
            avg_cl=results.get('avg_cl'),
            avg_drag_n=results.get('avg_drag_n'),
            avg_lift_n=results.get('avg_lift_n'),
            std_cd=results.get('std_cd'),
            std_cl=results.get('std_cl'),
            std_drag_n=results.get('std_drag_n'),
            std_lift_n=results.get('std_lift_n')
        )
        
        logger.debug(f"Updated record with results: converged={results.get('converged')}")
        
        return simulation_record
    
    def find_results_folder(self, unique_id: str) -> tuple[Optional[str], str]:
        """
        Find the results folder matching simulation unique_id.
        
        Args:
            unique_id: Unique simulation ID from geometry
            
        Returns:
            Tuple of (results_folder_path, simulator_name) or (None, "")
        """
        # List all folders under results_prefix
        all_folders = self.data_source.list_folders(self.results_prefix)
        
        # Look for exact match or match with simulator prefix
        for folder in all_folders:
            folder_name = self.data_source.extract_folder_name(folder)
            
            # Check for exact match (baseline/JakubNet)
            if folder_name == unique_id:
                return folder, "JakubNet"
            
            # Check for match with simulator prefix
            # Format: <SIMULATOR_PREFIX>_<unique_id>
            if unique_id in folder_name:
                # Extract simulator prefix
                simulator = folder_name.replace(f"_{unique_id}", "").replace(unique_id, "")
                if simulator:
                    simulator = simulator.strip('_')
                else:
                    simulator = "JakubNet"
                
                return folder, simulator
        
        return None, ""
