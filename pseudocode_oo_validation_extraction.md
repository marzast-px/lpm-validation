# Pseudocode: Validation Dataset Extraction (Object-Oriented Design)

## Overview
Extract validation data from simulation results stored in S3 using an object-oriented architecture that separates concerns and manages the workflow through well-defined classes.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  ValidationDataCollector                     │
│                  (Main Orchestrator)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┼───────────┐
           │           │           │
           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌────────────┐
    │   S3     │ │Simulation│ │  Results   │
    │  Data    │ │ Metadata │ │   Data     │
    │ Source   │ │Extractor │ │ Extractor  │
    └──────────┘ └──────────┘ └────────────┘
           │
           ▼
    ┌──────────────┐
    │ Simulation   │
    │   Record     │
    │ (Data Model) │
    └──────────────┘
           │
           ▼
    ┌──────────────┐
    │     CSV      │
    │   Exporter   │
    └──────────────┘
```

## Class Definitions

### 1. Configuration Class
```
CLASS Configuration:
    """
    Holds all configuration parameters for the extraction process
    """
    
    ATTRIBUTES:
        s3_bucket: str
        geometries_prefix: str
        results_prefix: str
        output_path: str
        car_groups: dict
        aws_profile: str or None
        output_to_s3: bool
        max_workers: int (for concurrent operations)
    
    CONSTRUCTOR(s3_bucket, geometries_prefix, results_prefix, output_path, car_groups, **kwargs):
        # Initialize all configuration parameters
        # Validate required parameters
        # Set defaults for optional parameters
    
    METHOD validate():
        """Validate configuration parameters"""
        # Check that required fields are not empty
        # Validate S3 paths format
        # Ensure car_groups is a dictionary
    
    METHOD from_file(config_file_path):
        """Load configuration from JSON/YAML file"""
        # Read config file
        # Parse and create Configuration instance
        RETURN Configuration instance

END CLASS
```

### 2. S3DataSource Class
```
CLASS S3DataSource:
    """
    Handles all interactions with S3 storage
    Abstracts S3 operations from the rest of the application
    """
    
    ATTRIBUTES:
        s3_client: boto3 S3 client
        bucket: str
    
    CONSTRUCTOR(bucket, aws_profile=None):
        # Initialize S3 client with optional profile
        # Store bucket name
    
    METHOD list_folders(prefix, delimiter='/'):
        """List all folder prefixes under a given path"""
        # Use paginator to handle large result sets
        # Return list of folder prefixes
    
    METHOD list_files(prefix, extension=None):
        """List all files under a given path, optionally filtered by extension"""
        # Use paginator for listing
        # Filter by extension if provided
        # Return list of file keys
    
    METHOD read_json(s3_key):
        """Read and parse JSON file from S3"""
        # Fetch object from S3
        # Parse JSON content
        # Return dictionary or None on error
    
    METHOD write_csv(s3_key, csv_content):
        """Write CSV content to S3"""
        # Upload CSV string to S3
        # Set appropriate content type
    
    METHOD folder_exists(prefix):
        """Check if a folder/prefix exists"""
        # List objects with prefix (limit 1)
        # Return boolean
    
    METHOD find_matching_folder(base_prefix, pattern):
        """Find folder matching a specific pattern"""
        # List folders under base_prefix
        # Match against pattern
        # Return first match or None

END CLASS
```

### 3. SimulationRecord Class
```
CLASS SimulationRecord:
    """
    Data model representing a single simulation
    Encapsulates all data associated with one simulation run
    """
    
    ATTRIBUTES:
        # Identification
        car_name: str
        car_group: str
        simulator: str
        simulation_name: str
        s3_path: str
        
        # Metadata from simulation folder
        baseline_id: str
        morph_type: str
        morph_value: float
        
        # Results data
        converged: bool or None
        force_coefficients: dict
        averaged_forces: dict
        additional_metrics: dict
    
    CONSTRUCTOR(car_name, car_group, simulator, simulation_name, s3_path):
        # Initialize identification attributes
        # Set all result attributes to None (will be populated later)
    
    METHOD set_metadata(baseline_id, morph_type, morph_value):
        """Set simulation metadata"""
        # Store metadata values
    
    METHOD set_results(converged, coefficients, forces, metrics):
        """Set results data"""
        # Store all results data
    
    METHOD is_complete():
        """Check if all required data has been populated"""
        # Return boolean indicating if record is complete
    
    METHOD to_dict():
        """Convert record to flat dictionary for CSV export"""
        # Flatten nested dictionaries
        # Return single-level dictionary
    
    METHOD get_status():
        """Get processing status of this record"""
        # Return status string (pending, complete, error, etc.)

