# 3dsconv Refactoring Plan: From Monolith to Maintainable Architecture

## Executive Summary

**Current State:** 737-line monolithic script with global state, nested functions, and tight coupling  
**Target State:** Modular, testable architecture following SOLID principles and clean code practices  
**Approach:** Phased refactoring with incremental, agent-executable tasks  
**Test Coverage Goal:** 80% line coverage, 70% branch coverage  
**Timeline:** 8-10 phases with 3-6 tasks each

---

## Architectural Vision

### Current Architecture Problems

1. **Monolithic Structure** - Single 737-line file mixing concerns
2. **Global State Pollution** - Module-level variables (`args`, `keys_set`, `orig_ncch_key`, etc.)
3. **No Separation of Concerns** - I/O, business logic, crypto, and CLI all intermingled
4. **Nested Functions with Closures** - Key loading logic trapped in nested functions with global side effects
5. **Side Effects Everywhere** - File I/O, `print()`, `sys.exit()` throughout execution
6. **Untestable Main Loop** - 350+ lines of procedural code (lines 313-665) with no isolation
7. **Tight Coupling** - Direct file operations, crypto libraries, and business logic tightly bound

### Target Architecture (Clean Architecture Principles)

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer (Entry Point)              │
│              Command-line parsing & orchestration        │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                Application Service Layer                 │
│         ConversionService - High-level workflows         │
└───────────────────┬─────────────────────────────────────┘
                    │
      ┌─────────────┼─────────────┐
      │             │             │
┌─────▼─────┐ ┌────▼────┐ ┌──────▼──────┐
│  Domain   │ │ Readers │ │   Writers   │
│  Models   │ │ (Input) │ │  (Output)   │
└─────┬─────┘ └────┬────┘ └──────┬──────┘
      │            │              │
┌─────▼────────────▼──────────────▼──────┐
│         Infrastructure Layer            │
│  Crypto │ FileSystem │ Validation       │
└─────────────────────────────────────────┘
```

**Layers:**
- **CLI Layer**: Argument parsing, user interaction, progress reporting
- **Application Service**: Orchestration, workflow coordination
- **Domain Layer**: Business logic, models (CCI, CIA, NCCH, encryption state)
- **I/O Layer**: File readers, writers (separate concerns)
- **Infrastructure**: Crypto operations, filesystem abstraction, validation

---

## Refactoring Principles

### SOLID Principles Application

1. **Single Responsibility Principle (SRP)**
   - Each class has one reason to change
   - Example: `CCIReader` only reads CCI files, `CryptoService` only handles encryption

2. **Open/Closed Principle (OCP)**
   - Open for extension (new encryption types), closed for modification
   - Use strategy pattern for encryption methods

3. **Liskov Substitution Principle (LSP)**
   - Abstraction for readers/writers allows substitution
   - Mock implementations for testing

4. **Interface Segregation Principle (ISP)**
   - Small, focused interfaces
   - Example: `IKeyProvider`, `IHashValidator`, `IProgressReporter`

5. **Dependency Inversion Principle (DIP)**
   - Depend on abstractions, not concretions
   - Inject dependencies (crypto, filesystem, config)

### Design Patterns to Apply

1. **Strategy Pattern** - Encryption detection and decryption strategies
2. **Factory Pattern** - Create readers/writers based on format
3. **Builder Pattern** - Construct complex CIA files step-by-step
4. **Repository Pattern** - Abstract key storage (boot9, prod.keys)
5. **Adapter Pattern** - Wrap pyaes library for testability
6. **Command Pattern** - Encapsulate conversion operations

---

## Phase 1: Extract Domain Models (Foundation)

**Goal:** Create pure domain models representing CCI/CIA structures  
**Agent Focus:** Data structure extraction  
**Dependencies:** None  
**Risk:** Low

### Tasks

#### Task 1.1: Create NCCH Header Model
**File:** `dsconv/models/ncch.py`
```python
@dataclass
class NCCHHeader:
    """NCCH (Nintendo Content Container Header) structure"""
    signature: bytes
    magic: bytes  # Should be b'NCCH'
    content_size: int
    partition_id: bytes
    title_id: bytes
    encryption_flags: int
    # ... other fields
    
    @property
    def is_encrypted(self) -> bool:
        """Check if content is encrypted"""
        return not (self.encryption_flags & 0x04)
    
    @property
    def uses_zerokey(self) -> bool:
        """Check if uses zero-key encryption"""
        return bool(self.encryption_flags & 0x01)
```

**Acceptance Criteria:**
- Dataclass with all NCCH header fields
- Type hints on all fields
- Property methods for computed values
- No I/O operations
- 100% test coverage

#### Task 1.2: Create NCSD (CCI) Container Model
**File:** `dsconv/models/ncsd.py`
```python
@dataclass
class NCSDPartition:
    """Represents a partition in NCSD container"""
    offset: int
    size: int
    partition_type: str  # 'game', 'manual', 'dlpchild'

@dataclass  
class NCSDContainer:
    """NCSD Container (CCI file structure)"""
    magic: bytes  # Should be b'NCSD'
    title_id: bytes
    partitions: list[NCSDPartition]
    
    def get_game_partition(self) -> NCSDPartition | None:
        """Get the main game executable partition"""
        ...
