---
name: new-project
description: Create a new project from template and set up a GitHub repo (public or private)
user-invocable: true
disable-model-invocation: true
---

# Create New Project from Template

Create a new game documentation project from the `game-doc-template` repository and set up a GitHub repository (public or private).

## Prerequisites

- `gh` CLI is installed and authenticated.
- `git` is configured.
- Source PDF is available.

## Process

### 1. Gather Information

Use AskUserQuestion once to collect the following:

**Question 1: Project Path**
- header: "Project Path"
- question: "Where should the new project be created?"
- options:
  - `../` (default, sibling to template)
  - Custom path

**Question 2: Game Title (zh-TW)**
- header: "Game Title"
- question: "What is the Traditional Chinese title for this game?"
- Extract the original title from the PDF filename as reference.

**Question 3: Project Name** (if `$ARGUMENTS` does not include it)
- header: "Project Name"
- question: "What should the project folder and repo name be?"
- Suggest a lowercase hyphenated slug from the PDF filename.

**Question 4: Repository Visibility**
- header: "Repo Type"
- question: "Should the GitHub repo be public or private?"
- options:
  - Private repo (default)
  - Public repo

Example:
```
PDF: "Blades in the Dark.pdf"
Original title: Blades in the Dark
zh-TW title: 暗夜冷鋒
Suggested project name: blades-in-the-dark
```

### 2. Determine Paths and Variables

```bash
# Template repo (current project)
TEMPLATE_REPO="weihung/game-doc-template"

# Target directory (user specified, default: ../)
TARGET_DIR="<user_specified_path>/<project_name>"

# PDF path (from arguments)
PDF_PATH="$ARGUMENTS[0]"

# Game titles
GAME_TITLE_EN="<extracted_from_pdf>"
GAME_TITLE_ZH="<user_specified>"

# Repo visibility
REPO_VISIBILITY="<private_or_public>"

# GitHub URL
REPO_URL="https://github.com/<username>/<project_name>"
```

### 3. Clone Template

```bash
# Navigate to parent directory
cd <user_specified_path>

# Create from template and clone
gh repo create <project_name> --template $TEMPLATE_REPO --$REPO_VISIBILITY --clone

# Local-copy fallback:
# cp -r <template_path> <TARGET_DIR>
# cd <TARGET_DIR>
# rm -rf .git
# git init
```

### 4. Create GitHub Repository (Local-Copy Mode Only)

```bash
cd <TARGET_DIR>

# Create repo using selected visibility
gh repo create <project_name> --$REPO_VISIBILITY --source=. --remote=origin

# Push initial commit
git add .
git commit -m "Initial commit from game-doc-template"
git push -u origin main
```

### 5. Copy PDF

```bash
mkdir -p data/pdfs
cp "<pdf_path>" data/pdfs/
```

### 6. Update Project Configuration

Edit `docs/astro.config.mjs`:
- Update `SITE_CONFIG.title` with `GAME_TITLE_ZH`.
- If `REPO_VISIBILITY=public`, add Starlight GitHub social link:

```js
social: [
  { icon: 'github', label: 'GitHub', href: 'https://github.com/<username>/<project_name>' },
],
```

Edit `style-decisions.json`:
- Store repository metadata as the source of truth:

```json
{
  "repository": {
    "visibility": "public",
    "url": "https://github.com/<username>/<project_name>",
    "show_on_homepage": true
  }
}
```

Homepage behavior:
- If `REPO_VISIBILITY=public` and `show_on_homepage=true`, include repo link in `docs/src/content/docs/index.md`.
- If `REPO_VISIBILITY=private`, keep metadata but do not expose repo links in UI.

Edit `CLAUDE.md`:
- Update project description with both original and zh-TW game titles.

### 7. Verify Setup

```bash
ls -la
ls -la data/pdfs/
ls -la docs/
git remote -v
```

### 8. Next Steps

Inform user:
```
✓ Project created: <project_name>
✓ Game title: <GAME_TITLE_EN>（<GAME_TITLE_ZH>）
✓ Project path: <TARGET_DIR>
✓ Repo type: <REPO_VISIBILITY>
✓ GitHub repo: https://github.com/<username>/<project_name>
✓ PDF copied to: data/pdfs/<filename>

Next:
1. cd <TARGET_DIR>
2. Run /init-doc
```

## Example Usage

```
/new-project ~/Downloads/Blades-in-the-Dark.pdf
/new-project ~/Downloads/game.pdf my-game-docs
```

## Error Handling

- If `gh` is missing: provide install instructions.
- If not authenticated: run `gh auth login`.
- If repo name is taken: suggest alternatives.
- If PDF is missing: ask for correct path.
