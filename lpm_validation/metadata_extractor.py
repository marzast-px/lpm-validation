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
        # JSON file has the same name as the folder
        folder_name = geometry_folder.rstrip('/').split('/')[-1]
        json_path = f"{geometry_folder.rstrip('/')}/{folder_name}.json"
        
        json_data = self.data_source.read_json(json_path)
        
        if not json_data:
            logger.warning(f"No JSON data found at {json_path}")
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
        
        # Determine morph type and value
        morph_type, morph_value = self._extract_morph_info(morph_parameters)
        
        metadata = {
            'unique_id': unique_id,
            'baseline_id': parent_baseline_id,
            'morph_type': morph_type,
            'morph_value': morph_value,
            'morph_parameters': morph_parameters
        }
        
        logger.debug(f"Extracted metadata: {metadata}")
        return metadata
    
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
