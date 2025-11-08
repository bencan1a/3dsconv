---
name: Technical Debt - Direct File I/O
about: Refactor to use CIAWriter abstraction instead of direct file writes
title: '[Tech Debt] Use CIAWriter abstraction instead of direct file I/O'
labels: 'technical-debt, refactoring, architecture'
assignees: ''
---

## Description
The `_write_cia()` method writes directly to the file handle instead of using CIAWriter's higher-level methods. This bypasses the abstraction layer and alignment handling.

## Current Implementation
```python
# Direct file writes bypass CIAWriter abstraction
self.cia_writer.writer.file.seek(0)
self.cia_writer.writer.file.write(header)
self.cia_writer.writer.file.write(certchain)
self.cia_writer.writer.file.write(ticket_tmd_template)
```

## Problems
- Bypasses CIAWriter's `_align_offset()` methods
- Couples ConversionService to low-level file operations
- Harder to test and mock
- Violates separation of concerns
- Duplicates alignment logic

## Recommended Solution
1. Enhance CIAWriter with high-level methods:
   ```python
   class CIAWriter:
       def write_cia_structure(self, header, certchain, ticket_tmd, chunk_records):
           """Write CIA structure with proper alignment."""
           
       def update_tmd_field(self, field_offset, value):
           """Update TMD field at given offset."""
           
       def write_content_aligned(self, content_data, alignment=256):
           """Write content with automatic alignment padding."""
   ```

2. Update ConversionService to use these methods
3. Keep alignment logic centralized in CIAWriter

## Benefits
- Better abstraction and encapsulation
- Reusable CIAWriter for other CIA operations
- Easier to test with mocks
- Centralized alignment handling
- Clearer separation of concerns

## Files to Modify
- `dsconv/io/cia_writer.py` - Add new high-level methods
- `dsconv/services/conversion_service.py` - Use CIAWriter methods instead of direct I/O

## Priority
Medium - Affects architecture and testability

## Related Issues
- Part of Task 8.1 technical debt cleanup
- May depend on Issue #1 (TMD offsets) for clean implementation

## Acceptance Criteria
- [ ] CIAWriter has high-level methods for CIA structure writing
- [ ] ConversionService uses CIAWriter methods (no direct file.write())
- [ ] Alignment logic is centralized in CIAWriter
- [ ] All existing tests pass
- [ ] Validation script still passes (byte-identical output)
- [ ] Unit tests added for new CIAWriter methods
