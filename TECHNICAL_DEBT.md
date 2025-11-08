# Technical Debt Items - Task 8.1

This document tracks technical debt introduced during Task 8.1 implementation. These items should be addressed in future refactoring tasks.

## Issue 1: Hardcoded TMD Offsets Should Be Calculated

**Priority:** Medium  
**Category:** Code Quality, Maintainability  
**Introduced in:** Task 8.1 (commit c2035fe)

### Description
The `_write_cia()` method in `dsconv/services/conversion_service.py` uses hardcoded offsets for TMD structure updates:
- `0x2FA4` - Info records hash offset
- `0x2FC7` - Chunk records hash offset  
- `0x38D4` - Game CXI content hash offset
- `0x2F9F` - Content count offset
- `0x2C1C` - Title ID in ticket offset
- `0x2F4C` - Title ID in TMD offset
- `0x2F5A` - Save size offset

### Current Implementation
```python
# Update content count in TMD
self.cia_writer.writer.file.seek(0x2F9F)
self.cia_writer.writer.file.write(bytes([content_count]))

# Update title ID in ticket and TMD
self.cia_writer.writer.file.seek(0x2C1C)
self.cia_writer.writer.file.write(title_id)
```

### Recommended Solution
Calculate offsets dynamically based on TMD structure:
1. Create TMD structure model with field definitions
2. Calculate offsets from header size + cert size + ticket size + TMD base
3. Define constants for relative offsets within TMD structure
4. Use structure-aware methods for updates

### Benefits
- More maintainable code
- Self-documenting structure
- Easier to support different TMD variants
- Reduces risk of offset calculation errors

### Related Files
- `dsconv/services/conversion_service.py` (lines 465-479, 511-537)
- `dsconv/models/cia.py` (potential new TMD model)

---

## Issue 2: Direct File I/O Bypasses CIAWriter Abstraction

**Priority:** Medium  
**Category:** Architecture, Code Quality  
**Introduced in:** Task 8.1 (commit c2035fe)

### Description
The `_write_cia()` method writes directly to the file handle instead of using CIAWriter's higher-level methods. This bypasses the abstraction layer and alignment handling that CIAWriter provides.

### Current Implementation
```python
# Direct file writes
self.cia_writer.writer.file.seek(0)
self.cia_writer.writer.file.write(header)
self.cia_writer.writer.file.write(certchain)
```

### Problems
- Bypasses CIAWriter's alignment methods (`_align_offset()`)
- Couples ConversionService to low-level file operations
- Harder to test and mock
- Violates separation of concerns

### Recommended Solution
1. Enhance CIAWriter with high-level methods:
   - `write_cia_structure(header, certchain, ticket_tmd, chunk_records)`
   - `update_tmd_field(field_name, value)`
   - `write_content_aligned(content_data)`
2. Keep alignment logic in CIAWriter
3. Use dependency injection for testability

### Benefits
- Better abstraction and encapsulation
- Reusable CIAWriter for other CIA operations
- Easier to test with mocks
- Centralized alignment handling

### Related Files
- `dsconv/services/conversion_service.py` (lines 446-555)
- `dsconv/io/cia_writer.py` (needs new methods)

---

## Issue 3: Certificate Chain and Ticket/TMD Templates Should Be Refactored

**Priority:** High  
**Category:** Architecture, Security  
**Related Tasks:** Task 8.2 (Certificate Chain Provider)

### Description
Binary templates are currently stored as base64-encoded strings in `dsconv/data/__init__.py`. This was a temporary solution to avoid module-level execution issues in `legacy.py`.

### Current Implementation
```python
# dsconv/data/__init__.py
certchain_retail = b"""eJytkvk/E44fx9GsT58Z..."""
ticket_tmd = b"""eJxjYGRgYRgFZIOg/PwSXW..."""
```

### Problems
1. **Certificate Chain Issues:**
   - Hardcoded retail certificate chain
   - Dev certificate chain loading not implemented
   - No validation or verification
   - Security concerns with embedded binary data

2. **Ticket/TMD Template Issues:**
   - Opaque binary templates instead of programmatic builders
   - Hard to understand structure
   - Difficult to modify for different scenarios
   - No support for multiple content types

### Recommended Solution

#### Part A: Certificate Chain Provider (Task 8.2)
Create `dsconv/crypto/certchain_provider.py`:
```python
class CertChainProvider:
    """Provides certificate chains for CIA generation."""
    
    @staticmethod
    def load_retail() -> bytes:
        """Load retail certificate chain."""
        
    @staticmethod
    def load_dev(path: str) -> bytes:
        """Load dev certificate chain from file."""
        
    def validate(self, certchain: bytes) -> bool:
        """Validate certificate chain structure."""
```

#### Part B: Ticket and TMD Builders
Create `dsconv/models/ticket.py` and `dsconv/models/tmd.py`:
```python
class TicketBuilder:
    """Builds CIA ticket structure programmatically."""
    
    def with_title_id(self, title_id: bytes) -> 'TicketBuilder':
        """Set title ID in ticket."""
        
    def build(self) -> bytes:
        """Build ticket binary structure."""

class TMDBuilder:
    """Builds TMD (Title Metadata) structure."""
    
    def with_title_id(self, title_id: bytes) -> 'TMDBuilder':
        """Set title ID."""
        
    def with_content(self, content_id: int, size: int, index: int) -> 'TMDBuilder':
        """Add content record."""
        
    def build(self) -> bytes:
        """Build TMD binary structure."""
```

