# LPM Validation

Validation data collection and export tool for LPM (Laminar Particle Model) simulation results stored in AWS S3.

## Overview

This tool discovers geometry metadata and simulation results from S3, matches them together, calculates force coefficients, and exports structured CSV files with validation data.

**Key Features:**
- Discovers geometries with morph parameters from S3
- Matches geometries with simulation results from multiple simulators
- Calculates drag (Cd) and lift (Cl) coefficients from force data
- Averages time series data from force monitors
- Exports CSV files grouped by car
- Generates summary reports showing results availability

## Project Structure

```
lpm-validation/
├── lpm_validation/           # Main Python package
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── s3_data_source.py    # S3 data access layer
│   ├── simulation_record.py # Data model
│   ├── metadata_extractor.py # Parse geometry JSON
│   ├── results_extractor.py  # Parse results and calculate coefficients
│   ├── discovery.py         # Discover geometries
│   ├── results_matcher.py   # Match results to geometries
│   ├── csv_exporter.py      # Export CSV files
│   ├── summary_report.py    # Generate summary reports
│   ├── collector.py         # Main orchestrator
│   └── main.py              # CLI entry point
├── config.example.yaml      # Example configuration
├── scripts/                 # Additional scripts
├── tests/                   # Test files
├── README.md
├── pyproject.toml
└── requirements.txt
```

## Installation

```bash
# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Configuration

Create a configuration file (YAML or JSON) with your S3 bucket and path settings:

```yaml
# config.yaml
s3_bucket: "your-s3-bucket-name"
geometries_prefix: "sim-data/validation/geometries"
results_prefix: "sim-data/validation/outputs"
output_path: "./validation_output"

car_groups:
  Polestar3: "Polestar3"
  Polestar4: "Polestar4"
  EX90: "EX90"
```

See [config.example.yaml](config.example.yaml) for a template.

## Usage

### Command Line

```bash
# Process all cars
lpm-validation --config config.yaml

# Process specific car only
lpm-validation --config config.yaml --car Polestar3

# Output to S3 instead of local files
lpm-validation --config config.yaml --output-s3

# Test S3 connection
lpm-validation --config config.yaml --test-connection

# Enable verbose logging
lpm-validation --config config.yaml --verbose
```

### Python API

```python
from lpm_validation import Configuration, ValidationDataCollector

# Load configuration
config = Configuration.from_file('config.yaml')

# Initialize collector
collector = ValidationDataCollector(config, output_to_s3=False)

# Test connection (optional)
collector.test_connection()

# Execute collection
result = collector.execute(car_filter='Polestar3')

print(f"Processed {result['total_geometries']} geometries")
print(f"Found results for {result['with_results']} geometries")
```

## Data Processing Workflow

1. **Discovery Phase**
   - Lists all geometry folders from S3
   - Extracts metadata from `geometry.json` files
   - Identifies car name, baseline ID, and morph parameters

2. **Results Matching Phase**
   - Searches for corresponding results folders
   - Handles multiple simulators (JakubNet, DES, SiemensSolve, etc.)
   - Extracts force data from `results.json` and `Force_Series.csv`
   - Calculates Cd/Cl coefficients using: `C = 2*F/(ρ*v²*A)`
   - Averages last 300 iterations from time series

3. **Export Phase**
   - Groups results by car
   - Exports CSV files: `{car_name}_validation_data.csv`
   - Includes all metadata, coefficients, and statistics

4. **Summary Report Phase**
   - Generates validation summary report
   - Shows total/available/missing results per car
   - Displays simulator and convergence statistics

## Output Files

### CSV Format

Each car gets a CSV file with columns:
- `Name`, `Unique_ID`, `Car_Name`, `Car_Group`, `Simulator`
- `Baseline_ID`, `Morph_Type`, `Morph_Value`
- `Converged`, `Cd`, `Cl`, `Drag_N`, `Lift_N`
- `Avg_Cd`, `Avg_Cl`, `Avg_Drag_N`, `Avg_Lift_N`
- `Std_Cd`, `Std_Cl`, `Std_Drag_N`, `Std_Lift_N`
- `Has_Results`, `Status`

### Summary Report

Text file showing:
- Overall statistics (total, with/without results)
- Per-car breakdown with percentages
- Simulator distribution
- Convergence statistics

## AWS Credentials

Ensure AWS credentials are configured:

```bash
# Via AWS CLI
aws configure

# Or via environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Code formatting
black lpm_validation/

# Linting
flake8 lpm_validation/
```

## License

TBD
