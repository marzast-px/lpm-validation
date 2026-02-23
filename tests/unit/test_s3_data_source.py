"""Integration tests for S3DataSource module.

These tests verify actual connectivity to S3 and data availability.
They require valid AWS credentials for the 'coreweave' profile.
"""

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from lpm_validation.s3_data_source import S3DataSource


class TestS3DataSourceIntegration:
    """Integration tests for S3DataSource class."""
    
    @pytest.fixture
    def s3_bucket(self):
        """Default S3 bucket for testing."""
        return "sim-data"
    
    @pytest.fixture
    def geometries_prefix(self):
        """Default geometries prefix."""
        return "validation/geometries"
    
    @pytest.fixture
    def s3_source(self, s3_bucket):
        """Create S3DataSource with default profile."""
        try:
            return S3DataSource(bucket=s3_bucket, aws_profile="coreweave")
        except (ClientError, NoCredentialsError) as e:
            pytest.fail(f"Failed to initialize S3 connection: {e}")
    
    def test_s3_connection(self, s3_source, geometries_prefix):
        """Test that we can connect to S3 and access the geometries prefix."""
        try:
            # Try to list folders in the geometries prefix
            folders = s3_source.list_folders(geometries_prefix)
            print(folders)
            # We should have at least some data
            assert len(folders) > 0, f"No geometry folders found in {geometries_prefix}"
        except ClientError as e:
            pytest.fail(f"Failed to access S3: {e}")
    
    def test_geometry_data_exists(self, s3_source, geometries_prefix):
        """Test that geometry data actually exists in the bucket."""
        try:
            folders = s3_source.list_folders(geometries_prefix)
            assert len(folders) > 0, f"No data found in {geometries_prefix}"
            
            # Verify we can access at least one folder's contents
            first_folder = folders[0]
            files = s3_source.list_files(first_folder, extension=".json")
            assert len(files) > 0, f"No JSON files found in {first_folder}"
        except ClientError as e:
            pytest.fail(f"Failed to access geometry data: {e}")
    
    def test_read_geometry_json(self, s3_source, geometries_prefix):
        """Test that we can read a geometry JSON file."""
        try:
            # Get first geometry folder
            folders = s3_source.list_folders(geometries_prefix)
            assert len(folders) > 0, "No geometry folders found"
            
            # Get JSON files from first folder
            first_folder = folders[0]
            json_files = s3_source.list_files(first_folder, extension=".json")
            assert len(json_files) > 0, f"No JSON files in {first_folder}"
            
            # Try to read the first JSON file
            first_json = json_files[0]
            data = s3_source.read_json(first_json)
            assert data is not None, f"Failed to read {first_json}"
            assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        except ClientError as e:
            pytest.fail(f"Failed to read geometry JSON: {e}")
    
    def test_list_files_with_extension_filter(self, s3_source, geometries_prefix):
        """Test listing files with extension filter."""
        try:
            folders = s3_source.list_folders(geometries_prefix)
            assert len(folders) > 0, "No geometry folders found"
            
            first_folder = folders[0]
            json_files = s3_source.list_files(first_folder, extension=".json")
            
            # All returned files should end with .json
            for file in json_files:
                assert file.endswith(".json"), f"File {file} doesn't have .json extension"
        except ClientError as e:
            pytest.fail(f"Failed to list files: {e}")
    
    def test_folder_exists(self, s3_source, geometries_prefix):
        """Test folder existence check."""
        # Test that the geometries prefix exists
        exists = s3_source.folder_exists(geometries_prefix)
        assert exists is True, f"Geometries prefix {geometries_prefix} should exist"
        
        # Test that a non-existent folder returns False
        fake_prefix = "this/definitely/does/not/exist/anywhere/"
        exists = s3_source.folder_exists(fake_prefix)
        assert exists is False, "Non-existent folder should return False"
    
    def test_find_matching_folder(self, s3_source, geometries_prefix):
        """Test finding a folder matching a pattern."""
        try:
            folders = s3_source.list_folders(geometries_prefix)
            assert len(folders) > 0, "No geometry folders found"
            
            # Extract name from first folder to use as pattern
            first_folder_name = s3_source.extract_folder_name(folders[0])
            # Use a substring of the folder name as pattern
            pattern = first_folder_name[:5] if len(first_folder_name) >= 5 else first_folder_name
            
            # Should find at least the first folder
            matching = s3_source.find_matching_folder(geometries_prefix, pattern)
            assert matching is not None, f"Should find folder matching pattern '{pattern}'"
            assert pattern in s3_source.extract_folder_name(matching)
        except ClientError as e:
            pytest.fail(f"Failed to find matching folder: {e}")
    
    def test_extract_folder_name(self):
        """Test extracting folder name from S3 path (no S3 connection needed)."""
        assert S3DataSource.extract_folder_name("path/to/folder/") == "folder"
        assert S3DataSource.extract_folder_name("path/to/folder") == "folder"
        assert S3DataSource.extract_folder_name("single/") == "single"
        assert S3DataSource.extract_folder_name("root") == "root"

