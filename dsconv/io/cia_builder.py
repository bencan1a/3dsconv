"""CIA header builder for constructing CIA archive headers."""

import struct


class CIAHeaderBuilder:
    """Builder for constructing CIA archive headers.

    This builder class provides a fluent interface for constructing CIA headers
    step by step. CIA headers are 0x2020 bytes in size and contain metadata
    about the certificate chain, ticket, TMD, meta, and content sections.

    The builder pattern allows for flexible construction while maintaining
    validation before the final header is built.

    Example:
        >>> builder = CIAHeaderBuilder()
        >>> builder.with_content(0x100000, 0).with_content(0x50000, 1)
        >>> header_bytes = builder.build()

    Reference: 3dbrew.org/wiki/CIA
    """

    def __init__(self):
        """Initialize builder with default values.

        Default values:
        - cert_chain_size: 0xA00 (retail certificate chain)
        - ticket_size: 0x350 (standard ticket size)
        - tmd_size: 0xB04 (base TMD size for 1 content)
        - meta_size: 0x3AC0 (standard meta size)
        - content_size: 0 (to be set via with_content)
        - content_index: 0 (bitmap of present content indices)
        """
        self._cert_chain_size = 0xA00
        self._ticket_size = 0x350
        self._tmd_size = 0xB04  # Base size for 1 content
        self._meta_size = 0x3AC0
        self._content_size = 0
        self._content_index = 0
        self._content_count = 0

    def with_cert_chain_size(self, size: int) -> "CIAHeaderBuilder":
        """Set certificate chain size.

        Args:
            size: Certificate chain size in bytes (default: 0xA00)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If size is negative
        """
        if size < 0:
            raise ValueError(f"cert_chain_size must be non-negative, got {size}")
        self._cert_chain_size = size
        return self

    def with_ticket_size(self, size: int) -> "CIAHeaderBuilder":
        """Set ticket size.

        Args:
            size: Ticket size in bytes (default: 0x350)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If size is negative
        """
        if size < 0:
            raise ValueError(f"ticket_size must be non-negative, got {size}")
        self._ticket_size = size
        return self

    def with_tmd_size(self, size: int) -> "CIAHeaderBuilder":
        """Set TMD (Title Metadata) size.

        The TMD size varies based on the number of contents:
        - Base size: 0xB04 bytes (for 1 content)
        - Each additional content adds 0x30 bytes

        Args:
            size: TMD size in bytes

        Returns:
            Self for method chaining

        Raises:
            ValueError: If size is negative or less than minimum
        """
        if size < 0:
            raise ValueError(f"tmd_size must be non-negative, got {size}")
        if size < 0xB04:
            raise ValueError(f"tmd_size must be at least 0xB04 bytes, got 0x{size:X}")
        self._tmd_size = size
        return self

    def with_meta_size(self, size: int) -> "CIAHeaderBuilder":
        """Set meta section size.

        Args:
            size: Meta size in bytes (default: 0x3AC0)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If size is negative
        """
        if size < 0:
            raise ValueError(f"meta_size must be non-negative, got {size}")
        self._meta_size = size
        return self

    def with_content(self, size: int, index: int) -> "CIAHeaderBuilder":
        """Add content to CIA.

        This method adds a content chunk to the CIA header. The content size
        is accumulated and the content index bitmap is updated.

        Args:
            size: Content size in bytes
            index: Content index (0-7 for first byte of content index bitmap)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If size is negative or index is out of range
        """
        if size < 0:
            raise ValueError(f"content size must be non-negative, got {size}")
        if index < 0 or index > 7:
            raise ValueError(f"content index must be 0-7, got {index}")

        self._content_size += size
        self._content_index |= 0x80 >> index
        self._content_count += 1

        # Update TMD size for additional contents
        # Base TMD is 0xB04 for 1 content, each additional adds 0x30
        if self._content_count > 1:
            self._tmd_size = 0xB04 + (self._content_count - 1) * 0x30

        return self

    def build(self) -> bytes:
        """Build CIA header bytes.

        Constructs the complete 0x2020 byte CIA header with all configured
        values. The header structure is:
        - 0x00-0x04: Archive header size (always 0x2020)
        - 0x04-0x06: Type (always 0 for standard CIA)
        - 0x06-0x08: Version (always 0 for standard)
        - 0x08-0x0C: Certificate chain size
        - 0x0C-0x10: Ticket size
        - 0x10-0x14: TMD size
        - 0x14-0x18: Meta size
        - 0x18-0x20: Content size (8 bytes)
        - 0x20-0x24: Content index (first 4 bytes)
        - 0x24-0x2020: Reserved/padding (rest of content index)

        Returns:
            CIA header as bytes (0x2020 bytes)

        Raises:
            ValueError: If validation fails (e.g., no content added)
        """
        # Validate before building
        if self._content_count == 0:
            raise ValueError("At least one content must be added before building")
        if self._content_size == 0:
            raise ValueError("Total content size must be greater than 0")

        # Build the 0x20 byte header
        header = struct.pack(
            "<IHHIIIIQ",
            0x2020,  # Archive header size
            0,  # Type
            0,  # Version
            self._cert_chain_size,  # Certificate chain size
            self._ticket_size,  # Ticket size
            self._tmd_size,  # TMD size
            self._meta_size,  # Meta size
            self._content_size,  # Content size (8 bytes)
        )

        # Build content index (0x2000 bytes)
        # First byte contains the content bitmap
        content_index = struct.pack("<I", self._content_index)
        # Pad the rest with zeros to make it 0x2000 bytes
        content_index += bytes(0x2000 - 4)

        # Combine header and content index
        return header + content_index

    def reset(self) -> "CIAHeaderBuilder":
        """Reset builder to initial state.

        Returns:
            Self for method chaining
        """
        self._cert_chain_size = 0xA00
        self._ticket_size = 0x350
        self._tmd_size = 0xB04
        self._meta_size = 0x3AC0
        self._content_size = 0
        self._content_index = 0
        self._content_count = 0
        return self
