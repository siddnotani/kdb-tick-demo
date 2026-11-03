# AGENTS.md

kdb+/q tick stack demo with a PyKX/FastAPI service. For q work, follow `.devin/skills/kdb-q/SKILL.md`.

- Lint: `ruff check . && ruff format --check .`
- Test: `q tests/q/run.q -q && pytest -q`
- Run: `scripts/start.sh`, then `uvicorn app.main:app --port 8000`. Stop with `scripts/stop.sh`.
- Commit messages start with `feat:`, `fix:` or `chore:`. Work on `devin/<slug>` branches with one PR per change.
