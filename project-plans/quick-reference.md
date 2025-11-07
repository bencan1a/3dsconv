# Refactoring Quick Reference

## Task Priority Matrix

### High Priority (Start Here)
These tasks provide maximum value with minimal dependencies:

1. **Task 1.1-1.4**: Domain Models (Phase 1)
   - Pure data structures
   - No dependencies
   - Foundation for everything else
   - Estimated: 4-6 hours total

2. **Task 4.1-4.2**: Validation Services (Phase 4)
   - Pure logic
   - Easy to test
   - Quick wins
   - Estimated: 2-3 hours total

### Medium Priority
These tasks build on the foundation:

3. **Task 2.1-2.3**: Crypto Infrastructure (Phase 2)
   - Depends on Phase 1
   - Critical for functionality
   - Estimated: 6-8 hours total

4. **Task 3.1-3.2**: Basic I/O (Phase 3)
   - Depends on Phase 1
   - Needed for integration
   - Estimated: 4-5 hours total

### Lower Priority
These tasks integrate everything:

5. **Task 6.1-6.4**: Application Services (Phase 6)
   - Depends on all previous phases
   - Main orchestration
   - Estimated: 8-10 hours total

---

## Command Cheat Sheet

### Development Workflow

```bash
# 1. Install dependencies
cd /home/runner/work/3dsconv/3dsconv
pip install -e .[dev]

# 2. Create new module
mkdir -p dsconv/models
touch dsconv/models/__init__.py
touch dsconv/models/ncch.py

# 3. Create test file
mkdir -p tests/unit/models
touch tests/unit/models/__init__.py
touch tests/unit/models/test_ncch.py

# 4. Run tests (watch mode)
pytest tests/unit/models/test_ncch.py -v --tb=short

# 5. Check coverage
pytest tests/unit/models/test_ncch.py \
    --cov=dsconv.models.ncch \
    --cov-report=term-missing \
    --cov-report=html

# 6. View HTML coverage report
# Open htmlcov/index.html in browser

# 7. Format code
black dsconv/models/ncch.py

# 8. Lint code
ruff check dsconv/models/ncch.py

# 9. Auto-fix linting issues
ruff check --fix dsconv/models/ncch.py

# 10. Run all tests
pytest tests/ -v

# 11. Run tests with coverage for whole package
pytest tests/ --cov=dsconv --cov-report=term-missing

# 12. Type check (if mypy configured)
mypy dsconv/models/ncch.py
```

### Git Workflow

```bash
# Check status
git status

# Add files
git add dsconv/models/ncch.py tests/unit/models/test_ncch.py

# Commit
git commit -m "Add NCCH header model (Task 1.1)"

# Push (handled by report_progress tool)
```

---

## Code Templates

### Minimal Dataclass

```python
from dataclasses import dataclass

@dataclass
class ClassName:
    """Description."""
    field: type
    
    def __post_init__(self):
        """Validate."""
        pass
    
    @property
    def computed(self) -> type:
        """Compute value."""
        return self.field
```

### Minimal Service

```python
class ServiceName:
    """Description."""
    
    def __init__(self, dependency: DependencyType):
        """Initialize."""
        self.dependency = dependency
    
    def method(self, param: type) -> type:
        """Do something."""
        return result
```

### Minimal Test

```python
import pytest

class TestClassName:
    """Tests for ClassName."""
    
    def test_method_success(self):
        """Test method succeeds."""
        # Arrange
        obj = ClassName(field=value)
        
        # Act
        result = obj.method()
        
        # Assert
        assert result == expected
```

### Minimal Interface

```python
from abc import ABC, abstractmethod

class IInterfaceName(ABC):
    """Interface for X."""
    
    @abstractmethod
    def method(self, param: type) -> type:
        """Do something."""
        pass
```

---

## Testing Patterns Quick Ref

### Parametrize Test

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

### Test Exception

```python
def test_raises_error():
    with pytest.raises(ValueError, match="error message"):
        function_that_raises()
```

### Fixture

```python
@pytest.fixture
def sample_object():
    """Create sample object."""
    return Object(field=value)

def test_using_fixture(sample_object):
    assert sample_object.field == value
```

### Mock

```python
from unittest.mock import Mock

def test_with_mock():
    mock_dep = Mock()
    mock_dep.method.return_value = 42
    
    service = Service(mock_dep)
    result = service.do_something()
    
    mock_dep.method.assert_called_once()
    assert result == 42
```

---

## File Organization Reference

```
dsconv/
├── models/          # Pure data structures (Phase 1)
├── crypto/          # Encryption services (Phase 2)
├── io/              # Readers/Writers (Phase 3-5)
├── validation/      # Validators (Phase 4)
├── services/        # Orchestration (Phase 6)
└── cli/             # CLI mapping (Phase 7)

tests/
├── unit/            # Unit tests (one per module)
├── integration/     # Multi-component tests
└── e2e/             # Full workflow tests
```

---

## Common Issues and Fixes

### Import Error

