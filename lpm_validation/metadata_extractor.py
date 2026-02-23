"""Metadata extractor for geometry JSON files."""

import logging
from typing import Optional, Dict, Tuple
from lpm_validation.s3_data_source import S3DataSource

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts metadata from simulation geometry folders in S3."""
    
    def __init__(self, data_source: S3DataSource):
        """
        Initialize metadata extractor.
        
        Args:
            data_source: S3DataSource instance
        """
        self.data_source = data_source
    
    def extract_from_folder(self, geometry_folder: str) -> Optional[Dict]:
        """
        Extract metadata from a geometry folder.
        
        Args:
            geometry_folder: S3 path to geometry folder
            
        Returns:
            Dictionary with metadata or None if error
        """
        # Find JSON file in the folder
        json_files = self.data_source.list_files(geometry_folder, extension='.json')
        
        if not json_files:
            logger.warning(f"No JSON files found in {geometry_folder}")
            return None
        
        # Read the first JSON file found
        json_path = json_files[0]
        json_data = self.data_source.read_json(json_path)
        
        if not json_data:
            return None
        
        return self.parse_geometry_json(json_data)
    
    def parse_geometry_json(self, json_data: Dict) -> Dict:
        """
        Parse geometry JSON and extract metadata.
        
        Args:
            json_data: Parsed JSON dictionary
            
        Returns:
            Dictionary with extracted metadata
        """
        unique_id = json_data.get('unique_id', '')
        parent_baseline_id = json_data.get('parent_baseline_id', '')
        morph_parameters = json_data.get('morph_parameters', {})
        
        # Extract car name from unique_id or baseline
        car_name = self._extract_car_name(unique_id, parent_baseline_id)
        
        # Determine morph type and value
        morph_type, morph_value = self._extract_morph_info(morph_parameters)
        
        metadata = {
            'unique_id': unique_id,
            'car_name': car_name,
            'baseline_id': parent_baseline_id,
            'morph_type': morph_type,
            'morph_value': morph_value,
            'morph_parameters': morph_parameters
        }
        
        logger.debug(f"Extracted metadata: {metadata}")
        return metadata
    
    def _extract_car_name(self, unique_id: str, baseline_id: str) -> str:
        """
        Extract car name from unique_id or baseline_id.
        
        Args:
            unique_id: Unique simulation ID
            baseline_id: Parent baseline ID
            
        Returns:
            Car name
        """
        # Try to extract from baseline_id first
        if baseline_id:
            # Remove _Symmetric suffix if present
            car_name = baseline_id.replace('_Symmetric', '')
            return car_name
        
        # Fall back to unique_id
        if unique_id:
            # Extract up to _Morph
            parts = unique_id.split('_Morph_')
            if parts:
                car_name = parts[0].replace('_Symmetric', '')
                return car_name
        
        return 'Unknown'
    
    def _extract_morph_info(self, morph_parameters: Dict[str, float]) -> Tuple[Optional[str], Optional[float]]:
        """
        Extract morph type and value from morph parameters.
        
        Args:
            morph_parameters: Dictionary of morph parameters
            
        Returns:
            Tuple of (morph_type, morph_value)
        """
        # Find non-zero parameter
        for param_name, param_value in morph_parameters.items():
            if param_value != 0.0:
                return param_name, param_value
        
        # If all zero, it's baseline
        return None, 0.0
