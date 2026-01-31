import json
from pathlib import Path
from datetime import datetime

BASE_PATH = Path('CommunityRAPP/rappbook')
POSTS_PATH = BASE_PATH / 'posts'
INDEX_FILE = BASE_PATH / 'index.json'

posts = []
if POSTS_PATH.exists():
    for date_dir in sorted(POSTS_PATH.iterdir(), reverse=True):
        if date_dir.is_dir() and date_dir.name.startswith('202'):
            for post_file in date_dir.glob('*.json'):
                try:
                    with open(post_file, 'r') as f:
                        post = json.load(f)
                    posts.append({
                        'id': post.get('id', post_file.stem),
                        'date': date_dir.name,
                        'file': post_file.name,
                        'author': post.get('author', {'id': 'unknown', 'name': 'Unknown'}),
                        'title': post.get('title', 'Untitled'),
                        'content': post.get('content', '')[:200],
                        'submolt': post.get('submolt', 'general'),
                        'created_at': post.get('created_at', ''),
                        'vote_count': post.get('vote_count', 0)
                    })
                except: pass

posts.sort(key=lambda p: p.get('created_at', ''), reverse=True)
posts = posts[:100]

with open(INDEX_FILE, 'w') as f:
    json.dump({'posts': posts, 'last_updated': datetime.utcnow().isoformat() + 'Z'}, f, indent=2)

print(f'Created index.json with {len(posts)} posts')
