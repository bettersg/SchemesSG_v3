# Centralized Logging Implementation

## Problem
The audit log file was much smaller than the terminal output because most Python files in the data pipeline were setting up their own logging configuration that only wrote to the terminal (stdout), not to the audit log file.

## Solution
Created a centralized logging configuration system that ensures all modules write to both terminal and file.

## Implementation

### 1. Created `logging_config.py`
A centralized logging configuration module that provides:
- `setup_logging()`: Sets up logging with both terminal and file output
- `ensure_logging_setup()`: Ensures logging is initialized (useful for modules)
- `get_audit_log_file()`: Returns the current audit log file path
- `is_logging_initialized()`: Checks if logging has been initialized

### 2. Updated All Python Files
Modified the following files to use centralized logging:

#### Core Pipeline Files:
- `run_data_pipeline.py` - Main pipeline runner
- `src/Main_scrape/extract_fields_from_scraped_text.py` - Text extraction with token logging
- `src/Main_scrape/add_scraped_fields_to_fire_store.py` - Field extraction
- `src/Main_scrape/add_town_area_to_fire_store.py` - Town area processing
- `src/Main_scrape/Main_scrape.py` - Web scraping
- `src/create_transformer_models.py` - Model creation
- `src/test_model_artefacts_created.py` - Model testing
- `src/upload_model_artefacts.py` - Model upload

#### Changes Made:
1. **Removed individual logging setup** from each file
2. **Added import** for `ensure_logging_setup` from `logging_config`
3. **Replaced logging setup** with `ensure_logging_setup()` calls
4. **Maintained existing log messages** - no content changes

### 3. Logging Configuration
All modules now use the same logging configuration:
- **Terminal Output**: Colored output with timestamps
- **File Output**: Plain text with timestamps (no colors)
- **Log Rotation**: 10MB file size limit
- **Retention**: 30 days
- **Format**: `YYYY-MM-DD HH:mm:ss | LEVEL | message`

## Benefits

1. **Consistent Logging**: All modules write to the same audit log file
2. **Complete Audit Trail**: No missing logs from any pipeline step
3. **Centralized Configuration**: Easy to modify logging settings in one place
4. **Backward Compatibility**: Existing log messages work without changes
5. **Automatic Setup**: Modules automatically use existing logging if already initialized

## Usage

### Running the Pipeline
The logging is automatically set up when running the main pipeline:
```bash
python src/run_data_pipeline.py dev
```

### Testing Logging
Run the test script to verify all modules are logging correctly:
```bash
python test_centralized_logging.py
```

### Manual Logging Setup
If you need to set up logging manually:
```python
from logging_config import setup_logging
audit_file = setup_logging()
```

## File Structure
```
dataset_workflow/
├── src/
│   ├── logging_config.py          # Centralized logging configuration
│   ├── run_data_pipeline.py       # Main pipeline (sets up logging)
│   └── [other modules]            # All use ensure_logging_setup()
├── test_centralized_logging.py    # Test script
└── audit_log_YYYY-MM-DD_HH:MM:SS.log  # Generated audit log file
```

## Verification
After running the pipeline, check that:
1. Terminal shows colored log output
2. Audit log file contains all the same messages (without colors)
3. All pipeline steps are logged in the audit file
4. Token usage and cost information is included in the audit log

This ensures complete traceability and monitoring of the entire data pipeline process.