```

**Acceptance Criteria:**
- Dataclasses for NCSD and partitions
- Methods to access partitions by type
- No I/O or business logic
- 100% test coverage

#### Task 1.3: Create CIA Structure Models
**File:** `dsconv/models/cia.py`
```python
@dataclass
class CIAHeader:
    """CIA Archive header structure"""
    cert_chain_size: int
    ticket_size: int
    tmd_size: int
    meta_size: int
    content_size: int
    content_index: int

@dataclass
class CIAContent:
    """Individual content in CIA"""
    content_id: int
    index: int
    size: int
    hash: bytes
```

**Acceptance Criteria:**
- Complete CIA structure models
- Type-safe field definitions
- No coupling to I/O
- Unit tests for all properties

#### Task 1.4: Create Encryption State Model
**File:** `dsconv/models/encryption.py`
```python
from enum import Enum

class EncryptionType(Enum):
    DECRYPTED = "decrypted"
    ZEROKEY = "zerokey"
    ORIGINAL_NCCH = "original_ncch"

@dataclass
class EncryptionContext:
    """Encryption state and keys for conversion"""
    encryption_type: EncryptionType
    normal_key: bytes | None
    title_id: bytes
    
    @property
    def needs_decryption(self) -> bool:
        return self.encryption_type != EncryptionType.DECRYPTED
```

**Acceptance Criteria:**
- Enum for encryption types
- Context object for encryption state
- No crypto operations (pure data)
- Full test coverage

---

## Phase 2: Extract Crypto Services (Pure Functions → Services)

**Goal:** Isolate cryptographic operations into testable services  
**Agent Focus:** Crypto abstraction  
**Dependencies:** Phase 1 models  
**Risk:** Medium (crypto complexity)

### Tasks

#### Task 2.1: Create Crypto Adapter (Wrapper for pyaes)
**File:** `dsconv/crypto/aes_adapter.py`
```python
from abc import ABC, abstractmethod

class IAESCipher(ABC):
    """Interface for AES encryption operations"""
    
    @abstractmethod
    def decrypt(self, data: bytes) -> bytes:
        pass
    
    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        pass

class PyAESAdapter(IAESCipher):
    """Adapter wrapping pyaes library"""
    
    def __init__(self, key: bytes, counter_value: int):
        self.key = key
        self.counter_value = counter_value
    
    def decrypt(self, data: bytes) -> bytes:
        import pyaes
        ctr = pyaes.Counter(initial_value=self.counter_value)
        cipher = pyaes.AESModeOfOperationCTR(self.key, counter=ctr)
        return cipher.decrypt(data)
```

**Acceptance Criteria:**
- Abstract interface for AES operations
- PyAES adapter implementation
- Mock adapter for testing
- No global state
- 100% test coverage

#### Task 2.2: Create Key Derivation Service
**File:** `dsconv/crypto/key_derivation.py`
```python
class KeyDerivationService:
    """Service for deriving encryption keys"""
    
    def __init__(self, original_ncch_key: int):
        self.original_ncch_key = original_ncch_key
    
    def derive_normal_key(self, key_y: bytes) -> bytes:
        """Derive normal key from key_y and original NCCH key"""
        from dsconv.utils import rol
        
        key_y_int = int.from_bytes(key_y, byteorder="big")
        key_int = rol(
            (rol(self.original_ncch_key, 2, 128) ^ key_y_int) 
            + 0x1FF9E9AAC5FE0408024591DC5D52768A,
            87,
            128,
        )
        return key_int.to_bytes(0x10, byteorder="big")
```

**Acceptance Criteria:**
- Pure function for key derivation
- Dependency injection for original key
- Comprehensive unit tests with known test vectors
- No global state

#### Task 2.3: Create Key Provider Service (Repository Pattern)
**File:** `dsconv/crypto/key_provider.py`
```python
from abc import ABC, abstractmethod

class IKeyProvider(ABC):
    """Interface for encryption key providers"""
    
    @abstractmethod
    def get_original_ncch_key(self) -> int:
        pass

class ProdKeysKeyProvider(IKeyProvider):
    """Loads keys from prod.keys file"""
    
    def __init__(self, prod_keys_path: str):
        self.prod_keys_path = prod_keys_path
    
    def get_original_ncch_key(self) -> int:
        from dsconv.utils import get_slot0x2c_key_from_prod_keys
        return get_slot0x2c_key_from_prod_keys(self.prod_keys_path)

class Boot9KeyProvider(IKeyProvider):
    """Loads keys from boot9.bin"""
    
    def __init__(self, boot9_path: str, dev_keys: bool = False):
        self.boot9_path = boot9_path
        self.dev_keys = dev_keys
    
    def get_original_ncch_key(self) -> int:
        # Extract key from boot9.bin
        ...
