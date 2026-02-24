"""S3 data source module for accessing S3 storage."""

import json
import logging
from typing import List, Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
import io
import csv

logger = logging.getLogger(__name__)


class S3DataSource:
    """Handles all interactions with S3 storage."""
    
    def __init__(self, bucket: str, aws_profile: str = "coreweave"):
        """
        Initialize S3 data source.
        
        Args:
            bucket: S3 bucket name
            aws_profile: AWS profile name (default: 'coreweave')
        """
        self.bucket = bucket
        self.aws_profile = aws_profile
        
        session = boto3.Session(profile_name=aws_profile)
        self.s3_client = session.client('s3')
        
        logger.info(f"Initialized S3DataSource for bucket: {bucket}")
    
    def list_folders(self, prefix: str, delimiter: str = '/', leaf_only: bool = True) -> List[str]:
        """
        List folder prefixes under a given path.
        
        Args:
            prefix: S3 prefix to list
            delimiter: Delimiter for folder structure
            leaf_only: If True, return only leaf folders (folders with no subfolders) recursively
            
        Returns:
            List of folder prefixes
        """
        if leaf_only:
            return self._list_leaf_folders_recursive(prefix)
        
        folders = []
        continuation_token = None
        
        # Ensure prefix ends with delimiter if not empty
        if prefix and not prefix.endswith(delimiter):
            prefix = prefix + delimiter
        
        while True:
            params = {
                'Bucket': self.bucket,
                'Prefix': prefix,
                'Delimiter': delimiter
            }
            
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            
            try:
                response = self.s3_client.list_objects_v2(**params)
                
                # Collect folder prefixes
                if 'CommonPrefixes' in response:
                    for prefix_obj in response['CommonPrefixes']:
                        folders.append(prefix_obj['Prefix'])
                
                # Check if there are more results
                if response.get('IsTruncated', False):
                    continuation_token = response.get('NextContinuationToken')
                else:
                    break
                    
            except ClientError as e:
                logger.error(f"Error listing folders in {prefix}: {e}")
                raise
        
        logger.debug(f"Found {len(folders)} folders in {prefix}")
        return folders
    
    def _list_leaf_folders_recursive(self, prefix: str) -> List[str]:
        """
        Recursively find all leaf folders (folders with no subfolders).
        
        Args:
            prefix: S3 prefix to search
            
        Returns:
            List of leaf folder prefixes
        """
        leaf_folders = []
        
        # Ensure prefix ends with /
        if prefix and not prefix.endswith('/'):
            prefix = prefix + '/'
        
        # Get immediate subdirectories (non-recursive)
        subfolders = self.list_folders(prefix, leaf_only=False)
        
        if not subfolders:
            # No subfolders means this is a leaf folder (if it has files)
            # Check if folder has any content
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=prefix,
                    MaxKeys=1
                )
                if 'Contents' in response:
                    leaf_folders.append(prefix)
            except ClientError as e:
                logger.error(f"Error checking folder {prefix}: {e}")
        else:
            # Recursively check each subfolder
            for subfolder in subfolders:
                leaf_folders.extend(self._list_leaf_folders_recursive(subfolder))
        
        logger.debug(f"Found {len(leaf_folders)} leaf folders in {prefix}")
        return leaf_folders
    
    def list_files(self, prefix: str, extension: Optional[str] = None) -> List[str]:
        """
        List all files under a given path.
        
        Args:
            prefix: S3 prefix to list
            extension: Optional file extension filter (e.g., '.json')
            
        Returns:
            List of file keys
        """
        files = []
        continuation_token = None
        
        while True:
            params = {
                'Bucket': self.bucket,
                'Prefix': prefix
            }
            
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            
            try:
                response = self.s3_client.list_objects_v2(**params)
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        key = obj['Key']
                        if extension is None or key.endswith(extension):
                            files.append(key)
                
                if response.get('IsTruncated', False):
                    continuation_token = response.get('NextContinuationToken')
                else:
                    break
                    
            except ClientError as e:
                logger.error(f"Error listing files in {prefix}: {e}")
                raise
        
        logger.debug(f"Found {len(files)} files in {prefix}")
        return files
    
    def read_json(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Read and parse JSON file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Parsed JSON dictionary or None if error
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            json_content = response['Body'].read().decode('utf-8')
            data = json.loads(json_content)
            logger.debug(f"Successfully read JSON from {s3_key}")
            return data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found: {s3_key}")
            else:
                logger.error(f"Error reading JSON from {s3_key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {s3_key}: {e}")
            return None
    
    def read_csv(self, s3_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Read CSV file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            List of dictionaries or None if error
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            csv_content = response['Body'].read().decode('utf-8')
            
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))
            data = list(reader)
            
            logger.debug(f"Successfully read CSV from {s3_key}, {len(data)} rows")
            return data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found: {s3_key}")
            else:
                logger.error(f"Error reading CSV from {s3_key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing CSV from {s3_key}: {e}")
            return None
    
    def folder_exists(self, prefix: str) -> bool:
        """
        Check if a folder/prefix exists in S3.
        
        Args:
            prefix: S3 prefix to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=1
            )
            return 'Contents' in response or 'CommonPrefixes' in response
        except ClientError as e:
            logger.error(f"Error checking folder existence {prefix}: {e}")
            return False
    
    def find_matching_folder(self, base_prefix: str, pattern: str) -> Optional[str]:
        """
        Find folder matching a specific pattern.
        
        Args:
            base_prefix: Base S3 prefix to search in
            pattern: Pattern to match (substring)
            
        Returns:
            First matching folder path or None
        """
        folders = self.list_folders(base_prefix)
        
        for folder in folders:
            folder_name = self.extract_folder_name(folder)
            if pattern in folder_name:
                logger.debug(f"Found matching folder: {folder}")
                return folder
        
        logger.debug(f"No folder matching pattern '{pattern}' in {base_prefix}")
        return None
    
    @staticmethod
    def extract_folder_name(s3_path: str) -> str:
        """
        Extract folder name from S3 path.
        
        Args:
            s3_path: S3 path (e.g., 'path/to/folder/')
            
        Returns:
            Folder name (e.g., 'folder')
        """
        return s3_path.rstrip('/').split('/')[-1]
