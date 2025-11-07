"""
Unit tests for prod.keys parsing functionality.

This module tests the functions that parse prod.keys files and extract
the slot0x2CKey needed for decryption.
"""

import os
import tempfile

import pytest

from dsconv.utils import get_slot0x2c_key_from_prod_keys, parse_prod_keys


class TestParseProdKeys:
    """Test suite for the parse_prod_keys() function."""

    def test_parse_simple_prod_keys_file(self):
        """Test parsing a simple prod.keys file with one key."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x2CKey=D4333DFACA8924EA492CC6DA3F617A54\n")
            temp_file = f.name

        try:
            # Act
            result = parse_prod_keys(temp_file)

            # Assert
            assert "slot0x2CKey" in result
            assert result["slot0x2CKey"] == "D4333DFACA8924EA492CC6DA3F617A54"
        finally:
            os.unlink(temp_file)

    def test_parse_prod_keys_with_comments(self):
        """Test that comments are properly ignored."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("# This is a comment\n")
            f.write("slot0x2CKey=D4333DFACA8924EA492CC6DA3F617A54\n")
            f.write("# Another comment\n")
            temp_file = f.name

        try:
            # Act
            result = parse_prod_keys(temp_file)

            # Assert
            assert len(result) == 1
            assert "slot0x2CKey" in result
        finally:
            os.unlink(temp_file)

    def test_parse_prod_keys_with_empty_lines(self):
        """Test that empty lines are properly ignored."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("\n")
            f.write("slot0x2CKey=D4333DFACA8924EA492CC6DA3F617A54\n")
            f.write("\n")
            f.write("slot0x18Key=B6302EA37709B7234B4FE9F424002673\n")
            f.write("\n")
            temp_file = f.name

        try:
            # Act
            result = parse_prod_keys(temp_file)

            # Assert
            assert len(result) == 2
            assert "slot0x2CKey" in result
            assert "slot0x18Key" in result
        finally:
            os.unlink(temp_file)

    def test_parse_multiple_keys(self):
        """Test parsing a prod.keys file with multiple keys."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("generator=4DBA6A5574EE33C1333EFF0092CF2DEC\n")
            f.write("slot0x18Key=B6302EA37709B7234B4FE9F424002673\n")
            f.write("slot0x2CKey=D4333DFACA8924EA492CC6DA3F617A54\n")
            f.write("slot0x3DKey=6AF0398E7C90C7A39F85CDB46FD71A4B\n")
            temp_file = f.name

        try:
            # Act
            result = parse_prod_keys(temp_file)

            # Assert
            assert len(result) == 4
            assert result["generator"] == "4DBA6A5574EE33C1333EFF0092CF2DEC"
            assert result["slot0x18Key"] == "B6302EA37709B7234B4FE9F424002673"
            assert result["slot0x2CKey"] == "D4333DFACA8924EA492CC6DA3F617A54"
            assert result["slot0x3DKey"] == "6AF0398E7C90C7A39F85CDB46FD71A4B"
        finally:
            os.unlink(temp_file)

    def test_parse_prod_keys_with_whitespace(self):
        """Test that whitespace around keys and values is handled correctly."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("  slot0x2CKey  =  D4333DFACA8924EA492CC6DA3F617A54  \n")
            temp_file = f.name

        try:
            # Act
            result = parse_prod_keys(temp_file)

            # Assert
            assert "slot0x2CKey" in result
            assert result["slot0x2CKey"] == "D4333DFACA8924EA492CC6DA3F617A54"
        finally:
            os.unlink(temp_file)

    def test_parse_prod_keys_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        # Arrange
        # Create a path that definitely doesn't exist without relying on /tmp
        import uuid

        non_existent_file = f"this_file_does_not_exist_{uuid.uuid4()}.keys"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            parse_prod_keys(non_existent_file)

    def test_parse_prod_keys_invalid_format_no_equals(self):
        """Test that ValueError is raised for lines without '=' separator."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x2CKey D4333DFACA8924EA492CC6DA3F617A54\n")
            temp_file = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="expected 'key=value'"):
                parse_prod_keys(temp_file)
        finally:
            os.unlink(temp_file)

    def test_parse_prod_keys_empty_value(self):
        """Test that ValueError is raised for empty values."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x2CKey=\n")
            temp_file = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="Empty value"):
                parse_prod_keys(temp_file)
        finally:
            os.unlink(temp_file)

    def test_parse_prod_keys_invalid_hex_value(self):
        """Test that ValueError is raised for non-hexadecimal values."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x2CKey=ZZZZZZZZZZZZZZZZ\n")
            temp_file = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid hexadecimal value"):
                parse_prod_keys(temp_file)
        finally:
            os.unlink(temp_file)

    def test_parse_prod_keys_duplicate_keys(self):
        """Test that duplicate keys result in the last value being used."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x2CKey=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n")
            f.write("slot0x2CKey=D4333DFACA8924EA492CC6DA3F617A54\n")
            temp_file = f.name

        try:
            # Act
            result = parse_prod_keys(temp_file)

            # Assert
            # The last value should be used
            assert result["slot0x2CKey"] == "D4333DFACA8924EA492CC6DA3F617A54"
        finally:
            os.unlink(temp_file)


class TestGetSlot0x2cKeyFromProdKeys:
    """Test suite for the get_slot0x2c_key_from_prod_keys() function."""

    def test_get_slot0x2c_key_success(self):
        """Test successful extraction of slot0x2CKey."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x2CKey=D4333DFACA8924EA492CC6DA3F617A54\n")
            temp_file = f.name

        try:
            # Act
            result = get_slot0x2c_key_from_prod_keys(temp_file)

            # Assert
            # The hex value should be converted to an integer
            expected = 0xD4333DFACA8924EA492CC6DA3F617A54
            assert result == expected
            assert isinstance(result, int)
        finally:
            os.unlink(temp_file)

    def test_get_slot0x2c_key_among_multiple_keys(self):
        """Test extraction when slot0x2CKey is among multiple keys."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("generator=4DBA6A5574EE33C1333EFF0092CF2DEC\n")
            f.write("slot0x18Key=B6302EA37709B7234B4FE9F424002673\n")
            f.write("slot0x2CKey=D4333DFACA8924EA492CC6DA3F617A54\n")
            f.write("slot0x3DKey=6AF0398E7C90C7A39F85CDB46FD71A4B\n")
            temp_file = f.name

        try:
            # Act
            result = get_slot0x2c_key_from_prod_keys(temp_file)

            # Assert
            expected = 0xD4333DFACA8924EA492CC6DA3F617A54
            assert result == expected
        finally:
            os.unlink(temp_file)

    def test_get_slot0x2c_key_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        # Arrange
        # Create a path that definitely doesn't exist without relying on /tmp
        import uuid

        non_existent_file = f"this_file_does_not_exist_{uuid.uuid4()}.keys"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            get_slot0x2c_key_from_prod_keys(non_existent_file)

    def test_get_slot0x2c_key_missing_key(self):
        """Test that KeyError is raised when slot0x2CKey is not in the file."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x18Key=B6302EA37709B7234B4FE9F424002673\n")
            f.write("slot0x3DKey=6AF0398E7C90C7A39F85CDB46FD71A4B\n")
            temp_file = f.name

        try:
            # Act & Assert
            with pytest.raises(KeyError, match="slot0x2CKey not found"):
                get_slot0x2c_key_from_prod_keys(temp_file)
        finally:
            os.unlink(temp_file)

    def test_get_slot0x2c_key_with_comments_and_whitespace(self):
        """Test extraction with comments and whitespace in the file."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("# Production keys file\n")
            f.write("\n")
            f.write("  slot0x2CKey  =  D4333DFACA8924EA492CC6DA3F617A54  \n")
            f.write("\n")
            f.write("# End of file\n")
            temp_file = f.name

        try:
            # Act
            result = get_slot0x2c_key_from_prod_keys(temp_file)

            # Assert
            expected = 0xD4333DFACA8924EA492CC6DA3F617A54
            assert result == expected
        finally:
            os.unlink(temp_file)

    def test_get_slot0x2c_key_lowercase_hex(self):
        """Test that lowercase hex values are correctly parsed."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x2CKey=d4333dfaca8924ea492cc6da3f617a54\n")
            temp_file = f.name

        try:
            # Act
            result = get_slot0x2c_key_from_prod_keys(temp_file)

            # Assert
            # Lowercase and uppercase hex should produce the same integer
            expected = 0xD4333DFACA8924EA492CC6DA3F617A54
            assert result == expected
        finally:
            os.unlink(temp_file)

    def test_get_slot0x2c_key_mixed_case_hex(self):
        """Test that mixed case hex values are correctly parsed."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".keys") as f:
            f.write("slot0x2CKey=D4333dfAcA8924EA492cc6da3f617A54\n")
            temp_file = f.name

        try:
            # Act
            result = get_slot0x2c_key_from_prod_keys(temp_file)

            # Assert
            expected = 0xD4333DFACA8924EA492CC6DA3F617A54
            assert result == expected
        finally:
            os.unlink(temp_file)