```

**Acceptance Criteria:**
- Interface for key providers
- Two implementations (prod.keys, boot9)
- Error handling with specific exceptions
- Mock provider for testing
- Full test coverage

#### Task 2.4: Create Decryption Service
**File:** `dsconv/crypto/decryption_service.py`
```python
class DecryptionService:
    """Service for decrypting NCCH content"""
    
    def __init__(
        self, 
        key_derivation: KeyDerivationService,
        aes_cipher_factory: Callable[[bytes, int], IAESCipher]
    ):
        self.key_derivation = key_derivation
        self.aes_cipher_factory = aes_cipher_factory
    
    def decrypt_extheader(
        self, 
        encrypted_data: bytes, 
        key_y: bytes,
        title_id: bytes
    ) -> bytes:
        """Decrypt extended header"""
        normal_key = self.key_derivation.derive_normal_key(key_y)
        ctr_value = int.from_bytes(title_id + b"\x01" + bytes(7), "big")
        cipher = self.aes_cipher_factory(normal_key, ctr_value)
        return cipher.decrypt(encrypted_data)
```

**Acceptance Criteria:**
- Dependency injection for all dependencies
- Separate methods for extheader, exefs
- Testable with mock cipher
- No file I/O

---

## Phase 3: Extract File I/O (Readers)

**Goal:** Separate file reading from business logic  
**Agent Focus:** I/O abstraction  
**Dependencies:** Phase 1 models  
**Risk:** Medium (binary parsing complexity)

### Tasks

#### Task 3.1: Create Binary Reader Utility
**File:** `dsconv/io/binary_reader.py`
```python
class BinaryReader:
    """Utility for reading binary data with seeking"""
    
    def __init__(self, file_handle):
        self.file = file_handle
    
    def read_at(self, offset: int, length: int) -> bytes:
        """Read bytes at specific offset"""
        self.file.seek(offset)
        return self.file.read(length)
    
    def read_struct(self, offset: int, format_str: str) -> tuple:
        """Read and unpack struct at offset"""
        import struct
        size = struct.calcsize(format_str)
        data = self.read_at(offset, size)
        return struct.unpack(format_str, data)
```

**Acceptance Criteria:**
- Wrapper around file handle
- Convenience methods for common operations
- No business logic
- Unit tests with BytesIO

#### Task 3.2: Create NCSD Reader
**File:** `dsconv/io/ncsd_reader.py`
```python
class NCSDReader:
    """Reads NCSD container structure from CCI files"""
    
    def __init__(self, binary_reader: BinaryReader):
        self.reader = binary_reader
    
    def read_container(self) -> NCSDContainer:
        """Parse NCSD container header and partitions"""
        # Read magic at 0x100
        magic = self.reader.read_at(0x100, 4)
        if magic != b'NCSD':
            raise ValueError("Invalid NCSD magic")
        
        # Read title ID at 0x108
        title_id = self.reader.read_at(0x108, 8)[::-1]
        
        # Parse partitions
        partitions = self._read_partitions()
        
        return NCSDContainer(
            magic=magic,
            title_id=title_id,
            partitions=partitions
        )
    
    def _read_partitions(self) -> list[NCSDPartition]:
        """Parse partition table"""
        ...
```

**Acceptance Criteria:**
- Reads and validates NCSD structure
- Returns domain model
- Proper error handling
- Unit tests with fixture files

#### Task 3.3: Create NCCH Reader
**File:** `dsconv/io/ncch_reader.py`
```python
class NCCHReader:
    """Reads NCCH header and content"""
    
    def __init__(self, binary_reader: BinaryReader):
        self.reader = binary_reader
    
    def read_header(self, offset: int = 0) -> NCCHHeader:
        """Read NCCH header at given offset"""
        magic = self.reader.read_at(offset + 0x100, 4)
        if magic != b'NCCH':
            raise ValueError("Invalid NCCH magic")
        
        # Parse all header fields
        ...
        
        return NCCHHeader(...)
    
    def read_extheader(
        self, 
        offset: int, 
        decrypt: bool = False,
        decryption_service: DecryptionService | None = None
    ) -> bytes:
        """Read extended header, optionally decrypting"""
        data = self.reader.read_at(offset + 0x200, 0x400)
        
        if decrypt and decryption_service:
            # Decrypt using service
            ...
        
        return data
```

**Acceptance Criteria:**
- Reads NCCH structure
- Optional decryption via injected service
- Validates magic bytes
- Full test coverage

#### Task 3.4: Create ExeFS Reader
**File:** `dsconv/io/exefs_reader.py`
```python
@dataclass
class ExeFSFile:
    """Represents a file in ExeFS"""
    name: str
    offset: int
    size: int

class ExeFSReader:
    """Reads ExeFS filesystem structure"""
    
    def __init__(self, binary_reader: BinaryReader):
        self.reader = binary_reader
    
    def read_file_headers(self, exefs_offset: int) -> list[ExeFSFile]:
        """Parse ExeFS file headers"""
        # Read up to 10 file headers
        ...
    
    def read_file(
        self, 
        exefs_offset: int, 
        file_info: ExeFSFile,
        decrypt: bool = False,
        cipher: IAESCipher | None = None
    ) -> bytes:
        """Read file content from ExeFS"""
        ...
