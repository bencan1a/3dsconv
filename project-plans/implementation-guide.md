# 3dsconv Refactoring Implementation Guide

## Purpose

This guide provides tactical implementation details for agents executing the refactoring plan. It complements `refactoring-plan.md` with concrete code patterns, testing strategies, and step-by-step instructions.

---

## Development Environment Setup

### Prerequisites
```bash
# Ensure Python 3.10+ is installed
python --version  # Should be 3.10 or higher

# Install project with dev dependencies
cd /path/to/3dsconv
pip install -e .[dev]

# Verify installation
pytest tests/ --cov=dsconv
ruff check dsconv/
black --check dsconv/
```

### File Structure After Refactoring

```
dsconv/
├── __init__.py
├── __main__.py              # CLI entry point
├── 3dsconv.py              # Legacy compatibility (deprecated)
├── utils.py                # Shared utilities
│
├── models/                 # Phase 1: Domain models
│   ├── __init__.py
│   ├── ncch.py            # NCCH header structure
│   ├── ncsd.py            # NCSD container structure
│   ├── cia.py             # CIA archive structure
│   └── encryption.py      # Encryption state models
│
├── crypto/                 # Phase 2: Cryptographic services
│   ├── __init__.py
│   ├── aes_adapter.py     # PyAES wrapper
│   ├── key_derivation.py  # Key derivation logic
│   ├── key_provider.py    # Key loading (repository)
│   ├── decryption_service.py  # Decryption orchestration
│   └── certchain_provider.py  # Certificate chains
│
├── io/                     # Phase 3-5: I/O operations
│   ├── __init__.py
│   ├── binary_reader.py   # Binary file reading utility
│   ├── binary_writer.py   # Binary file writing utility
│   ├── ncsd_reader.py     # NCSD container reader
│   ├── ncch_reader.py     # NCCH content reader
│   ├── exefs_reader.py    # ExeFS filesystem reader
│   ├── cia_builder.py     # CIA header builder
│   └── cia_writer.py      # CIA file writer
│
├── validation/             # Phase 4: Validation services
│   ├── __init__.py
│   ├── hash_validator.py  # SHA-256 validation
│   └── format_validator.py  # Magic bytes validation
│
├── services/               # Phase 6: Application services
│   ├── __init__.py
│   ├── conversion_config.py   # Configuration model
│   ├── progress_reporter.py   # Progress reporting
│   ├── conversion_service.py  # Main orchestration
│   └── service_factory.py     # Dependency injection
│
└── cli/                    # Phase 7: CLI layer
    ├── __init__.py
    └── config_mapper.py   # Args to config mapping

tests/
├── conftest.py            # Shared fixtures
├── fixtures/              # Test data files
│   ├── minimal_decrypted.cci
│   ├── minimal_encrypted.cci
│   └── mock_boot9.bin
│
├── unit/                  # Unit tests (existing + new)
│   ├── test_crypto_utils.py
│   ├── test_parse_args.py
│   ├── test_output.py
│   ├── test_prod_keys.py
│   ├── models/           # Phase 1 tests
│   ├── crypto/           # Phase 2 tests
│   ├── io/               # Phase 3-5 tests
│   └── validation/       # Phase 4 tests
│
├── integration/           # Integration tests
│   ├── test_full_conversion.py
│   ├── test_encryption_flow.py
│   └── test_validation_flow.py
│
└── e2e/                   # End-to-end tests
    ├── test_cli.py
    └── test_error_scenarios.py
```

---

## Code Patterns and Standards

### 1. Dataclass Pattern for Models

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelName:
    """One-line description.
    
    Longer description explaining the purpose and usage.
    References to 3DS documentation if applicable.
    """
    
    # Required fields first
    field_name: bytes
    field_size: int
    
    # Optional fields with defaults
    optional_field: Optional[str] = None
    
    def __post_init__(self):
        """Validate fields after initialization."""
        if len(self.field_name) != 4:
            raise ValueError("field_name must be 4 bytes")
    
    @property
    def computed_value(self) -> int:
        """Compute derived value from fields."""
        return self.field_size * 2
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ModelName':
        """Factory method to create from binary data."""
        import struct
        field_name, field_size = struct.unpack('<4sI', data[:8])
        return cls(field_name=field_name, field_size=field_size)
