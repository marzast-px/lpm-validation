#!/usr/bin/env python3
"""Command-line entry point for LPM validation data collection."""

import argparse
import logging
import sys
from pathlib import Path
from lpm_validation.config import Configuration
from lpm_validation.collector import ValidationDataCollector


def setup_logging(verbose: bool = False):
    """
    Configure logging.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce boto3 logging noise
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Collect and export validation data from S3 simulation results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all cars with simulators from config file
  %(prog)s --config config.yaml
  
  # Process specific car with simulators from config file
  %(prog)s --config config.yaml --car Polestar3
  
  # Process all cars with specific simulator (override config)
  %(prog)s --config config.yaml --simulator DES
  
  # Process specific car with specific simulator (override config)
  %(prog)s --config config.yaml --car Audi_RS7_Sportback_Symmetric --simulator DES
  
  # Process all cars into a single CSV file
  %(prog)s --config config.yaml --single-file
  
  # Process multiple specific simulators (override config)
  %(prog)s --config config.yaml --simulator JakubNet,DES,SiemensMesh
  
  # Verbose logging
  %(prog)s --config config.yaml --verbose
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to configuration file (JSON or YAML)'
    )
    
    parser.add_argument(
        '--car',
        type=str,
        default=None,
        help='Process only this specific car (optional)'
    )
    
    parser.add_argument(
        '--simulator',
        type=str,
        default=None,
        help='Simulator(s) to process (overrides config file). Options: specific name (e.g., JakubNet, DES) or comma-separated list (e.g., JakubNet,DES,SiemensMesh). If not specified, uses simulators from config file.'
    )
    
    parser.add_argument(
        '--single-file',
        action='store_true',
        help='Export all data to a single CSV file instead of separate files per car'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from: {args.config}")
        config = Configuration.from_file(args.config)
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"S3 Bucket: {config.s3_bucket}")
        logger.info(f"Geometries Prefix: {config.geometries_prefix}")
        logger.info(f"Results Prefix: {config.results_prefix}")
        logger.info(f"Output Path: {config.output_path}")
        logger.info(f"Car Groups: {len(config.car_groups)} configured")
        logger.info(f"Default Simulators: {', '.join(config.simulators)}")
        
        # CLI simulator override
        if args.simulator:
            logger.info(f"CLI Override - Target Simulator(s): {args.simulator}")
        
        # Initialize collector
        collector = ValidationDataCollector(config=config)
        
        # Execute collection
        group_by_car = not args.single_file
        result = collector.execute(car_filter=args.car, simulator_filter=args.simulator, group_by_car=group_by_car)
        
        # Print final summary
        if result['status'] == 'success':
            logger.info("")
            logger.info("Final Statistics:")
            logger.info(f"  Total Geometries: {result['total_geometries']}")
            
            # Print stats for each processed simulator
            if 'simulators_processed' in result:
                for sim_name, sim_stats in result['simulators_processed'].items():
                    logger.info(f"  {sim_name}:")
                    logger.info(f"    With Results: {sim_stats['with_results']}")
                    logger.info(f"    Without Results: {sim_stats['without_results']}")
            
            logger.info(f"  Output Location: {result['output_path']}")
            sys.exit(0)
        else:
            logger.warning(f"Collection completed with status: {result['status']}")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