```python
# Problem
from dsconv.models import NCCHHeader  # ModuleNotFoundError

# Solution: Check __init__.py exports
# In dsconv/models/__init__.py:
from .ncch import NCCHHeader
__all__ = ['NCCHHeader']
```

### Test Not Found

```bash
# Problem
pytest tests/unit/models/test_ncch.py  # No tests found

# Solution: Check naming
# - File must start with test_
# - Class must start with Test
# - Method must start with test_
```

### Import Order

```python
# Correct order:
import stdlib  # Standard library
import thirdparty  # Third party
import dsconv  # Local
```

### Type Hint Import

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dsconv.crypto import Service  # Only for type checking

def method(self, service: 'Service') -> None:  # String quote
    ...
```

---

## Phase Completion Checklist

### Phase 1: Models
- [ ] Task 1.1: NCCH model ✓
- [ ] Task 1.2: NCSD model ✓
- [ ] Task 1.3: CIA model ✓
- [ ] Task 1.4: Encryption model ✓
- [ ] All models tested 100%
- [ ] `dsconv/models/__init__.py` exports all
- [ ] No dependencies on I/O or services

### Phase 2: Crypto
- [ ] Task 2.1: AES adapter ✓
- [ ] Task 2.2: Key derivation ✓
- [ ] Task 2.3: Key provider ✓
- [ ] Task 2.4: Decryption service ✓
- [ ] All crypto tested with mocks
- [ ] No global state
- [ ] Depends only on Phase 1

### Phase 3-5: I/O
- [ ] Task 3.1: Binary reader ✓
- [ ] Task 3.2: NCSD reader ✓
- [ ] Task 3.3: NCCH reader ✓
- [ ] Task 3.4: ExeFS reader ✓
- [ ] Task 4.1: Hash validator ✓
- [ ] Task 4.2: Format validator ✓
- [ ] Task 5.1: Binary writer ✓
- [ ] Task 5.2: CIA builder ✓
- [ ] Task 5.3: CIA writer ✓
- [ ] All I/O tested with BytesIO
- [ ] Readers/writers decoupled

### Phase 6: Services
- [ ] Task 6.1: Conversion config ✓
- [ ] Task 6.2: Progress reporter ✓
- [ ] Task 6.3: Conversion service ✓
- [ ] Task 6.4: Service factory ✓
- [ ] Integration tests pass
- [ ] No global state
- [ ] Dependencies injected

### Phase 7: CLI
- [ ] Task 7.1: Config mapper ✓
- [ ] Task 7.2: Main refactor ✓
- [ ] CLI identical to original
- [ ] All options work
- [ ] Error handling preserved

### Phase 8: Cleanup
- [ ] Task 8.1: Remove globals ✓
- [ ] Task 8.2: Certchain provider ✓
- [ ] Task 8.3: Legacy cleanup ✓
- [ ] No module-level execution
- [ ] Backward compatible
- [ ] Deprecation warnings

### Phase 9: Testing
- [ ] Task 9.1: Integration tests ✓
- [ ] Task 9.2: Architecture docs ✓
- [ ] Task 9.3: Migration guide ✓
- [ ] 80%+ coverage achieved
- [ ] All documentation complete

---

## Performance Benchmarks

Track these metrics before/after refactoring:

```bash
# Conversion time for 1GB file
time 3dsconv game.cci

# Memory usage
/usr/bin/time -v 3dsconv game.cci

# Test suite speed
pytest tests/ --durations=10
```

**Targets:**
- Conversion time: Within 10% of original
- Memory usage: Within 20% of original
- Test suite: < 5 seconds for unit tests

---

## Need Help?

1. **Stuck on imports?** → Check `implementation-guide.md` Section "Common Pitfalls"
2. **Don't know how to test?** → Check `implementation-guide.md` Section "Testing Patterns"
3. **Confused about architecture?** → Read `refactoring-plan.md` Section "Target Architecture"
4. **Need code examples?** → Check `implementation-guide.md` Section "Code Patterns"

---

## Success Indicators

You're on track if:
- ✅ Each task takes 1-8 hours
- ✅ Tests pass before moving to next task
- ✅ Coverage stays at 100% for new code
- ✅ No global state in new code
- ✅ All dependencies injected
- ✅ Existing tests still pass

Red flags:
- ❌ Task taking > 12 hours
- ❌ Coverage dropping below 80%
- ❌ Global state appearing
- ❌ Existing tests breaking
- ❌ Tight coupling appearing

---

## Quick Start for New Task

1. Read task description in `refactoring-plan.md`
2. Create file: `dsconv/<area>/<module>.py`
3. Create test: `tests/unit/<area>/test_<module>.py`
4. Write code using patterns from `implementation-guide.md`
5. Run tests: `pytest tests/unit/<area>/test_<module>.py -v`
6. Check coverage: `pytest ... --cov=dsconv.<area>.<module>`
7. Format: `black dsconv/<area>/<module>.py`
8. Lint: `ruff check dsconv/<area>/<module>.py`
9. Verify all tests: `pytest tests/ -v`
10. Mark task complete ✓

---

**Last Updated:** 2025-11-07  
**Version:** 1.0
