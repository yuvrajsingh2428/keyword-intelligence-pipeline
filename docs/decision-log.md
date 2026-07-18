# Decision Log

> Architecture Decision Records (ADRs) for the Keyword Intelligence Pipeline.
> Each entry documents a key technical decision, its context, and rationale.

---

## ADR-001: Loguru over structlog for Logging

**Date**: 2024-01-15
**Status**: Accepted

### Context

The project needs a structured logging solution that supports both human-readable console output (development) and JSON-formatted output (production). Two leading candidates were evaluated: `structlog` and `loguru`.

### Decision

Use **Loguru** as the logging framework.

### Rationale

- **Zero configuration**: Loguru works out of the box with sensible defaults. structlog requires boilerplate processor chain setup.
- **Built-in rotation**: Loguru natively supports file rotation, retention, and compression. structlog requires additional setup with stdlib `logging.handlers`.
- **Simpler API**: `logger.info("msg", key=value)` vs structlog's processor pipeline.
- **Better DX**: Coloured output, exception formatting, and context binding with minimal code.
- **Single dependency**: Loguru is self-contained. structlog often requires additional packages for full functionality.

### Trade-offs

- structlog has deeper stdlib integration and more granular processor control.
- Loguru's singleton logger pattern is less explicit than structlog's bound loggers.
- structlog is more common in large-scale distributed systems.

---

## ADR-002: Pydantic BaseSettings for Configuration

**Date**: 2024-01-15
**Status**: Accepted

### Context

The application needs typed, validated configuration loaded from environment variables and `.env` files.

### Decision

Use **pydantic-settings** (`BaseSettings`) for all configuration management.

### Rationale

- **Type safety**: Every setting has a declared type — the app fails fast on invalid values.
- **Validation**: Pydantic validates values at construction time, not at first use.
- **Documentation**: Field types, defaults, and descriptions serve as living documentation.
- **Testing**: Settings can be constructed with overrides — no env var manipulation needed.
- **Native .env support**: Built-in `env_file` parameter with `python-dotenv` integration.

---

## ADR-003: `keyword_intelligence` Package Name

**Date**: 2024-01-15
**Status**: Accepted

### Context

The project needs a top-level Python package name. Options considered: `src`, `app`, `kip`, `keyword_intel`, `keyword_intelligence`.

### Decision

Use **`keyword_intelligence`** as the top-level package name.

### Rationale

- **Descriptive**: Immediately communicates the project's domain.
- **No collisions**: Unlikely to conflict with any third-party package.
- **Import clarity**: `from keyword_intelligence.config import Settings` is self-documenting.
- **PyPI-ready**: Works as a proper distribution name if the project is ever published.

### Rejected

- `src`: Too generic, collision risk, unclear in imports.
- `kip`: Too abbreviated, unclear to new contributors.
- `app`: Conflicts with common patterns and framework conventions.

---

## ADR-004: Separate requirements.txt and requirements-dev.txt

**Date**: 2024-01-15
**Status**: Accepted

### Context

Dependencies need to be managed for both production and development environments.

### Decision

Maintain two separate requirements files:
- `requirements.txt`: Runtime dependencies only.
- `requirements-dev.txt`: Development dependencies, inheriting runtime via `-r requirements.txt`.

### Rationale

- **Lean production images**: Docker containers install only `requirements.txt`.
- **Clear separation**: Developers know exactly which deps are runtime vs dev-only.
- **Simple inheritance**: `-r requirements.txt` in dev file avoids duplication.
- **No complex tooling**: No need for poetry, pdm, or pip-tools for Phase 1.

---

## ADR-005: Cross-Platform Developer Scripts

**Date**: 2024-01-15
**Status**: Accepted

### Context

The team uses a mix of Windows and Linux/macOS. Developer commands need to work on all platforms.

### Decision

Ship both a **Makefile** and **PowerShell scripts** (`scripts/*.ps1`).

### Rationale

- **Makefile**: Industry standard for Python projects. Works in CI (Ubuntu). Concise syntax.
- **PowerShell**: Native Windows experience. No additional tooling needed.
- **Mirror targets**: Both systems provide the same commands to avoid confusion.

### Trade-offs

- Two command systems can diverge. Mitigated by keeping both minimal in Phase 1.
- Future consideration: migrate to `just` or `invoke` for a single cross-platform solution.

---

## ADR-006: Abstract Base Service with Lifecycle

**Date**: 2024-01-15
**Status**: Accepted

### Context

The application will integrate multiple external services (LLM providers, search APIs, databases). These services need consistent initialization, shutdown, and health checking.

### Decision

Define a `BaseService` ABC with `initialize()`, `shutdown()`, and `health_check()` lifecycle methods.

### Rationale

- **Consistent lifecycle**: All services follow the same startup/teardown pattern.
- **Constructor injection**: Settings are injected via `__init__`, not read from globals.
- **Health monitoring**: Standardized health checks enable a unified status dashboard.
- **Graceful shutdown**: Explicit `shutdown()` prevents resource leaks.

---

*To add a new decision, copy the template below and append to this file.*

```markdown
## ADR-NNN: [Title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated | Superseded

### Context
[What is the issue or need?]

### Decision
[What was decided?]

### Rationale
[Why was this decided?]

### Trade-offs
[What are the downsides?]
```
