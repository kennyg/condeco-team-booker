"""
Secure authentication management for Condeco team booking.
Supports browser-based login with secure credential storage.
"""

import os
import json
import keyring
import getpass
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()
logger = logging.getLogger(__name__)

class CondecoAuth:
    """Manages Condeco authentication with secure credential storage."""
    
    SERVICE_NAME = "condeco-team-booker"
    
    def __init__(self, unique_key: Optional[str] = None):
        """Initialize authentication manager.
        
        Args:
            unique_key: Condeco unique key (e.g., 'company.condecosoftware.com')
        """
        self.unique_key = unique_key
        self.config_dir = Path.home() / ".condeco-booker"
        self.config_file = self.config_dir / "config.json"
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True, mode=0o700)
    
    def setup_initial_auth(self) -> bool:
        """Guide user through initial authentication setup.
        
        Returns:
            bool: True if setup was successful
        """
        console.print("\n[bold blue]Condeco Team Booker - Initial Setup[/bold blue]")
        console.print("This will help you set up authentication for your Condeco system.\n")
        
        if not self.unique_key:
            self.unique_key = Prompt.ask(
                "Enter your Condeco unique key (e.g., 'company.condecosoftware.com')"
            )
        
        email = Prompt.ask("Enter your email address")
        
        # Store basic config
        config = {
            "unique_key": self.unique_key,
            "email": email,
            "setup_completed": False
        }
        
        self._save_config(config)
        
        console.print(f"\n[yellow]Step 1: Request Magic Link[/yellow]")
        console.print(f"A magic link will be sent to: {email}")
        
        if not Confirm.ask("Continue with sending magic link?"):
            return False
        
        # Import here to avoid circular imports
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / 'Hybrid-Worker' / 'Python' / 'src'))
        
        try:
            from hybrid_worker.condeco import Condeco
        except ImportError:
            console.print("[red]Error: Cannot import Condeco module. Please ensure Hybrid-Worker is properly set up.[/red]")
            return False
        
        # Send magic link
        condeco = Condeco(unique_key=self.unique_key)
        
        try:
            response = condeco.sendMagicLink(email=email)
            response_data = response.json()
            
            if response.status_code == 200:
                console.print("[green]✓ Magic link sent successfully![/green]")
                console.print("Check your email for the validation code.\n")
                
                validation_key = Prompt.ask("Enter the validation code from your email")
                
                # Exchange validation key for token
                token_response = condeco.loginWithMagicLink(validation_key=validation_key)
                token_data = token_response.json()
                
                if token_response.status_code == 200 and 'token' in token_data:
                    # Store token securely
                    self._store_token(token_data['token'])
                    
                    config['setup_completed'] = True
                    self._save_config(config)
                    
                    console.print("[green]✓ Authentication setup completed successfully![/green]")
                    return True
                else:
                    console.print(f"[red]Failed to obtain token: {token_data}[/red]")
                    return False
            else:
                console.print(f"[red]Failed to send magic link: {response_data}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Error during authentication setup: {str(e)}[/red]")
            return False
    
    def get_token(self) -> Optional[str]:
        """Retrieve stored authentication token.
        
        Returns:
            str: JWT token if available, None otherwise
        """
        try:
            token = keyring.get_password(self.SERVICE_NAME, "jwt_token")
            return token
        except Exception as e:
            logger.error(f"Error retrieving token: {e}")
            return None
    
    def _store_token(self, token: str) -> None:
        """Store JWT token securely.
        
        Args:
            token: JWT token to store
        """
        try:
            keyring.set_password(self.SERVICE_NAME, "jwt_token", token)
        except Exception as e:
            logger.error(f"Error storing token: {e}")
            # Fallback to environment variable warning
            console.print("[yellow]Warning: Could not store token in keyring. Consider setting CONDECO_TOKEN environment variable.[/yellow]")
    
    def get_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            dict: Configuration data
        """
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration data to save
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Secure the config file
            os.chmod(self.config_file, 0o600)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def is_setup_complete(self) -> bool:
        """Check if initial authentication setup is complete.
        
        Returns:
            bool: True if setup is complete
        """
        config = self.get_config()
        return config.get('setup_completed', False) and self.get_token() is not None
    
    def validate_token(self) -> bool:
        """Validate current token and check expiration.
        
        Returns:
            bool: True if token is valid and not expired
        """
        token = self.get_token()
        if not token:
            return False
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / 'Hybrid-Worker' / 'Python' / 'src'))
            from hybrid_worker.condeco import Condeco
            
            decoded_jwt = Condeco.decode_jwt(token)
            
            import datetime
            expiration = datetime.datetime.fromtimestamp(decoded_jwt['exp'])
            
            if expiration < datetime.datetime.now():
                logger.warning("Token has expired")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False
    
    def clear_credentials(self) -> None:
        """Clear all stored credentials and configuration."""
        try:
            keyring.delete_password(self.SERVICE_NAME, "jwt_token")
        except:
            pass
        
        if self.config_file.exists():
            self.config_file.unlink()
        
        console.print("[green]Credentials cleared successfully.[/green]")

def get_auth_token() -> Optional[str]:
    """Convenience function to get authentication token.
    
    Returns:
        str: JWT token if available
    """
    # Try environment variable first
    token = os.getenv('CONDECO_TOKEN')
    if token:
        return token
    
    # Try keyring
    auth = CondecoAuth()
    return auth.get_token()