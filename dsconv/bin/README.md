# Bundled Executables

This directory contains platform-specific executables bundled with the package.

## ctrtool

To enable automatic ctrtool support, place the ctrtool executable here:

- **Windows**: `ctrtool.exe`
- **Linux/macOS**: `ctrtool`

Download ctrtool from [Project_CTR releases](https://github.com/3DSGuy/Project_CTR/releases).

### Notes

- Only Windows (ctrtool.exe) is bundled by default
- Linux/macOS users should install ctrtool via package manager or add to PATH
- These executables are searched automatically if `--ctrtool-path` is not specified
