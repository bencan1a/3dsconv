# Development Container Configuration

This directory contains the configuration for the development container used by:
- GitHub Codespaces
- VS Code Remote - Containers
- GitHub Copilot Workspace

## What This Does

The `devcontainer.json` file configures a containerized development environment that:

1. **Uses Python 3.12** - Matches the project's supported Python version
2. **Installs all dev dependencies** - Automatically runs `pip install -e '.[dev]'` which installs:
   - pytest (testing framework)
   - pytest-cov (code coverage)
   - black (code formatter)
   - ruff (linter)
   - mypy (type checker)
   - build and twine (packaging tools)

3. **Configures VS Code** - Sets up recommended extensions and settings:
   - Python language support with Pylance
   - Black formatter (auto-format on save)
   - Ruff linter (auto-fix on save)
   - Proper Python settings (4 spaces, etc.)

## Using This Configuration

### With GitHub Codespaces

1. Click the "Code" button on GitHub
2. Select "Codespaces" tab
3. Click "Create codespace on main"
4. Wait for the container to build and start

### With VS Code

1. Install the "Remote - Containers" extension
2. Open the repository in VS Code
3. Press F1 and select "Remote-Containers: Reopen in Container"
4. Wait for the container to build

### With GitHub Copilot Workspace

When you use GitHub Copilot Workspace, it automatically uses this configuration to set up the development environment with all necessary tools.

## Maintaining This Configuration

When updating development dependencies:
1. Update `pyproject.toml` with new dependencies
2. The devcontainer will automatically pick up changes via the `postCreateCommand`

For major changes to the development environment:
1. Test locally with VS Code Remote - Containers
2. Update this README if needed
3. Commit both `devcontainer.json` and README changes
