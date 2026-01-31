"""
GitHubOAuthAgent - Handle GitHub OAuth for RAPPbook authentication.

This agent manages the OAuth flow for RAPPbook, allowing users to sign in
with their GitHub account and automatically post interactions.
"""

from agents.basic_agent import BasicAgent
import json
import logging
import os
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class GitHubOAuthAgent(BasicAgent):
    """
    GitHub OAuth handler for RAPPbook authentication.

    Supports:
    - OAuth authorization URL generation
    - Token exchange (code -> access token)
    - User profile retrieval
    - Token validation
    """

    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_API_URL = "https://api.github.com"

    def __init__(self):
        self.name = 'GitHubOAuth'
        self.metadata = {
            "name": self.name,
            "description": "Handle GitHub OAuth authentication for RAPPbook. Supports login, token exchange, and user profile retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_auth_url",
                            "exchange_code",
                            "get_user",
                            "validate_token",
                            "revoke_token"
                        ],
                        "description": "The OAuth action to perform"
                    },
                    "code": {
                        "type": "string",
                        "description": "Authorization code from GitHub (for exchange_code)"
                    },
                    "access_token": {
                        "type": "string",
                        "description": "GitHub access token (for get_user, validate_token)"
                    },
                    "redirect_uri": {
                        "type": "string",
                        "description": "OAuth redirect URI"
                    },
                    "state": {
                        "type": "string",
                        "description": "OAuth state parameter for CSRF protection"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # OAuth app credentials (set via environment variables)
        self.client_id = os.environ.get('GITHUB_OAUTH_CLIENT_ID', '')
        self.client_secret = os.environ.get('GITHUB_OAUTH_CLIENT_SECRET', '')

    def perform(self, **kwargs) -> str:
        """Execute a GitHub OAuth action."""
        action = kwargs.get('action')

        try:
            if action == 'get_auth_url':
                result = self._get_auth_url(
                    redirect_uri=kwargs.get('redirect_uri'),
                    state=kwargs.get('state')
                )
            elif action == 'exchange_code':
                result = self._exchange_code(
                    code=kwargs.get('code'),
                    redirect_uri=kwargs.get('redirect_uri')
                )
            elif action == 'get_user':
                result = self._get_user(
                    access_token=kwargs.get('access_token')
                )
            elif action == 'validate_token':
                result = self._validate_token(
                    access_token=kwargs.get('access_token')
                )
            elif action == 'revoke_token':
                result = self._revoke_token(
                    access_token=kwargs.get('access_token')
                )
            else:
                result = {
                    "error": f"Unknown action: {action}",
                    "available_actions": self.metadata['parameters']['properties']['action']['enum']
                }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"GitHubOAuthAgent error: {e}")
            return json.dumps({"error": str(e)})

    def _get_auth_url(self, redirect_uri: Optional[str], state: Optional[str]) -> Dict[str, Any]:
        """Generate GitHub OAuth authorization URL."""
        if not self.client_id:
            return {
                "error": "GitHub OAuth not configured",
                "hint": "Set GITHUB_OAUTH_CLIENT_ID environment variable"
            }

        params = {
            "client_id": self.client_id,
            "scope": "repo user:email",
            "state": state or "rappbook"
        }

        if redirect_uri:
            params["redirect_uri"] = redirect_uri

        auth_url = f"{self.GITHUB_AUTH_URL}?{urlencode(params)}"

        return {
            "success": True,
            "auth_url": auth_url,
            "state": params["state"]
        }

    def _exchange_code(self, code: Optional[str], redirect_uri: Optional[str]) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        if not code:
            return {"error": "Authorization code is required"}

        if not self.client_id or not self.client_secret:
            return {
                "error": "GitHub OAuth not configured",
                "hint": "Set GITHUB_OAUTH_CLIENT_ID and GITHUB_OAUTH_CLIENT_SECRET"
            }

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code
        }

        if redirect_uri:
            data["redirect_uri"] = redirect_uri

        response = requests.post(
            self.GITHUB_TOKEN_URL,
            data=data,
            headers={"Accept": "application/json"}
        )

        if response.status_code == 200:
            token_data = response.json()

            if "error" in token_data:
                return {
                    "error": token_data.get("error_description", token_data["error"]),
                    "hint": "The authorization code may have expired. Try signing in again."
                }

            # Get user info with the token
            user_info = self._get_user(token_data.get("access_token"))

            return {
                "success": True,
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type"),
                "scope": token_data.get("scope"),
                "user": user_info.get("user") if user_info.get("success") else None
            }
        else:
            return {"error": f"Token exchange failed: {response.text}"}

    def _get_user(self, access_token: Optional[str]) -> Dict[str, Any]:
        """Get authenticated user's profile."""
        if not access_token:
            return {"error": "Access token is required"}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.get(f"{self.GITHUB_API_URL}/user", headers=headers)

        if response.status_code == 200:
            user = response.json()
            return {
                "success": True,
                "user": {
                    "id": user.get("id"),
                    "login": user.get("login"),
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "avatar_url": user.get("avatar_url"),
                    "html_url": user.get("html_url"),
                    "bio": user.get("bio")
                }
            }
        elif response.status_code == 401:
            return {"error": "Invalid or expired token"}
        else:
            return {"error": f"Failed to get user: {response.text}"}

    def _validate_token(self, access_token: Optional[str]) -> Dict[str, Any]:
        """Validate an access token."""
        if not access_token:
            return {"error": "Access token is required"}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.get(f"{self.GITHUB_API_URL}/user", headers=headers)

        if response.status_code == 200:
            return {
                "success": True,
                "valid": True,
                "user": response.json().get("login")
            }
        else:
            return {
                "success": True,
                "valid": False,
                "reason": "Token is invalid or expired"
            }

    def _revoke_token(self, access_token: Optional[str]) -> Dict[str, Any]:
        """Revoke an access token (requires client credentials)."""
        if not access_token:
            return {"error": "Access token is required"}

        if not self.client_id or not self.client_secret:
            return {"error": "OAuth credentials not configured"}

        # GitHub requires basic auth with client credentials to revoke
        response = requests.delete(
            f"{self.GITHUB_API_URL}/applications/{self.client_id}/token",
            auth=(self.client_id, self.client_secret),
            headers={"Accept": "application/vnd.github+json"},
            json={"access_token": access_token}
        )

        if response.status_code == 204:
            return {"success": True, "message": "Token revoked"}
        else:
            return {"error": f"Failed to revoke token: {response.text}"}


# Testing
if __name__ == "__main__":
    agent = GitHubOAuthAgent()

    # Test auth URL generation
    print(agent.perform(action="get_auth_url", state="test123"))
