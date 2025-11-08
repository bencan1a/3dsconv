#!/bin/bash
set -e

# Test CCI Generation Script
# Generates a suite of small test CCI files with various encryption configurations
# for testing CCI to CIA conversion tools

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/test-ccis"
RSF_DIR="${SCRIPT_DIR}/rsf-templates"
BUILD_OUTPUT_DIR="${SCRIPT_DIR}/build-outputs"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}3DS Test CCI Generation Script${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check for required tools
echo -e "${YELLOW}Checking for required tools...${NC}"
if ! command -v makerom &> /dev/null; then
    echo "Error: makerom not found in PATH"
    echo "Please install makerom from 3DS development tools"
    exit 1
fi
echo -e "${GREEN}✓ makerom found${NC}\n"

# Step 1: Build hello-world if not present
echo -e "${YELLOW}Step 1: Checking for hello-world build...${NC}"
if [ ! -f "${BUILD_OUTPUT_DIR}/hello-world.3dsx" ]; then
    echo "hello-world.3dsx not found. Building..."
    ./build-with-docker.sh graphics/printing/hello-world
else
    echo -e "${GREEN}✓ hello-world.3dsx exists${NC}"
fi

# Also check for the ELF file
HELLO_WORLD_ELF="${SCRIPT_DIR}/graphics/printing/hello-world/project.elf"
if [ ! -f "${HELLO_WORLD_ELF}" ]; then
    echo "Error: project.elf not found at ${HELLO_WORLD_ELF}"
    echo "Expected location after build. Please check build process."
    exit 1
fi
echo -e "${GREEN}✓ project.elf found${NC}\n"

# Step 2: Create temporary work directory
WORK_DIR="${OUTPUT_DIR}/work"
mkdir -p "${WORK_DIR}"
mkdir -p "${OUTPUT_DIR}"

echo -e "${YELLOW}Step 2: Building NCCH files from ELF...${NC}\n"

# Function to build NCCH
build_ncch() {
    local RSF_FILE="$1"
    local OUTPUT_FILE="$2"
    local EXTRA_FLAGS="$3"
    local DESCRIPTION="$4"

    echo -e "  Building ${BLUE}$(basename ${OUTPUT_FILE})${NC} - ${DESCRIPTION}"
    makerom -f ncch -o "${OUTPUT_FILE}" \
        -rsf "${RSF_FILE}" \
        -elf "${HELLO_WORLD_ELF}" \
        -icon /opt/devkitpro/libctru/default_icon.png \
        -target t \
        ${EXTRA_FLAGS} > /dev/null 2>&1

    local SIZE=$(du -h "${OUTPUT_FILE}" | cut -f1)
    echo -e "    ${GREEN}✓ Created (${SIZE})${NC}"
}

# Build all NCCH files
build_ncch "${RSF_DIR}/basic-nocrypt.rsf" "${WORK_DIR}/nocrypt.cxi" "" "No encryption"
build_ncch "${RSF_DIR}/basic-ncch-original.rsf" "${WORK_DIR}/ncch-original.cxi" "-ncchseckey 0" "Original NCCH (slot 0x2C)"
build_ncch "${RSF_DIR}/basic-ncch-7x.rsf" "${WORK_DIR}/ncch-7x.cxi" "-ncchseckey 1" "7.x crypto (slot 0x25)"
build_ncch "${RSF_DIR}/basic-fixed-key.rsf" "${WORK_DIR}/fixed-key.cxi" "-ncchseckey 0" "Fixed key encryption"
build_ncch "${RSF_DIR}/basic-compressed.rsf" "${WORK_DIR}/compressed.cxi" "" "Compressed ExeFS"
build_ncch "${RSF_DIR}/multi-partition-main.rsf" "${WORK_DIR}/multi-main.cxi" "" "Multi-partition main"
build_ncch "${RSF_DIR}/basic-new3ds.rsf" "${WORK_DIR}/new3ds.cxi" "-ncchseckey 1" "New3DS optimized"

echo ""

# Step 3: Note about multi-partition tests
echo -e "${YELLOW}Step 3: Note on multi-partition tests${NC}"
echo -e "  Multi-partition CCIs require proper RomFS binaries for CFA files."
echo -e "  For simplicity, focusing on single-partition tests with various encryption modes."
echo -e "  This covers the critical conversion scenarios.\n"

# Step 4: Build CCI files with various configurations
echo -e "${YELLOW}Step 4: Building test CCI files...${NC}\n"

# Function to build CCI (via CIA intermediate)
build_cci() {
    local OUTPUT_CCI="$1"
    local CXI_FILE="$2"
    local DESCRIPTION="$3"

    local BASENAME=$(basename "${OUTPUT_CCI}" .cci)
    local TMP_CIA="${WORK_DIR}/${BASENAME}.cia"

    echo -e "  Building ${BLUE}$(basename ${OUTPUT_CCI})${NC}"
    echo -e "    ${DESCRIPTION}"

    # Step 1: CXI -> CIA
    makerom -f cia -o "${TMP_CIA}" -content "${CXI_FILE}:0:0" -target t > /dev/null 2>&1

    # Step 2: CIA -> CCI
    makerom -ciatocci "${TMP_CIA}" -o "${OUTPUT_CCI}" > /dev/null 2>&1

    local SIZE=$(du -h "${OUTPUT_CCI}" | cut -f1)
    echo -e "    ${GREEN}✓ Created (${SIZE})${NC}\n"
}

# Test 1: Unencrypted, single partition
build_cci "${OUTPUT_DIR}/test-01-nocrypt.cci" \
    "${WORK_DIR}/nocrypt.cxi" \
    "Unencrypted, single partition (baseline test)"

# Test 2: Original NCCH encryption (slot 0x2C)
build_cci "${OUTPUT_DIR}/test-02-ncch-original.cci" \
    "${WORK_DIR}/ncch-original.cxi" \
    "Original NCCH encryption (slot 0x2C)"

# Test 3: 7.x crypto (slot 0x25)
build_cci "${OUTPUT_DIR}/test-03-ncch-7x.cci" \
    "${WORK_DIR}/ncch-7x.cxi" \
    "7.x crypto encryption (slot 0x25)"

# Test 4: Fixed key encryption
build_cci "${OUTPUT_DIR}/test-04-fixed-key.cci" \
    "${WORK_DIR}/fixed-key.cxi" \
    "Fixed key encryption"

# Test 5: Compressed ExeFS
build_cci "${OUTPUT_DIR}/test-05-compressed.cci" \
    "${WORK_DIR}/compressed.cxi" \
    "Compressed ExeFS code"

# Test 6: New3DS optimized
build_cci "${OUTPUT_DIR}/test-06-new3ds.cci" \
    "${WORK_DIR}/new3ds.cxi" \
    "New3DS optimized with 7.x crypto"

# Step 5: Copy CIA files to main directory
echo -e "${YELLOW}Step 5: Copying CIA files to output directory...${NC}\n"
cp "${WORK_DIR}"/*.cia "${OUTPUT_DIR}/"
echo -e "${GREEN}✓ CIA files copied${NC}\n"

# Step 6: Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Test CCI Generation Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "Generated test files in: ${OUTPUT_DIR}/"
echo -e "\nTest suite includes:"
echo -e "  • 6 test CCI files + 6 matching CIA files (all with icons in ExeFS)"
echo -e "  • Multiple encryption modes (none, 0x2C, 0x25, fixed)"
echo -e "  • Single-partition configurations"
echo -e "  • Compressed and uncompressed content"
echo -e "  • New3DS optimized build\n"

echo -e "Total output size:"
du -sh "${OUTPUT_DIR}" | awk '{print "  " $1}'

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "  1. Review TEST-MATRIX.md for details on each test file"
echo -e "  2. Test your CCI to CIA converter with these files"
echo -e "  3. Verify encryption detection and proper conversion\n"

echo -e "${GREEN}Done!${NC}"
