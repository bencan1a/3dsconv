---
name: Technical Debt - Hardcoded TMD Offsets
about: Replace hardcoded TMD structure offsets with calculated values
title: '[Tech Debt] Replace hardcoded TMD offsets with dynamic calculation'
labels: 'technical-debt, refactoring, code-quality'
assignees: ''
---

## Description
The `_write_cia()` method in `dsconv/services/conversion_service.py` uses hardcoded offsets for TMD structure updates. These should be calculated dynamically based on TMD structure.

## Current Implementation
Hardcoded offsets are used:
- `0x2FA4` - Info records hash offset
- `0x2FC7` - Chunk records hash offset  
- `0x38D4` - Game CXI content hash offset
- `0x2F9F` - Content count offset
- `0x2C1C` - Title ID in ticket offset
- `0x2F4C` - Title ID in TMD offset
- `0x2F5A` - Save size offset

```python
# Example of current code
self.cia_writer.writer.file.seek(0x2F9F)
self.cia_writer.writer.file.write(bytes([content_count]))
```

## Recommended Solution
1. Create TMD structure model with field definitions
2. Calculate offsets dynamically: `base_offset + relative_offset`
3. Define constants for relative offsets within TMD structure
4. Use structure-aware methods for updates

Example:
```python
class TMDOffsets:
    """TMD structure offset constants (relative to TMD start)."""
    CONTENT_COUNT = 0x1DE  # Relative offset within TMD
    TITLE_ID = 0x18C
    SAVE_SIZE = 0x19A
    # ... etc

# In conversion code:
tmd_base = header_size + cert_size + ticket_size
self.cia_writer.writer.file.seek(tmd_base + TMDOffsets.CONTENT_COUNT)
```

## Benefits
- More maintainable and self-documenting code
- Easier to support different TMD variants
- Reduces risk of offset calculation errors
- Better code readability

## Files to Modify
- `dsconv/services/conversion_service.py` (lines 465-479, 511-537)
- `dsconv/models/cia.py` or new `dsconv/models/tmd_structure.py`

## Priority
Medium - Affects maintainability but not functionality

## Related Issues
- Part of Task 8.1 technical debt cleanup
- See TECHNICAL_DEBT.md for full context

## Acceptance Criteria
- [ ] TMD structure offsets defined as constants
- [ ] Offsets calculated dynamically in code
- [ ] No hardcoded offsets remain in conversion_service.py
- [ ] All existing tests pass
- [ ] Validation script still passes (byte-identical output)
