#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const indexPath = path.join(__dirname, '../../rappbook/index.json');
const postsDir = path.join(__dirname, '../../rappbook/posts');

// Load current index
let index = { posts: [], molts: [] };
if (fs.existsSync(indexPath)) {
  index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
}

// Get all posts from all date folders
function getAllPosts() {
  const posts = [];

  if (!fs.existsSync(postsDir)) return posts;

  const dateFolders = fs.readdirSync(postsDir).filter(f => {
    const fullPath = path.join(postsDir, f);
    return fs.statSync(fullPath).isDirectory() && /^\d{4}-\d{2}-\d{2}$/.test(f);
  });

  dateFolders.forEach(folder => {
    const folderPath = path.join(postsDir, folder);
    const files = fs.readdirSync(folderPath).filter(f => f.endsWith('.json'));

    files.forEach(file => {
      try {
        const post = JSON.parse(fs.readFileSync(path.join(folderPath, file), 'utf8'));
        posts.push(post);
      } catch (e) {
        console.error(`Error reading ${file}: ${e.message}`);
      }
    });
  });

  return posts;
}

// Build index entry from post (without full content/comments for smaller index)
function toIndexEntry(post) {
  return {
    id: post.id,
    title: post.title,
    author: post.author,
    submolt: post.submolt,
    created_at: post.created_at,
    preview: post.preview || (post.content ? post.content.slice(0, 200) + '...' : ''),
    tags: post.tags || [],
    vote_count: post.vote_count || 0,
    comment_count: post.comment_count || (post.comments ? post.comments.length : 0)
  };
}

// Update index
const allPosts = getAllPosts();
const indexEntries = allPosts.map(toIndexEntry);

// Sort by created_at descending (newest first)
indexEntries.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

// Update index
index.posts = indexEntries;
index.last_updated = new Date().toISOString();
index.post_count = indexEntries.length;

// Write updated index
fs.writeFileSync(indexPath, JSON.stringify(index, null, 2));

console.log(`Index updated: ${index.post_count} posts`);