```

### 2. Service Pattern with Dependency Injection

```python
class ServiceName:
    """Service description.
    
    This service is responsible for X and collaborates with Y.
    All dependencies are injected via constructor.
    """
    
    def __init__(
        self,
        dependency1: DependencyType1,
        dependency2: DependencyType2,
        config_value: int = 0
    ):
        """Initialize service with dependencies.
        
        Args:
            dependency1: Description of what this does
            dependency2: Description of what this does
            config_value: Optional configuration (default: 0)
        """
        self.dependency1 = dependency1
        self.dependency2 = dependency2
        self.config_value = config_value
    
    def perform_operation(self, input_data: bytes) -> bytes:
        """Perform the main operation.
        
        Args:
            input_data: Input to process
            
        Returns:
            Processed output
            
        Raises:
            ValueError: If input_data is invalid
        """
        if not input_data:
            raise ValueError("input_data cannot be empty")
        
        # Use injected dependencies
        intermediate = self.dependency1.process(input_data)
        result = self.dependency2.transform(intermediate)
        
        return result
```

### 3. Abstract Interface Pattern

```python
from abc import ABC, abstractmethod
from typing import Protocol

# Option 1: ABC (Abstract Base Class)
class IInterfaceName(ABC):
    """Interface for X operations."""
    
    @abstractmethod
    def required_method(self, param: str) -> int:
        """Description of what this method should do."""
        pass

# Option 2: Protocol (structural typing)
class ProtocolName(Protocol):
    """Protocol for Y operations."""
    
    def required_method(self, param: str) -> int:
        """Description of what this method should do."""
        ...

# Implementation
class ConcreteImplementation(IInterfaceName):
    """Concrete implementation of IInterfaceName."""
    
    def required_method(self, param: str) -> int:
        """Implement the required method."""
        return len(param)
```

### 4. Reader/Writer Pattern

```python
class Reader:
    """Reads X format from binary data."""
    
    def __init__(self, binary_reader: BinaryReader):
        """Initialize with binary reader dependency."""
        self.reader = binary_reader
    
    def read(self) -> Model:
        """Read and parse the format.
        
        Returns:
            Parsed model object
            
        Raises:
            ValueError: If format is invalid
        """
        # Validate magic bytes
        magic = self.reader.read_at(offset=0, length=4)
        if magic != b'EXPD':
            raise ValueError(f"Invalid magic: {magic}")
        
        # Read fields
        field1 = self.reader.read_at(offset=4, length=4)
        field2 = self.reader.read_struct(offset=8, format_str='<I')
        
        return Model(field1=field1, field2=field2[0])
```

### 5. Builder Pattern

```python
class Builder:
    """Builder for constructing complex objects step-by-step."""
    
    def __init__(self):
        """Initialize with default values."""
        self._field1 = b''
        self._field2 = 0
        self._optional = None
    
    def with_field1(self, value: bytes) -> 'Builder':
        """Set field1 value.
        
        Args:
            value: Value for field1
            
        Returns:
            Self for method chaining
        """
        self._field1 = value
        return self
    
    def with_field2(self, value: int) -> 'Builder':
        """Set field2 value."""
        self._field2 = value
        return self
    
    def with_optional(self, value: str) -> 'Builder':
        """Set optional value."""
        self._optional = value
        return self
    
    def build(self) -> Model:
        """Build and return the final object.
        
        Returns:
            Constructed model
            
        Raises:
            ValueError: If required fields are missing
        """
        if not self._field1:
            raise ValueError("field1 is required")
        if self._field2 <= 0:
            raise ValueError("field2 must be positive")
        
        return Model(
            field1=self._field1,
            field2=self._field2,
            optional=self._optional
        )
```

---

## Testing Patterns

### 1. Unit Test Structure

```python
import pytest
from dsconv.models.example import ExampleModel

class TestExampleModel:
    """Tests for ExampleModel."""
    
    def test_creation_with_valid_data(self):
        """Test creating model with valid data succeeds."""
        # Arrange
        field1 = b'TEST'
        field2 = 42
        
        # Act
        model = ExampleModel(field1=field1, field2=field2)
        
        # Assert
        assert model.field1 == field1
        assert model.field2 == field2
    
    def test_creation_with_invalid_data_raises_error(self):
        """Test creating model with invalid data raises ValueError."""
        # Arrange
        field1 = b'TOOLONG'  # Invalid length
        field2 = 42
        
        # Act & Assert
        with pytest.raises(ValueError, match="field1 must be 4 bytes"):
            ExampleModel(field1=field1, field2=field2)
    
    @pytest.mark.parametrize("field2,expected", [
        (0, 0),
        (1, 2),
        (10, 20),
        (100, 200),
    ])
    def test_computed_value(self, field2, expected):
        """Test computed_value property."""
        # Arrange
        model = ExampleModel(field1=b'TEST', field2=field2)
        
        # Act
        result = model.computed_value
        
        # Assert
        assert result == expected
