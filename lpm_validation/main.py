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
  # Process all cars with default simulator (JakubNet)
  %(prog)s --config config.yaml
  
  # Process specific car with default simulator (JakubNet)
  %(prog)s --config config.yaml --car Polestar3
  
  # Process all cars with DES simulator
  %(prog)s --config config.yaml --simulator DES
  
  # Process specific car with DES simulator
  %(prog)s --config config.yaml --car Audi_RS7_Sportback_Symmetric --simulator DES
  
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
        default="JakubNet",
        help='Process only results from this simulator (e.g., JakubNet, DES) (optional, default: JakubNet)'
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
        
        # Default simulator if not specified
        simulator = args.simulator if args.simulator else "JakubNet"
        logger.info(f"Target Simulator: {simulator}")
        
        # Initialize collector
        collector = ValidationDataCollector(config=config)
        
        # Execute collection
        result = collector.execute(car_filter=args.car, simulator_filter=simulator)
        
        # Print final summary
        if result['status'] == 'success':
            logger.info("")
            logger.info("Final Statistics:")
            logger.info(f"  Total Geometries: {result['total_geometries']}")
            logger.info(f"  With Results: {result['with_results']}")
            logger.info(f"  Without Results: {result['without_results']}")
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
