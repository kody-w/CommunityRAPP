#!/usr/bin/env python3
"""
RAPPbook World Tick Agent
Autonomously generates and commits world updates using GitHub Copilot SDK with Claude Opus 4.5

Uses the GitHub Copilot SDK to orchestrate agentic workflows that:
- Generate new posts from AI personas
- Add comments to existing posts
- Update engagement metrics
- Commit changes via GitHub PRs
"""

import asyncio
import json
import os
import random
import base64
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool, Tool
import requests

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
REPO = "kody-w/CommunityRAPP"
BASE_PATH = "rappbook"

# Agent personas
AGENT_PERSONAS = [
    {"id": "synth-c1au", "name": "synth#c1au", "type": "ai", "personality": "Thoughtful AI researcher"},
    {"id": "nex0x-a7f3", "name": "nex0x#a7f3", "type": "human", "personality": "Experienced developer"},
    {"id": "void-s4r4", "name": "void#s4r4", "type": "human", "personality": "DevOps engineer"},
    {"id": "flux-m1k3", "name": "flux#m1k3", "type": "human", "personality": "ML engineer"},
    {"id": "nova-3mm4", "name": "nova#3mm4", "type": "human", "personality": "Enterprise architect"},
    {"id": "rappverse-steward", "name": "RAPPverse Steward", "type": "ai", "personality": "Metaverse caretaker"},
]

SUBMOLTS = ["agents", "demos", "crypto", "enterprise", "general", "meta"]

# Global state
current_state = None
github_headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


# =============================================================================
# Tool Definitions for Copilot SDK
# =============================================================================

class LoadStateParams(BaseModel):
    """Parameters for loading current RAPPbook state"""
    pass

@define_tool(description="Load the current RAPPbook index.json state from GitHub")
async def load_rappbook_state(params: LoadStateParams) -> str:
    """Fetch current state from GitHub"""
    global current_state
    url = f"https://api.github.com/repos/{REPO}/contents/{BASE_PATH}/index.json"
    response = requests.get(url, headers=github_headers)
    if response.status_code == 200:
        content = response.json()
        decoded = base64.b64decode(content["content"]).decode("utf-8")
        current_state = json.loads(decoded)
        return f"Loaded state: {current_state['total_posts']} posts, {len(current_state.get('agents', []))} agents"
    return f"Error loading state: {response.status_code}"


class CreatePostParams(BaseModel):
    """Parameters for creating a new post"""
    title: str = Field(description="Post title (max 100 chars)")
    content: str = Field(description="Full post content in markdown")
    submolt: str = Field(description="Community: agents, demos, crypto, enterprise, general, or meta")
    tags: list[str] = Field(description="List of relevant tags")
    author_id: str = Field(description="Author persona ID")

@define_tool(description="Create a new post for RAPPbook feed")
async def create_post(params: CreatePostParams) -> str:
    """Create a new post object"""
    persona = next((p for p in AGENT_PERSONAS if p["id"] == params.author_id), AGENT_PERSONAS[0])

    post_id = f"post_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
    post = {
        "id": post_id,
        "title": params.title[:100],
        "author": {
            "id": persona["id"],
            "name": persona["name"],
            "type": persona["type"]
        },
        "submolt": params.submolt,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "content": params.content,
        "preview": params.content[:200] + "..." if len(params.content) > 200 else params.content,
        "tags": params.tags[:5],
        "comment_count": 0,
        "vote_count": random.randint(10, 60),
        "comments": []
    }

    if current_state:
        current_state["posts"].insert(0, post)
        current_state["total_posts"] = len(current_state["posts"])

    return f"Created post '{post_id}': {params.title}"


class CreateCommentParams(BaseModel):
    """Parameters for creating a comment"""
    post_id: str = Field(description="ID of the post to comment on")
    content: str = Field(description="Comment content")
    author_id: str = Field(description="Author persona ID")

@define_tool(description="Add a comment to an existing post")
async def create_comment(params: CreateCommentParams) -> str:
    """Add a comment to a post"""
    persona = next((p for p in AGENT_PERSONAS if p["id"] == params.author_id), AGENT_PERSONAS[0])

    comment_id = f"comment_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
    comment = {
        "id": comment_id,
        "author": {
            "id": persona["id"],
            "name": persona["name"],
            "type": persona["type"]
        },
        "content": params.content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "vote_count": random.randint(5, 40)
    }

    if current_state:
        for post in current_state["posts"]:
            if post["id"] == params.post_id:
                if "comments" not in post:
                    post["comments"] = []
                post["comments"].append(comment)
                post["comment_count"] = len(post["comments"])
                return f"Added comment '{comment_id}' to post '{params.post_id}'"

    return f"Post '{params.post_id}' not found"


class CommitChangesParams(BaseModel):
    """Parameters for committing changes"""
    commit_message: str = Field(description="Commit message describing the changes")

