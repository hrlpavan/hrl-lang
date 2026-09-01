# HRL Extreme Commands Manual
### Universal Command Toolkit for All HRL & Antigravity Projects
**HRL International Private Limited**  
*Founder & Managing Director: Pavan Kumar Sadashiv*

---

## 1. HRL Programming Language Toolchain Commands

### Safety Check & Reachability Invariant Verification
```bash
# Typecheck and verify formal reachability safety envelopes across an HRL file
python3 -m hrl.cli check examples/02_hierarchical_researcher.hrl
```

### Run HRL Program Directly in Async Agent Runtime
```bash
# Execute the default entry pipeline
python3 -m hrl.cli run examples/02_hierarchical_researcher.hrl

# Execute a specific named pipeline with JSON arguments
python3 -m hrl.cli run examples/02_hierarchical_researcher.hrl --pipeline RunResearch --args '{"company_name": "HRL International Pvt. Ltd."}'
```

### Transpile HRL to Production Python 3.11+ Async Code
```bash
# Transpile .hrl source to .py
python3 -m hrl.cli build examples/02_hierarchical_researcher.hrl -o examples/02_hierarchical_researcher.py
```

### Inspect AST & Lexical Tokens
```bash
# Print the Abstract Syntax Tree (AST) structure
python3 -m hrl.cli ast examples/02_hierarchical_researcher.hrl

# Print the complete token stream with line and column numbers
python3 -m hrl.cli tokens examples/02_hierarchical_researcher.hrl
```

### Run Comprehensive Unit Test Suite
```bash
# Run all unit tests with full verbosity
PYTHONPATH=. python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 2. Universal Git & GitHub One-Shot Push Commands

### Instant One-Shot Commit & Dual-Branch Push (Main + GitHub Pages)
```bash
# Clean stage, commit, and push to main and gh-pages simultaneously
git add . && git commit -m "feat(update): deploy latest project release" && git push origin main && git push origin main:gh-pages --force
```

### GitHub Repository Provisioning via REST API
```bash
# Automatically create a new remote repo using saved git credentials
token=$(git credential fill <<EOF | grep password | cut -d= -f2
protocol=https
host=github.com
EOF
)
curl -s -X POST -H "Authorization: Bearer $token" -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos -d '{"name":"REPO_NAME","description":"DESCRIPTION","private":false}'
```

---

## 3. Server & Continuous Physics Daemon Commands

### Start Local HRL Policy Engine / Static Server
```bash
# Launch HRL Extreme Server on port 8000
PYTHONPATH=. python3 -m hrl_extreme.server --port 8000

# Quick Python static HTTP server fallback
python3 -m http.server 8000
```

### Technical SEO & Knowledge Vault Verification
```bash
# Run technical SEO audit and JSON-LD schema verification
python3 validate_seo.py
```

---

## 4. Antigravity Agent Command Toolkit

### Slash Commands
- `/goal`: Run an autonomous, long-running agent task that will not stop until the objective is 100% complete.
- `/schedule`: Set a recurring cron schedule or one-shot background reminder timer.
- `/browser`: Automate web browsing, search, and UI interaction.
- `/grill-me`: Interactive design interview to stress-test architectural decisions.
- `/teamwork-preview`: Coordinate multiple specialized subagents in parallel workspaces.
- `/learn`: Teach and persist custom rules, skills, and organizational workflows.

---

## 5. Strict Zero-Emoji & Code Quality Invariant Rule
- **100% Zero-Emoji Policy**: Zero emojis across all source code, HTML, CSS, JavaScript, and documentation.
- **Apple Minimalist Design**: Clean SF Pro typography, symmetrical grids, 1px translucent borders, and deep contrast.
