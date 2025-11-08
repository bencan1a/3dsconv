"""Tests for CIA header builder."""

import struct

import pytest

from dsconv.io.cia_builder import CIAHeaderBuilder


class TestCIAHeaderBuilderInit:
    """Tests for CIAHeaderBuilder initialization."""

    def test_init_sets_default_values(self):
        """Test initialization sets correct default values."""
        # Arrange & Act
        builder = CIAHeaderBuilder()

        # Assert
        assert builder._cert_chain_size == 0xA00
        assert builder._ticket_size == 0x350
        assert builder._tmd_size == 0xB04
        assert builder._meta_size == 0x3AC0
        assert builder._content_size == 0
        assert builder._content_index == 0
        assert builder._content_count == 0


class TestCIAHeaderBuilderWithMethods:
    """Tests for CIAHeaderBuilder with_* configuration methods."""

    def test_with_cert_chain_size_sets_value(self):
        """Test with_cert_chain_size sets the certificate chain size."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        result = builder.with_cert_chain_size(0x1000)

        # Assert
        assert builder._cert_chain_size == 0x1000
        assert result is builder  # Fluent interface

    def test_with_cert_chain_size_with_negative_value_raises_error(self):
        """Test with_cert_chain_size with negative value raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="cert_chain_size must be non-negative"):
            builder.with_cert_chain_size(-1)

    def test_with_ticket_size_sets_value(self):
        """Test with_ticket_size sets the ticket size."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        result = builder.with_ticket_size(0x400)

        # Assert
        assert builder._ticket_size == 0x400
        assert result is builder  # Fluent interface

    def test_with_ticket_size_with_negative_value_raises_error(self):
        """Test with_ticket_size with negative value raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="ticket_size must be non-negative"):
            builder.with_ticket_size(-1)

    def test_with_tmd_size_sets_value(self):
        """Test with_tmd_size sets the TMD size."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        result = builder.with_tmd_size(0xC00)

        # Assert
        assert builder._tmd_size == 0xC00
        assert result is builder  # Fluent interface

    def test_with_tmd_size_with_negative_value_raises_error(self):
        """Test with_tmd_size with negative value raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="tmd_size must be non-negative"):
            builder.with_tmd_size(-1)

    def test_with_tmd_size_below_minimum_raises_error(self):
        """Test with_tmd_size below minimum raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="tmd_size must be at least 0xB04"):
            builder.with_tmd_size(0x100)

    def test_with_meta_size_sets_value(self):
        """Test with_meta_size sets the meta size."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        result = builder.with_meta_size(0x5000)

        # Assert
        assert builder._meta_size == 0x5000
        assert result is builder  # Fluent interface

    def test_with_meta_size_with_negative_value_raises_error(self):
        """Test with_meta_size with negative value raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="meta_size must be non-negative"):
            builder.with_meta_size(-1)

    def test_with_content_adds_single_content(self):
        """Test with_content adds a single content."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        result = builder.with_content(size=0x100000, index=0)

        # Assert
        assert builder._content_size == 0x100000
        assert builder._content_index == 0x80  # Bit 7 set
        assert builder._content_count == 1
        assert builder._tmd_size == 0xB04  # Base TMD size for 1 content
        assert result is builder  # Fluent interface

    def test_with_content_adds_multiple_contents(self):
        """Test with_content adds multiple contents."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        builder.with_content(size=0x100000, index=0).with_content(size=0x50000, index=1)

        # Assert
        assert builder._content_size == 0x150000
        assert builder._content_index == 0xC0  # Bits 7 and 6 set (0x80 | 0x40)
        assert builder._content_count == 2
        assert builder._tmd_size == 0xB34  # Base + 1 * 0x30

    def test_with_content_adds_three_contents(self):
        """Test with_content adds three contents."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        builder.with_content(0x100000, 0).with_content(0x50000, 1).with_content(0x20000, 2)

        # Assert
        assert builder._content_size == 0x170000
        assert builder._content_index == 0xE0  # Bits 7, 6, 5 set
        assert builder._content_count == 3
        assert builder._tmd_size == 0xB64  # Base + 2 * 0x30

    def test_with_content_with_negative_size_raises_error(self):
        """Test with_content with negative size raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="content size must be non-negative"):
            builder.with_content(-1, 0)

    def test_with_content_with_negative_index_raises_error(self):
        """Test with_content with negative index raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="content index must be 0-7"):
            builder.with_content(0x100000, -1)

    def test_with_content_with_index_too_large_raises_error(self):
        """Test with_content with index > 7 raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="content index must be 0-7"):
            builder.with_content(0x100000, 8)

    @pytest.mark.parametrize(
        "index,expected_bit",
        [
            (0, 0x80),  # Bit 7
            (1, 0x40),  # Bit 6
            (2, 0x20),  # Bit 5
            (3, 0x10),  # Bit 4
            (4, 0x08),  # Bit 3
            (5, 0x04),  # Bit 2
            (6, 0x02),  # Bit 1
            (7, 0x01),  # Bit 0
        ],
    )
    def test_with_content_sets_correct_bit_for_index(self, index, expected_bit):
        """Test with_content sets correct bit in content index for each index."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        builder.with_content(0x100000, index)

        # Assert
        assert builder._content_index == expected_bit

    def test_fluent_interface_chain(self):
        """Test fluent interface allows method chaining."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        result = (
            builder.with_cert_chain_size(0x1000)
            .with_ticket_size(0x400)
            .with_tmd_size(0xC00)
            .with_meta_size(0x5000)
            .with_content(0x100000, 0)
            .with_content(0x50000, 1)
        )

        # Assert
        assert result is builder
        assert builder._cert_chain_size == 0x1000
        assert builder._ticket_size == 0x400
        assert builder._tmd_size == 0xB34  # Overridden by with_content
        assert builder._meta_size == 0x5000
        assert builder._content_size == 0x150000
        assert builder._content_count == 2


class TestCIAHeaderBuilderBuild:
    """Tests for CIAHeaderBuilder build method."""

    def test_build_with_no_content_raises_error(self):
        """Test build without adding content raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act & Assert
        with pytest.raises(ValueError, match="At least one content must be added"):
            builder.build()

    def test_build_with_zero_size_content_raises_error(self):
        """Test build with zero total content size raises ValueError."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_content(0, 0)

        # Act & Assert
        with pytest.raises(ValueError, match="Total content size must be greater than 0"):
            builder.build()

    def test_build_returns_correct_size(self):
        """Test build returns exactly 0x2020 bytes."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_content(0x100000, 0)

        # Act
        result = builder.build()

        # Assert
        assert len(result) == 0x2020

    def test_build_with_single_content(self):
        """Test build with single content creates valid header."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_content(0x100000, 0)

        # Act
        result = builder.build()

        # Assert - Parse the header
        header_size, type_, version = struct.unpack("<IHH", result[0x00:0x08])
        cert_size, ticket_size, tmd_size, meta_size = struct.unpack("<IIII", result[0x08:0x18])
        (content_size,) = struct.unpack("<Q", result[0x18:0x20])
        (content_index,) = struct.unpack("<I", result[0x20:0x24])

        assert header_size == 0x2020
        assert type_ == 0
        assert version == 0
        assert cert_size == 0xA00
        assert ticket_size == 0x350
        assert tmd_size == 0xB04
        assert meta_size == 0x3AC0
        assert content_size == 0x100000
        assert content_index == 0x80  # Bit 7 set

    def test_build_with_multiple_contents(self):
        """Test build with multiple contents creates valid header."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_content(0x100000, 0).with_content(0x50000, 1)

        # Act
        result = builder.build()

        # Assert
        (content_size,) = struct.unpack("<Q", result[0x18:0x20])
        (content_index,) = struct.unpack("<I", result[0x20:0x24])
        (tmd_size,) = struct.unpack("<I", result[0x10:0x14])

        assert content_size == 0x150000
        assert content_index == 0xC0  # Bits 7 and 6 set
        assert tmd_size == 0xB34  # Base + 1 * 0x30

    def test_build_with_custom_sizes(self):
        """Test build with custom sizes."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_cert_chain_size(0x1000).with_ticket_size(0x400).with_meta_size(
            0x5000
        ).with_content(0x200000, 0)

        # Act
        result = builder.build()

        # Assert
        cert_size, ticket_size, tmd_size, meta_size = struct.unpack("<IIII", result[0x08:0x18])
        (content_size,) = struct.unpack("<Q", result[0x18:0x20])

        assert cert_size == 0x1000
        assert ticket_size == 0x400
        assert meta_size == 0x5000
        assert content_size == 0x200000

    def test_build_content_index_padding(self):
        """Test build pads content index to 0x2000 bytes."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_content(0x100000, 0)

        # Act
        result = builder.build()

        # Assert - Check that padding is all zeros
        content_index_section = result[0x20:0x2020]
        assert len(content_index_section) == 0x2000
        # First 4 bytes contain the index bitmap
        assert content_index_section[0] == 0x80
        assert content_index_section[1] == 0
        assert content_index_section[2] == 0
        assert content_index_section[3] == 0
        # Rest should be all zeros
        assert content_index_section[4:] == bytes(0x2000 - 4)

    def test_build_header_structure(self):
        """Test build creates correct header structure."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_content(0x100000, 0)

        # Act
        result = builder.build()

        # Assert - Verify each field
        # 0x00-0x04: Archive header size
        assert result[0x00:0x04] == struct.pack("<I", 0x2020)
        # 0x04-0x06: Type
        assert result[0x04:0x06] == struct.pack("<H", 0)
        # 0x06-0x08: Version
        assert result[0x06:0x08] == struct.pack("<H", 0)
        # 0x08-0x0C: Cert chain size
        assert result[0x08:0x0C] == struct.pack("<I", 0xA00)
        # 0x0C-0x10: Ticket size
        assert result[0x0C:0x10] == struct.pack("<I", 0x350)
        # 0x10-0x14: TMD size
        assert result[0x10:0x14] == struct.pack("<I", 0xB04)
        # 0x14-0x18: Meta size
        assert result[0x14:0x18] == struct.pack("<I", 0x3AC0)
        # 0x18-0x20: Content size
        assert result[0x18:0x20] == struct.pack("<Q", 0x100000)

    @pytest.mark.parametrize(
        "contents,expected_index,expected_tmd",
        [
            ([(0x100000, 0)], 0x80, 0xB04),
            ([(0x100000, 0), (0x50000, 1)], 0xC0, 0xB34),
            ([(0x100000, 0), (0x50000, 1), (0x20000, 2)], 0xE0, 0xB64),
            ([(0x100000, 7)], 0x01, 0xB04),  # Last bit
            ([(0x100000, 0), (0x50000, 7)], 0x81, 0xB34),  # First and last
        ],
    )
    def test_build_with_various_content_configurations(
        self, contents, expected_index, expected_tmd
    ):
        """Test build with various content configurations."""
        # Arrange
        builder = CIAHeaderBuilder()
        for size, index in contents:
            builder.with_content(size, index)

        # Act
        result = builder.build()

        # Assert
        (content_index,) = struct.unpack("<I", result[0x20:0x24])
        (tmd_size,) = struct.unpack("<I", result[0x10:0x14])
        assert content_index == expected_index
        assert tmd_size == expected_tmd


class TestCIAHeaderBuilderReset:
    """Tests for CIAHeaderBuilder reset method."""

    def test_reset_restores_default_values(self):
        """Test reset restores all default values."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_cert_chain_size(0x1000).with_ticket_size(0x400).with_content(0x100000, 0)

        # Act
        result = builder.reset()

        # Assert
        assert builder._cert_chain_size == 0xA00
        assert builder._ticket_size == 0x350
        assert builder._tmd_size == 0xB04
        assert builder._meta_size == 0x3AC0
        assert builder._content_size == 0
        assert builder._content_index == 0
        assert builder._content_count == 0
        assert result is builder  # Fluent interface

    def test_reset_allows_building_new_header(self):
        """Test reset allows building a new header after previous build."""
        # Arrange
        builder = CIAHeaderBuilder()
        builder.with_content(0x100000, 0)
        first_header = builder.build()

        # Act
        builder.reset()
        builder.with_content(0x200000, 1)
        second_header = builder.build()

        # Assert
        assert len(first_header) == 0x2020
        assert len(second_header) == 0x2020
        assert first_header != second_header

        # Verify first header
        (first_content_size,) = struct.unpack("<Q", first_header[0x18:0x20])
        (first_index,) = struct.unpack("<I", first_header[0x20:0x24])
        assert first_content_size == 0x100000
        assert first_index == 0x80

        # Verify second header
        (second_content_size,) = struct.unpack("<Q", second_header[0x18:0x20])
        (second_index,) = struct.unpack("<I", second_header[0x20:0x24])
        assert second_content_size == 0x200000
        assert second_index == 0x40


