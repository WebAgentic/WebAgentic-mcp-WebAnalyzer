# Data Directory

This directory contains data files and storage for the MCP WebAnalyzer.

## Contents

- `cache/` - Cached web analysis results
- `reports/` - Generated analysis reports
- `exports/` - Exported data files
- `temp/` - Temporary processing files

## Structure

```
data/
├── cache/          # Cached analysis results
├── reports/        # Generated reports
├── exports/        # Exported data
└── temp/          # Temporary files
```

## Usage

This directory is automatically created and managed by the application.
Data files are stored here for persistence and caching purposes.

## Cleanup

Temporary files are automatically cleaned up after processing.
Cache files follow TTL (Time To Live) policies.