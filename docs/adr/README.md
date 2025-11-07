# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) for the 3dsconv project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences. ADRs help:

- **Document decisions** for future reference
- **Explain rationale** behind technical choices
- **Track evolution** of the project's architecture
- **Onboard new contributors** faster
- **Support AI assistants** with historical context

## ADR Format

Each ADR follows this structure:

```markdown
# [Number]. [Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed | Accepted | Deprecated | Superseded by ADR-XXX]
**Deciders:** [Names or roles]
**Tags:** [relevant, tags]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

### Positive Consequences
- ...

### Negative Consequences
- ...

## Alternatives Considered

What other options were considered and why were they rejected?

## Related Decisions

Links to related ADRs or issues.
```

## Existing ADRs

### ADR-001: Package Naming (dsconv vs 3dsconv)
**File:** [001-package-naming.md](001-package-naming.md)  
**Status:** Accepted  
**Summary:** Use `dsconv` as package name because Python modules cannot start with digits

### ADR-002: Modern Python Packaging
**File:** [002-modern-packaging.md](002-modern-packaging.md)  
**Status:** Accepted  
**Summary:** Migrate to pyproject.toml and modern Python packaging standards

### ADR-003: Test Automation Strategy
**File:** [003-test-automation-strategy.md](003-test-automation-strategy.md)  
**Status:** Accepted  
**Summary:** Three-phase testing approach (unit, integration, e2e)

## Creating a New ADR

1. **Copy the template:**
   ```bash
   cp docs/adr/000-template.md docs/adr/XXX-title.md
   ```

2. **Use the next available number:** Check existing ADRs and increment

3. **Fill in all sections:** Provide complete context and rationale

4. **Update this README:** Add entry to the list above

5. **Submit for review:** Create PR with ADR included

## ADR Lifecycle

### Status Values

- **Proposed:** Under discussion, not yet decided
- **Accepted:** Decision has been made and implemented
- **Deprecated:** No longer relevant or recommended
- **Superseded:** Replaced by a newer ADR

### When to Create an ADR

Create an ADR when:
- Making significant architectural changes
- Choosing between multiple technical approaches
- Establishing new patterns or conventions
- Changing existing architectural decisions
- Adding or removing major dependencies
- Modifying core data structures or algorithms

### When NOT to Create an ADR

Don't create ADRs for:
- Bug fixes (unless they involve architectural changes)
- Minor refactoring
- Documentation updates
- Routine maintenance
- Implementation details that don't affect architecture

## For AI Assistants

When working on this project, AI assistants should:

1. **Read relevant ADRs** before proposing architectural changes
2. **Suggest new ADRs** for significant decisions
3. **Reference ADRs** in code comments and PRs
4. **Update ADRs** if decisions change
5. **Check status** - don't follow deprecated patterns

## Resources

- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [Architecture Decision Records (ThoughtWorks)](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)