class TestCIAHeaderBuilderIntegration:
    """Integration tests for CIAHeaderBuilder."""

    def test_typical_usage_scenario(self):
        """Test typical usage scenario with game executable and manual."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act - Build CIA with game executable and manual
        header = (
            builder.with_content(size=0x500000, index=0)  # Game executable
            .with_content(size=0x100000, index=1)  # Manual
            .build()
        )

        # Assert
        assert len(header) == 0x2020
        (content_size,) = struct.unpack("<Q", header[0x18:0x20])
        (content_index,) = struct.unpack("<I", header[0x20:0x24])
        (tmd_size,) = struct.unpack("<I", header[0x10:0x14])

        assert content_size == 0x600000  # Total of both contents
        assert content_index == 0xC0  # Bits 7 and 6 set
        assert tmd_size == 0xB34  # Base + 1 * 0x30

    def test_builder_reuse_with_reset(self):
        """Test builder can be reused with reset."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act - Build first CIA
        header1 = builder.with_content(0x100000, 0).build()

        # Build second CIA after reset
        header2 = builder.reset().with_content(0x200000, 1).build()

        # Assert
        assert len(header1) == 0x2020
        assert len(header2) == 0x2020
        assert header1 != header2

    def test_complex_configuration(self):
        """Test complex configuration with all custom values."""
        # Arrange
        builder = CIAHeaderBuilder()

        # Act
        header = (
            builder.with_cert_chain_size(0xB00)
            .with_ticket_size(0x400)
            .with_tmd_size(0xB64)  # Will be overridden by with_content
            .with_meta_size(0x4000)
            .with_content(0x800000, 0)
            .with_content(0x200000, 1)
            .with_content(0x100000, 2)
            .build()
        )

        # Assert
        cert_size, ticket_size, tmd_size, meta_size = struct.unpack("<IIII", header[0x08:0x18])
        (content_size,) = struct.unpack("<Q", header[0x18:0x20])
        (content_index,) = struct.unpack("<I", header[0x20:0x24])

        assert cert_size == 0xB00
        assert ticket_size == 0x400
        assert tmd_size == 0xB64  # Base + 2 * 0x30
        assert meta_size == 0x4000
        assert content_size == 0xB00000  # Sum of all contents
        assert content_index == 0xE0  # Bits 7, 6, 5 set
