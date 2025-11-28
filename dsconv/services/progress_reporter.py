"""Progress reporting interfaces and implementations.

This module provides abstractions for reporting conversion progress
to different outputs (console, GUI, etc.) following the dependency
inversion principle.
"""

from abc import ABC, abstractmethod


class IProgressReporter(ABC):
    """Interface for reporting conversion progress.

    This abstract interface allows different implementations to report
    progress in various ways (console, GUI, logging, etc.) without
    changing the conversion service logic.
    """

    @abstractmethod
    def report_stage(self, stage: str) -> None:
        """Report current conversion stage.

        Args:
            stage: Human-readable description of current stage
                   (e.g., "Reading CCI structure", "Writing CIA")
        """
        pass

    @abstractmethod
    def report_progress(self, current: int, total: int) -> None:
        """Report progress within a stage.

        Args:
            current: Current progress value
            total: Total value representing 100% completion
        """
        pass


class ConsoleProgressReporter(IProgressReporter):
    """Reports progress to console output.

    This implementation uses print statements to display progress
    to the console, with optional verbose mode for stage reporting.
    Supports batch mode with file-level progress tracking.
    """

    def __init__(
        self,
        verbose: bool = False,
        batch_mode: bool = False,
        current_file: int = 1,
        total_files: int = 1,
        filename: str = "",
    ):
        """Initialize console progress reporter.

        Args:
            verbose: If True, report stage changes. If False, only show progress bars.
            batch_mode: If True, show file-level batch progress information
            current_file: Current file number (1-indexed) in batch mode
            total_files: Total number of files in batch mode
            filename: Name of current file being processed
        """
        self.verbose = verbose
        self.batch_mode = batch_mode
        self.current_file = current_file
        self.total_files = total_files
        self.filename = filename

    def report_file_start(self, filename: str, current_file: int, total_files: int) -> None:
        """Report the start of processing a file in batch mode.

        Args:
            filename: Name of the file being processed
            current_file: Current file number (1-indexed)
            total_files: Total number of files to process
        """
        self.filename = filename
        self.current_file = current_file
        self.total_files = total_files
        print(f"\n[{current_file}/{total_files}] Processing: {filename}")

    def report_file_success(self, filename: str, output_path: str) -> None:
        """Report successful conversion of a file.

        Args:
            filename: Name of the file that was converted
            output_path: Path to the output CIA file
        """
        print(f"✓ Successfully converted: {filename} -> {output_path}")

    def report_file_error(self, filename: str, error: str) -> None:
        """Report failed conversion of a file.

        Args:
            filename: Name of the file that failed
            error: Error message
        """
        print(f"✗ Failed: {filename}")
        print(f"  Error: {error}")

    def report_stage(self, stage: str) -> None:
        """Report current conversion stage to console.

        Args:
            stage: Human-readable description of current stage
        """
        if self.verbose:
            print(f"\n{stage}...")

    def report_progress(self, current: int, total: int) -> None:
        """Report progress using the show_progress utility.

        Args:
            current: Current progress value
            total: Total value representing 100% completion
        """
        from dsconv.utils import show_progress

        show_progress(current, total)


class MockProgressReporter(IProgressReporter):
    """Mock progress reporter for testing.

    Records all calls to report_stage and report_progress for verification
    in unit tests. Does not produce any actual output.
    """

    def __init__(self):
        """Initialize mock progress reporter."""
        self.stages = []
        self.progress_calls = []
        self.stage_call_count = 0
        self.progress_call_count = 0

    def report_stage(self, stage: str) -> None:
        """Record stage report call.

        Args:
            stage: Human-readable description of current stage
        """
        self.stages.append(stage)
        self.stage_call_count += 1

    def report_progress(self, current: int, total: int) -> None:
        """Record progress report call.

        Args:
            current: Current progress value
            total: Total value representing 100% completion
        """
        self.progress_calls.append((current, total))
        self.progress_call_count += 1

    def reset(self) -> None:
        """Reset all recorded calls.

        Useful for testing multiple operations with the same mock instance.
        """
        self.stages = []
        self.progress_calls = []
        self.stage_call_count = 0
        self.progress_call_count = 0
