"""Google Cloud Secret Manager client implementation."""
import logging
from typing import Optional
from google.cloud import secretmanager
from google.api_core import exceptions

from ..utils.retry import default_retry

logger = logging.getLogger("stock_data_collector")


class SecretManagerError(Exception):
    """Secret Manager specific error."""
    pass


class SecretManagerClient:
    """Client for Google Cloud Secret Manager."""
    
    def __init__(self, project_id: str):
        """Initialize Secret Manager client."""
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
        logger.info(f"Initialized Secret Manager client for project: {project_id}")
    
    @default_retry
    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """Retrieve secret value from Secret Manager."""
        logger.info(f"Retrieving secret: {secret_id} (version: {version})")
        
        # Build the resource name
        if version == "latest":
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        else:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
        
        try:
            # Access the secret version
            response = self.client.access_secret_version(request={"name": name})
            
            # Extract the secret value
            secret_value = response.payload.data.decode("UTF-8")
            logger.info(f"Successfully retrieved secret: {secret_id}")
            
            return secret_value
            
        except exceptions.NotFound:
            error_msg = f"Secret not found: {secret_id}"
            logger.error(error_msg)
            raise SecretManagerError(error_msg)
        except exceptions.PermissionDenied:
            error_msg = f"Permission denied accessing secret: {secret_id}"
            logger.error(error_msg)
            raise SecretManagerError(error_msg)
        except Exception as e:
            error_msg = f"Failed to retrieve secret {secret_id}: {str(e)}"
            logger.error(error_msg)
            raise SecretManagerError(error_msg) from e
    
    def get_refresh_token(self, secret_id: str) -> str:
        """Get J-Quants refresh token from Secret Manager."""
        return self.get_secret(secret_id)
    
    def get_jquants_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Get J-Quants email and password from Secret Manager."""
        email = None
        password = None
        
        try:
            email = self.get_secret("jquants-mail-address")
        except SecretManagerError:
            logger.warning("J-Quants email not found in Secret Manager")
        
        try:
            password = self.get_secret("jquants-password")
        except SecretManagerError:
            logger.warning("J-Quants password not found in Secret Manager")
        
        return email, password
    
    @default_retry
    def create_or_update_secret(self, secret_id: str, secret_value: str) -> None:
        """Create or update a secret in Secret Manager."""
        logger.info(f"Creating/updating secret: {secret_id}")
        
        parent = f"projects/{self.project_id}"
        secret_name = f"{parent}/secrets/{secret_id}"
        
        try:
            # Try to get existing secret
            self.client.get_secret(request={"name": secret_name})
            logger.info(f"Secret {secret_id} already exists, adding new version")
            
            # Add new version
            self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": secret_value.encode("UTF-8")}
                }
            )
            
        except exceptions.NotFound:
            # Create new secret
            logger.info(f"Creating new secret: {secret_id}")
            
            try:
                self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {
                            "replication": {
                                "automatic": {}
                            }
                        }
                    }
                )
                
                # Add initial version
                self.client.add_secret_version(
                    request={
                        "parent": secret_name,
                        "payload": {"data": secret_value.encode("UTF-8")}
                    }
                )
                
                logger.info(f"Successfully created secret: {secret_id}")
                
            except Exception as e:
                error_msg = f"Failed to create secret {secret_id}: {str(e)}"
                logger.error(error_msg)
                raise SecretManagerError(error_msg) from e
                
        except Exception as e:
            error_msg = f"Failed to update secret {secret_id}: {str(e)}"
            logger.error(error_msg)
            raise SecretManagerError(error_msg) from e