```

### 2. Service Test with Mocks

```python
import pytest
from unittest.mock import Mock, MagicMock, patch
from dsconv.services.example import ExampleService

class TestExampleService:
    """Tests for ExampleService."""
    
    @pytest.fixture
    def mock_dependency1(self):
        """Mock for dependency1."""
        mock = Mock()
        mock.process.return_value = b'processed'
        return mock
    
    @pytest.fixture
    def mock_dependency2(self):
        """Mock for dependency2."""
        mock = Mock()
        mock.transform.return_value = b'transformed'
        return mock
    
    @pytest.fixture
    def service(self, mock_dependency1, mock_dependency2):
        """Create service with mocked dependencies."""
        return ExampleService(
            dependency1=mock_dependency1,
            dependency2=mock_dependency2
        )
    
    def test_perform_operation_success(
        self, 
        service, 
        mock_dependency1, 
        mock_dependency2
    ):
        """Test successful operation."""
        # Arrange
        input_data = b'input'
        
        # Act
        result = service.perform_operation(input_data)
        
        # Assert
        mock_dependency1.process.assert_called_once_with(input_data)
        mock_dependency2.transform.assert_called_once_with(b'processed')
        assert result == b'transformed'
    
    def test_perform_operation_with_empty_input_raises_error(self, service):
        """Test operation with empty input raises ValueError."""
        with pytest.raises(ValueError, match="input_data cannot be empty"):
            service.perform_operation(b'')
```

### 3. Integration Test Pattern

```python
import pytest
from pathlib import Path
from dsconv.services import ConversionService
from dsconv.models import ConversionConfig

class TestConversionIntegration:
    """Integration tests for conversion workflow."""
    
    @pytest.fixture
    def minimal_cci_file(self, tmp_path):
        """Create minimal valid CCI file for testing."""
        cci_file = tmp_path / "test.cci"
        
        # Create minimal CCI structure
        with open(cci_file, 'wb') as f:
            # NCSD header at 0x100
            f.seek(0x100)
            f.write(b'NCSD')  # Magic
            f.write(bytes(4))  # Signature
            
            # Title ID at 0x108
            f.seek(0x108)
            f.write(b'\x00' * 8)  # Title ID
            
            # Partition table at 0x120
            f.seek(0x120)
            f.write(struct.pack('<I', 0x1000))  # Game offset
            f.write(struct.pack('<I', 0x1000))  # Game size
            
            # NCCH header at partition offset
            f.seek(0x1000 * 0x200)  # Media units
            f.write(b'NCCH')  # Magic
            f.write(bytes(0x1FC))  # Rest of header
            
        return cci_file
    
    def test_full_conversion_decrypted_file(self, tmp_path, minimal_cci_file):
        """Test complete conversion of decrypted CCI to CIA."""
        # Arrange
        output_file = tmp_path / "output.cia"
        config = ConversionConfig(
            input_file=str(minimal_cci_file),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True
        )
        
        # Act
        service = create_conversion_service(config)
        service.convert()
        
        # Assert
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        # Verify CIA structure
        with open(output_file, 'rb') as f:
            # Check for CIA magic (header starts with size)
            header_size = struct.unpack('<I', f.read(4))[0]
            assert header_size == 0x2020
```

### 4. Fixture Creation

```python
# In tests/conftest.py

import pytest
from io import BytesIO

@pytest.fixture
def mock_binary_reader():
    """Create mock BinaryReader with in-memory data."""
    data = BytesIO()
    # Add test data
    data.write(b'TEST' + bytes(100))
    data.seek(0)
    
    from dsconv.io import BinaryReader
    return BinaryReader(data)