```

**Acceptance Criteria:**
- Parses ExeFS headers
- Reads individual files
- Optional decryption
- Unit tests

---

## Phase 4: Extract Validation Services

**Goal:** Isolate hash validation and format verification  
**Agent Focus:** Validation logic  
**Dependencies:** Phase 1 models, Phase 3 readers  
**Risk:** Low

### Tasks

#### Task 4.1: Create Hash Validator
**File:** `dsconv/validation/hash_validator.py`
```python
class HashValidator:
    """Service for validating SHA-256 hashes"""
    
    def __init__(self, ignore_bad_hashes: bool = False):
        self.ignore_bad_hashes = ignore_bad_hashes
    
    def validate_extheader_hash(
        self, 
        extheader: bytes, 
        expected_hash: bytes
    ) -> bool:
        """Validate extended header hash"""
        import hashlib
        actual_hash = hashlib.sha256(extheader).digest()
        
        if actual_hash != expected_hash:
            if self.ignore_bad_hashes:
                return True  # Ignore and continue
            return False
        
        return True
    
    def compute_content_hash(self, content: bytes) -> bytes:
        """Compute SHA-256 hash of content"""
        import hashlib
        return hashlib.sha256(content).digest()
```

**Acceptance Criteria:**
- Pure validation functions
- Configurable ignore flag
- No I/O operations
- Test with known hashes

#### Task 4.2: Create Format Validator
**File:** `dsconv/validation/format_validator.py`
```python
class FormatValidator:
    """Validates file format structures"""
    
    @staticmethod
    def validate_ncsd_magic(magic: bytes) -> None:
        """Validate NCSD magic bytes"""
        if magic != b'NCSD':
            raise ValueError("Invalid NCSD magic, not a CCI file")
    
    @staticmethod
    def validate_ncch_magic(magic: bytes) -> None:
        """Validate NCCH magic bytes"""
        if magic != b'NCCH':
            raise ValueError("Invalid NCCH magic, not a valid partition")
    
    @staticmethod
    def validate_partition_exists(partition: NCSDPartition | None) -> None:
        """Validate that required partition exists"""
        if partition is None:
            raise ValueError("Required partition not found")
```

**Acceptance Criteria:**
- Static validation methods
- Descriptive error messages
- No side effects
- Full test coverage

---

## Phase 5: Extract File Writers

**Goal:** Separate CIA file writing into dedicated components  
**Agent Focus:** Output abstraction  
**Dependencies:** Phase 1 models  
**Risk:** Medium (complex CIA structure)

### Tasks

#### Task 5.1: Create Binary Writer Utility
**File:** `dsconv/io/binary_writer.py`
```python
class BinaryWriter:
    """Utility for writing binary data"""
    
    def __init__(self, file_handle):
        self.file = file_handle
    
    def write_at(self, offset: int, data: bytes) -> None:
        """Write bytes at specific offset"""
        self.file.seek(offset)
        self.file.write(data)
    
    def write_struct(self, offset: int, format_str: str, *values) -> None:
        """Pack and write struct at offset"""
        import struct
        data = struct.pack(format_str, *values)
        self.write_at(offset, data)
    
    def append(self, data: bytes) -> None:
        """Append data to end of file"""
        self.file.seek(0, 2)  # Seek to end
        self.file.write(data)
```

**Acceptance Criteria:**
- Wrapper around file handle
- Convenience methods
- No business logic
- Tests with BytesIO

#### Task 5.2: Create CIA Header Builder
**File:** `dsconv/io/cia_builder.py`
```python
class CIAHeaderBuilder:
    """Builder for constructing CIA headers"""
    
    def __init__(self):
        self.cert_chain_size = 0xA00
        self.ticket_size = 0x350
        self.tmd_size = 0xB34
        self.meta_size = 0x3AC0
        self.content_size = 0
        self.content_index = 0
    
    def with_content(self, size: int, index: int) -> 'CIAHeaderBuilder':
        """Add content to CIA"""
        self.content_size += size
        self.content_index |= (0x80 >> index)
        return self
    
    def build(self) -> bytes:
        """Build CIA header bytes"""
        import struct
        return struct.pack(
            "<IHHII",
            0x2020, 0, 0,
            self.cert_chain_size,
            self.ticket_size
        ) + ...
```

**Acceptance Criteria:**
- Builder pattern for CIA header
- Fluent interface
- Validates before build
- Unit tests

#### Task 5.3: Create CIA Writer
**File:** `dsconv/io/cia_writer.py`
```python
class CIAWriter:
    """Writes CIA archive files"""
    
    def __init__(
        self, 
        binary_writer: BinaryWriter,
        cert_chain: bytes,
        dev_mode: bool = False
    ):
        self.writer = binary_writer
        self.cert_chain = cert_chain
        self.dev_mode = dev_mode
    
    def write_header(self, header: CIAHeader) -> None:
        """Write CIA header"""
        ...
    
    def write_content(
        self, 
        content_data: bytes,
        compute_hash: bool = True
    ) -> bytes:
        """Write content and return its hash"""
        import hashlib
        hash_obj = hashlib.sha256()
        
        # Write in chunks
        offset = 0
        chunk_size = 0x800000
        while offset < len(content_data):
            chunk = content_data[offset:offset + chunk_size]
            self.writer.append(chunk)
            hash_obj.update(chunk)
            offset += chunk_size
        
        return hash_obj.digest() if compute_hash else b''
