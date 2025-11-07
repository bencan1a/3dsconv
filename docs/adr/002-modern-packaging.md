# 2. Modern Python Packaging with pyproject.toml

**Date:** 2025-11-07  
**Status:** Accepted  
**Deciders:** Project maintainers  
**Tags:** packaging, build-system, modernization

## Context

The project originally used the traditional `setup.py` approach for Python packaging. However, the Python packaging ecosystem has evolved:

- **PEP 517/518:** Define modern build system requirements
- **PEP 621:** Standardize project metadata in `pyproject.toml`
- **Industry trend:** Major projects migrating to `pyproject.toml`
- **Tool support:** Better integration with modern development tools
- **Dependency management:** More reliable and reproducible

The old approach had several issues:
- Scattered configuration across multiple files
- Difficult to parse programmatically
- No standardized format
- Limited tool integration

## Decision

**Migrate to modern Python packaging using `pyproject.toml`:**

1. **Primary configuration:** Use `pyproject.toml` for all project metadata and build configuration
2. **Build system:** Use setuptools as build backend (most compatible)
3. **Tool configuration:** Consolidate black, ruff, mypy, pytest configs in `pyproject.toml`
4. **Backward compatibility:** Keep `setup.py` minimal for legacy compatibility
5. **Requirements files:** Maintain for explicit dependency installation

**Project structure:**
```
pyproject.toml          # Primary configuration (new)
setup.py                # Legacy compatibility (minimal)
requirements.txt        # Production dependencies
requirements-dev.txt    # Development dependencies
.python-version         # Python version for pyenv
```

## Consequences

### Positive Consequences

- ✅ **Standardized format** - PEP 621 compliant metadata
- ✅ **Better tool support** - Modern tools prefer `pyproject.toml`
- ✅ **Centralized config** - All tool configs in one file
- ✅ **Declarative dependencies** - Clear, reproducible dependency specification
- ✅ **Optional dependencies** - Support for dev dependencies with `[dev]` extra
- ✅ **Future-proof** - Following Python community direction
- ✅ **Easier CI/CD** - Better integration with GitHub Actions and other CI tools
- ✅ **Editable installs** - `pip install -e ".[dev]"` for development

### Negative Consequences

- ⚠️ **Older tool compatibility** - Very old pip versions may not support it
- ⚠️ **Migration effort** - Required moving configuration from multiple files
- ⚠️ **Documentation updates** - Need to update installation instructions

### Neutral Consequences

- ℹ️ **Multiple installation methods** - Both modern and legacy work:
  - Modern: `pip install -e ".[dev]"`
  - Legacy: `python setup.py install`
  - Requirements: `pip install -r requirements-dev.txt`

## Alternatives Considered

### Alternative 1: Poetry

**Description:** Use Poetry for dependency and package management

**Pros:**
- Modern dependency resolver
- Lock file support
- Integrated virtual environment management
- Better dependency conflict resolution

**Cons:**
- Additional tool dependency
- Non-standard for simple projects
- Learning curve for contributors
- Requires Poetry installation for development

**Why rejected:** Adds unnecessary complexity for a single-file CLI tool. setuptools is sufficient and more widely understood.

### Alternative 2: Keep setup.py Only

**Description:** Continue using only `setup.py` for all configuration

**Pros:**
- No migration needed
- Familiar to existing contributors
- Works everywhere

**Cons:**
- Against Python community direction (PEPs 517/518/621)
- Poor tool integration
- Hard to parse programmatically
- Scattered configuration

**Why rejected:** Not future-proof, doesn't support modern tooling well

### Alternative 3: Flit

**Description:** Use Flit for simpler packaging

**Pros:**
- Simpler than setuptools for pure Python
- Built-in support for pyproject.toml
- Less boilerplate

**Cons:**
- Less widely used
- May not handle edge cases as well
- Additional tool to learn

**Why rejected:** setuptools is more standard and better supported

## Implementation Notes

### Configuration Sections in pyproject.toml

```toml
[build-system]  # PEP 517 build system
[project]       # PEP 621 project metadata
[project.scripts]  # CLI entry points
[project.optional-dependencies]  # Dev dependencies
[tool.black]    # Black formatter config
[tool.ruff]     # Ruff linter config
[tool.mypy]     # Mypy type checker config
[tool.pytest.ini_options]  # Pytest config
```

### Dependency Installation

**For users:**
```bash
pip install 3dsconv
```

**For developers:**
```bash
pip install -e ".[dev]"  # Editable install with dev tools
```

**Alternative (requirements files):**
```bash
pip install -r requirements-dev.txt
```

### Python Version Requirement

- **Minimum:** Python 3.10
- **Tested:** Python 3.10, 3.11, 3.12, 3.13
- **Specified in:** `pyproject.toml` and `.python-version`

## References

- [PEP 517 - Build System Interface](https://peps.python.org/pep-0517/)
- [PEP 518 - Build System Requirements](https://peps.python.org/pep-0518/)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [setuptools Documentation](https://setuptools.pypa.io/)

## Related Decisions

- [ADR-001: Package Naming](001-package-naming.md) - Naming convention used in pyproject.toml
- [ADR-003: Test Automation Strategy](003-test-automation-strategy.md) - Pytest configuration in pyproject.toml

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-11-07 | AI Agent | Initial documentation of migration |