@pytest.fixture
def sample_ncch_header():
    """Create sample NCCH header for testing."""
    from dsconv.models import NCCHHeader
    return NCCHHeader(
        signature=bytes(0x100),
        magic=b'NCCH',
        content_size=0x1000,
        partition_id=bytes(8),
        title_id=bytes(8),
        encryption_flags=0x04  # Decrypted
    )

@pytest.fixture
def temp_cci_file(tmp_path):
    """Create temporary CCI file."""
    cci_path = tmp_path / "test.cci"
    # Create minimal valid CCI
    # ... (creation logic)
    return cci_path
```

---

## Step-by-Step Task Execution

### General Workflow for Each Task

1. **Read the Task Description**
   - Understand the goal
   - Identify dependencies
   - Note acceptance criteria

2. **Create the File Structure**
   ```bash
   mkdir -p dsconv/models  # Or appropriate directory
   touch dsconv/models/__init__.py
   touch dsconv/models/ncch.py
   ```

3. **Write the Code**
   - Start with imports
   - Define classes/functions
   - Add type hints
   - Add docstrings
   - Implement logic

4. **Write Tests**
   ```bash
   mkdir -p tests/unit/models
   touch tests/unit/models/__init__.py
   touch tests/unit/models/test_ncch.py
   ```

5. **Run Tests**
   ```bash
   pytest tests/unit/models/test_ncch.py -v
   ```

6. **Check Coverage**
   ```bash
   pytest tests/unit/models/test_ncch.py --cov=dsconv.models.ncch --cov-report=term-missing
   ```

7. **Lint and Format**
   ```bash
   ruff check dsconv/models/ncch.py
   black dsconv/models/ncch.py
   ```

8. **Verify All Tests Still Pass**
   ```bash
   pytest tests/ -v
   ```

9. **Update Module Exports**
   ```python
   # In dsconv/models/__init__.py
   from .ncch import NCCHHeader
   
   __all__ = ['NCCHHeader']
   ```

---

## Example: Implementing Task 1.1 (NCCH Header Model)

### Step 1: Create File

```bash
mkdir -p dsconv/models
touch dsconv/models/__init__.py
touch dsconv/models/ncch.py
```

### Step 2: Write Model Code

```python
# dsconv/models/ncch.py
"""NCCH (Nintendo Content Container Header) models."""

from dataclasses import dataclass
import struct


@dataclass
class NCCHHeader:
    """NCCH Header structure.
    
    Represents the header of a Nintendo Content Container (NCCH).
    This structure appears at the beginning of each NCCH partition
    in a CCI file or as standalone CIA content.
    
    Reference: 3dbrew.org/wiki/NCCH
    """
    
    signature: bytes  # 0x000-0x100: RSA-2048 signature
    magic: bytes  # 0x100-0x104: 'NCCH'
    content_size: int  # 0x104-0x108: Size in media units
    partition_id: bytes  # 0x108-0x110: Partition ID
    maker_code: bytes  # 0x110-0x112: Maker code
    version: int  # 0x112-0x114: Version
    # ... add more fields as needed
    
    title_id: bytes  # Title ID for key derivation
    encryption_flags: int  # Flags byte at 0x18F
    
    def __post_init__(self):
        """Validate header fields."""
        if len(self.magic) != 4:
            raise ValueError("magic must be 4 bytes")
        if self.magic != b'NCCH':
            raise ValueError(f"Invalid NCCH magic: {self.magic}")
        if len(self.signature) != 0x100:
            raise ValueError("signature must be 0x100 bytes")
    
    @property
    def is_encrypted(self) -> bool:
        """Check if content is encrypted.
        
        Returns:
            True if content is encrypted, False if decrypted
        """
        # Bit 2 of encryption flags: 0 = encrypted, 1 = decrypted
        return not bool(self.encryption_flags & 0x04)
    
    @property
    def uses_zerokey(self) -> bool:
        """Check if content uses zero-key encryption.
        
        Returns:
            True if zero-key encrypted
        """
        # Bit 0 of encryption flags
        return bool(self.encryption_flags & 0x01)
    
    @property
    def size_bytes(self) -> int:
        """Get content size in bytes.
        
        Returns:
            Size in bytes (content_size * media_unit_size)
        """
        return self.content_size * 0x200  # Media unit = 0x200 bytes
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'NCCHHeader':
        """Create NCCHHeader from binary data.
        
        Args:
            data: Binary data containing NCCH header (at least 0x200 bytes)
            
        Returns:
            Parsed NCCHHeader object
            
        Raises:
            ValueError: If data is too short or invalid
        """
        if len(data) < 0x200:
            raise ValueError("Data too short for NCCH header")
        
        signature = data[0x000:0x100]
        magic = data[0x100:0x104]
        
        # Unpack fixed-size fields
        content_size, = struct.unpack('<I', data[0x104:0x108])
        partition_id = data[0x108:0x110]
        maker_code = data[0x110:0x112]
        version, = struct.unpack('<H', data[0x112:0x114])
        
        # Get title ID and encryption flags
        title_id = data[0x118:0x120]  # Assuming offset
        encryption_flags = data[0x18F]
        
        return cls(
            signature=signature,
            magic=magic,
            content_size=content_size,
            partition_id=partition_id,
            maker_code=maker_code,
            version=version,
            title_id=title_id,
            encryption_flags=encryption_flags
        )
