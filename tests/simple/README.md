# Evaluation Framework

A comprehensive evaluation system for the Agentic RAG Medical VR system with clean tabular output and detailed failure analysis.

## Overview

The evaluation framework provides comprehensive testing across different priority levels:

- **Critical Priority**: Foundation metrics that must be fixed (Target: ≥90%)
- **Important Priority**: Core functionality metrics that should be addressed (Target: ≥80%)
- **Enhancement Priority**: Enhancement metrics that can be improved (Target: ≥70%)

## Metrics by Priority

### Critical Priority (Must Fix)

| Metric | Target | Description |
|--------|--------|-------------|
| **Intent Classification** | ≥90% | Correctly identifying user intent (control vs info vs clarification) |
| **Entity Resolution** | ≥95% | Correctly identifying target entities from user input |
| **Response Type** | ≥90% | Correctly determining response type (tool_action, answer, clarification) |

### Important Priority (Should Fix)

| Metric | Target | Description |
|--------|--------|-------------|
| **Value Parsing** | ≥95% | Correctly parsing and validating numeric values |
| **Ambiguity Handling** | ≥80% | Properly handling incomplete or ambiguous inputs |
| **Medical Context** | ≥95% | Providing medically accurate definitions |

### Enhancement Priority (Can Improve)

| Metric | Target | Description |
|--------|--------|-------------|
| **Typo Robustness** | ≥90% | Handling spelling errors and variations |
| **Complex Phrasing** | ≥85% | Handling natural language variations |

## Usage

### Running the Evaluation

```bash
# From the project root
conda run -n medallion_agents python tests/simple/evaluation.py
```

### Output Format

The evaluation produces clean tabular output and exports detailed results to CSV:

**Console Output:**
```
EVALUATION RESULTS SUMMARY
================================================================================

OVERALL PERFORMANCE:
--------------------------------------------------------------------------------
Metric                Priority     Score      Target   Status   Details
--------------------------------------------------------------------------------
Intent Classification  Critical     25/38      90%      FAIL     65.8%
Entity Resolution      Critical     12/20      95%      FAIL     60.0%
Response Type          Critical     30/38      90%      FAIL     78.9%
Value Parsing          Important    1/2        80%      FAIL     50.0%
Ambiguity Handling     Important    0/3        80%      FAIL     0.0%
Medical Context        Important    3/3        80%      PASS     100.0%
Typo Robustness       Enhancement  3/4        70%      WARN     75.0%
Complex Phrasing       Enhancement  2/3        70%      WARN     66.7%
--------------------------------------------------------------------------------
CRITICAL TOTAL         Critical     67/96      90%      FAIL     69.8%
IMPORTANT TOTAL        Important    4/8        80%      FAIL     50.0%
ENHANCEMENT TOTAL      Enhancement  5/7        70%      WARN     71.4%
--------------------------------------------------------------------------------
OVERALL TOTAL          All          76/111     85%      FAIL     68.5%
```

**CSV Export (`evaluation_results.csv`):**
The CSV file contains detailed Expected vs Actual values for every test case:

| Column | Description |
|--------|-------------|
| `Test_ID` | Unique identifier for each test |
| `Input_Text` | The user input that was tested |
| `Category` | Test category (control_on, info_definition, etc.) |
| `Priority` | Critical, Important, or Enhancement |
| `Metric_Name` | Which metric this test evaluates |
| `Expected_Type` | Expected response type (tool_action, answer, clarification) |
| `Actual_Type` | Actual response type returned by system |
| `Expected_Target` | Expected target entity |
| `Actual_Target` | Actual target entity returned |
| `Expected_Value` | Expected value for control actions |
| `Actual_Value` | Actual value returned |
| `Expected_Contains` | Expected text in answer responses |
| `Actual_Answer` | Actual answer text returned |
| `Status` | PASS, FAIL, or ERROR |
| `Test_Result` | Passed, Failed, or Error |
| `Confidence_Score` | Confidence score (1.0 for pass, 0.0 for fail) |
| `Error_Message` | Error details if test failed |

### Detailed Failure Analysis

The system provides detailed failure analysis showing exactly what went wrong:

```
DETAILED FAILURE ANALYSIS
================================================================================

Intent Classification (Critical Priority):
------------------------------------------------------------
Input                     Expected         Actual           Category
------------------------------------------------------------
what is xray flashlight   info            control          info_definition
tell me about implants    info            clarification    info_definition
where are the implants    info            clarification    info_location
```

### Exit Codes

- `0`: Success (Critical ≥90%, Important ≥80%)
- `1`: Warning (Critical ≥80%)
- `2`: Failure (Critical <80%)

### CSV Analysis

The CSV export allows for detailed analysis of system performance:

**Filtering Failed Tests:**
```bash
# View only failed tests
grep "FAIL" evaluation_results.csv

# View specific metric failures
grep "Intent Classification.*FAIL" evaluation_results.csv
```

**Analyzing Patterns:**
```bash
# Count failures by category
cut -d',' -f3 evaluation_results.csv | sort | uniq -c

# Count failures by priority
cut -d',' -f4 evaluation_results.csv | sort | uniq -c
```

**Expected vs Actual Comparison:**
The CSV clearly shows discrepancies between expected and actual values:
- **Entity Resolution Issues**: `Expected_Target` vs `Actual_Target` columns
- **Value Parsing Issues**: `Expected_Value` vs `Actual_Value` columns  
- **Response Type Issues**: `Expected_Type` vs `Actual_Type` columns
- **Medical Context Issues**: `Expected_Contains` vs `Actual_Answer` columns

## Test Categories

The evaluation uses test cases organized by category:

- **control_on**: Turn on/activate commands
- **control_off**: Turn off/deactivate commands  
- **control_value**: Set numeric values (brightness, contrast, implant sizes)
- **info_definition**: "What is/are" questions
- **info_location**: "Where is/are" questions
- **size_request**: Implant size requests without specific dimensions
- **ambiguous**: Incomplete or ambiguous inputs
- **edge_cases**: Typos and variations
- **complex_phrasing**: Natural language variations

## Success Criteria

### Production Ready
- **Critical Priority**: All metrics ≥ 90%
- **Important Priority**: All metrics ≥ 80%
- **Enhancement Priority**: All metrics ≥ 70%
- **Overall System**: ≥ 85%

### Development Phase
- **Critical Priority**: All metrics ≥ 80%
- **Important Priority**: All metrics ≥ 70%
- **Enhancement Priority**: All metrics ≥ 60%

## Integration with CI/CD

The evaluation can be integrated into continuous integration:

```yaml
# .github/workflows/evaluation.yml
name: System Evaluation
on: [push, pull_request]
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run evaluation
        run: python tests/simple/evaluation.py
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: evaluation-results
          path: evaluation_results.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Missing Dependencies**: Install requirements.txt in conda environment
3. **Test Data Issues**: Verify test_data.json format and content
4. **Router Errors**: Check decision_router initialization and configuration

## Contributing

When adding new test cases:

1. **Categorize properly**: Use appropriate category tags
2. **Include expected values**: Provide expected_type, expected_target, etc.
3. **Test edge cases**: Include typos, variations, ambiguous inputs
4. **Update documentation**: Document new test categories