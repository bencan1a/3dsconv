# Bundling ctrtool with 3dsconv

This guide explains how to bundle `ctrtool.exe` with your 3dsconv distribution.

## Quick Start

1. **Download ctrtool**
   - Get it from [Project_CTR releases](https://github.com/3DSGuy/Project_CTR/releases)
   - Download the Windows version (`ctrtool.exe`)

2. **Place it in the package**
   ```
   dsconv/bin/ctrtool.exe
   ```

3. **Rebuild the wheel**
   ```bash
   python -m build
   ```

4. **Distribute the wheel**
   ```
   dist/3dsconv-4.21-py3-none-any.whl
   ```

## How It Works

### Search Order

When you use `--to-cxi`, 3dsconv searches for ctrtool in this order:

1. **Custom path** (if `--ctrtool-path` is specified)
2. **Environment variable** (`CTRTOOL_PATH`)
3. **Bundled executable** (in `dsconv/bin/`) ⭐ NEW!
4. **System PATH** (standard installation)

### Example Usage

After installing the wheel with bundled ctrtool:

```powershell
# Automatic - uses bundled ctrtool.exe
3dsconv --to-cxi game.cci

# Override with custom path if needed
3dsconv --to-cxi --ctrtool-path C:\custom\ctrtool.exe game.cci
```

## Directory Structure

```
dsconv/
├── bin/                      # Bundled executables
│   ├── README.md            # Instructions
│   ├── .gitignore           # Optional - ignore binaries
│   └── ctrtool.exe          # ⭐ Place your ctrtool.exe here
├── cli/
├── crypto/
└── ...
```

## Git Considerations

### Option 1: Commit ctrtool.exe (Recommended for Distribution)

Remove the ignore rule in `dsconv/bin/.gitignore`:

```bash
# Delete or comment out this line in dsconv/bin/.gitignore:
# ctrtool.exe
```

**Pros:**
- ✅ Fully self-contained distribution
- ✅ Users don't need to download ctrtool separately
- ✅ Version control ensures everyone has the same version

**Cons:**
- ❌ Binary file in git (~1-2 MB)
- ❌ Binary changes aren't human-readable in diffs

### Option 2: Don't Commit (Cleaner Repo)

Keep the ignore rule in `dsconv/bin/.gitignore`:

```gitignore
ctrtool.exe
```

**Pros:**
- ✅ Clean git repository
- ✅ No binary bloat

**Cons:**
- ❌ Users must manually add ctrtool.exe before building
- ❌ CI/CD builds won't include ctrtool

## Building Without ctrtool

The wheel will build successfully even without `ctrtool.exe` in the directory:

- The `dsconv/bin/` directory will be included (with README.md)
- Users can add ctrtool.exe later by installing to a custom location
- The code gracefully falls back to PATH search if bundled version not found

## Platform Notes

### Windows (Primary Target)
- Bundle: `ctrtool.exe` (binary)
- Automatically detected and used

### Linux/macOS
- Bundling not recommended (different binaries per platform)
- Users should install ctrtool via package manager
- Set `CTRTOOL_PATH` or use `--ctrtool-path` if needed

## Testing the Bundled Version

After building the wheel, test it:

```powershell
# Create a test virtual environment
python -m venv test_env
test_env\Scripts\activate

# Install your wheel
pip install dist/3dsconv-4.21-py3-none-any.whl

# Verify bundled ctrtool is found
python -c "from dsconv.utils import find_ctrtool; print(find_ctrtool())"
# Should output: C:\...\site-packages\dsconv\bin\ctrtool.exe
```

## Updating ctrtool

To update the bundled ctrtool version:

1. Download new version
2. Replace `dsconv/bin/ctrtool.exe`
3. Bump version in `pyproject.toml` (optional but recommended)
4. Rebuild: `python -m build`
5. Redistribute the new wheel

## Distribution Checklist

Before distributing your wheel:

- [ ] `ctrtool.exe` is in `dsconv/bin/`
- [ ] Wheel rebuilds successfully: `python -m build`
- [ ] Wheel contains `dsconv/bin/ctrtool.exe`:
  ```bash
  python -m zipfile -l dist/*.whl | grep ctrtool
  ```
- [ ] Test in clean environment (see "Testing" above)
- [ ] Optional: Commit `ctrtool.exe` to git for team/CI use

## Troubleshooting

### "ctrtool not found" error

Even with bundled ctrtool, you might see this if:
- Permissions issue (Windows blocked the file)
- Corrupt download
- Platform mismatch (Linux binary on Windows)

**Fix:** Right-click `ctrtool.exe` → Properties → Unblock

### Bundled ctrtool not detected

Check the installation:

```powershell
# Find where it's installed
python -c "import dsconv; print(dsconv.__file__)"
# Navigate to that directory and check bin/ subdirectory

# Check if find_ctrtool sees it
python -c "from dsconv.utils import find_ctrtool; print(find_ctrtool())"
```

### Want to use system PATH instead

Even with bundled ctrtool, you can override:

```bash
# Use system PATH version
set CTRTOOL_PATH=C:\Program Files\ctrtool\ctrtool.exe
3dsconv --to-cxi game.cci

# Or use command-line flag
3dsconv --to-cxi --ctrtool-path C:\path\to\other\ctrtool.exe game.cci
```

---

**Last Updated:** 2025-11-28
