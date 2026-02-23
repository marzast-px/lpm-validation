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
    
    def __init__(self, bucket: str, aws_profile: Optional[str] = None):
        """
        Initialize S3 data source.
        
        Args:
            bucket: S3 bucket name
            aws_profile: Optional AWS profile name
        """
        self.bucket = bucket
        
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
        else:
            self.s3_client = boto3.client('s3')
        
        logger.info(f"Initialized S3DataSource for bucket: {bucket}")
    
    def list_folders(self, prefix: str, delimiter: str = '/') -> List[str]:
        """
        List all folder prefixes under a given path.
        
        Args:
            prefix: S3 prefix to list
            delimiter: Delimiter for folder structure
            
        Returns:
            List of folder prefixes
        """
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
    
    def write_text(self, s3_key: str, content: str, content_type: str = 'text/plain'):
        """
        Write text content to S3.
        
        Args:
            s3_key: S3 object key
            content: Text content to write
            content_type: Content type
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType=content_type
            )
            logger.info(f"Successfully wrote file to {s3_key}")
        except ClientError as e:
            logger.error(f"Error writing to {s3_key}: {e}")
            raise
    
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