```

**Acceptance Criteria:**
- Writes CIA structure
- Computes hashes
- Handles large files
- Full test coverage

---

## Phase 6: Create Application Service (Orchestration)

**Goal:** High-level conversion workflow  
**Agent Focus:** Workflow orchestration  
**Dependencies:** All previous phases  
**Risk:** Medium (integration complexity)

### Tasks

#### Task 6.1: Create Conversion Configuration
**File:** `dsconv/services/conversion_config.py`
```python
@dataclass
class ConversionConfig:
    """Configuration for CCI to CIA conversion"""
    
    input_file: str
    output_file: str
    key_provider: IKeyProvider | None
    ignore_bad_hashes: bool = False
    ignore_encryption: bool = False
    dev_keys: bool = False
    verbose: bool = False
    
    def validate(self) -> None:
        """Validate configuration"""
        if not os.path.isfile(self.input_file):
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
```

**Acceptance Criteria:**
- Dataclass for all config
- Validation method
- Type hints
- Unit tests

#### Task 6.2: Create Progress Reporter Interface
**File:** `dsconv/services/progress_reporter.py`
```python
from abc import ABC, abstractmethod

class IProgressReporter(ABC):
    """Interface for reporting conversion progress"""
    
    @abstractmethod
    def report_stage(self, stage: str) -> None:
        """Report current conversion stage"""
        pass
    
    @abstractmethod
    def report_progress(self, current: int, total: int) -> None:
        """Report progress within a stage"""
        pass

