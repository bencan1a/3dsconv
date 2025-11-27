"""
Unit tests for batch file discovery in 3dsconv.

This module tests the discover_cci_files() function which is used
to find CCI files for batch conversion mode.
"""

import os

import pytest

from dsconv.utils import discover_cci_files


class TestDiscoverCciFiles:
    """Test suite for the discover_cci_files() function."""

    def test_discover_finds_cci_files(self, tmp_path):
        """Test that .cci files are discovered."""
        # Arrange
        cci_file = tmp_path / "game1.cci"
        cci_file.write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 1
        assert result[0] == str(cci_file)

    def test_discover_finds_3ds_files(self, tmp_path):
        """Test that .3ds files are discovered."""
        # Arrange
        ds_file = tmp_path / "game2.3ds"
        ds_file.write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 1
        assert result[0] == str(ds_file)

    def test_discover_finds_both_extensions(self, tmp_path):
        """Test that both .cci and .3ds files are discovered."""
        # Arrange
        cci_file = tmp_path / "game1.cci"
        cci_file.write_bytes(b"test")
        ds_file = tmp_path / "game2.3ds"
        ds_file.write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 2
        assert str(cci_file) in result
        assert str(ds_file) in result

    def test_discover_case_insensitive_extensions(self, tmp_path):
        """Test that file extension matching is case-insensitive."""
        # Arrange
        files = [
            tmp_path / "game1.CCI",
            tmp_path / "game2.Cci",
            tmp_path / "game3.3DS",
            tmp_path / "game4.3Ds",
        ]
        for f in files:
            f.write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 4

    def test_discover_returns_sorted_results(self, tmp_path):
        """Test that results are returned in sorted order."""
        # Arrange
        files = ["zebra.cci", "alpha.cci", "beta.3ds", "gamma.cci"]
        for name in files:
            (tmp_path / name).write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        basenames = [os.path.basename(f) for f in result]
        assert basenames == sorted(basenames)

    def test_discover_returns_full_paths(self, tmp_path):
        """Test that full absolute paths are returned."""
        # Arrange
        cci_file = tmp_path / "game.cci"
        cci_file.write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 1
        assert os.path.isabs(result[0])
        assert result[0] == str(cci_file)

    def test_discover_ignores_other_extensions(self, tmp_path):
        """Test that non-CCI files are ignored."""
        # Arrange
        (tmp_path / "game.cci").write_bytes(b"test")
        (tmp_path / "readme.txt").write_bytes(b"test")
        (tmp_path / "data.bin").write_bytes(b"test")
        (tmp_path / "output.cia").write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 1
        assert result[0].endswith(".cci")

    def test_discover_ignores_directories_with_cci_extension(self, tmp_path):
        """Test that directories with .cci in their name are ignored."""
        # Arrange
        cci_dir = tmp_path / "subdir.cci"
        cci_dir.mkdir()
        (tmp_path / "game.cci").write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 1
        assert "subdir.cci" not in result[0]

    def test_discover_does_not_recurse_subdirectories(self, tmp_path):
        """Test that subdirectories are not searched."""
        # Arrange
        (tmp_path / "game1.cci").write_bytes(b"test")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "game2.cci").write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 1
        assert "game1.cci" in result[0]

    def test_discover_returns_empty_list_for_empty_folder(self, tmp_path):
        """Test that empty folder returns empty list."""
        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert result == []

    def test_discover_returns_empty_list_for_folder_with_no_cci_files(self, tmp_path):
        """Test that folder with no CCI files returns empty list."""
        # Arrange
        (tmp_path / "readme.txt").write_bytes(b"test")
        (tmp_path / "data.bin").write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert result == []

    def test_discover_raises_on_nonexistent_folder(self):
        """Test that FileNotFoundError is raised for nonexistent folder."""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Batch folder not found"):
            discover_cci_files("/nonexistent/folder/path")

    def test_discover_raises_on_file_not_directory(self, tmp_path):
        """Test that NotADirectoryError is raised when path is a file."""
        # Arrange
        file_path = tmp_path / "some_file.txt"
        file_path.write_bytes(b"test")

        # Act & Assert
        with pytest.raises(NotADirectoryError, match="Batch path is not a directory"):
            discover_cci_files(str(file_path))

    def test_discover_handles_special_characters_in_filenames(self, tmp_path):
        """Test that files with special characters in names are handled."""
        # Arrange
        special_names = [
            "game with spaces.cci",
            "game-with-dashes.3ds",
            "game_with_underscores.cci",
            "game.version.1.0.cci",
        ]
        for name in special_names:
            (tmp_path / name).write_bytes(b"test")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 4

    def test_discover_handles_unicode_filenames(self, tmp_path):
        """Test that unicode filenames are handled correctly."""
        # Arrange
        unicode_names = ["ゲーム.cci", "游戏.3ds"]
        for name in unicode_names:
            try:
                (tmp_path / name).write_bytes(b"test")
            except OSError:
                pytest.skip("Filesystem does not support unicode filenames")

        # Act
        result = discover_cci_files(str(tmp_path))

        # Assert
        assert len(result) == 2
