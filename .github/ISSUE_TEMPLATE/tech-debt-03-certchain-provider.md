---
name: Technical Debt - Certificate Chain Provider (Task 8.2)
about: Implement proper certificate chain provider to replace hardcoded templates
title: '[Task 8.2] Implement Certificate Chain Provider'
labels: 'enhancement, refactoring, security, task-8.2'
assignees: ''
---

## Description
Binary certificate chain is currently hardcoded as base64-encoded string in `dsconv/data/__init__.py`. This was a temporary solution to avoid module-level execution issues. Task 8.2 calls for proper certificate chain provider implementation.

## Current Implementation
```python
# dsconv/data/__init__.py
certchain_retail = b"""eJytkvk/E44fx9GsT58Z..."""  # Base64-encoded binary
```

## Problems
1. Hardcoded retail certificate chain
2. Dev certificate chain loading not implemented (raises NotImplementedError)
3. No validation or verification
4. Security concerns with embedded binary data
5. Opaque implementation

## Recommended Solution
Create `dsconv/crypto/certchain_provider.py`:

```python
class CertChainProvider:
    """Provides certificate chains for CIA generation."""
    
    @staticmethod
    def load_retail() -> bytes:
        """Load retail certificate chain.
        
        Returns:
            Retail certificate chain bytes (0xA00)
        """
        # Load from embedded resource or file
        
    @staticmethod
    def load_dev(path: str) -> bytes:
        """Load dev certificate chain from file.
        
        Args:
            path: Path to dev certificate chain file
            
        Returns:
            Dev certificate chain bytes
            
        Raises:
            FileNotFoundError: If cert chain file not found
            ValueError: If cert chain is invalid
        """
        
    def validate(self, certchain: bytes) -> bool:
        """Validate certificate chain structure.
        
        Args:
            certchain: Certificate chain bytes to validate
            
        Returns:
            True if valid, False otherwise
        """
```

## Implementation Steps
1. Create `dsconv/crypto/certchain_provider.py` module
2. Implement `CertChainProvider` class with methods above
3. Add certificate chain validation (size, structure)
4. Support loading dev cert chain from file (path from config)
5. Update `ServiceFactory` to use `CertChainProvider`
6. Update `ConversionService._write_cia()` to use provider
7. Add tests for cert chain loading and validation
8. Remove hardcoded cert chain from `dsconv/data/__init__.py`

## Benefits
- Proper separation of concerns
- Support for both retail and dev cert chains
- Validation ensures correctness
- Better security practices
- Testable implementation

## Files to Modify
- `dsconv/crypto/certchain_provider.py` (new)
- `dsconv/services/service_factory.py` (use CertChainProvider)
- `dsconv/services/conversion_service.py` (use CertChainProvider)
- `dsconv/data/__init__.py` (remove certchain_retail after migration)
- `tests/unit/crypto/test_certchain_provider.py` (new)

## Priority
High - This is Task 8.2 from the refactoring plan

## Related Issues
- Part of refactoring plan Task 8.2
- Blocks completion of Task 8.1 technical debt cleanup

## Acceptance Criteria
- [ ] `CertChainProvider` class implemented
- [ ] Retail cert chain loading works
- [ ] Dev cert chain loading from file works
- [ ] Certificate chain validation implemented
- [ ] ServiceFactory uses CertChainProvider
- [ ] ConversionService updated to use provider
- [ ] Unit tests added (>80% coverage)
- [ ] All existing tests pass
- [ ] Validation script still passes (byte-identical output)
- [ ] Documentation updated