class ConsoleProgressReporter(IProgressReporter):
    """Reports progress to console"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def report_stage(self, stage: str) -> None:
        if self.verbose:
            print(f"\n{stage}...")
    
    def report_progress(self, current: int, total: int) -> None:
        from dsconv.utils import show_progress
        show_progress(current, total)
```

**Acceptance Criteria:**
- Abstract interface
- Console implementation
- Mock for testing
- No global state

#### Task 6.3: Create Conversion Service (Main Orchestration)
**File:** `dsconv/services/conversion_service.py`
```python
class ConversionService:
    """Main service orchestrating CCI to CIA conversion"""
    
    def __init__(
        self,
        ncsd_reader: NCSDReader,
        ncch_reader: NCCHReader,
        exefs_reader: ExeFSReader,
        cia_writer: CIAWriter,
        decryption_service: DecryptionService | None,
        hash_validator: HashValidator,
        progress_reporter: IProgressReporter
    ):
        # All dependencies injected
        self.ncsd_reader = ncsd_reader
        self.ncch_reader = ncch_reader
        self.exefs_reader = exefs_reader
        self.cia_writer = cia_writer
        self.decryption_service = decryption_service
        self.hash_validator = hash_validator
        self.progress_reporter = progress_reporter
    
    def convert(self, config: ConversionConfig) -> None:
        """Execute conversion from CCI to CIA"""
        
        # Stage 1: Read and validate CCI structure
        self.progress_reporter.report_stage("Reading CCI structure")
        container = self.ncsd_reader.read_container()
        
        # Stage 2: Read NCCH header and determine encryption
        self.progress_reporter.report_stage("Analyzing encryption")
        ncch_header = self.ncch_reader.read_header(...)
        encryption_ctx = self._determine_encryption(ncch_header, config)
        
        # Stage 3: Read and validate extended header
        self.progress_reporter.report_stage("Verifying ExtHeader")
        extheader = self._read_and_validate_extheader(...)
        
        # Stage 4: Extract icon from ExeFS
        self.progress_reporter.report_stage("Getting SMDH")
        icon = self._extract_icon(...)
        
        # Stage 5: Write CIA
        self.progress_reporter.report_stage("Writing CIA")
        self._write_cia(container, extheader, icon, encryption_ctx)
    
    def _determine_encryption(
        self, 
        ncch_header: NCCHHeader, 
        config: ConversionConfig
    ) -> EncryptionContext:
        """Determine encryption type and setup context"""
        ...
    
    def _read_and_validate_extheader(self, ...) -> bytes:
        """Read extended header and validate hash"""
        ...
    
    def _extract_icon(self, ...) -> bytes:
        """Extract SMDH icon from ExeFS"""
        ...
    
    def _write_cia(self, ...) -> None:
        """Write CIA file with all content"""
        ...
```

**Acceptance Criteria:**
- All dependencies injected
- Clear workflow stages
- Error handling
- Integration tests with mocks

#### Task 6.4: Create Service Factory
**File:** `dsconv/services/service_factory.py`
```python
class ServiceFactory:
    """Factory for creating conversion services with dependencies"""
    
    @staticmethod
    def create_conversion_service(
        input_file: str,
        output_file: str,
        config: ConversionConfig
    ) -> ConversionService:
        """Create fully configured conversion service"""
        
        # Open files
        input_handle = open(input_file, 'rb')
        output_handle = open(output_file, 'wb')
        
        # Create readers
        binary_reader = BinaryReader(input_handle)
        ncsd_reader = NCSDReader(binary_reader)
        ncch_reader = NCCHReader(binary_reader)
        exefs_reader = ExeFSReader(binary_reader)
        
        # Create writers
        binary_writer = BinaryWriter(output_handle)
        cia_writer = CIAWriter(binary_writer, ...)
        
        # Create services
        key_derivation = None
        decryption_service = None
        if config.key_provider:
            orig_key = config.key_provider.get_original_ncch_key()
            key_derivation = KeyDerivationService(orig_key)
            decryption_service = DecryptionService(key_derivation, ...)
        
        hash_validator = HashValidator(config.ignore_bad_hashes)
        progress_reporter = ConsoleProgressReporter(config.verbose)
        
        return ConversionService(
            ncsd_reader,
            ncch_reader,
            exefs_reader,
            cia_writer,
            decryption_service,
            hash_validator,
            progress_reporter
        )
```

**Acceptance Criteria:**
- Factory creates all dependencies
- Proper dependency wiring
- Resource management
- Unit tests

---

## Phase 7: Refactor CLI Layer

**Goal:** Clean up command-line interface and entry point  
**Agent Focus:** CLI refactoring  
**Dependencies:** Phase 6  
**Risk:** Low

### Tasks

#### Task 7.1: Create CLI Configuration Mapper
**File:** `dsconv/cli/config_mapper.py`
```python
class CLIConfigMapper:
    """Maps CLI arguments to domain configuration"""
    
    @staticmethod
    def map_to_conversion_config(args: argparse.Namespace) -> ConversionConfig:
        """Convert CLI args to conversion configuration"""
        
        # Determine key provider
        key_provider = CLIConfigMapper._create_key_provider(args)
        
        return ConversionConfig(
            input_file=args.game[0],  # Handle first file
            output_file=...,
            key_provider=key_provider,
            ignore_bad_hashes=args.ignore_bad_hashes,
            ignore_encryption=args.ignore_encryption,
            dev_keys=args.dev_keys,
            verbose=args.verbose
        )
    
    @staticmethod
    def _create_key_provider(args: argparse.Namespace) -> IKeyProvider | None:
        """Create appropriate key provider based on args"""
        
        if args.prod_keys:
            return ProdKeysKeyProvider(args.prod_keys)
        elif args.boot9:
            return Boot9KeyProvider(args.boot9, args.dev_keys)
        else:
            # Auto-detect
            return CLIConfigMapper._auto_detect_key_provider()
    
    @staticmethod
    def _auto_detect_key_provider() -> IKeyProvider | None:
        """Auto-detect available key source"""
        # Try prod.keys first
        for path in ["prod.keys", "~/.3ds/prod.keys"]:
            if os.path.isfile(os.path.expanduser(path)):
                return ProdKeysKeyProvider(path)
        
        # Try boot9 files
        for path in ["boot9.bin", "boot9_prot.bin", ...]:
            if os.path.isfile(os.path.expanduser(path)):
                return Boot9KeyProvider(path)
        
        return None
```

**Acceptance Criteria:**
- Maps args to config
- Auto-detection logic
- No global state
- Unit tests

#### Task 7.2: Refactor Main Entry Point
**File:** `dsconv/__main__.py`
```python
def main() -> None:
    """Main entry point for 3dsconv CLI"""
    
    # Parse arguments
    args = parse_args()
    
    # Handle deprecated options
    if args.use_deprecated:
        print("Note: Deprecated options are being used...")
        return
    
    # Process each game file
    total_files = len(args.game)
    processed_files = 0
    
    for game_file in args.game:
        try:
            # Map to configuration
            config = CLIConfigMapper.map_to_conversion_config(args)
            config.input_file = game_file
            
            # Create service
            service = ServiceFactory.create_conversion_service(
                game_file,
                _determine_output_path(game_file, args.output),
                config
            )
            
            # Execute conversion
            service.convert(config)
            processed_files += 1
            
        except Exception as e:
            print(f"Error converting {game_file}: {e}")
            continue
    
    print(f"Done converting {processed_files} out of {total_files} files.")

def _determine_output_path(input_file: str, output_dir: str) -> str:
    """Determine output CIA file path"""
    rom_name = os.path.basename(os.path.splitext(input_file)[0])
    return os.path.join(output_dir, rom_name + ".cia")
```

**Acceptance Criteria:**
- Clean entry point
- Error handling
- No global state
- Integration tests

---

## Phase 8: Remove Module-Level Execution

**Goal:** Eliminate global state and module-level code execution  
**Agent Focus:** Global state removal  
**Dependencies:** All previous phases  
**Risk:** High (breaking changes)

### Tasks

#### Task 8.1: Move Global Variables to Configuration
**Current:**
```python
# Global state in 3dsconv.py
args = parse_args()
keys_set = False
orig_ncch_key = 0
certchain_dev = b""
```

**Target:**
```python
# No global variables - all in configuration or injected
```

**Actions:**
- Remove all module-level variable assignments
- Ensure all state is in config or service instances
- Update all references to use injected dependencies

**Acceptance Criteria:**
- No module-level execution
- Import doesn't execute code
- All tests still pass

#### Task 8.2: Extract Certificate Chain Loading
**File:** `dsconv/crypto/certchain_provider.py`
```python
class CertChainProvider:
    """Provides certificate chains for CIA signing"""
    
    @staticmethod
    def get_retail_certchain() -> bytes:
        """Get retail certificate chain"""
        import zlib
        import base64
        certchain_retail = b"..."  # Base64 encoded
        return zlib.decompress(base64.b64decode(certchain_retail))
    
    @staticmethod
    def get_dev_certchain(search_paths: list[str] | None = None) -> bytes:
        """Get developer certificate chain"""
        if search_paths is None:
            search_paths = [
                "certchain-dev.bin",
                os.path.expanduser("~/.3ds/certchain-dev.bin")
            ]
        
        for path in search_paths:
            if os.path.isfile(path):
                with open(path, 'rb') as f:
                    certchain = f.read(0xA00)
                    correct_hash = "d5c3d811a7eb87340aa9f4ab1841b6c4"
                    if hashlib.md5(certchain).hexdigest() == correct_hash:
                        return certchain
        
        raise FileNotFoundError("Invalid or missing dev certchain")
```

**Acceptance Criteria:**
- Static methods for cert chains
- No global variables
- Proper error handling
- Unit tests

#### Task 8.3: Clean Up Legacy 3dsconv.py
**Actions:**
- Mark `dsconv/3dsconv.py` as deprecated
- Move any remaining logic to appropriate services
- Update entry point to use new architecture
- Keep file for backward compatibility (just imports)

**File:** `dsconv/3dsconv.py` (legacy compatibility)
```python
"""
Legacy 3dsconv module - DEPRECATED

