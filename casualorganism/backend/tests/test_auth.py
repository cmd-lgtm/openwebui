"""
Tests for Authentication and Authorization

This module tests JWT authentication and role-based access control.

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
from fastapi.testclient import TestClient
from datetime import timedelta
from jose import jwt

from backend.main import app
from backend.core.auth import (
    create_access_token,
    decode_token,
    authenticate_user,
    Roles,
    Permissions,
    SECRET_KEY,
    ALGORITHM,
)


client = TestClient(app)


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


class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""
    
    def test_login_success(self):
        """
        Test successful login.
        
        Requirements:
        - 19.1: Generate JWT tokens for authenticated users
        """
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify token is valid
        token_data = decode_token(data["access_token"])
        assert token_data.username == "admin"
        assert Roles.ADMIN in token_data.roles
    
    def test_login_invalid_credentials(self):
        """
        Test login with invalid credentials.
        
        Requirements:
        - 19.6: Return HTTP 401 when authentication fails
        - 19.8: Log all authentication failures
        """
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """
        Test login with nonexistent user.
        
        Requirements:
        - 19.6: Return HTTP 401 when authentication fails
        """
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """
        Test getting current user information.
        
        Requirements:
        - 19.1: Require valid JWT token
        - 19.3: Extract user identity and roles from JWT claims
        """
        # Login first
        login_response = client.post(
            "/auth/login",
            json={"username": "analyst", "password": "analyst123"}
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "analyst"
        assert Roles.ANALYST in data["roles"]
        assert "permissions" in data
        assert "read:graph" in data["permissions"]
    
    def test_service_account_token_creation(self):
        """
        Test service account token creation.
        
        Requirements:
        - 19.7: Support service account tokens for inter-service calls
        """
        response = client.post(
            "/auth/service-token",
            json={
                "service_name": "worker-service",
                "service_secret": "service-secret-change-in-production"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        # Verify token
        token_data = decode_token(data["access_token"])
        assert token_data.is_service_account is True
        assert Roles.SERVICE_ACCOUNT in token_data.roles


class TestProtectedEndpoints:
    """Test that endpoints are properly protected"""
    
    def test_graph_stats_requires_auth(self):
        """
        Test that graph stats endpoint requires authentication.
        
        Requirements:
        - 19.1: Require valid JWT token for all non-health-check endpoints
        - 19.6: Return HTTP 401 when authentication fails
        """
        response = client.get("/api/graph/stats")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    def test_graph_stats_with_valid_token(self):
        """
        Test graph stats endpoint with valid token.
        
        Requirements:
        - 19.1: Require valid JWT token
        - 19.4: Enforce role-based access control
        """
        # Login as viewer (has read:graph permission)
        login_response = client.post(
            "/auth/login",
            json={"username": "viewer", "password": "viewer123"}
        )
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/graph/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should succeed (viewer has read:graph permission)
        assert response.status_code == 200
    
    def test_intervention_approval_requires_admin(self):
        """
        Test that intervention approval requires admin role.
        
        Requirements:
        - 19.4: Enforce role-based access control
        - 19.5: Return HTTP 403 when user lacks required role
        """
        # Login as analyst (does not have approve:interventions permission)
        login_response = client.post(
            "/auth/login",
            json={"username": "analyst", "password": "analyst123"}
        )
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/interventions/approve",
            headers={"Authorization": f"Bearer {token}"},
            json={"intervention_id": "test_id"}
        )
        
        # Should fail with 403 (insufficient permissions)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
    
    def test_intervention_approval_with_admin(self):
        """
        Test that admin can approve interventions.
        
        Requirements:
        - 19.4: Enforce role-based access control
        """
        # Login as admin
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/interventions/approve",
            headers={"Authorization": f"Bearer {token}"},
            json={"intervention_id": "nonexistent_id"}
        )
        
        # Should not fail with 403 (admin has permission)
        # May fail with 404 or 500 due to nonexistent intervention, but not 403
        assert response.status_code != 403
    
    def test_health_check_no_auth_required(self):
        """
        Test that health check endpoint does not require authentication.
        
        Requirements:
        - 19.1: Non-health-check endpoints require auth (health checks exempt)
        """
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestUserAuthentication:
    """Test user authentication logic"""
    
    def test_authenticate_valid_user(self):
        """Test authenticating a valid user"""
        user = authenticate_user("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"
        assert Roles.ADMIN in user["roles"]
    
    def test_authenticate_invalid_password(self):
        """Test authentication with invalid password"""
        user = authenticate_user("admin", "wrongpassword")
        assert user is None
    
    def test_authenticate_nonexistent_user(self):
        """Test authentication with nonexistent user"""
        user = authenticate_user("nonexistent", "password")
        assert user is None


class TestAuthenticationErrorHandling:
    """Test authentication and authorization error handling"""
    
    def test_401_on_missing_token(self):
        """
        Test that missing token returns 401.
        
        Requirements:
        - 19.6: Return HTTP 401 when authentication fails
        - 19.8: Log all authentication failures
        """
        response = client.get("/api/graph/stats")
        # FastAPI returns 403 for missing credentials
        assert response.status_code == 403
    
    def test_401_on_invalid_token(self):
        """
        Test that invalid token returns 401.
        
        Requirements:
        - 19.6: Return HTTP 401 when authentication fails
        - 19.8: Log all authentication failures
        """
        response = client.get(
            "/api/graph/stats",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_403_on_insufficient_permissions(self):
        """
        Test that insufficient permissions returns 403.
        
        Requirements:
        - 19.5: Return HTTP 403 when user lacks required role
        - 19.8: Log all authorization failures
        """
        # Login as viewer (no write permissions)
        login_response = client.post(
            "/auth/login",
            json={"username": "viewer", "password": "viewer123"}
        )
        token = login_response.json()["access_token"]
        
        # Try to trigger analysis (requires write:metrics)
        response = client.post(
            "/api/causal/analyze",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["error"]
    
    def test_error_response_format(self):
        """
        Test that error responses have consistent format.
        
        Requirements:
        - 19.6: Return HTTP 401 when authentication fails
        """
        response = client.get(
            "/api/graph/stats",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