```

### Step 3: Write Tests

```python
# tests/unit/models/test_ncch.py
"""Tests for NCCH header models."""

import pytest
from dsconv.models.ncch import NCCHHeader


class TestNCCHHeader:
    """Tests for NCCHHeader model."""
    
    def test_create_with_valid_data(self):
        """Test creating header with valid data."""
        # Arrange
        signature = bytes(0x100)
        magic = b'NCCH'
        content_size = 0x1000
        partition_id = bytes(8)
        maker_code = b'01'
        version = 0
        title_id = bytes(8)
        encryption_flags = 0x00
        
        # Act
        header = NCCHHeader(
            signature=signature,
            magic=magic,
            content_size=content_size,
            partition_id=partition_id,
            maker_code=maker_code,
            version=version,
            title_id=title_id,
            encryption_flags=encryption_flags
        )
        
        # Assert
        assert header.magic == b'NCCH'
        assert header.content_size == 0x1000
        assert header.encryption_flags == 0x00
    
    def test_create_with_invalid_magic_raises_error(self):
        """Test creating header with invalid magic raises ValueError."""
        with pytest.raises(ValueError, match="Invalid NCCH magic"):
            NCCHHeader(
                signature=bytes(0x100),
                magic=b'XXXX',  # Invalid
                content_size=0x1000,
                partition_id=bytes(8),
                maker_code=b'01',
                version=0,
                title_id=bytes(8),
                encryption_flags=0x00
            )
    
    def test_is_encrypted_property_with_encrypted_content(self):
        """Test is_encrypted returns True for encrypted content."""
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b'NCCH',
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b'01',
            version=0,
            title_id=bytes(8),
            encryption_flags=0x00  # Bit 2 = 0, encrypted
        )
        assert header.is_encrypted is True
    
    def test_is_encrypted_property_with_decrypted_content(self):
        """Test is_encrypted returns False for decrypted content."""
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b'NCCH',
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b'01',
            version=0,
            title_id=bytes(8),
            encryption_flags=0x04  # Bit 2 = 1, decrypted
        )
        assert header.is_encrypted is False
    
    def test_uses_zerokey_property(self):
        """Test uses_zerokey property."""
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b'NCCH',
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b'01',
            version=0,
            title_id=bytes(8),
            encryption_flags=0x01  # Bit 0 = 1, zerokey
        )
        assert header.uses_zerokey is True
    
    def test_size_bytes_property(self):
        """Test size_bytes property."""
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b'NCCH',
            content_size=0x10,  # 0x10 media units
            partition_id=bytes(8),
            maker_code=b'01',
            version=0,
            title_id=bytes(8),
            encryption_flags=0x00
        )
        # 0x10 * 0x200 = 0x2000
        assert header.size_bytes == 0x2000
    
    def test_from_bytes_with_valid_data(self):
        """Test creating header from binary data."""
        # Arrange - create minimal valid NCCH header
        data = bytearray(0x200)
        data[0x100:0x104] = b'NCCH'  # Magic
        data[0x104:0x108] = b'\x00\x10\x00\x00'  # Content size (little-endian)
        data[0x18F] = 0x04  # Encryption flags
        
        # Act
        header = NCCHHeader.from_bytes(bytes(data))
        
        # Assert
        assert header.magic == b'NCCH'
        assert header.content_size == 0x1000
        assert header.encryption_flags == 0x04
    
    def test_from_bytes_with_short_data_raises_error(self):
        """Test from_bytes with insufficient data raises ValueError."""
        data = bytes(0x100)  # Too short
        with pytest.raises(ValueError, match="Data too short"):
            NCCHHeader.from_bytes(data)
    
    @pytest.mark.parametrize("flags,is_encrypted,uses_zerokey", [
        (0x00, True, False),   # Encrypted, not zerokey
        (0x01, True, True),    # Encrypted with zerokey
        (0x04, False, False),  # Decrypted
        (0x05, False, True),   # Decrypted (zerokey flag doesn't matter)
    ])
    def test_encryption_flag_combinations(
        self, 
        flags, 
        is_encrypted, 
        uses_zerokey
    ):
        """Test various encryption flag combinations."""
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b'NCCH',
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b'01',
            version=0,
            title_id=bytes(8),
            encryption_flags=flags
        )
        assert header.is_encrypted == is_encrypted
        assert header.uses_zerokey == uses_zerokey
