# Testing Documentation

## Overview

The lpm-validation package includes a comprehensive test suite with unit tests, integration tests, and end-to-end tests to validate all functionality.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared pytest fixtures
├── pytest.ini                     # Pytest configuration
├── fixtures/                      # Test data files
│   ├── geometry.json             # Sample geometry metadata
│   ├── geometry_morph.json       # Sample morph geometry
│   ├── results.json              # Sample results data
│   ├── Force_Series.csv          # Sample time series data
│   └── config_test.yaml          # Sample configuration
├── unit/                          # Unit tests
│   ├── test_config.py            # Configuration tests
│   ├── test_simulation_record.py # Data model tests
│   ├── test_metadata_extractor.py# Metadata extraction tests
│   ├── test_results_extractor.py # Results extraction tests
│   ├── test_csv_exporter.py      # CSV export tests
│   └── test_summary_report.py    # Report generation tests
└── integration/                   # Integration tests
    ├── test_collector.py         # Collector workflow tests
    └── test_end_to_end.py        # End-to-end tests
```

## Running Tests

### Run All Tests

```bash
# Using test runner script (recommended)
./run_tests.sh

# Using pytest directly
pytest tests/

# With coverage report
pytest --cov=lpm_validation --cov-report=html tests/
```

### Run Specific Test Categories

```bash
# Unit tests only
./run_tests.sh --unit-only
pytest tests/unit/

# Integration tests only
./run_tests.sh --integration-only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_config.py

# Specific test class
pytest tests/unit/test_config.py::TestConfiguration

# Specific test method
pytest tests/unit/test_config.py::TestConfiguration::test_init_with_valid_params
```

### Test Options

```bash
# Verbose output
./run_tests.sh --verbose
pytest -vv

# Skip coverage
./run_tests.sh --no-coverage

# Show print statements
pytest -s

# Stop at first failure
pytest -x

# Run last failed tests
pytest --lf

# Show slowest tests
pytest --durations=10
```

## Test Coverage

The test suite aims for >70% code coverage. Current coverage includes:

- **Configuration**: Loading, validation, car name extraction
- **Data Models**: SimulationRecord creation and status
- **Metadata Extraction**: Geometry JSON parsing, morph detection
- **Results Extraction**: Coefficient calculation, time series averaging
- **CSV Export**: Grouping, formatting, file writing
- **Summary Reports**: Statistics calculation, report generation
- **Integration**: Full workflow orchestration

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=lpm_validation --cov-report=html tests/

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Fixtures

### Shared Fixtures (conftest.py)

- `fixtures_dir`: Path to test fixtures directory
- `sample_geometry_json`: Sample baseline geometry data
- `sample_geometry_morph_json`: Sample morph geometry data
- `sample_results_json`: Sample results data
- `sample_force_series_csv`: Path to sample force series CSV
- `sample_config_file`: Path to sample configuration file
- `sample_config`: Pre-configured Configuration object
- `sample_simulation_record`: Empty SimulationRecord
- `sample_simulation_record_with_results`: Populated SimulationRecord
- `mock_s3_client`: Mocked boto3 S3 client
- `mock_s3_data_source`: Mocked S3DataSource

### Using Fixtures in Tests

```python
def test_my_function(sample_config, sample_geometry_json):
    """Test with fixtures."""
    # Fixtures are automatically injected
    result = my_function(sample_config, sample_geometry_json)
    assert result is not None
```

## Writing New Tests

### Unit Test Example

```python
"""Unit tests for my_module."""

import pytest
from lpm_validation.my_module import MyClass


class TestMyClass:
    """Test MyClass."""
    
    def test_method_success(self):
        """Test method with valid input."""
        obj = MyClass()
        result = obj.method(valid_input)
        assert result == expected_value
    
    def test_method_invalid_input(self):
        """Test method with invalid input."""
        obj = MyClass()
        with pytest.raises(ValueError):
            obj.method(invalid_input)
```

### Integration Test Example

```python
"""Integration test for workflow."""

import pytest
from unittest.mock import patch


class TestWorkflow:
    """Test complete workflow."""
    
    @patch('module.external_dependency')
    def test_workflow(self, mock_external, sample_config):
        """Test end-to-end workflow."""
        # Setup mocks
        mock_external.return_value = mock_data
        
        # Execute workflow
        result = run_workflow(sample_config)
        
        # Verify
        assert result['status'] == 'success'
```

## Mocking S3

Tests use mocked S3 clients to avoid actual AWS calls:

```python
from unittest.mock import MagicMock, patch

@patch('lpm_validation.s3_data_source.boto3.client')
def test_with_mock_s3(mock_boto_client):
    """Test with mocked S3."""
    # Setup mock
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {
        'Contents': [{'Key': 'test/file.json'}],
        'IsTruncated': False
    }
    mock_boto_client.return_value = mock_s3
    
    # Test code using S3
    ...
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest --cov=lpm_validation --cov-report=xml tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Categories

Tests are organized by markers:

```python
# Unit test
@pytest.mark.unit
def test_unit():
    ...

# Integration test
@pytest.mark.integration
def test_integration():
    ...

# Slow test
@pytest.mark.slow
def test_slow_operation():
    ...

# S3 test (mocked)
@pytest.mark.s3
def test_s3_operation():
    ...
```

Run by marker:
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Debugging Tests

```bash
# Run with debugger
pytest --pdb

# Drop into debugger on failure
pytest --pdb -x

# Print full stack traces
pytest --tb=long

# Show local variables in tracebacks
pytest -l
```

## Known Limitations

1. **S3 Mocking**: Tests use mocked S3 clients. For testing with actual S3, set environment variables and use separate test bucket.

2. **Time Series Data**: Force series CSV fixtures contain limited data (20 rows). Real data has 5000+ iterations.

3. **Parallel Execution**: Some integration tests may have race conditions when run in parallel.

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Fixtures**: Use fixtures for common setup instead of duplicating code
3. **Descriptive Names**: Test names should clearly describe what they test
4. **Assertions**: Include clear assertion messages for failures
5. **Coverage**: Aim for high coverage but prioritize meaningful tests
6. **Fast Tests**: Keep unit tests fast; use mocks for external dependencies
7. **Documentation**: Add docstrings explaining what each test validates

## Troubleshooting

### Import Errors

```
ModuleNotFoundError: No module named 'lpm_validation'
```
**Solution**: Install package in development mode: `pip install -e .`

### Fixture Not Found

```
fixture 'sample_config' not found
```
**Solution**: Check conftest.py is present and fixture is defined

### S3 Errors During Tests

```
botocore.exceptions.NoCredentialsError
```
**Solution**: Tests should use mocked S3. Verify `@patch` decorators are applied.

### Coverage Too Low

```
ERROR: coverage required 70%, actual 45%
```
**Solution**: Add tests for untested modules or adjust threshold in pytest.ini

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
