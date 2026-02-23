# Quick Start Guide

## Installation

```bash
# Option 1: Run setup script
./setup.sh

# Option 2: Manual installation
pip install -e .
```

## Configuration

1. Copy the example configuration:
```bash
cp config.example.yaml config.yaml
```

2. Edit `config.yaml` with your settings:
```yaml
s3_bucket: "your-actual-bucket-name"
geometries_prefix: "sim-data/validation/geometries"
results_prefix: "sim-data/validation/outputs"
output_path: "./validation_output"

car_groups:
  Polestar3: "Polestar3"
  Polestar4: "Polestar4"
  EX90: "EX90"
```

3. Configure AWS credentials:
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
```

## Usage

### Test Connection

```bash
lpm-validation --config config.yaml --test-connection
```

### Process All Cars

```bash
lpm-validation --config config.yaml
```

### Process Single Car

```bash
lpm-validation --config config.yaml --car Polestar3
```

### Output to S3

```bash
lpm-validation --config config.yaml --output-s3
```

### Enable Verbose Logging

```bash
lpm-validation --config config.yaml --verbose
```

## Expected Output

After successful execution, you'll find:

```
validation_output/
├── Polestar3_validation_data.csv
├── Polestar4_validation_data.csv
├── EX90_validation_data.csv
└── validation_summary.txt
```

## Troubleshooting

### AWS Credentials Error
```
Error: Unable to locate credentials
```
**Solution:** Run `aws configure` or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### S3 Access Denied
```
Error: Access Denied
```
**Solution:** Verify your AWS credentials have read access to the S3 bucket.

### No Geometries Found
```
Warning: No geometry folders found
```
**Solution:** Check that `geometries_prefix` in config.yaml matches the S3 structure.

### Import Errors (Development)
```
Import "boto3" could not be resolved
```
**Solution:** Install dependencies: `pip install -e .`

## Module Structure

The tool is organized into modular components:

- `config.py` - Configuration management
- `s3_data_source.py` - S3 operations
- `simulation_record.py` - Data model
- `metadata_extractor.py` - Parse geometry JSON
- `results_extractor.py` - Parse results, calculate coefficients
- `discovery.py` - Discover geometries
- `results_matcher.py` - Match results to geometries
- `csv_exporter.py` - Export CSV files
- `summary_report.py` - Generate reports
- `collector.py` - Main orchestrator
- `main.py` - CLI entry point

## Python API Example

```python
from lpm_validation import Configuration, ValidationDataCollector

# Load config
config = Configuration.from_file('config.yaml')

# Create collector
collector = ValidationDataCollector(
    config=config,
    output_to_s3=False  # Use True for S3 output
)

# Run collection
result = collector.execute(car_filter=None)  # None = all cars

# Check results
print(f"Status: {result['status']}")
print(f"Total geometries: {result['total_geometries']}")
print(f"With results: {result['with_results']}")
print(f"Without results: {result['without_results']}")
```

## Support

For issues or questions, check the [README.md](README.md) for detailed documentation.
