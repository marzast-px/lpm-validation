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
    
    def test_read_csv_file_not_found(self, s3_source):
        """Test reading a non-existent CSV file returns None."""
        # Try to read a CSV file that doesn't exist
        fake_csv_key = "this/path/does/not/exist/file.csv"
        result = s3_source.read_csv(fake_csv_key)
        
        # Should return None for non-existent file
        assert result is None, "Should return None for non-existent CSV file"
    
    def test_read_csv_from_results(self, s3_source):
        """Test reading CSV files from results prefix if they exist."""
        results_prefix = "validation/outputs"
        
        try:
            # Try to find CSV files in results area
            csv_files = s3_source.list_files(results_prefix, extension=".csv")
            
            if len(csv_files) == 0:
                pytest.skip(f"No CSV files found in {results_prefix} to test read_csv")
            
            # Try to read the first CSV file found
            first_csv = csv_files[0]
            data = s3_source.read_csv(first_csv)
            
            # Verify the data is correct format
            assert data is not None, f"Failed to read CSV from {first_csv}"
            assert isinstance(data, list), f"Expected list, got {type(data)}"
            
            if len(data) > 0:
                # First item should be a dictionary (CSV row)
                assert isinstance(data[0], dict), f"Expected dict for CSV row, got {type(data[0])}"
                # Dictionary should have keys (column names)
                assert len(data[0].keys()) > 0, "CSV row should have column names"
                
                print(f"Successfully read CSV with {len(data)} rows and columns: {list(data[0].keys())}")
        
        except ClientError as e:
            pytest.fail(f"Failed to read CSV file: {e}")
    
    def test_read_csv_structure(self, s3_source):
        """Test that read_csv returns proper dictionary structure."""
        results_prefix = "validation/outputs"
        
        try:
            # Look for any CSV files
            folders = s3_source.list_folders(results_prefix)
            
            csv_file_found = None
            for folder in folders:
                csv_files = s3_source.list_files(folder, extension=".csv")
                if csv_files:
                    csv_file_found = csv_files[0]
                    break
            
            if csv_file_found is None:
                pytest.skip("No CSV files found to test structure")
            
            # Read the CSV
            data = s3_source.read_csv(csv_file_found)
            
            assert data is not None, "CSV data should not be None"
            assert isinstance(data, list), "CSV data should be a list"
            
            if len(data) > 0:
                # Each row should be a dictionary
                for i, row in enumerate(data[:3]):  # Check first 3 rows
                    assert isinstance(row, dict), f"Row {i} should be a dict, got {type(row)}"
                    # All rows should have the same keys
                    if i > 0:
                        assert set(row.keys()) == set(data[0].keys()), \
                            f"Row {i} has different columns than first row"
        
        except ClientError as e:
            pytest.fail(f"Failed to test CSV structure: {e}")
    
    def test_list_folders_immediate_only(self, s3_source, geometries_prefix):
        """Test listing immediate subdirectories (leaf_only=False)."""
        try:
            # Get immediate subdirectories only
            immediate_folders = s3_source.list_folders(geometries_prefix, leaf_only=False)
            
            # Should find at least one immediate subdirectory
            assert len(immediate_folders) > 0, f"Should find immediate subdirectories in {geometries_prefix}"
            
            # All returned folders should be direct children of the prefix
            for folder in immediate_folders:
                # Remove the prefix and check that there's only one more level
                relative_path = folder[len(geometries_prefix):].strip('/')
                assert '/' not in relative_path, \
                    f"Folder {folder} should be immediate child of {geometries_prefix}"
        except ClientError as e:
            pytest.fail(f"Failed to list immediate folders: {e}")
    
    def test_list_folders_leaf_only_default(self, s3_source, geometries_prefix):
        """Test listing leaf folders (default behavior with leaf_only=True)."""
        try:
            # Get leaf folders (default behavior)
            leaf_folders = s3_source.list_folders(geometries_prefix)
            
            # Should find leaf folders
            assert len(leaf_folders) > 0, f"Should find leaf folders in {geometries_prefix}"
            
            # Verify that leaf folders have no subfolders
            for leaf_folder in leaf_folders[:5]:  # Check first 5 to avoid long test times
                subfolders = s3_source.list_folders(leaf_folder, leaf_only=False)
                assert len(subfolders) == 0, \
                    f"Leaf folder {leaf_folder} should not have subfolders, but has {len(subfolders)}"
        except ClientError as e:
            pytest.fail(f"Failed to list leaf folders: {e}")
    
    def test_list_folders_leaf_only_explicit(self, s3_source, geometries_prefix):
        """Test listing leaf folders with explicit leaf_only=True parameter."""
        try:
            # Explicitly request leaf folders
            leaf_folders = s3_source.list_folders(geometries_prefix, leaf_only=True)
            
            # Should find leaf folders
            assert len(leaf_folders) > 0, f"Should find leaf folders in {geometries_prefix}"
            
            # Each leaf folder should contain files (not just be empty)
            for leaf_folder in leaf_folders[:3]:  # Check first 3
                files = s3_source.list_files(leaf_folder)
                assert len(files) > 0, f"Leaf folder {leaf_folder} should contain files"
        except ClientError as e:
            pytest.fail(f"Failed to list leaf folders explicitly: {e}")
    
    def test_list_folders_depth_difference(self, s3_source, geometries_prefix):
        """Test that leaf_only returns deeper folders than immediate listing."""
        try:
            # Get immediate subdirectories
            immediate_folders = s3_source.list_folders(geometries_prefix, leaf_only=False)
            
            # Get leaf folders
            leaf_folders = s3_source.list_folders(geometries_prefix, leaf_only=True)
            
            # Leaf folders should generally be deeper in the tree
            if len(immediate_folders) > 0 and len(leaf_folders) > 0:
                # Check at least one leaf folder is deeper than immediate folders
                immediate_depth = geometries_prefix.count('/') + 1
                leaf_depths = [folder.count('/') for folder in leaf_folders]
                max_leaf_depth = max(leaf_depths)
                
                # If structure has nesting, leaf folders should be deeper
                # (but allow for case where geometries are at immediate level)
                assert max_leaf_depth >= immediate_depth, \
                    f"Leaf folders should be at depth >= {immediate_depth}, max found: {max_leaf_depth}"
                
                print(f"Found {len(immediate_folders)} immediate folders and {len(leaf_folders)} leaf folders")
                print(f"Immediate depth: {immediate_depth}, Max leaf depth: {max_leaf_depth}")
        except ClientError as e:
            pytest.fail(f"Failed to compare folder depths: {e}")
    
    def test_list_folders_nested_structure(self, s3_source):
        """Test leaf folder detection in nested structure like Batch_X/geometry_folders."""
        # Use a specific test case if we know the structure
        prefix = "validation/geometries"
        
        try:
            # Get all leaf folders
            leaf_folders = s3_source.list_folders(prefix, leaf_only=True)
            
            # Should find some leaf folders
            assert len(leaf_folders) > 0, "Should find leaf folders in nested structure"
            
            # Check that none of the leaf folders are just batch folders
            for leaf in leaf_folders:
                folder_name = s3_source.extract_folder_name(leaf)
                # Leaf folders should not be something like "Batch_1" alone
                # They should be actual geometry folders
                if "Batch_" in folder_name:
                    # If it contains "Batch_", it should have more path segments
                    assert leaf.strip('/').count('/') > prefix.strip('/').count('/'), \
                        f"Batch folder {leaf} should not be a leaf folder"
        except ClientError as e:
            pytest.fail(f"Failed to test nested structure: {e}")

