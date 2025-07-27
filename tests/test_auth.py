"""
Tests for the authentication functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from team_booker.auth import CondecoAuth, get_auth_token

class TestCondecoAuth:
    """Tests for CondecoAuth class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def auth(self, temp_config_dir):
        """Create CondecoAuth instance with temporary config directory."""
        auth = CondecoAuth("test.condecosoftware.com")
        auth.config_dir = temp_config_dir
        auth.config_file = temp_config_dir / "config.json"
        return auth
    
    def test_initialization(self, auth):
        """Test CondecoAuth initialization."""
        assert auth.unique_key == "test.condecosoftware.com"
        assert auth.SERVICE_NAME == "condeco-team-booker"
        assert auth.config_file.name == "config.json"
    
    def test_save_and_load_config(self, auth):
        """Test saving and loading configuration."""
        config = {
            "unique_key": "test.condecosoftware.com",
            "email": "test@example.com",
            "setup_completed": True
        }
        
        auth._save_config(config)
        loaded_config = auth.get_config()
        
        assert loaded_config == config
        
        # Check file permissions are secure
        assert oct(auth.config_file.stat().st_mode)[-3:] == '600'
    
    def test_get_config_file_not_exists(self, auth):
        """Test getting config when file doesn't exist."""
        config = auth.get_config()
        assert config == {}
    
    @patch('team_booker.auth.keyring.get_password')
    def test_get_token_success(self, mock_get_password, auth):
        """Test successful token retrieval."""
        mock_get_password.return_value = "test_token"
        
        token = auth.get_token()
        
        assert token == "test_token"
        mock_get_password.assert_called_once_with("condeco-team-booker", "jwt_token")
    
    @patch('team_booker.auth.keyring.get_password')
    def test_get_token_failure(self, mock_get_password, auth):
        """Test token retrieval failure."""
        mock_get_password.side_effect = Exception("Keyring error")
        
        token = auth.get_token()
        
        assert token is None
    
    @patch('team_booker.auth.keyring.set_password')
    def test_store_token_success(self, mock_set_password, auth):
        """Test successful token storage."""
        auth._store_token("test_token")
        
        mock_set_password.assert_called_once_with("condeco-team-booker", "jwt_token", "test_token")
    
    @patch('team_booker.auth.keyring.set_password')
    def test_store_token_failure(self, mock_set_password, auth):
        """Test token storage failure."""
        mock_set_password.side_effect = Exception("Keyring error")
        
        # Should not raise exception
        auth._store_token("test_token")
    
    def test_is_setup_complete_true(self, auth):
        """Test setup completion check when complete."""
        # Save config indicating completion
        auth._save_config({"setup_completed": True})
        
        with patch.object(auth, 'get_token', return_value="test_token"):
            assert auth.is_setup_complete() is True
    
    def test_is_setup_complete_false_no_config(self, auth):
        """Test setup completion check when no config exists."""
        assert auth.is_setup_complete() is False
    
    def test_is_setup_complete_false_no_token(self, auth):
        """Test setup completion check when no token exists."""
        auth._save_config({"setup_completed": True})
        
        with patch.object(auth, 'get_token', return_value=None):
            assert auth.is_setup_complete() is False
    
    @patch('team_booker.auth.Condeco')
    def test_validate_token_success(self, mock_condeco_class, auth):
        """Test successful token validation."""
        # Mock JWT decoding
        mock_condeco_class.decode_jwt.return_value = {
            'exp': 9999999999  # Far future timestamp
        }
        
        with patch.object(auth, 'get_token', return_value="valid_token"):
            assert auth.validate_token() is True
    
    @patch('team_booker.auth.Condeco')
    def test_validate_token_expired(self, mock_condeco_class, auth):
        """Test token validation with expired token."""
        # Mock JWT decoding with expired timestamp
        mock_condeco_class.decode_jwt.return_value = {
            'exp': 1000000000  # Past timestamp
        }
        
        with patch.object(auth, 'get_token', return_value="expired_token"):
            assert auth.validate_token() is False
    
    def test_validate_token_no_token(self, auth):
        """Test token validation when no token exists."""
        with patch.object(auth, 'get_token', return_value=None):
            assert auth.validate_token() is False
    
    @patch('team_booker.auth.keyring.delete_password')
    def test_clear_credentials(self, mock_delete_password, auth):
        """Test clearing credentials."""
        # Create config file
        auth._save_config({"test": "data"})
        assert auth.config_file.exists()
        
        auth.clear_credentials()
        
        # Config file should be deleted
        assert not auth.config_file.exists()
        mock_delete_password.assert_called_once_with("condeco-team-booker", "jwt_token")
    
    @patch('team_booker.auth.Prompt.ask')
    @patch('team_booker.auth.Confirm.ask')
    @patch('team_booker.auth.Condeco')
    def test_setup_initial_auth_success(self, mock_condeco_class, mock_confirm, mock_prompt, auth):
        """Test successful initial authentication setup."""
        # Mock user inputs
        mock_prompt.side_effect = ["test@example.com", "validation123"]
        mock_confirm.return_value = True
        
        # Mock Condeco instance and responses
        mock_condeco = Mock()
        mock_condeco_class.return_value = mock_condeco
        
        # Mock successful magic link send
        mock_magic_response = Mock()
        mock_magic_response.status_code = 200
        mock_magic_response.json.return_value = {"success": True}
        mock_condeco.sendMagicLink.return_value = mock_magic_response
        
        # Mock successful token exchange
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"token": "new_jwt_token"}
        mock_condeco.loginWithMagicLink.return_value = mock_token_response
        
        with patch.object(auth, '_store_token') as mock_store:
            result = auth.setup_initial_auth()
            
            assert result is True
            mock_store.assert_called_once_with("new_jwt_token")
            
            # Check config was saved
            config = auth.get_config()
            assert config["email"] == "test@example.com"
            assert config["setup_completed"] is True

class TestGetAuthToken:
    """Tests for get_auth_token convenience function."""
    
    @patch.dict('os.environ', {'CONDECO_TOKEN': 'env_token'})
    def test_get_auth_token_from_env(self):
        """Test getting token from environment variable."""
        token = get_auth_token()
        assert token == 'env_token'
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('team_booker.auth.CondecoAuth')
    def test_get_auth_token_from_keyring(self, mock_auth_class):
        """Test getting token from keyring when env var not set."""
        mock_auth = Mock()
        mock_auth.get_token.return_value = 'keyring_token'
        mock_auth_class.return_value = mock_auth
        
        token = get_auth_token()
        
        assert token == 'keyring_token'
        mock_auth.get_token.assert_called_once()