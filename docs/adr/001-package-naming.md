# 1. Package Naming: dsconv vs 3dsconv

**Date:** 2025-11-07  
**Status:** Accepted  
**Deciders:** Project maintainers  
**Tags:** packaging, python, naming

## Context

The project was originally named `3dsconv` to reflect its purpose: converting Nintendo 3DS files. However, Python has strict naming requirements for module and package names:

- **Python requirement:** Module names must be valid Python identifiers
- **Python identifiers:** Cannot start with a digit
- **User expectation:** Users expect to install and reference the tool as `3dsconv`
- **Distribution naming:** PyPI allows names with digits

This creates a conflict between:
1. What users expect (`3dsconv`)
2. What Python allows for imports (`cannot start with digit`)
3. Package manager compatibility (PyPI allows it)

## Decision

We will use **two different names** for different contexts:

1. **Package directory name:** `dsconv`
   - Used for Python imports: `import dsconv`
   - Used for module execution: `python -m dsconv`
   - Valid Python identifier

2. **Distribution name:** `3dsconv`
   - Used for pip installation: `pip install 3dsconv`
   - Used for command-line tool: `3dsconv [options]`
   - Maintains user expectations and branding

**Implementation in pyproject.toml:**
```toml
[project]
name = "3dsconv"  # Distribution name (PyPI package name)

[project.scripts]
3dsconv = "dsconv.__main__:main"  # CLI entry point

[tool.setuptools]
packages = ["dsconv"]  # Actual package directory
```

## Consequences

### Positive Consequences

- ✅ **Complies with Python naming rules** - No syntax errors or import issues
- ✅ **Maintains user-facing branding** - Tool is still called `3dsconv`
- ✅ **Works with PyPI** - Can publish with expected name
- ✅ **Clear separation** - Distribution name vs. module name
- ✅ **Standard practice** - Other Python projects use similar approach

### Negative Consequences

- ⚠️ **Potential confusion** - Directory name doesn't match distribution name
- ⚠️ **Import discrepancy** - `import dsconv` vs. `pip install 3dsconv`
- ⚠️ **Documentation burden** - Need to explain the naming in multiple places
- ⚠️ **Repository mismatch** - Repo might still reference old name

### Neutral Consequences

- ℹ️ **Multiple execution methods** - All work correctly:
  - `3dsconv [options]` (installed command)
  - `python -m dsconv [options]` (module execution)
  - `python dsconv/3dsconv.py [options]` (direct script - backward compatible)

## Alternatives Considered

### Alternative 1: Rename Everything to "dsconv"

**Description:** Change the project name entirely to `dsconv` everywhere

**Pros:**
- Consistent naming across all contexts
- No confusion between names
- Simpler to explain

**Cons:**
- Loses established branding (`3dsconv` is known in community)
- Breaks existing user scripts and documentation
- Less descriptive (doesn't mention "3ds" directly)
- Existing PyPI package might exist under different name

**Why rejected:** Breaking change with significant user impact, loses brand recognition

### Alternative 2: Use Underscore Prefix "_3dsconv"

**Description:** Prefix with underscore to make valid identifier: `_3dsconv`

**Pros:**
- Includes "3ds" in module name
- Technically valid Python identifier
- More obvious connection to purpose

**Cons:**
- Underscore prefix conventionally means "private" in Python
- Awkward to type: `import _3dsconv`
- Violates Python conventions
- Still confusing for users

**Why rejected:** Violates Python conventions, awkward to use

### Alternative 3: Use "threedsconv"

**Description:** Spell out "three" instead of using digit

**Pros:**
- Valid Python identifier
- Could use same name everywhere
- Clear pronunciation

**Cons:**
- Harder to type
- Less clear connection to "3DS"
- Would need to migrate from `3dsconv` brand
- Longer name

**Why rejected:** Less clear branding, more typing, migration burden

## Implementation Notes

When working with this codebase:

1. **Imports:** Always use `import dsconv` or `from dsconv import X`
2. **CLI references:** Use `3dsconv` in documentation
3. **Package references:** `pip install 3dsconv` but imports are `dsconv`
4. **File paths:** The package lives in `dsconv/` directory
5. **Documentation:** Always explain both names where relevant

## References

- [PEP 8 - Package and Module Names](https://peps.python.org/pep-0008/#package-and-module-names)
- [Python Language Reference - Identifiers](https://docs.python.org/3/reference/lexical_analysis.html#identifiers)
- [PyPI Package Naming Guidelines](https://packaging.python.org/guides/distributing-packages-using-setuptools/#choosing-a-versioning-scheme)

## Related Decisions

- [ADR-002: Modern Python Packaging](002-modern-packaging.md) - Uses this naming convention in pyproject.toml

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-11-07 | AI Agent | Initial documentation of existing decision |