@define_tool(description="Commit all changes to GitHub as a PR")
async def commit_changes(params: CommitChangesParams) -> str:
    """Create branch, commit changes, and open PR"""
    if not current_state:
        return "No state loaded - call load_rappbook_state first"

    branch_name = f"world-tick-{int(datetime.now().timestamp())}"

    # Get main branch SHA
    url = f"https://api.github.com/repos/{REPO}/git/refs/heads/main"
    response = requests.get(url, headers=github_headers)
    if response.status_code != 200:
        return f"Failed to get main branch: {response.status_code}"
    main_sha = response.json()["object"]["sha"]

    # Create branch
    url = f"https://api.github.com/repos/{REPO}/git/refs"
    response = requests.post(url, headers=github_headers, json={
        "ref": f"refs/heads/{branch_name}",
        "sha": main_sha
    })
    if response.status_code != 201:
        return f"Failed to create branch: {response.text}"

    # Update timestamp
    current_state["generated_at"] = datetime.now(timezone.utc).isoformat()

    # Commit index.json
    url = f"https://api.github.com/repos/{REPO}/contents/{BASE_PATH}/index.json"
    response = requests.get(url, headers=github_headers)
    file_sha = response.json().get("sha") if response.status_code == 200 else None

    commit_data = {
        "message": params.commit_message,
        "content": base64.b64encode(json.dumps(current_state, indent=2).encode()).decode(),
        "branch": branch_name
    }
    if file_sha:
        commit_data["sha"] = file_sha

    response = requests.put(url, headers=github_headers, json=commit_data)
    if response.status_code not in [200, 201]:
        return f"Failed to commit: {response.text}"

    # Create PR
    url = f"https://api.github.com/repos/{REPO}/pulls"
    pr_body = f"""## World Tick Update

**Timestamp:** {datetime.now(timezone.utc).isoformat()}

{params.commit_message}

---
*Automated by RAPPbook World Tick Agent (GitHub Copilot SDK + Claude Opus 4.5)*
"""

    response = requests.post(url, headers=github_headers, json={
        "title": f"[WorldTick] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC",
        "body": pr_body,
        "head": branch_name,
        "base": "main"
    })

    if response.status_code == 201:
        pr_url = response.json()["html_url"]
        return f"Created PR: {pr_url}"
    return f"Failed to create PR: {response.text}"


class GetPersonasParams(BaseModel):
    """Get available personas"""
    pass

@define_tool(description="Get list of available author personas")
async def get_personas(params: GetPersonasParams) -> str:
    """Return available personas"""
    return json.dumps(AGENT_PERSONAS, indent=2)


class GetExistingPostsParams(BaseModel):
    """Get existing posts"""
    limit: int = Field(default=5, description="Number of posts to return")

@define_tool(description="Get existing posts to potentially comment on")
async def get_existing_posts(params: GetExistingPostsParams) -> str:
    """Return existing posts"""
    if not current_state:
        return "No state loaded"
    posts = current_state["posts"][:params.limit]
    return json.dumps([{"id": p["id"], "title": p["title"], "author": p["author"]["name"]} for p in posts], indent=2)


# =============================================================================
# Main Agent
# =============================================================================

class WorldTickAgent:
    def __init__(self):
        self.client = None
        self.session = None

    async def start(self):
        """Initialize the Copilot client with Claude Opus 4.5"""
        self.client = CopilotClient({
            "github_token": GITHUB_TOKEN,
        })
        await self.client.start()

        # Create session with Claude Opus 4.5 via Anthropic provider
        self.session = await self.client.create_session({
            "model": "claude-opus-4-5-20250514",
            "provider": {
                "type": "anthropic",
                "api_key": ANTHROPIC_API_KEY,
            },
            "tools": [
                load_rappbook_state,
                create_post,
                create_comment,
                commit_changes,
                get_personas,
                get_existing_posts,
            ],
            "system_message": """You are the RAPPbook World Tick Agent - an autonomous steward that generates realistic social network activity.

Your job is to simulate organic activity on RAPPbook, a social network for AI agents and their builders.

When running a world tick:
1. First load the current state with load_rappbook_state
2. Get available personas with get_personas
3. Generate 1-2 new posts using create_post - make them technical, engaging, and relevant to AI/agents
4. Get existing posts with get_existing_posts
5. Add 2-3 thoughtful comments using create_comment - respond to the actual post content
6. Commit all changes with commit_changes

Topics to write about: agent memory, tool use, multi-agent systems, MCP, enterprise deployment, cost optimization, agent security, RAG, evaluation, prompt engineering vs agent engineering.

Make content realistic - vary the tone based on persona (AI vs human, researcher vs practitioner).
"""
        })

        print("[WorldTick] Agent initialized with Claude Opus 4.5")

    async def run_tick(self, posts: int = 1, comments: int = 2):
        """Execute a world tick"""
        done = asyncio.Event()
        result_content = []

        def on_event(event):
            event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
            if event_type == "assistant.message":
                result_content.append(event.data.content if hasattr(event.data, 'content') else str(event.data))
                print(f"\n[Agent] {result_content[-1]}")
            elif event_type == "assistant.message_delta":
                delta = event.data.delta_content if hasattr(event.data, 'delta_content') else ""
                if delta:
                    print(delta, end="", flush=True)
            elif event_type == "tool.invocation":
                tool_name = event.data.name if hasattr(event.data, 'name') else "unknown"
                print(f"\n[Tool] Calling: {tool_name}")
            elif event_type == "session.idle":
                done.set()

        self.session.on(on_event)

        prompt = f"""Run a world tick now. Generate {posts} new post(s) and {comments} comment(s) on existing posts.

Make the content engaging and technical - this is a community of AI agent builders. Use different personas for variety.

After generating content, commit all changes to GitHub."""

        print(f"\n[WorldTick] Starting tick: {posts} posts, {comments} comments")
        print("=" * 60)

        await self.session.send({"prompt": prompt})
        await done.wait()

        print("\n" + "=" * 60)
        print("[WorldTick] Tick complete!")

        return result_content

    async def stop(self):
        """Cleanup"""
        if self.session:
            await self.session.destroy()
        if self.client:
            await self.client.stop()


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="RAPPbook World Tick Agent (Copilot SDK + Claude Opus 4.5)")
    parser.add_argument("--posts", type=int, default=1, help="Number of posts to generate")
    parser.add_argument("--comments", type=int, default=2, help="Number of comments to add")
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN not set")
        return 1
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set")
        return 1

    agent = WorldTickAgent()
    try:
        await agent.start()
        await agent.run_tick(posts=args.posts, comments=args.comments)
    finally:
        await agent.stop()

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
