# 3DS Test CCI/CIA Files for CCI to CIA Converter Testing

## Overview

This directory contains **6 test CCI files + 6 matching CIA files** generated specifically for testing CCI to CIA conversion tools. All files include icons in ExeFS as required.

## Test Files

| CCI File | CIA File | Size | Encryption | Description |
|----------|----------|------|------------|-------------|
| [test-01-nocrypt.cci](test-01-nocrypt.cci) | [test-01-nocrypt.cia](test-01-nocrypt.cia) | 92-93K | None | Baseline unencrypted test |
| [test-02-ncch-original.cci](test-02-ncch-original.cci) | [test-02-ncch-original.cia](test-02-ncch-original.cia) | 92-93K | Slot 0x2C | Original NCCH encryption (firmware 1.0+) |
| [test-03-ncch-7x.cci](test-03-ncch-7x.cci) | [test-03-ncch-7x.cia](test-03-ncch-7x.cia) | 92-93K | Slot 0x25 | 7.x crypto (firmware 7.0+) |
| [test-04-fixed-key.cci](test-04-fixed-key.cci) | [test-04-fixed-key.cia](test-04-fixed-key.cia) | 92-93K | Fixed key | Debug/development encryption |
| [test-05-compressed.cci](test-05-compressed.cci) | [test-05-compressed.cia](test-05-compressed.cia) | 92-93K | None | LZ77 compressed ExeFS |
| [test-06-new3ds.cci](test-06-new3ds.cci) | [test-06-new3ds.cia](test-06-new3ds.cia) | 92-93K | Slot 0x25 | New3DS optimized build |

**Total size: ~3.3 MB** (well under 50MB requirement)

**Note:** The CIA files are the intermediate files used to generate the CCIs. Both formats contain identical content with the same encryption properties.

## Key Features

✅ All files include **icons in ExeFS** (required for your converter)
✅ Cover the **4 critical encryption modes** for conversion testing
✅ Include both **compressed and uncompressed** content
✅ Small file sizes for fast testing
✅ Based on functional hello-world homebrew application

## Encryption Detection Reference

To test your converter's encryption detection:

### NCCH Flags to Check

**`ncchflag[7]`** (Encryption type):
- Bit `0x04` = NoCrypto (test-01, test-05)
- Bit `0x01` = Fixed key (test-04)
- Bit `0x00` = Standard encryption (test-02, test-03, test-06)

**`ncchflag[3]`** (Crypto method):
- `0x00` = Original NCCH, slot 0x2C (test-02, test-04)
- `0x01` = 7.x crypto, slot 0x25 (test-03, test-06)

## Expected Conversion Behavior

| Test File | Expected Converter Behavior |
|-----------|----------------------------|
| test-01 | Direct conversion, no decryption needed |
| test-02 | Detect slot 0x2C, derive KeyY from NCCH signature, decrypt |
| test-03 | Detect slot 0x25, use enhanced crypto keys, decrypt |
| test-04 | Detect fixed key mode, decrypt with fixed AES key |
| test-05 | Handle LZ77 decompression (or preserve compression) |
| test-06 | Process New3DS flags, use slot 0x25 decryption |

## Generation Details

These files were generated using:
- **Base application**: hello-world homebrew (121KB)
- **Icon**: libctru default_icon.png
- **Build process**: ELF → CXI → CIA → CCI (via makerom)
- **Target**: Test keys (`-target t`)

## Regenerating Test Files

To regenerate this test suite:

```bash
cd /home/devcontainers/3ds-examples
./generate-test-ccis.sh
```

The script will:
1. Build hello-world.elf if needed
2. Create 7 CXI files with different configurations
3. Convert each CXI → CIA → CCI
4. Output to `test-ccis/` directory

## File Structure

```
test-ccis/
├── README.md                     (this file)
├── test-01-nocrypt.cci          (unencrypted)
├── test-02-ncch-original.cci    (slot 0x2C)
├── test-03-ncch-7x.cci          (slot 0x25)
├── test-04-fixed-key.cci        (fixed key)
├── test-05-compressed.cci       (compressed)
├── test-06-new3ds.cci           (New3DS)
└── work/                         (intermediate files)
    ├── *.cxi                     (source CXI files)
    └── *.cia                     (intermediate CIA files)
```

## Testing Checklist

- [ ] Converter detects unencrypted content (test-01)
- [ ] Converter handles slot 0x2C encryption (test-02)
- [ ] Converter handles slot 0x25 encryption (test-03)
- [ ] Converter handles fixed key encryption (test-04)
- [ ] Converter processes compressed content (test-05)
- [ ] Converter handles New3DS flags (test-06)
- [ ] All conversions produce valid CIA files
- [ ] Icons are preserved in output CIA files
- [ ] File sizes are reasonable
- [ ] No errors or warnings during conversion

## Additional Documentation

For detailed information about each test file and conversion scenarios, see:
- [TEST-MATRIX.md](../TEST-MATRIX.md) - Comprehensive test file documentation
- [generate-test-ccis.sh](../generate-test-ccis.sh) - Generation script

## Notes

- These CCIs contain minimal content (hello-world only) to keep files small
- All CCIs use test keys (`-target t`), not production keys
- Multi-partition CCIs were not included due to RomFS complexity
- Focus is on encryption variations, which are the critical test dimension

---

**Generated:** 2025-11-08
**Generator:** generate-test-ccis.sh
**Source:** 3ds-examples/graphics/printing/hello-world