### Benefits
- More maintainable and testable
- Self-documenting structure
- Support for different scenarios (retail/dev, multiple contents)
- Better security practices
- Alignment with refactoring plan

### Migration Path
1. Implement CertChainProvider (Task 8.2)
2. Create TicketBuilder and TMDBuilder
3. Update ConversionService to use builders
4. Remove binary templates from `dsconv/data/__init__.py`
5. Add tests for builders

### Related Files
- `dsconv/data/__init__.py` (current location, to be removed)
- `dsconv/crypto/certchain_provider.py` (new, Task 8.2)
- `dsconv/models/ticket.py` (new)
- `dsconv/models/tmd.py` (new)
- `dsconv/services/conversion_service.py` (to be updated)

---

## Issue 4: Missing Unit Tests for CIA Writing

**Priority:** High  
**Category:** Testing  
**Introduced in:** Task 8.1

### Description
The `_write_cia()` method lacks unit tests. Currently only validated through integration/E2E tests via the validation script.

### Current Test Coverage
- ✅ Integration test: `scripts/validate_refactor.py` (byte-comparison)
- ❌ Unit tests for individual components
- ❌ Unit tests for edge cases
- ❌ Unit tests for error handling

### Recommended Tests
Create `tests/unit/services/test_conversion_service_write_cia.py`:

1. **Structure Tests:**
   - Test CIA header generation with correct sizes
   - Test alignment padding calculations (256-byte boundaries)
   - Test dependency list extraction from extheader

2. **Hash Tests:**
   - Test game CXI hash calculation
   - Test chunk records hash calculation
   - Test info records hash calculation

3. **Edge Cases:**
   - Empty icon data
   - Zero-size content
   - Multiple content types (when supported)
   - Very large files (streaming behavior)

4. **Error Handling:**
   - Invalid extheader data
   - I/O errors during write
   - Insufficient disk space

### Benefits
- Faster feedback during development
- Better code coverage metrics
- Easier regression testing
- Documents expected behavior

### Related Files
- `tests/unit/services/test_conversion_service_write_cia.py` (new)
- `dsconv/services/conversion_service.py`

---

## Issue 5: Meta Region Structure Should Use Builder Pattern

**Priority:** Low  
**Category:** Code Quality  
**Introduced in:** Task 8.1

### Description
The Meta region is constructed using raw byte concatenation, making it hard to understand and maintain.

### Current Implementation
```python
dependency_list = extheader[0x40:0x1C0]
self.cia_writer.writer.file.write(
    dependency_list + bytes(0x180) + struct.pack("<I", 0x2) + bytes(0xFC) + icon
)
```

### Recommended Solution
Create `dsconv/models/meta.py`:
```python
class MetaBuilder:
    """Builds CIA Meta region structure."""
    
    def __init__(self):
        self.dependency_list = bytes(0x180)
        self.core_version = 2
        self.icon = bytes(0x36C0)
    
    def with_dependencies(self, dependencies: bytes) -> 'MetaBuilder':
        """Set dependency list (0x180 bytes)."""
        if len(dependencies) != 0x180:
            raise ValueError("Dependency list must be 0x180 bytes")
        self.dependency_list = dependencies
        return self
    
    def with_icon(self, icon: bytes) -> 'MetaBuilder':
        """Set SMDH icon data."""
        if len(icon) != 0x36C0:
            raise ValueError("Icon must be 0x36C0 bytes (SMDH format)")
        self.icon = icon
        return self
    
    def build(self) -> bytes:
        """Build Meta region (0x3AC0 bytes total)."""
        return (
            self.dependency_list +  # 0x180
            bytes(0x180) +          # Padding
            struct.pack("<I", self.core_version) +  # 4 bytes
            bytes(0xFC) +           # Padding
            self.icon               # 0x36C0
        )
```

### Benefits
- Self-documenting structure
- Type safety
- Easier to test
- Clearer field purposes

### Related Files
- `dsconv/models/meta.py` (new)
- `dsconv/services/conversion_service.py` (to be updated)

---

## Summary

| Issue | Priority | Category | Estimated Effort | Blocks |
|-------|----------|----------|------------------|--------|
| #1: Hardcoded TMD Offsets | Medium | Maintainability | 4-6 hours | - |
| #2: Direct File I/O | Medium | Architecture | 6-8 hours | - |
| #3: Certificate/Template Refactor | High | Architecture | 12-16 hours | Task 8.2 |
| #4: Missing Unit Tests | High | Testing | 8-10 hours | - |
| #5: Meta Builder Pattern | Low | Code Quality | 2-3 hours | - |

**Total Estimated Effort:** 32-43 hours

## Recommended Prioritization

1. **Issue #3** (Certificate/Template Refactor) - Highest priority, blocks Task 8.2
2. **Issue #4** (Unit Tests) - Ensures code quality and prevents regressions
3. **Issue #2** (CIAWriter Abstraction) - Improves architecture
4. **Issue #1** (TMD Offsets) - Code maintainability
5. **Issue #5** (Meta Builder) - Nice to have, lowest priority

## Notes

- Issues #1, #2, and #5 can be combined into a single refactoring task
- Issue #3 Part A is specifically Task 8.2 in the refactoring plan
- Issue #4 should be done incrementally as other issues are addressed
