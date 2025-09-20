# Token Usage and Cost Logging Implementation

## Overview
Added comprehensive token usage and cost tracking to the `extract_fields_from_scraped_text.py` file to monitor LLM API calls and their associated costs.

## Changes Made

### 1. Added Dependencies
- `loguru` for structured logging
- `datetime` for timestamp tracking

### 2. Created TokenCostTracker Class
A utility class that provides:
- **Token Estimation**: Rough estimation of token count based on text length (1 token ≈ 4 characters)
- **Cost Calculation**: Calculates costs based on Azure OpenAI pricing
- **Usage Logging**: Logs detailed information about each LLM call

#### Pricing Configuration
```python
PRICING = {
    "gpt-4.1": {
        "input": 0.40,  # $0.40 per 1000 input tokens
        "output": 1.60  # $1.60 per 1000 output tokens
    },
    "gpt-4.1-mini": {
        "input": 0.30,  # $0.30 per 1000 input tokens
        "output": 1.20  # $1.20 per 1000 output tokens
    },
    "gpt-5": {
        "input": 0.50,  # $0.50 per 1000 input tokens
        "output": 2.00  # $2.00 per 1000 output tokens
    },
    "gpt-5-nano": {
        "input": 0.40,  # $0.40 per 1000 input tokens
        "output": 1.60  # $1.60 per 1000 output tokens
    },
    # Legacy models for backward compatibility
    "gpt-4": {
        "input": 0.03,  # $0.03 per 1000 input tokens
        "output": 0.06  # $0.06 per 1000 output tokens
    },
    "gpt-4-32k": {
        "input": 0.06,  # $0.06 per 1000 input tokens
        "output": 0.12  # $0.12 per 1000 output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.0015,  # $0.0015 per 1000 input tokens
        "output": 0.002   # $0.002 per 1000 output tokens
    }
}
```

### 3. Enhanced Methods with Logging

#### `reformat_llm_description()` Method
- Logs input tokens before making the LLM call
- Logs output tokens after receiving the response
- Tracks cost for the formatting operation

#### `extract_text()` Method
- **Single Text Processing**: Logs token usage for non-chunked text
- **Chunked Text Processing**:
  - Logs token usage for each chunk individually
  - Provides a summary of total tokens and cost across all chunks
  - Tracks the number of chunks processed

### 4. Logging Format
Each log entry includes:
- **Operation**: Description of the LLM operation
- **Model**: Name of the model used
- **Input Tokens**: Number of input tokens
- **Output Tokens**: Number of output tokens
- **Total Tokens**: Sum of input and output tokens
- **Estimated Cost**: Calculated cost in USD
- **Timestamp**: When the operation occurred

### 5. Example Log Output
```
2024-01-15 10:30:45 | INFO | LLM Usage - extract_text_single | Model: gpt-4.1-mini | Input tokens: 1250 | Output tokens: 300 | Total tokens: 1550 | Estimated cost: $0.735000
2024-01-15 10:30:46 | INFO | LLM Usage - reformat_llm_description | Model: gpt-4.1-mini | Input tokens: 200 | Output tokens: 150 | Total tokens: 350 | Estimated cost: $0.240000
```

## Usage

### Running with Logging
The logging is automatically enabled when using the `TextExtract` class. No additional configuration is required.

### Test Script
A test script `test_token_logging.py` is provided to demonstrate the functionality:

```bash
cd dataset_workflow
python test_token_logging.py
```

### Log Files
- Logs are written to both console (with colors) and file
- Log files are named with timestamp: `token_usage_log_YYYY-MM-DD_HH:MM:SS.log`
- Log files rotate at 10MB and are retained for 30 days

## Benefits

1. **Cost Monitoring**: Track spending on LLM API calls
2. **Performance Analysis**: Monitor token usage patterns
3. **Optimization**: Identify high-cost operations for optimization
4. **Audit Trail**: Complete record of all LLM interactions
5. **Debugging**: Detailed logs help troubleshoot issues

## Notes

- Token estimation is approximate (1 token ≈ 4 characters)
- Pricing is based on 2024 Azure OpenAI rates and may need updates
- Cache hits are not logged (no cost incurred)
- All logging is non-blocking and doesn't affect performance