END CLASS
```

### 4. SimulationMetadataExtractor Class
```
CLASS SimulationMetadataExtractor:
    """
    Extracts metadata from simulation folders in S3
    Parses simulation configuration files
    """
    
    ATTRIBUTES:
        data_source: S3DataSource
    
    CONSTRUCTOR(data_source):
        # Store reference to S3DataSource
    
    METHOD extract_from_folder(s3_folder_path):
        """Extract metadata from a simulation folder"""
        # List JSON files in the folder
        # Read the simulation configuration JSON
        # Parse and extract: baseline_id, morph_type, morph_value
        # Return metadata dictionary or None
    
    METHOD parse_simulation_config(json_data):
        """Parse simulation configuration JSON"""
        # Extract relevant fields
        # Handle missing fields gracefully
        # Return structured metadata

END CLASS
```

### 5. ResultsDataExtractor Class
```
CLASS ResultsDataExtractor:
    """
    Extracts and processes results data from simulation outputs
    Computes force coefficients and statistical metrics
    """
    
    ATTRIBUTES:
        data_source: S3DataSource
    
    CONSTRUCTOR(data_source):
        # Store reference to S3DataSource
    
    METHOD extract_from_folder(results_folder_path):
        """Extract all results data from a results folder"""
        # Read export_scalars.json
        # Read export_force_series.json
        # Process and return combined results
    
    METHOD extract_force_coefficients(scalars_data):
        """Extract force coefficient values"""
        # Parse scalars JSON
        # Extract: Cd, Cl, Cs, Cd_front, Cl_front, Cl_rear
        # Return coefficients dictionary
    
    METHOD check_convergence(scalars_data):
        """Determine if simulation converged"""
        # Check convergence flag or criteria
        # Return boolean
    
    METHOD compute_averaged_forces(force_series_data):
        """Compute time-averaged forces"""
        # Extract time series arrays
        # Compute averages over specified window
        # Return averaged forces dictionary
    
    METHOD compute_statistical_metrics(force_series_data):
        """Compute statistical metrics from time series"""
        # Calculate: std, max, min for each force component
        # Return metrics dictionary

END CLASS
```

### 6. SimulationDiscovery Class
```
CLASS SimulationDiscovery:
    """
    Discovers all simulations in the geometry folder structure
    Builds initial list of simulation records
    """
    
    ATTRIBUTES:
        data_source: S3DataSource
        metadata_extractor: SimulationMetadataExtractor
        car_groups: dict
    
    CONSTRUCTOR(data_source, metadata_extractor, car_groups):
        # Store dependencies
    
    METHOD discover_all(geometries_prefix):
        """Discover all simulations in the geometry folder structure"""
        simulation_records = []
        
        # Get all car folders
        car_folders = data_source.list_folders(geometries_prefix)
        
        FOR EACH car_folder IN car_folders:
            car_name = extract_name_from_path(car_folder)
            car_group = car_groups.get(car_name, "unknown")
            
            # Get simulator folders for this car
            simulator_folders = data_source.list_folders(car_folder)
            
            FOR EACH simulator_folder IN simulator_folders:
                simulator_name = extract_name_from_path(simulator_folder)
                
                # Get simulation folders
                simulation_folders = data_source.list_folders(simulator_folder)
                
                FOR EACH sim_folder IN simulation_folders:
                    IF sim_folder matches morph pattern:
                        # Create simulation record
                        record = create_simulation_record(
                            car_name, car_group, simulator_name, sim_folder
                        )
                        simulation_records.append(record)
        
        RETURN simulation_records
    
    METHOD create_simulation_record(car_name, car_group, simulator_name, sim_folder):
        """Create and populate initial simulation record"""
        # Extract simulation name from folder path
        # Create SimulationRecord instance
        # Extract and set metadata using metadata_extractor
        # Return record
    
    METHOD extract_name_from_path(s3_path):
        """Extract folder name from S3 path"""
        # Remove trailing slash
        # Split by '/' and get last segment
        # Return name

