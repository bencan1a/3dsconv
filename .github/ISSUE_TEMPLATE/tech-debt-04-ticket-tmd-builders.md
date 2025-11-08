---
name: Technical Debt - Ticket and TMD Builders
about: Replace binary templates with programmatic builders for Ticket and TMD
title: '[Tech Debt] Implement TicketBuilder and TMDBuilder classes'
labels: 'technical-debt, refactoring, architecture'
assignees: ''
---

## Description
Ticket and TMD structures are currently built from opaque base64-encoded binary templates. These should be replaced with programmatic builders for clarity, maintainability, and flexibility.

## Current Implementation
```python
# dsconv/data/__init__.py
ticket_tmd = b"""eJxjYGRgYRgFZIOg/PwSXW..."""  # Opaque binary template

# In conversion code:
ticket_tmd_template = zlib.decompress(base64.b64decode(ticket_tmd))
# Then patch specific offsets with title ID, save size, etc.
```

## Problems
1. Opaque binary templates - hard to understand
2. Difficult to modify for different scenarios
3. No support for multiple content types
4. Maintenance burden (what if structure changes?)
5. Harder to test individual components
6. Magic offset patching instead of structured updates

## Recommended Solution
Create `dsconv/models/ticket.py` and `dsconv/models/tmd.py`:

```python
class TicketBuilder:
    """Builds CIA ticket structure programmatically."""
    
    def __init__(self):
        self.title_id = bytes(8)
        self.title_key = bytes(16)
        # ... other fields
    
    def with_title_id(self, title_id: bytes) -> 'TicketBuilder':
        """Set title ID in ticket (8 bytes)."""
        if len(title_id) != 8:
            raise ValueError("Title ID must be 8 bytes")
        self.title_id = title_id
        return self
    
    def with_title_key(self, key: bytes) -> 'TicketBuilder':
        """Set title key (16 bytes, typically zeros for retail)."""
        self.title_key = key
        return self
    
    def build(self) -> bytes:
        """Build ticket binary structure (0x350 bytes)."""
        # Construct ticket from fields
        
class TMDBuilder:
    """Builds TMD (Title Metadata) structure."""
    
    def __init__(self):
        self.title_id = bytes(8)
        self.save_data_size = 0
        self.contents = []
    
    def with_title_id(self, title_id: bytes) -> 'TMDBuilder':
        """Set title ID (8 bytes)."""
        self.title_id = title_id
        return self
    
    def with_save_data_size(self, size: int) -> 'TMDBuilder':
        """Set save data size (8 bytes)."""
        self.save_data_size = size
        return self
    
    def add_content(self, content_id: int, size: int, index: int, 
                    content_type: int = 0) -> 'TMDBuilder':
        """Add content record to TMD.
        
        Args:
            content_id: Content ID
            size: Content size in bytes
            index: Content index
            content_type: Content type flags
        """
        self.contents.append({
            'id': content_id,
            'size': size,
            'index': index,
            'type': content_type,
            'hash': bytes(32)  # Placeholder, updated later
        })
        return self
    
    def build(self) -> bytes:
        """Build TMD binary structure.
        
        Returns:
            TMD bytes (size varies based on content count)
        """
        # Construct TMD header + content info records + chunk records
```

## Usage Example
```python
# Instead of patching binary template:
ticket = (TicketBuilder()
    .with_title_id(container.title_id)
    .with_title_key(bytes(16))  # Zero key for retail
    .build())

tmd = (TMDBuilder()
    .with_title_id(container.title_id)
    .with_save_data_size(save_size)
    .add_content(content_id=0, size=game_cxi_size, index=0)
    .build())
```

## Implementation Steps
1. Create `dsconv/models/ticket.py` with `TicketBuilder`
2. Create `dsconv/models/tmd.py` with `TMDBuilder`
3. Research 3DS ticket/TMD formats (3dbrew.org)
4. Implement field-by-field construction
5. Add tests for builders
6. Update `ConversionService._write_cia()` to use builders
7. Verify byte-identical output with validation script
8. Remove binary templates from `dsconv/data/__init__.py`

## Benefits
- Self-documenting code
- Type safety and validation
- Support for different scenarios (multiple contents, etc.)
- Easier to test individual components
- Better maintainability
- Clear structure definition

## Files to Modify
- `dsconv/models/ticket.py` (new)
- `dsconv/models/tmd.py` (new)
- `dsconv/services/conversion_service.py` (use builders)
- `dsconv/data/__init__.py` (remove templates after migration)
- `tests/unit/models/test_ticket_builder.py` (new)
- `tests/unit/models/test_tmd_builder.py` (new)

## Priority
High - Directly improves code quality and maintainability

## Related Issues
- Part of Task 8.1 technical debt cleanup
- Related to Issue #3 (Certificate Chain Provider)

## Acceptance Criteria
- [ ] `TicketBuilder` class implemented with all fields
- [ ] `TMDBuilder` class implemented with content record support
- [ ] Builders produce byte-identical output to current templates
- [ ] Unit tests added for both builders (>80% coverage)
- [ ] ConversionService updated to use builders
- [ ] All existing tests pass
- [ ] Validation script still passes (byte-identical output)
- [ ] Documentation added for ticket/TMD structure