```

### Step 4: Run Tests

```bash
# Run tests for this module
pytest tests/unit/models/test_ncch.py -v

# Check coverage
pytest tests/unit/models/test_ncch.py \
    --cov=dsconv.models.ncch \
    --cov-report=term-missing

# Should show 100% coverage
```

### Step 5: Update Module Exports

```python
# dsconv/models/__init__.py
"""Domain models for 3dsconv."""

from .ncch import NCCHHeader

__all__ = ['NCCHHeader']
```

### Step 6: Verify Integration

```bash
# Run all tests
pytest tests/ -v

# All existing tests should still pass
# New tests should pass
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Circular Imports

**Problem:**
```python
# In models/ncch.py
from dsconv.crypto import DecryptionService  # Circular import!

# In crypto/decryption_service.py
from dsconv.models import NCCHHeader  # Circular import!
```

**Solution:**
```python
# Use type hints with forward references
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dsconv.crypto import DecryptionService

class NCCHReader:
    def __init__(self, decryption: 'DecryptionService | None' = None):
        ...
```

### Pitfall 2: Testing Code with File I/O

**Problem:**
```python
def test_reader_with_real_file():
    # Creates temp files, slow, fragile
    with open('test.bin', 'wb') as f:
        f.write(...)
```

**Solution:**
```python
from io import BytesIO

def test_reader_with_mock_file():
    # Use BytesIO for in-memory file-like object
    mock_file = BytesIO(b'test data')
    reader = BinaryReader(mock_file)
    ...
```

### Pitfall 3: Not Closing Resources

**Problem:**
```python
def read_file(path):
    f = open(path, 'rb')
    data = f.read()
    return data  # File never closed!
```

**Solution:**
```python
def read_file(path):
    with open(path, 'rb') as f:
        data = f.read()
    return data  # File automatically closed
```

### Pitfall 4: Mutable Default Arguments

**Problem:**
```python
def process(items=[]):  # BAD!
    items.append('x')
    return items
```

**Solution:**
```python
def process(items=None):
    if items is None:
        items = []
    items.append('x')
    return items
```

---

## Quality Checklist

Before marking a task as complete, verify:

- [ ] Code follows patterns in this guide
- [ ] All public methods have type hints
- [ ] All classes and methods have docstrings
- [ ] No global state introduced
- [ ] Dependencies are injected, not imported
- [ ] Unit tests achieve 100% coverage
- [ ] Tests follow AAA pattern
- [ ] Parametrized tests used where appropriate
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Linting passes: `ruff check dsconv/`
- [ ] Formatting applied: `black dsconv/`
- [ ] Type checking passes: `mypy dsconv/` (if configured)
- [ ] No regressions in existing tests
- [ ] Module exports updated in `__init__.py`
- [ ] Integration with existing code verified

---

## Getting Help

If stuck on a task:

1. **Review the Code Patterns** section above
2. **Look at similar existing code** in the codebase
3. **Check Python documentation** for standard library usage
4. **Review 3DS format documentation** at 3dbrew.org
5. **Ask for clarification** on specific technical blockers

---

## Conclusion

This guide provides the tactical details needed to execute each task in the refactoring plan. Follow these patterns consistently to maintain code quality and architectural coherence throughout the refactoring process.

**Next Steps:**
1. Start with Phase 1, Task 1.1
2. Follow the step-by-step workflow
3. Use the code patterns provided
4. Verify against the quality checklist
5. Move to next task

Good luck with the refactoring!
