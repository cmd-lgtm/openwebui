"""
Unit Tests for Authentication and Authorization

This module tests JWT authentication and role-based access control without importing the full app.

Requirements:
- 19.1: Require valid JWT token for all non-health-check endpoints
- 19.2: Validate JWT signature and expiration
- 19.3: Extract user identity and roles from JWT claims
- 19.4: Enforce role-based access control on all endpoints
- 19.5: Return HTTP 403 when user lacks required role
- 19.6: Return HTTP 401 when authentication fails
- 19.7: Support service account tokens for inter-service calls
- 19.8: Log all authentication and authorization failures
"""

import pytest
from datetime import timedelta
from jose import jwt

from backend.core.auth import (
    create_access_token,
    decode_token,
    authenticate_user,
    verify_password,
    get_password_hash,
    Roles,
    Permissions,
    SECRET_KEY,
    ALGORITHM,
)


class TestJWTAuthentication:
    """Test JWT token generation and validation"""
    
    def test_create_access_token(self):
        """
        Test JWT token creation.
        
        Requirements:
        - 19.1: Generate JWT tokens
        """
        data = {
            "sub": "testuser",
            "user_id": "user_123",
            "roles": [Roles.ANALYST],
        }
        
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == "user_123"
        assert payload["roles"] == [Roles.ANALYST]
        assert "exp" in payload
    
    def test_decode_valid_token(self):
        """
        Test decoding a valid JWT token.
        
        Requirements:
        - 19.2: Validate JWT signature and expiration
        - 19.3: Extract user identity and roles from JWT claims
        """
        data = {
            "sub": "testuser",
            "user_id": "user_123",
            "roles": [Roles.ADMIN, Roles.ANALYST],
        }
        
        token = create_access_token(data)
        token_data = decode_token(token)
        
        assert token_data.username == "testuser"
        assert token_data.user_id == "user_123"
        assert Roles.ADMIN in token_data.roles
        assert Roles.ANALYST in token_data.roles
    
    def test_decode_expired_token(self):
        """
        Test that expired tokens are rejected.
        
        Requirements:
        - 19.2: Validate JWT expiration
        - 19.6: Return HTTP 401 when authentication fails
        """
        data = {
            "sub": "testuser",
            "user_id": "user_123",
            "roles": [Roles.VIEWER],
        }
        
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(Exception) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401
    
    def test_decode_invalid_signature(self):
        """
        Test that tokens with invalid signatures are rejected.
        
        Requirements:
        - 19.2: Validate JWT signature
        - 19.6: Return HTTP 401 when authentication fails
        """
        # Create token with wrong secret
        data = {"sub": "testuser", "user_id": "user_123", "roles": []}
        token = jwt.encode(data, "wrong-secret", algorithm=ALGORITHM)
        
        with pytest.raises(Exception) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401
    
    def test_service_account_token(self):
        """
        Test service account token creation.
        
        Requirements:
        - 19.7: Support service account tokens for inter-service calls
        """
        data = {
            "sub": "worker-service",
            "user_id": "service_worker",
            "roles": [Roles.SERVICE_ACCOUNT],
            "is_service_account": True,
        }
        
        token = create_access_token(data, expires_delta=timedelta(hours=24))
        token_data = decode_token(token)
        
        assert token_data.username == "worker-service"
        assert token_data.is_service_account is True
        assert Roles.SERVICE_ACCOUNT in token_data.roles


class TestRoleBasedAccessControl:
    """Test role-based access control"""
    
    def test_role_permissions_mapping(self):
        """
        Test that roles have correct permissions.
        
        Requirements:
        - 19.3: Define roles and permissions
        """
        # Admin has all permissions
        admin_perms = Permissions.get_permissions([Roles.ADMIN])
        assert "read:graph" in admin_perms
        assert "write:graph" in admin_perms
        assert "approve:interventions" in admin_perms
        
        # Analyst has read/write but not approve
        analyst_perms = Permissions.get_permissions([Roles.ANALYST])
        assert "read:graph" in analyst_perms
        assert "write:interventions" in analyst_perms
        assert "approve:interventions" not in analyst_perms
        
        # Viewer has only read permissions
        viewer_perms = Permissions.get_permissions([Roles.VIEWER])
        assert "read:graph" in viewer_perms
        assert "write:graph" not in viewer_perms
        assert "write:interventions" not in viewer_perms
    
    def test_has_permission(self):
        """
        Test permission checking.
        
        Requirements:
        - 19.4: Enforce role-based access control
        """
        # Admin has approve permission
        assert Permissions.has_permission([Roles.ADMIN], "approve:interventions")
        
        # Analyst does not have approve permission
        assert not Permissions.has_permission([Roles.ANALYST], "approve:interventions")
        
        # Viewer has read permission
        assert Permissions.has_permission([Roles.VIEWER], "read:graph")
        
        # Viewer does not have write permission
        assert not Permissions.has_permission([Roles.VIEWER], "write:graph")
    
    def test_multiple_roles_permissions(self):
        """
        Test that users with multiple roles get combined permissions.
        
        Requirements:
        - 19.4: Enforce role-based access control
        """
        # User with both analyst and viewer roles
        combined_perms = Permissions.get_permissions([Roles.ANALYST, Roles.VIEWER])
        
        # Should have all analyst permissions
        assert "read:graph" in combined_perms
        assert "write:interventions" in combined_perms
        
        # Should not have admin-only permissions
        assert "approve:interventions" not in combined_perms


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_password_verification(self):
        """Test password verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Correct password should verify
        assert verify_password(password, hashed)
        
        # Wrong password should not verify
        assert not verify_password("wrong_password", hashed)


class TestUserAuthentication:
    """Test user authentication logic"""
    
    def test_authenticate_valid_user(self):
        """
        Test authenticating a valid user.
        
        Requirements:
        - 19.1: Authenticate users
        """
        user = authenticate_user("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"
        assert Roles.ADMIN in user["roles"]
    
    def test_authenticate_invalid_password(self):
        """
        Test authentication with invalid password.
        
        Requirements:
        - 19.6: Return None when authentication fails
        - 19.8: Log all authentication failures
        """
        user = authenticate_user("admin", "wrongpassword")
        assert user is None
    
    def test_authenticate_nonexistent_user(self):
        """
        Test authentication with nonexistent user.
        
        Requirements:
        - 19.6: Return None when authentication fails
        """
        user = authenticate_user("nonexistent", "password")
        assert user is None
    
    def test_all_default_users_exist(self):
        """Test that all default users can authenticate"""
        users = [
            ("admin", "admin123", Roles.ADMIN),
            ("analyst", "analyst123", Roles.ANALYST),
            ("viewer", "viewer123", Roles.VIEWER),
            ("service", "service123", Roles.SERVICE_ACCOUNT),
        ]
        
        for username, password, expected_role in users:
            user = authenticate_user(username, password)
            assert user is not None
            assert user["username"] == username
            assert expected_role in user["roles"]


class TestTokenDataModel:
    """Test TokenData model"""
    
    def test_token_data_creation(self):
        """Test creating TokenData from token"""
        data = {
            "sub": "testuser",
            "user_id": "user_123",
            "roles": [Roles.ANALYST],
            "is_service_account": False,
        }
        
        token = create_access_token(data)
        token_data = decode_token(token)
        
        assert token_data.username == "testuser"
        assert token_data.user_id == "user_123"
        assert token_data.roles == [Roles.ANALYST]
        assert token_data.is_service_account is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
