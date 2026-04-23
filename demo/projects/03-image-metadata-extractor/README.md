# Demo Project 03: Image Metadata Extractor

**Type:** CLI Tool
**Complexity:** Medium
**Purpose:** Test file processing, EXIF handling, output formatting

## Overview

Extract and display metadata from image files (EXIF, IPTC, XMP) with filtering and export options.

## Features

- [ ] Extract EXIF data from JPEG, PNG, TIFF
- [ ] Extract IPTC metadata
- [ ] Extract XMP metadata
- [ ] Filter by metadata category (camera, location, datetime)
- [ ] Output formats: table, JSON, CSV
- [ ] Batch processing directories
- [ ] GPS coordinates to human-readable location (optional)
- [ ] Remove metadata (privacy mode)

## Tech Stack

- **Language:** Python
- **Dependencies:** `pillow` for image handling, `piexif` or `exif` for EXIF

## CLI Interface

```bash
# Extract all metadata
imgmeta extract photo.jpg

# Filter by category
imgmeta extract photo.jpg --category camera
imgmeta extract photo.jpg --category location

# Output formats
imgmeta extract photo.jpg --format json
imgmeta extract photo.jpg --format csv

# Batch process directory
imgmeta extract ./photos --output report.json

# Remove metadata
imgmeta strip photo.jpg -o clean.jpg
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Extract JPEG EXIF | Camera make, model, date |
| TC02 | Extract PNG metadata | tEXt chunks |
| TC03 | GPS coordinates | Lat/long extracted |
| TC04 | Filter camera | Only camera fields |
| TC05 | Filter location | Only location fields |
| TC06 | JSON output | Valid JSON format |
| TC07 | Batch directory | All images processed |
| TC08 | Strip metadata | No EXIF in output |

## Task Breakdown

1. Create metadata extraction module
2. Implement EXIF reader for JPEG
3. Add PNG tEXt chunk support
4. Implement GPS coordinate extraction
5. Add filtering by category
6. Create output formatters (table, JSON, CSV)
7. Implement batch directory processing
8. Add metadata stripping functionality
9. Write unit tests for extraction
10. Write integration tests
11. Create e2e test report

## Success Criteria

- Extracts all standard EXIF fields
- GPS coordinates displayed correctly
- JSON output is valid
- CSV output is properly formatted
- Batch processes 100+ images
- Stripped images have no EXIF data
