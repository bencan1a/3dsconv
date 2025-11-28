#!/usr/bin/env python3
"""
Validation script to compare refactored vs legacy implementations.

Runs the same input through both implementations and compares:
- Output file sizes
- Output file hashes (MD5/SHA256)
- Byte-by-byte comparison
- Execution time comparison

Exit code:
    0: All files match (validation passed)
    1: One or more files differ (validation failed)

Usage:
    python scripts/validate_refactor.py input1.cci input2.cci
    python scripts/validate_refactor.py examples/test-ccis/*.cci -o validation_results/
"""

import hashlib
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def compute_hash(file_path: Path) -> tuple[str, str]:
    """Compute MD5 and SHA256 of a file.

    MD5 is used here for integrity verification and comparison of known output files,
    not for cryptographic security. The script compares both MD5 and SHA256 to validate
    that refactored code produces identical output to the legacy implementation.
    """
    md5 = hashlib.md5()  # codeql[py/weak-cryptographic-algorithm]
    sha256 = hashlib.sha256()

    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            md5.update(chunk)
            sha256.update(chunk)

    return md5.hexdigest(), sha256.hexdigest()


def validate_conversion(input_file: str, output_dir: Path) -> dict[str, Any]:
    """Run both implementations and compare outputs.

    Returns:
        dict with keys: input, legacy, refactored, match, differences
    """
    results: dict[str, Any] = {
        "input": input_file,
        "legacy": {},
        "refactored": {},
        "match": False,
        "differences": []
    }

    # Output paths
    legacy_output = output_dir / "legacy"
    refactored_output = output_dir / "refactored"
    legacy_output.mkdir(parents=True, exist_ok=True)
    refactored_output.mkdir(parents=True, exist_ok=True)

    input_name = Path(input_file).stem
    legacy_cia = legacy_output / f"{input_name}.cia"
    refactored_cia = refactored_output / f"{input_name}.cia"

    # Run legacy implementation
    print(f"  Running LEGACY on {Path(input_file).name}...")
    legacy_start = time.time()
    legacy_cmd = [sys.executable, "-m", "dsconv", "--legacy", input_file, "-o", str(legacy_output)]
    legacy_result = subprocess.run(legacy_cmd, capture_output=True, text=True)
    legacy_time = time.time() - legacy_start

    if legacy_result.returncode != 0:
        results["legacy"]["error"] = legacy_result.stderr
        results["legacy"]["returncode"] = legacy_result.returncode
        return results

    results["legacy"]["execution_time"] = legacy_time

    # Run refactored implementation
    print(f"  Running REFACTORED on {Path(input_file).name}...")
    refactored_start = time.time()
    refactored_cmd = [sys.executable, "-m", "dsconv", input_file, "-o", str(refactored_output)]
    refactored_result = subprocess.run(refactored_cmd, capture_output=True, text=True)
    refactored_time = time.time() - refactored_start

    if refactored_result.returncode != 0:
        results["refactored"]["error"] = refactored_result.stderr
        results["refactored"]["returncode"] = refactored_result.returncode
        return results

    results["refactored"]["execution_time"] = refactored_time

    # Verify outputs exist
    if not legacy_cia.exists():
        results["legacy"]["error"] = "Output file not created"
        return results

    if not refactored_cia.exists():
        results["refactored"]["error"] = "Output file not created"
        return results

    # Compare file sizes
    legacy_size = legacy_cia.stat().st_size
    refactored_size = refactored_cia.stat().st_size
    results["legacy"]["size"] = legacy_size
    results["refactored"]["size"] = refactored_size

    if legacy_size != refactored_size:
        results["differences"].append(
            f"Size mismatch: legacy={legacy_size}, refactored={refactored_size}"
        )

    # Compute and compare hashes
    legacy_md5, legacy_sha256 = compute_hash(legacy_cia)
    refactored_md5, refactored_sha256 = compute_hash(refactored_cia)

    results["legacy"]["md5"] = legacy_md5
    results["legacy"]["sha256"] = legacy_sha256
    results["refactored"]["md5"] = refactored_md5
    results["refactored"]["sha256"] = refactored_sha256

    # Check for byte-identical outputs
    if legacy_sha256 == refactored_sha256:
        results["match"] = True
        print(f"  ✅ MATCH: Outputs are identical (legacy: {legacy_time:.2f}s, refactored: {refactored_time:.2f}s)")
    else:
        results["match"] = False
        print("  ❌ MISMATCH: Outputs differ")

        # Find first difference for debugging
        with open(legacy_cia, 'rb') as f1, open(refactored_cia, 'rb') as f2:
            offset = 0
            while True:
                b1 = f1.read(1)
                b2 = f2.read(1)

                if b1 != b2:
                    results["differences"].append(
                        f"First diff at offset 0x{offset:X}: "
                        f"legacy=0x{b1.hex() if b1 else 'EOF'}, "
                        f"refactored=0x{b2.hex() if b2 else 'EOF'}"
                    )
                    break

                if not b1 and not b2:
                    break

                offset += 1

    return results


def main():
    """Run validation on test files."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate refactored implementation against legacy"
    )
    parser.add_argument("input_files", nargs="+", help="CCI files to test")
    parser.add_argument("-o", "--output", default="validation_output",
                       help="Output directory for validation results")

    args = parser.parse_args()
    output_dir = Path(args.output)

    print("=" * 80)
    print("3dsconv Refactoring Validation")
    print("=" * 80)

    all_results = []
    matches = 0

    for input_file in args.input_files:
        print(f"\nValidating: {input_file}")
        results = validate_conversion(input_file, output_dir)
        all_results.append(results)

        if results["match"]:
            matches += 1

    # Summary
    print("\n" + "=" * 80)
    print(f"VALIDATION SUMMARY: {matches}/{len(args.input_files)} files match")
    print("=" * 80)

    for result in all_results:
        status = "✅ PASS" if result["match"] else "❌ FAIL"
        print(f"{status}: {Path(result['input']).name}")

        if result.get("legacy", {}).get("error"):
            print(f"  Legacy error: {result['legacy']['error']}")
        if result.get("refactored", {}).get("error"):
            print(f"  Refactored error: {result['refactored']['error']}")

        if result["differences"]:
            for diff in result["differences"]:
                print(f"  - {diff}")

        # Performance comparison
        if result.get("legacy", {}).get("execution_time") and result.get("refactored", {}).get("execution_time"):
            legacy_time = result["legacy"]["execution_time"]
            refactored_time = result["refactored"]["execution_time"]
            speedup = legacy_time / refactored_time if refactored_time > 0 else 0
            print(f"  Performance: legacy={legacy_time:.2f}s, refactored={refactored_time:.2f}s (speedup: {speedup:.2f}x)")

    sys.exit(0 if matches == len(args.input_files) else 1)


if __name__ == "__main__":
    main()
