"""
Shared pytest fixtures for 3dsconv tests.

This module provides common fixtures used across unit, integration, and e2e tests.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_args():
    """
    Provides a mock argparse.Namespace object with default values.
    
    This fixture is useful for testing functions that depend on the global `args` object.
    """
    args = MagicMock()
    args.verbose = False
    args.output = ""
    args.boot9 = None
    args.overwrite = False
    args.ignore_bad_hashes = False
    args.ignore_encryption = False
    args.dev_keys = False
    args.game = []
    return args


@pytest.fixture
def clean_output_dir(tmp_path):
    """
    Provides a clean temporary directory for test outputs.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Returns:
        Path: A Path object pointing to a clean temporary directory
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def minimal_cci_decrypted(tmp_path):
    """
    Creates a minimal decrypted CCI file for testing.
    
    Note: This is a placeholder for Phase 2 integration tests.
    The actual binary data will be implemented when needed.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Returns:
        Path: A Path object pointing to the test CCI file
    """
    cci_file = tmp_path / "minimal_decrypted.cci"
    # Placeholder - will be implemented in Phase 2
    cci_file.write_bytes(b"")
    return cci_file


@pytest.fixture
def minimal_cci_encrypted(tmp_path):
    """
    Creates a minimal encrypted CCI file for testing.
    
    Note: This is a placeholder for Phase 2 integration tests.
    The actual binary data will be implemented when needed.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Returns:
        Path: A Path object pointing to the test CCI file
    """
    cci_file = tmp_path / "minimal_encrypted.cci"
    # Placeholder - will be implemented in Phase 2
    cci_file.write_bytes(b"")
    return cci_file


@pytest.fixture
def mock_boot9(tmp_path):
    """
    Creates a mock boot9.bin file for testing.
    
    Note: This is a placeholder for Phase 2 integration tests.
    The actual binary data will be implemented when needed.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Returns:
        Path: A Path object pointing to the mock boot9.bin file
    """
    boot9_file = tmp_path / "boot9.bin"
    # Placeholder - will be implemented in Phase 2
    boot9_file.write_bytes(b"")
    return boot9_file