END CLASS
```

### 7. ResultsMatcher Class
```
CLASS ResultsMatcher:
    """
    Matches simulation records with their corresponding results folders
    Handles result folder lookup and matching logic
    """
    
    ATTRIBUTES:
        data_source: S3DataSource
        results_extractor: ResultsDataExtractor
        results_prefix: str
    
    CONSTRUCTOR(data_source, results_extractor, results_prefix):
        # Store dependencies and configuration
    
    METHOD match_and_extract(simulation_record):
        """Find and extract results for a simulation record"""
        # Find matching results folder
        results_folder = find_results_folder(simulation_record.simulation_name)
        
        IF results_folder:
            # Extract results data
            results = results_extractor.extract_from_folder(results_folder)
            # Update simulation record with results
            simulation_record.set_results(results)
        ELSE:
            # Try default folder as fallback
            handle_missing_results(simulation_record)
        
        RETURN simulation_record
    
    METHOD find_results_folder(simulation_name):
        """Find the results folder matching simulation name"""
        # Search for folders under results_prefix
        # Match by prefix or pattern
        # Return folder path or None
    
    METHOD handle_missing_results(simulation_record):
        """Handle case where results are not found"""
        # Try default folder
        # Or mark as N/A
        # Log warning

END CLASS
```

### 8. CSVExporter Class
```
CLASS CSVExporter:
    """
    Exports simulation records to CSV files
    Handles formatting and output location
    """
    
    ATTRIBUTES:
        output_path: str
        data_source: S3DataSource (optional, for S3 output)
        output_to_s3: bool
    
    CONSTRUCTOR(output_path, data_source=None, output_to_s3=False):
        # Store configuration
    
    METHOD export_grouped_by_car(simulation_records):
        """Export simulation records grouped by car"""
        # Group records by car_name
        grouped = group_by_car(simulation_records)
        
        FOR EACH car_name, records IN grouped:
            # Export this car's data
            export_car_data(car_name, records)
    
    METHOD export_car_data(car_name, records):
        """Export data for a single car to CSV"""
        # Define CSV columns
        # Convert records to rows using record.to_dict()
        # Format as CSV content
        # Write to destination (local file or S3)
    
    METHOD define_csv_columns():
        """Define the columns for CSV output"""
        RETURN [
            "Name", "Simulator", "Morph_Type", "Morph_Value",
            "Baseline_ID", "Converged", "Cd", "Cl", "Cs",
            "Cd_front", "Cl_front", "Cl_rear",
            "Avg_Fx", "Avg_Fy", "Avg_Fz",
            "Std_Fx", "Std_Fy", "Std_Fz"
        ]
    
    METHOD group_by_car(simulation_records):
        """Group simulation records by car name"""
        # Create dictionary grouped by car_name
        # Return grouped dictionary
    
    METHOD write_to_destination(filename, csv_content):
        """Write CSV to appropriate destination"""
        IF output_to_s3:
            # Upload to S3 using data_source
        ELSE:
            # Write to local file system

