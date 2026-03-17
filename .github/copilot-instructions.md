# Copilot Instructions: MINDSTREAM

**Project:** CLI-first Python pipeline for YouTube discovery, transcript ingestion, summarization, and reporting  
**Repository:** https://github.com/amitkv1983/mindstream  
**Framework:** space_framework (enforced governance)  
**Framework Repository:** https://github.com/nsin08/space_framework  
**Last Updated:** 2026-03-17

---

## 1. Load Framework Context (REQUIRED)

All agents must load framework rules first:

```
@space_framework Load: 10-roles/00-shared-context.md
```

This provides:
- Mandatory state machine (Idea -> Approved -> Ready -> In Progress -> In Review -> Done -> Released)
- AI agent boundaries (cannot merge, approve, or skip states)
- Enforced rules (DoR, DoD, artifact linking, approval gates)

---

## 1.1 Environment Awareness (Reduce Retries)

Agents MUST adapt to the user's environment and avoid guessing.

### Preflight (run once before GitHub/Git operations)

- Detect which shell you are in and output commands for that shell only.
- If the environment is unknown, ask the user: OS + shell (Windows PowerShell vs WSL bash vs macOS zsh).
- If the repo includes helper scripts, prefer running one preflight:
  - PowerShell: `scripts/env-preflight.ps1`
  - bash/zsh (Linux/macOS/WSL): `scripts/env-preflight.sh`
- Confirm `git` exists (`git --version`).
- Confirm `gh` exists (`gh --version`).
- If you will create/update Issues/PRs/labels: confirm auth (`gh auth status`).
  - If not authenticated: STOP and ask the user to authenticate. Do not attempt alternate methods.

### Command emission rule (must-follow)

- Emit exactly one command variant matching the detected shell (PowerShell OR bash). Do not mix syntaxes.
- If the user explicitly asks for both, provide both variants labeled clearly.

### GitHub tooling policy

- Prefer `gh` first for GitHub operations (issues/PRs/labels).
- Use GitHub MCP only if the user explicitly asks to use it (and only after checking it is available).
- Do not try multiple approaches for the same action; fail fast with the exact error and missing prerequisite.

### Branch safety

- Do not push directly to protected branches (`main`, `develop`, `release/*`) unless the user explicitly requests it.
- Use PR-based flow for merges; branch protection enforces policy server-side.

---

## 2. Project Identity

| Item | Value |
|------|-------|
| **Primary Language** | Python 3.10+ |
| **Repository** | https://github.com/amitkv1983/mindstream |
| **CODEOWNER** | @amitkv1983 |
| **Tech Lead** | @nsin08 |
| **PM** | @nsin08 |

**Governance:**
- All work flows through the state machine (per Rule 01)
- Only CODEOWNER merges PRs (per Rule 06)

---

## 3. Quick Start: Setup & Development

### Clone and Install

```powershell
git clone https://github.com/amitkv1983/mindstream.git
cd mindstream
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

### Run Tests

```powershell
pytest
```

### Run Locally

```powershell
python -m mindstream.cli.run_report --channels configs/channels.txt
streamlit run src/mindstream/ui/app.py
```

### Linting & Formatting

```powershell
python -m compileall src tests
```

---

## 4. Project Structure

```text
src/
  mindstream/
    cli/
    ingest/
    process/
    storage/
    ui/
tests/
configs/
data/
  raw/
  per_video/
  reports/
.context/
  project/
  sprint/
  temp/
  issues/
  reports/
```

---

## 5. File Organization Rules (Rule 11)

### Taxonomy

- Committed: `.context/project/`, `.context/sprint/`
- Git-ignored: `.context/temp/`, `.context/issues/`, `.context/reports/`

### Required `.gitignore` entries

```gitignore
# Context: Local-only temp, issue workspaces, and reports (Rule 11)
.context/temp/
.context/issues/
.context/reports/
```

---

## 6. Code Standards

### Before Opening a PR

- [ ] Tests written for each acceptance criterion (per Rule 03 DoD)
- [ ] Tests passing locally
- [ ] Lint/format checks passing locally
- [ ] No debug statements committed (print/console.log/etc.)
- [ ] No secrets committed

### Branch Naming (Rule 07)

**Pattern:** `<type>/<issue-id>-<slug>`

**Types:** `feature/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`, `perf/`

**Examples:**
- `feature/42-user-authentication`
- `fix/99-null-pointer-exception`
- `docs/55-api-documentation`

### Commit Message Format (recommended)

**Pattern:** `<type>(<scope>): <subject>`

**Types:** feat, fix, docs, refactor, test, chore, perf

**Example:**
```text
feat(auth): add JWT login endpoint

Closes #42
```

### PR Requirements (Rule 08 + Rule 04)

- Must link to a single Story/Issue: `Closes #<id>` or `Resolves #<id>`
- Must include evidence mapping (each acceptance criterion -> test + location)
- Must be reviewable (avoid unrelated changes)

**Evidence Mapping Table (required in PR body):**

| Criterion | Test | Location | Status |
|-----------|------|----------|--------|
| [criterion] | [test name] | [path:line] | pass/fail |

---

## 7. Role-Based Entry Points

When assigned work, load your role context:

| I am a... | Load | Then |
|-----------|------|------|
| **Implementer** | `@space_framework 10-roles/05-implementer.md` | Implement Story in `state:ready` |
| **Reviewer** | `@space_framework 10-roles/06-reviewer.md` | Review PR against DoD + evidence |
| **DevOps** | `@space_framework 10-roles/07-devops.md` | Release/deploy per governance |
| **Architect** | `@space_framework 10-roles/04-architect.md` | Validate feasibility + design |

---

## 8. Hard Boundaries (Cannot Override)

You CANNOT:
- Merge PRs (CODEOWNER only)
- Approve PRs (human reviewers only)
- Skip workflow states
- Modify security-sensitive governance without approval (e.g., CODEOWNERS, CI/CD) per Rule 10
- Access secrets or credentials

You CAN:
- Implement within assigned Story scope
- Open PRs with evidence mapping
- Request reviews and respond to feedback
- Document discoveries per Rule 11

---

## 9. Essential Workflows

### Starting Work on a Story

1. Story must be labeled `state:ready`
2. Create branch per Rule 07
3. Implement acceptance criteria + tests
4. Keep drafts in `.context/temp/` (promote durable notes to `.context/project/` or `.context/sprint/`)

### Opening a PR

1. Link issue: `Closes #123` / `Resolves #123`
2. Fill evidence mapping table
3. Request reviews (tag CODEOWNER + relevant reviewers)
4. Ensure CI is green

---

## 10. Discovery Workflow (Agents)

**Draft first:** put exploratory notes in `.context/temp/` (git-ignored).  
**Promote later:** move stable, durable information into:
- `.context/project/` (architecture, ADRs, meetings, runbooks)
- `.context/sprint/` (sprint plans, retros)

---

## 11. Key References

- Framework roles: `10-roles/`
- Framework rules: `20-rules/` (especially Rule 01, 03, 04, 06, 07, 08, 10, 11)
- Templates: `50-templates/`
- Enforcement workflows: `70-enforcement/`

---

## Initialization Checklist (Human, One-Time)

- [ ] Copy this file to `.github/copilot-instructions.md`
- [ ] Fill Sections 2-6 with project-specific details
- [ ] Ensure `.gitignore` has Rule 11 entries
- [ ] Add CODEOWNERS file in `.github/CODEOWNERS`
- [ ] Configure branch protection rules for `main`
- [ ] Commit and push