This module is kept for backward compatibility.
All functionality has been moved to:
- dsconv.services for business logic
- dsconv.models for data structures
- dsconv.io for file operations
- dsconv.crypto for encryption

Use the new modular API or CLI via __main__.py
"""

import warnings
warnings.warn(
    "dsconv.3dsconv is deprecated. Use dsconv.services.ConversionService",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
from dsconv.utils import parse_args, rol, error, show_progress
from dsconv.services import ConversionService

# Old main() for compatibility
def main():
    """Deprecated main - use dsconv.__main__.main()"""
    from dsconv.__main__ import main as new_main
    new_main()
```

**Acceptance Criteria:**
- No breaking changes for CLI users
- Deprecation warnings
- Clean architecture

---

## Phase 9: Integration Testing & Documentation

**Goal:** Comprehensive testing and documentation  
**Agent Focus:** Testing and docs  
**Dependencies:** All phases complete  
**Risk:** Low

### Tasks

#### Task 9.1: Create Integration Test Suite
**File:** `tests/integration/test_full_conversion.py`
```python
class TestFullConversion:
    """Integration tests for complete CCI to CIA conversion"""
    
    def test_convert_decrypted_cci_to_cia(self, tmp_path, minimal_cci_fixture):
        """Test converting a decrypted CCI to CIA"""
        
        input_file = minimal_cci_fixture
        output_file = tmp_path / "output.cia"
        
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True,
            verbose=False
        )
        
        service = ServiceFactory.create_conversion_service(
            str(input_file),
            str(output_file),
            config
        )
        
        service.convert(config)
        
        # Verify CIA was created
        assert output_file.exists()
        
        # Verify CIA structure
        with open(output_file, 'rb') as f:
            magic = f.read(4)
            # Additional validations...
```

**Acceptance Criteria:**
- Tests for each conversion scenario
- End-to-end workflow validation
- Fixture files for testing
- 80%+ coverage

#### Task 9.2: Create Architecture Documentation
**File:** `docs/architecture.md`
```markdown
# 3dsconv Architecture

## Overview
Clean architecture with layered separation of concerns.

## Layers
1. CLI Layer - Command-line interface
2. Application Service - Orchestration
3. Domain Layer - Business logic and models
4. Infrastructure - I/O, crypto, validation

## Key Design Patterns
- Strategy: Encryption handling
- Repository: Key providers
- Builder: CIA construction
- Adapter: PyAES wrapper
- Factory: Service creation

## Dependency Flow
CLI → Service → Domain ← I/O
                 ↓
            Infrastructure
```

**Acceptance Criteria:**
- Complete architecture docs
- Diagrams
- Usage examples

#### Task 9.3: Create Migration Guide
**File:** `docs/migration-guide.md`
```markdown
# Migration Guide: Monolith to Clean Architecture

## For Developers

### Old Code (Monolithic)
```python
# Everything in one file with globals
args = parse_args()
keys_set = False
# ... 700 lines of code
```

### New Code (Modular)
```python
from dsconv.services import ConversionService, ConversionConfig
from dsconv.crypto import ProdKeysKeyProvider

config = ConversionConfig(
    input_file="game.cci",
    output_file="game.cia",
    key_provider=ProdKeysKeyProvider("prod.keys")
)

service = ServiceFactory.create_conversion_service(
    config.input_file,
    config.output_file,
    config
)

service.convert(config)
```

## Benefits
1. Testability - Each component independently testable
2. Maintainability - Clear responsibilities
3. Extensibility - Easy to add features
4. Reusability - Components usable in other contexts
```

**Acceptance Criteria:**
- Migration examples
- Before/after comparisons
- Benefits explanation

---

## Success Metrics

### Code Quality Metrics
- **Test Coverage:** 80% line coverage, 70% branch coverage
- **Cyclomatic Complexity:** < 10 per function (down from 20+)
- **Lines per Module:** < 250 (down from 737)
- **Coupling:** Low (dependency injection)
- **Cohesion:** High (single responsibility)

### Architecture Metrics
- **Layers:** 4 distinct layers (CLI, Service, Domain, Infrastructure)
- **Modules:** ~15 focused modules (from 1 monolith)
- **Classes:** ~20 classes (from 0)
- **Interfaces:** ~5 abstractions for testability
- **Global State:** 0 (from ~10 global variables)

### Testing Metrics
- **Unit Tests:** ~150 tests covering pure logic
- **Integration Tests:** ~30 tests covering workflows
- **E2E Tests:** ~15 tests covering full CLI
- **Test Speed:** < 1 second for unit tests
- **CI/CD Ready:** All tests automated

---

## Risk Mitigation

### High-Risk Areas

1. **Encryption Logic**
   - **Risk:** Breaking encryption/decryption
   - **Mitigation:** 
     - Create test fixtures with known encrypted data
     - Validate against original implementation
     - Comprehensive unit tests for crypto operations

2. **Binary Format Parsing**
   - **Risk:** Incorrect parsing breaking conversion
   - **Mitigation:**
     - Parse minimal test files first
     - Compare output byte-for-byte with original
     - Extensive integration tests

3. **Backward Compatibility**
   - **Risk:** Breaking existing CLI users
   - **Mitigation:**
     - Keep CLI interface identical
     - Maintain legacy module with deprecation
     - Integration tests for CLI

### Medium-Risk Areas

1. **Performance**
   - **Risk:** New architecture slower than monolith
   - **Mitigation:**
     - Profile before/after
     - Optimize hot paths
     - Maintain chunk reading for large files

2. **Error Handling**
   - **Risk:** Different error messages confusing users
   - **Mitigation:**
     - Match original error messages
     - Improve error context
     - Test error scenarios

---

## Task Distribution for Agents

### Quick Wins (1-2 hours each)
- Task 1.1: NCCH Header Model
- Task 1.2: NCSD Container Model
- Task 1.3: CIA Structure Models
- Task 1.4: Encryption State Model
- Task 4.1: Hash Validator
- Task 4.2: Format Validator

### Medium Complexity (3-4 hours each)
- Task 2.1: Crypto Adapter
- Task 2.2: Key Derivation Service
- Task 2.3: Key Provider Service
- Task 3.1: Binary Reader
- Task 3.2: NCSD Reader
- Task 5.1: Binary Writer
- Task 7.1: CLI Config Mapper

### High Complexity (5-8 hours each)
- Task 2.4: Decryption Service
- Task 3.3: NCCH Reader
- Task 3.4: ExeFS Reader
- Task 5.2: CIA Header Builder
- Task 5.3: CIA Writer
- Task 6.3: Conversion Service
- Task 6.4: Service Factory

### Integration Tasks (4-6 hours each)
- Task 7.2: Refactor Main Entry Point
- Task 8.1: Move Global Variables
- Task 8.2: Extract Certificate Chain
- Task 8.3: Clean Up Legacy Code
- Task 9.1: Integration Test Suite

---

## Phased Rollout Strategy

### Phase 1-2: Foundation (Week 1)
- Extract domain models
- Build crypto services
- **Validation:** Models fully tested, no I/O

### Phase 3-5: I/O Layer (Week 2)
- Extract readers and writers
- Build validation services
- **Validation:** Can read CCI and write CIA

### Phase 6: Application Layer (Week 3)
- Build conversion service
- Wire up dependencies
- **Validation:** Full conversion works

### Phase 7-8: CLI & Cleanup (Week 4)
- Refactor CLI
- Remove global state
- **Validation:** CLI identical to original

### Phase 9: Testing & Docs (Week 5)
- Integration tests
- Documentation
- **Validation:** 80% coverage, docs complete

---

## Definition of Done

Each task is considered complete when:
1. ✅ Code written and passing linting (ruff, black)
2. ✅ Unit tests with 100% coverage of new code
3. ✅ Integration tests for interactions
4. ✅ Type hints on all public methods
5. ✅ Docstrings on all classes and methods
6. ✅ No global state introduced
7. ✅ Dependencies injected, not hardcoded
8. ✅ Error handling with specific exceptions
9. ✅ Code review completed (automated)
10. ✅ Backward compatibility maintained

---

## Conclusion

This refactoring plan transforms 3dsconv from an untestable monolith into a maintainable, well-architected application following industry best practices. Each phase builds incrementally on the previous, with clear tasks that can be delegated to agents. The result will be:

- **80%+ test coverage** (from 0%)
- **Clean architecture** with proper separation of concerns
- **SOLID principles** applied throughout
- **Zero global state** (from 10+ global variables)
- **Dependency injection** enabling testability
- **15+ focused modules** (from 1 monolithic file)
- **Backward compatible** CLI interface

The plan balances craft excellence with pragmatic delivery, avoiding over-engineering while establishing a solid foundation for future development.

---

**Plan Version:** 1.0  
**Created:** 2025-11-07  
**Author:** Principal Software Engineer (Martin Fowler Mode)  
**Next Review:** After Phase 3 completion