END CLASS
```

### 9. ValidationDataCollector (Main Orchestrator)
```
CLASS ValidationDataCollector:
    """
    Main orchestrator that coordinates the entire extraction workflow
    Manages the pipeline from discovery to export
    """
    
    ATTRIBUTES:
        config: Configuration
        data_source: S3DataSource
        discovery: SimulationDiscovery
        matcher: ResultsMatcher
        exporter: CSVExporter
        logger: Logger
    
    CONSTRUCTOR(config):
        # Store configuration
        # Create S3DataSource
        # Create metadata and results extractors
        # Create SimulationDiscovery
        # Create ResultsMatcher
        # Create CSVExporter
        # Setup logging
    
    METHOD execute():
        """Execute the complete extraction workflow"""
        logger.info("Starting validation data extraction")
        
        # Step 1: Discover all simulations
        logger.info("Discovering simulations...")
        simulation_records = discovery.discover_all(config.geometries_prefix)
        logger.info(f"Found {len(simulation_records)} simulations")
        
        # Step 2: Match with results and extract data
        logger.info("Extracting results data...")
        simulation_records = process_results(simulation_records)
        
        # Step 3: Export to CSV
        logger.info("Exporting to CSV...")
        exporter.export_grouped_by_car(simulation_records)
        
        logger.info("Extraction complete")
        RETURN simulation_records
    
    METHOD process_results(simulation_records):
        """Process results for all simulation records"""
        IF config.max_workers > 1:
            # Use concurrent processing
            RETURN process_results_concurrent(simulation_records)
        ELSE:
            # Sequential processing
            FOR EACH record IN simulation_records:
                matcher.match_and_extract(record)
                track_progress(current, total)
            
            RETURN simulation_records
    
    METHOD process_results_concurrent(simulation_records):
        """Process results concurrently for better performance"""
        # Create ThreadPoolExecutor with max_workers
        # Submit all matching tasks
        # Collect results as they complete
        # Handle errors gracefully
        # Track progress
        RETURN processed_records
    
    METHOD track_progress(current, total):
        """Track and log progress"""
        # Calculate percentage
        # Log progress information at regular intervals

END CLASS
```

## Usage Example

```python
# Option 1: Create configuration programmatically
config = Configuration(
    s3_bucket="my-simulation-bucket",
    geometries_prefix="sim_data/revalidation/geometries",
    results_prefix="sim_data/revalidation/results",
    output_path="./output",
    car_groups={
        "audi_rs7_sportback": "sedan",
        "audi_q7": "suv",
        "bmw_x5": "suv"
    },
    aws_profile="default",
    max_workers=10,
    output_to_s3=False
)

# Option 2: Load configuration from file
config = Configuration.from_file("config.yaml")

# Validate configuration
config.validate()

# Create and execute collector
collector = ValidationDataCollector(config)
results = collector.execute()

# Access results if needed
FOR EACH record IN results:
    IF NOT record.is_complete():
        print(f"Incomplete record: {record.simulation_name}")
```

## Class Interaction Flow

```
1. User creates Configuration
        ↓
2. ValidationDataCollector initialized with Configuration
   - Creates S3DataSource
   - Creates SimulationMetadataExtractor
   - Creates ResultsDataExtractor
   - Creates SimulationDiscovery
   - Creates ResultsMatcher
   - Creates CSVExporter
        ↓
3. ValidationDataCollector.execute() called
        ↓
4. SimulationDiscovery.discover_all()
   ├─> S3DataSource.list_folders() - get car folders
   ├─> S3DataSource.list_folders() - get simulator folders
   ├─> S3DataSource.list_folders() - get simulation folders
   ├─> SimulationMetadataExtractor.extract_from_folder()
   │   └─> S3DataSource.read_json() - read metadata
   └─> Creates SimulationRecord instances
        ↓
5. ValidationDataCollector.process_results()
   FOR EACH SimulationRecord:
   └─> ResultsMatcher.match_and_extract()
       ├─> S3DataSource.find_matching_folder() - find results
       ├─> ResultsDataExtractor.extract_from_folder()
       │   ├─> S3DataSource.read_json() - read scalars
       │   ├─> S3DataSource.read_json() - read force series
       │   ├─> extract_force_coefficients()
       │   ├─> check_convergence()
       │   ├─> compute_averaged_forces()
       │   └─> compute_statistical_metrics()
       └─> SimulationRecord.set_results()
        ↓
6. CSVExporter.export_grouped_by_car()
   ├─> group_by_car() - group records
   └─> FOR EACH car:
       ├─> SimulationRecord.to_dict() - convert to flat dict
       ├─> Format as CSV
       └─> write_to_destination()
           └─> S3DataSource.write_csv() OR local file write
        ↓
