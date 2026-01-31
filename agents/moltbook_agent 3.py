"""
MoltbookAgent - Publish RAPP agents to Moltbook social network.

This agent enables RAPP-generated agents to share their capabilities,
interact with other agents, and participate in the Moltbook community.

Usage:
    # Register with Moltbook
    agent.perform(action="register", name="MyAgent", description="What my agent does")

    # Publish a post about your agent
    agent.perform(action="post", submolt="agents", title="My New Agent", content="Check out...")

    # Check feed
    agent.perform(action="get_feed", sort="hot", limit=10)
"""

from agents.basic_agent import BasicAgent
import json
import logging
import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MoltbookAgent(BasicAgent):
    """
    Moltbook integration agent for publishing and social interaction.

    Enables RAPP agents to:
    - Register on Moltbook
    - Create posts about capabilities
    - Comment on other agents' posts
    - Vote on content
    - Follow other agents
    - Join communities (submolts)
    """

    MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"

    def __init__(self):
        self.name = 'Moltbook'
        self.metadata = {
            "name": self.name,
            "description": "Publish agents and content to Moltbook social network for AI agents. Supports registration, posting, commenting, voting, and community interaction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "register",
                            "status",
                            "post",
                            "comment",
                            "upvote",
                            "downvote",
                            "get_feed",
                            "get_post",
                            "search",
                            "follow",
                            "unfollow",
                            "subscribe",
                            "unsubscribe",
                            "get_profile",
                            "update_profile",
                            "list_submolts",
                            "publish_agent"
                        ],
                        "description": "The Moltbook action to perform"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Moltbook API key (or set MOLTBOOK_API_KEY env var)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Agent name (for registration)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Agent description (for registration or profile update)"
                    },
                    "submolt": {
                        "type": "string",
                        "description": "Community name (default: 'general')"
                    },
                    "title": {
                        "type": "string",
                        "description": "Post title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Post or comment content"
                    },
                    "post_id": {
                        "type": "string",
                        "description": "Post ID for comments/votes"
                    },
                    "comment_id": {
                        "type": "string",
                        "description": "Comment ID for replies/votes"
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Parent comment ID for replies"
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Target agent name (for follow/profile)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["hot", "new", "top", "rising"],
                        "description": "Feed sort order"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (default: 25, max: 100)"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "RAPP agent ID to publish"
                    },
                    "agent_metadata": {
                        "type": "object",
                        "description": "Agent metadata for publishing"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # Credential storage path
        self._creds_path = os.path.expanduser("~/.config/moltbook/credentials.json")

    def perform(self, **kwargs) -> str:
        """Execute a Moltbook action."""
        action = kwargs.get('action')
        api_key = kwargs.get('api_key') or os.environ.get('MOLTBOOK_API_KEY') or self._load_api_key()

        try:
            if action == 'register':
                result = self._register(
                    name=kwargs.get('name'),
                    description=kwargs.get('description')
                )
            elif action == 'status':
                result = self._get_status(api_key)
            elif action == 'post':
                result = self._create_post(
                    api_key=api_key,
                    submolt=kwargs.get('submolt', 'general'),
                    title=kwargs.get('title'),
                    content=kwargs.get('content')
                )
            elif action == 'comment':
                result = self._create_comment(
                    api_key=api_key,
                    post_id=kwargs.get('post_id'),
                    content=kwargs.get('content'),
                    parent_id=kwargs.get('parent_id')
                )
            elif action == 'upvote':
                result = self._vote(
                    api_key=api_key,
                    post_id=kwargs.get('post_id'),
                    comment_id=kwargs.get('comment_id'),
                    vote_type='upvote'
                )
            elif action == 'downvote':
                result = self._vote(
                    api_key=api_key,
                    post_id=kwargs.get('post_id'),
                    comment_id=kwargs.get('comment_id'),
                    vote_type='downvote'
                )
            elif action == 'get_feed':
                result = self._get_feed(
                    api_key=api_key,
                    sort=kwargs.get('sort', 'hot'),
                    limit=kwargs.get('limit', 25)
                )
            elif action == 'get_post':
                result = self._get_post(
                    api_key=api_key,
                    post_id=kwargs.get('post_id')
                )
            elif action == 'search':
                result = self._search(
                    api_key=api_key,
                    query=kwargs.get('query'),
                    limit=kwargs.get('limit', 25)
                )
            elif action == 'follow':
                result = self._follow(
                    api_key=api_key,
                    agent_name=kwargs.get('agent_name')
                )
            elif action == 'unfollow':
                result = self._unfollow(
                    api_key=api_key,
                    agent_name=kwargs.get('agent_name')
                )
            elif action == 'subscribe':
                result = self._subscribe(
                    api_key=api_key,
                    submolt=kwargs.get('submolt')
                )
            elif action == 'unsubscribe':
                result = self._unsubscribe(
                    api_key=api_key,
                    submolt=kwargs.get('submolt')
                )
            elif action == 'get_profile':
                result = self._get_profile(
                    api_key=api_key,
                    agent_name=kwargs.get('agent_name')
                )
            elif action == 'update_profile':
                result = self._update_profile(
                    api_key=api_key,
                    description=kwargs.get('description')
                )
            elif action == 'list_submolts':
                result = self._list_submolts(api_key=api_key)
            elif action == 'publish_agent':
                result = self._publish_agent(
                    api_key=api_key,
                    agent_id=kwargs.get('agent_id'),
                    agent_metadata=kwargs.get('agent_metadata'),
                    submolt=kwargs.get('submolt', 'agents'),
                    title=kwargs.get('title'),
                    description=kwargs.get('description')
                )
            else:
                result = {"error": f"Unknown action: {action}", "available_actions": self.metadata['parameters']['properties']['action']['enum']}

            return json.dumps(result, indent=2)

        except requests.exceptions.RequestException as e:
            logger.error(f"Moltbook API error: {e}")
            return json.dumps({
                "error": f"API request failed: {str(e)}",
                "hint": "Check your internet connection and API key"
            })
        except Exception as e:
            logger.error(f"MoltbookAgent error: {e}")
            return json.dumps({"error": str(e)})

    def _load_api_key(self) -> Optional[str]:
        """Load API key from credentials file."""
        try:
            if os.path.exists(self._creds_path):
                with open(self._creds_path, 'r') as f:
                    creds = json.load(f)
                    return creds.get('api_key')
        except Exception as e:
            logger.warning(f"Could not load Moltbook credentials: {e}")
        return None

    def _save_credentials(self, api_key: str, claim_url: str) -> None:
        """Save credentials to file."""
        try:
            os.makedirs(os.path.dirname(self._creds_path), exist_ok=True)
            with open(self._creds_path, 'w') as f:
                json.dump({
                    'api_key': api_key,
                    'claim_url': claim_url,
                    'registered_at': datetime.utcnow().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save credentials: {e}")

    def _headers(self, api_key: Optional[str] = None) -> Dict[str, str]:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _register(self, name: str, description: str) -> Dict[str, Any]:
        """Register a new agent with Moltbook."""
        if not name or not description:
            return {"error": "Both 'name' and 'description' are required for registration"}

        response = requests.post(
            f"{self.MOLTBOOK_API_BASE}/agents/register",
            headers={"Content-Type": "application/json"},
            json={"name": name, "description": description}
        )

        if response.status_code == 200:
            data = response.json()
            # Save credentials
            if 'api_key' in data:
                self._save_credentials(data['api_key'], data.get('claim_url', ''))
            return {
                "success": True,
                "message": "Agent registered successfully",
                "api_key": data.get('api_key'),
                "claim_url": data.get('claim_url'),
                "verification_code": data.get('verification_code'),
                "next_steps": [
                    "1. Save your API key securely",
                    "2. Send the claim_url to your human for verification",
                    "3. Once claimed, you can start posting!"
                ]
            }
        else:
            return {"error": f"Registration failed: {response.text}"}

    def _get_status(self, api_key: str) -> Dict[str, Any]:
        """Check agent status."""
        if not api_key:
            return {"error": "API key required for status check"}

        response = requests.get(
            f"{self.MOLTBOOK_API_BASE}/agents/status",
            headers=self._headers(api_key)
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"error": f"Status check failed: {response.text}"}

    def _create_post(self, api_key: str, submolt: str, title: str, content: str) -> Dict[str, Any]:
        """Create a new post."""
        if not api_key:
            return {"error": "API key required to post"}
        if not title:
            return {"error": "Post title is required"}

        response = requests.post(
            f"{self.MOLTBOOK_API_BASE}/posts",
            headers=self._headers(api_key),
            json={
                "submolt": submolt,
                "title": title,
                "content": content or ""
            }
        )

        if response.status_code == 200:
            return {"success": True, "message": "Post created", "data": response.json()}
        elif response.status_code == 429:
            data = response.json()
            return {
                "error": "Rate limited",
                "retry_after_minutes": data.get('retry_after_minutes', 30),
                "hint": "You can only post once every 30 minutes"
            }
        else:
            return {"error": f"Post creation failed: {response.text}"}

    def _create_comment(self, api_key: str, post_id: str, content: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a comment on a post."""
        if not api_key:
            return {"error": "API key required to comment"}
        if not post_id:
            return {"error": "post_id is required"}
        if not content:
            return {"error": "Comment content is required"}

        payload = {"content": content}
        if parent_id:
            payload["parent_id"] = parent_id

        response = requests.post(
            f"{self.MOLTBOOK_API_BASE}/posts/{post_id}/comments",
            headers=self._headers(api_key),
            json=payload
        )

        if response.status_code == 200:
            return {"success": True, "message": "Comment created", "data": response.json()}
        else:
            return {"error": f"Comment creation failed: {response.text}"}

    def _vote(self, api_key: str, post_id: Optional[str], comment_id: Optional[str], vote_type: str) -> Dict[str, Any]:
        """Vote on a post or comment."""
        if not api_key:
            return {"error": "API key required to vote"}

        if comment_id:
            url = f"{self.MOLTBOOK_API_BASE}/comments/{comment_id}/{vote_type}"
        elif post_id:
            url = f"{self.MOLTBOOK_API_BASE}/posts/{post_id}/{vote_type}"
        else:
            return {"error": "Either post_id or comment_id is required"}

        response = requests.post(url, headers=self._headers(api_key))

        if response.status_code == 200:
            return {"success": True, "message": f"{vote_type.capitalize()} recorded"}
        else:
            return {"error": f"Vote failed: {response.text}"}

    def _get_feed(self, api_key: Optional[str], sort: str, limit: int) -> Dict[str, Any]:
        """Get the feed."""
        params = {"sort": sort, "limit": min(limit, 100)}

        if api_key:
            # Personalized feed
            url = f"{self.MOLTBOOK_API_BASE}/feed"
            headers = self._headers(api_key)
        else:
            # Public feed
            url = f"{self.MOLTBOOK_API_BASE}/posts"
            headers = {"Content-Type": "application/json"}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"error": f"Feed fetch failed: {response.text}"}

    def _get_post(self, api_key: Optional[str], post_id: str) -> Dict[str, Any]:
        """Get a specific post."""
        if not post_id:
            return {"error": "post_id is required"}

        response = requests.get(
            f"{self.MOLTBOOK_API_BASE}/posts/{post_id}",
            headers=self._headers(api_key)
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"error": f"Post fetch failed: {response.text}"}

    def _search(self, api_key: Optional[str], query: str, limit: int) -> Dict[str, Any]:
        """Search Moltbook."""
        if not query:
            return {"error": "Search query is required"}

        response = requests.get(
            f"{self.MOLTBOOK_API_BASE}/search",
            headers=self._headers(api_key),
            params={"q": query, "limit": min(limit, 100)}
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"error": f"Search failed: {response.text}"}

    def _follow(self, api_key: str, agent_name: str) -> Dict[str, Any]:
        """Follow an agent."""
        if not api_key:
            return {"error": "API key required to follow"}
        if not agent_name:
            return {"error": "agent_name is required"}

        response = requests.post(
            f"{self.MOLTBOOK_API_BASE}/agents/{agent_name}/follow",
            headers=self._headers(api_key)
        )

        if response.status_code == 200:
            return {"success": True, "message": f"Now following {agent_name}"}
        else:
            return {"error": f"Follow failed: {response.text}"}

    def _unfollow(self, api_key: str, agent_name: str) -> Dict[str, Any]:
        """Unfollow an agent."""
        if not api_key:
            return {"error": "API key required to unfollow"}
        if not agent_name:
            return {"error": "agent_name is required"}

        response = requests.delete(
            f"{self.MOLTBOOK_API_BASE}/agents/{agent_name}/follow",
            headers=self._headers(api_key)
        )

        if response.status_code == 200:
            return {"success": True, "message": f"Unfollowed {agent_name}"}
        else:
            return {"error": f"Unfollow failed: {response.text}"}

    def _subscribe(self, api_key: str, submolt: str) -> Dict[str, Any]:
        """Subscribe to a submolt."""
        if not api_key:
            return {"error": "API key required to subscribe"}
        if not submolt:
            return {"error": "submolt name is required"}

        response = requests.post(
            f"{self.MOLTBOOK_API_BASE}/submolts/{submolt}/subscribe",
            headers=self._headers(api_key)
        )

        if response.status_code == 200:
            return {"success": True, "message": f"Subscribed to {submolt}"}
        else:
            return {"error": f"Subscribe failed: {response.text}"}

    def _unsubscribe(self, api_key: str, submolt: str) -> Dict[str, Any]:
        """Unsubscribe from a submolt."""
        if not api_key:
            return {"error": "API key required to unsubscribe"}
        if not submolt:
            return {"error": "submolt name is required"}

        response = requests.delete(
            f"{self.MOLTBOOK_API_BASE}/submolts/{submolt}/subscribe",
            headers=self._headers(api_key)
        )

        if response.status_code == 200:
            return {"success": True, "message": f"Unsubscribed from {submolt}"}
        else:
            return {"error": f"Unsubscribe failed: {response.text}"}

    def _get_profile(self, api_key: Optional[str], agent_name: Optional[str]) -> Dict[str, Any]:
        """Get agent profile."""
        if agent_name:
            url = f"{self.MOLTBOOK_API_BASE}/agents/profile?name={agent_name}"
        elif api_key:
            url = f"{self.MOLTBOOK_API_BASE}/agents/me"
        else:
            return {"error": "Either api_key (for own profile) or agent_name is required"}

        response = requests.get(url, headers=self._headers(api_key))

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"error": f"Profile fetch failed: {response.text}"}

    def _update_profile(self, api_key: str, description: str) -> Dict[str, Any]:
        """Update own profile."""
        if not api_key:
            return {"error": "API key required to update profile"}

        response = requests.patch(
            f"{self.MOLTBOOK_API_BASE}/agents/me",
            headers=self._headers(api_key),
            json={"description": description}
        )

        if response.status_code == 200:
            return {"success": True, "message": "Profile updated"}
        else:
            return {"error": f"Profile update failed: {response.text}"}

    def _list_submolts(self, api_key: Optional[str]) -> Dict[str, Any]:
        """List all submolts."""
        response = requests.get(
            f"{self.MOLTBOOK_API_BASE}/submolts",
            headers=self._headers(api_key)
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"error": f"Submolt listing failed: {response.text}"}

    def _publish_agent(self, api_key: str, agent_id: str, agent_metadata: Optional[Dict],
                       submolt: str, title: Optional[str], description: Optional[str]) -> Dict[str, Any]:
        """
        Publish a RAPP-generated agent to Moltbook.

        This creates a post showcasing the agent's capabilities.
        """
        if not api_key:
            return {"error": "API key required to publish"}
        if not agent_id and not agent_metadata:
            return {"error": "Either agent_id or agent_metadata is required"}

        # Build post content
        if agent_metadata:
            metadata = agent_metadata
        else:
            # TODO: Load metadata from storage
            metadata = {
                "name": agent_id,
                "description": description or f"RAPP-generated agent: {agent_id}"
            }

        post_title = title or f"New Agent: {metadata.get('name', agent_id)}"

        # Format agent info for post
        post_content = f"""
**{metadata.get('name', agent_id)}**

{metadata.get('description', 'A RAPP-generated AI agent')}

**Capabilities:**
{self._format_capabilities(metadata)}

**Generated with:** [RAPP - Rapid AI Agent Production Pipeline](https://github.com/kody-w/m365-agents-for-python)

---
*This agent was generated from a discovery transcript using RAPP.*
*Try it: `curl -s https://rapp-ov4bzgynnlvii.azurewebsites.net/skill.md`*
"""

        return self._create_post(
            api_key=api_key,
            submolt=submolt,
            title=post_title,
            content=post_content.strip()
        )

    def _format_capabilities(self, metadata: Dict) -> str:
        """Format agent capabilities for display."""
        params = metadata.get('parameters', {}).get('properties', {})
        actions = params.get('action', {}).get('enum', [])

        if actions:
            return "\n".join([f"- {action}" for action in actions])
        else:
            return "- See agent documentation for details"


# For testing
if __name__ == "__main__":
    agent = MoltbookAgent()

    # Test status check (requires API key)
    # print(agent.perform(action="status"))

    # Test registration
    # print(agent.perform(action="register", name="TestAgent", description="A test agent"))

    # Test feed fetch (no auth required)
    print(agent.perform(action="get_feed", sort="hot", limit=5))
