#!/bin/bash
# ============================================================
# Data Product Concierge — GitHub + Streamlit Cloud Deploy
# ============================================================
# Run this script from inside the project folder on your machine.
# Prerequisites: git, gh (GitHub CLI) — install via https://cli.github.com
# ============================================================

set -e

REPO_NAME="data-product-concierge"

echo "✦ Data Product Concierge — Deploy Script"
echo "=========================================="

# 1. Check prerequisites
command -v git >/dev/null 2>&1 || { echo "❌ git is required. Install it first."; exit 1; }
command -v gh >/dev/null 2>&1 || { echo "❌ GitHub CLI (gh) is required. Install from https://cli.github.com"; exit 1; }

# 2. Check GitHub auth
echo "→ Checking GitHub authentication..."
gh auth status || { echo "❌ Not logged in. Run: gh auth login"; exit 1; }

# 3. Get GitHub username
GH_USER=$(gh api user --jq '.login')
echo "→ Logged in as: $GH_USER"

# 4. Initialize git if needed
if [ ! -d ".git" ]; then
    echo "→ Initializing git repository..."
    git init -b main
fi

# 5. Ensure we're on main branch
git branch -M main

# 6. Stage and commit
echo "→ Staging all files..."
git add -A
git commit -m "feat: Data Product Concierge — production build

Enterprise Streamlit application for finding, reusing, and creating
governed data products in Collibra with AI concierge guidance.

- APIM Gateway JWT authentication
- Live Collibra API integration (zero mock data)
- 30-field DataProductSpec with triple export (MD, JSON, CSV)
- LLM-powered concierge (OpenAI/Bedrock)
- PostgreSQL session tracking
- Enterprise design system (navy + teal)
- Docker + Streamlit Cloud deployment ready

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>" 2>/dev/null || echo "→ Already committed (no changes)"

# 7. Create GitHub repo
echo "→ Creating public GitHub repository: $GH_USER/$REPO_NAME ..."
gh repo create "$REPO_NAME" --public --source=. --remote=origin --push \
    --description "AI-powered Data Product Concierge for enterprise asset management — Collibra + Streamlit" \
    2>/dev/null || {
    echo "→ Repo may already exist. Pushing to existing remote..."
    git remote add origin "https://github.com/$GH_USER/$REPO_NAME.git" 2>/dev/null || true
    git push -u origin main
}

echo ""
echo "✅ Deployed to GitHub!"
echo "   https://github.com/$GH_USER/$REPO_NAME"
echo ""
echo "=========================================="
echo "NEXT: Deploy to Streamlit Cloud"
echo "=========================================="
echo ""
echo "1. Go to https://share.streamlit.io"
echo "2. Click 'New app'"
echo "3. Select repository: $GH_USER/$REPO_NAME"
echo "4. Branch: main"
echo "5. Main file path: app.py"
echo "6. Click 'Advanced settings' → paste your secrets from .streamlit/secrets.toml.example"
echo "7. Click 'Deploy'"
echo ""
echo "✦ Done! Your concierge is ready to serve."