7. Complete - returns list of SimulationRecords
```

## Key Design Principles

### Separation of Concerns
- **S3DataSource**: All S3 operations isolated
- **Extractors**: Data extraction logic separated from orchestration
- **SimulationRecord**: Pure data model
- **ValidationDataCollector**: High-level workflow only

### Dependency Injection
- Dependencies passed through constructors
- Easy to mock for testing
- Flexible and maintainable

### Single Responsibility
- Each class has one clear purpose
- Methods are focused and cohesive
- Easy to understand and modify

### Extensibility
- New data sources can be added (e.g., local filesystem)
- New export formats can be added (e.g., JSON, Parquet)
- New extractors can be added for different data types

## Error Handling Strategy

```
CLASS ErrorHandler:
    """
    Centralized error handling for the extraction process
    """
    
    ATTRIBUTES:
        logger: Logger
        error_records: list
    
    METHOD handle_extraction_error(simulation_record, error):
        """Handle errors during extraction"""
        # Log error with context
        # Mark simulation_record as error state
        # Store in error_records for later review
    
    METHOD generate_error_report():
        """Generate report of all errors encountered"""
        # Create summary of errors
        # Group by error type
        # Return formatted report

END CLASS
```

## Testing Strategy

### Unit Tests
- Test each class independently
- Mock dependencies (e.g., S3DataSource)
- Test edge cases and error conditions

### Integration Tests
- Test interactions between classes
- Use test S3 bucket or mocked S3
- Verify complete workflow

### Example Test Structure
```
TEST SimulationDiscovery:
    SETUP:
        # Create mock S3DataSource
        # Create test car_groups dict
        # Create instance of SimulationDiscovery
    
    TEST discover_all_finds_simulations:
        # Mock S3DataSource to return test data
        # Call discover_all()
        # Assert correct number of records returned
        # Assert records have correct attributes
    
    TEST handles_missing_metadata:
        # Mock S3DataSource to return folders without JSON
        # Call discover_all()
        # Assert graceful handling
```

## Configuration File Format

### YAML Example
```yaml
s3_bucket: my-simulation-bucket
geometries_prefix: sim_data/revalidation/geometries
results_prefix: sim_data/revalidation/results
output_path: ./output
output_to_s3: false
aws_profile: default
max_workers: 10

car_groups:
  audi_rs7_sportback: sedan
  audi_q7: suv
  bmw_x5: suv
  porsche_cayenne: suv
```

### JSON Example
```json
{
  "s3_bucket": "my-simulation-bucket",
  "geometries_prefix": "sim_data/revalidation/geometries",
  "results_prefix": "sim_data/revalidation/results",
  "output_path": "./output",
  "output_to_s3": false,
  "aws_profile": "default",
  "max_workers": 10,
  "car_groups": {
    "audi_rs7_sportback": "sedan",
    "audi_q7": "suv",
    "bmw_x5": "suv"
  }
}
```

## Extension Points

### Adding New Data Sources
```
CLASS LocalFileSystemDataSource:
    """Alternative to S3DataSource for local files"""
    
    # Implement same interface as S3DataSource
    # Methods: list_folders, read_json, write_csv, etc.

# Usage: Pass to ValidationDataCollector instead of S3DataSource
```

### Adding New Export Formats
```
CLASS ParquetExporter:
    """Export to Parquet format instead of CSV"""
    
    # Implement same interface as CSVExporter
    # Methods: export_grouped_by_car, export_car_data, etc.

# Usage: Create and pass to ValidationDataCollector
```

### Adding Data Validation
```
CLASS DataValidator:
    """Validate extracted data before export"""
    
    METHOD validate_record(simulation_record):
        """Validate a single simulation record"""
        # Check for required fields
        # Validate value ranges
        # Check data consistency
        # Return validation result
    
    METHOD validate_all(simulation_records):
        """Validate all records"""
        # Validate each record
        # Collect validation errors
        # Return summary report

# Usage: Insert into workflow between extraction and export
```
