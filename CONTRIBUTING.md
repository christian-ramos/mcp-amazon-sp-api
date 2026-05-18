# Contributing

Thanks for considering a contribution. This project is small and pragmatic; the guidelines below exist so changes stay easy to review and ship.

## Development setup

```bash
git clone https://github.com/christian-ramos/mcp-amazon-sp-api.git
cd mcp-amazon-sp-api
uv sync --group dev
```

You need:

- Python ≥ 3.12 (uv will install one if missing)
- [`uv`](https://docs.astral.sh/uv/) ≥ 0.5

You do **not** need Amazon SP-API credentials to run unit tests. Integration tests are skipped automatically when no credentials are present.

## Workflow

1. Open an issue first for non-trivial changes — describe the problem, not the implementation.
2. Fork the repo and create a topic branch from `master`.
3. Make focused commits. One logical change per commit. Conventional-style prefixes (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:`) are appreciated.
4. Run the full local check before pushing:

   ```bash
   uv run ruff check .
   uv run pytest tests/unit --no-cov
   ```

5. Open a pull request against `master`. The CI must pass before review.

## Code style

- Linted with `ruff` (config in `pyproject.toml`). Run `uv run ruff check . --fix` to apply autofixes.
- Type hints encouraged on public functions; not strictly enforced.
- No comments that restate what the code does. Comment only non-obvious *why*.
- Match the surrounding style — this repo deliberately keeps tools small and explicit.

## Tests

- New behaviour requires a unit test. Bug fixes require a regression test.
- Unit tests under `tests/unit/` must not hit the network or filesystem outside `tmp_path`.
- Integration tests (`tests/integration/`) use real SP-API sandbox credentials and are gated with `@skip_without_credentials`. They are optional for contributors.
- Aim to keep coverage at or above the current level (~95%).

## Pull requests

- Keep PRs small. Large refactors should be split or proposed in an issue first.
- Describe **why** in the PR body; the diff already shows **what**.
- Link the issue it resolves (e.g. `Closes #42`).
- Allow maintainer edits on your branch unless you have a reason not to.

## Reporting bugs

Open a GitHub issue with:

- What you expected to happen
- What actually happened (logs, stack traces, screenshots)
- Minimal reproduction steps
- Versions: `uv --version`, `python --version`, OS

## Security

Do **not** open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the same [MIT License](LICENSE) as the project.
