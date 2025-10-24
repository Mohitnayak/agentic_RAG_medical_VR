# Tiered Evaluation Framework

A comprehensive evaluation system for the Agentic RAG Medical VR system, organized by priority tiers to focus on the most critical metrics first.

## Overview

The evaluation framework is organized into three tiers based on system impact and user experience:

- **Tier 1 (Critical)**: Foundation metrics that must be fixed
- **Tier 2 (Important)**: Core functionality metrics that should be addressed  
- **Tier 3 (Nice-to-Have)**: Enhancement metrics that can be improved

## Metrics by Tier

### Tier 1: Critical Metrics (Must Fix)

| Metric | Target | Description |
|--------|--------|-------------|
| **Intent Classification Accuracy** | ≥90% | Correctly identifying user intent (control vs info vs clarification) |
| **Entity Resolution Accuracy** | ≥95% | Correctly identifying target entities from user input |
| **Response Type Accuracy** | ≥90% | Correctly determining response type (tool_action, answer, clarification) |

### Tier 2: Important Metrics (Should Fix)

| Metric | Target | Description |
|--------|--------|-------------|
| **Value Parsing Accuracy** | ≥95% | Correctly parsing and validating numeric values |
| **Ambiguity Handling** | ≥80% | Properly handling incomplete or ambiguous inputs |
| **Medical Context Accuracy** | ≥95% | Providing medically accurate definitions |

### Tier 3: Nice-to-Have Metrics (Can Improve)

| Metric | Target | Description |
|--------|--------|-------------|
| **Typo Robustness** | ≥90% | Handling spelling errors and variations |
| **Complex Phrasing** | ≥85% | Handling natural language variations |
| **Response Time** | ≤500ms | Time to process and respond to queries |

## Usage

### Running the Evaluation

```bash
# From the project root
conda run -n medallion_agents python tests/simple/tiered_evaluation.py
```

### Output

The evaluation produces:

1. **Console Report**: Detailed tiered analysis with pass/fail status
2. **JSON Results**: `tiered_evaluation_results.json` with complete metrics
3. **Exit Code**: 
   - `0`: Success (Tier 1 ≥ 90%)
   - `1`: Warning (Tier 1 ≥ 80%)
   - `2`: Failure (Tier 1 < 80%)

### Sample Output

```
TIERED EVALUATION REPORT
================================================================================

OVERALL PERFORMANCE:
  Score: 25/38
  Percentage: 65.79%

TIER 1 - CRITICAL METRICS (Must Fix):
  Overall: 15/20 (75.00%)
    ✗ Intent Classification Accuracy: 75.00% (FAIL)
    ✗ Entity Resolution Accuracy: 60.00% (FAIL)
    ✓ Response Type Accuracy: 90.00% (PASS)

TIER 2 - IMPORTANT METRICS (Should Fix):
  Overall: 8/12 (66.67%)
    ✗ Value Parsing Accuracy: 50.00% (FAIL)
    ✗ Ambiguity Handling: 0.00% (FAIL)
    ✗ Medical Context Accuracy: 100.00% (PASS)

TIER 3 - NICE-TO-HAVE METRICS (Can Improve):
  Overall: 2/6 (33.33%)
    ⚠ Typo Robustness: 75.00% (WARNING)
    ⚠ Complex Phrasing: 66.67% (WARNING)
    ⚠ Response Time: 150.00% (WARNING)

RECOMMENDATIONS:
  CRITICAL: Fix 2 Tier 1 metrics first:
    - Intent Classification Accuracy (75.00%)
    - Entity Resolution Accuracy (60.00%)
  IMPORTANT: Address 2 Tier 2 metrics:
    - Value Parsing Accuracy (50.00%)
    - Ambiguity Handling (0.00%)

SUCCESS CRITERIA:
  Tier 1 (Critical): All metrics ≥ 90%
  Tier 2 (Important): All metrics ≥ 80%
  Tier 3 (Nice-to-Have): All metrics ≥ 70%

⚠️  SYSTEM NEEDS IMPROVEMENT - Focus on Tier 1 metrics
```

## Test Categories

The evaluation uses test cases from `test_data.json` organized by category:

- **control_on**: Turn on/activate commands
- **control_off**: Turn off/deactivate commands  
- **control_value**: Set numeric values (brightness, contrast, implant sizes)
- **info_definition**: "What is/are" questions
- **info_location**: "Where is/are" questions
- **size_request**: Implant size requests without specific dimensions
- **ambiguous**: Incomplete or ambiguous inputs
- **edge_cases**: Typos and variations
- **complex_phrasing**: Natural language variations

## Evaluation Methodology

### Intent Classification
- Maps response types to intent categories
- Compares expected vs actual intent classification
- Handles tool_action → control, answer → info mappings

### Entity Resolution
- Focuses on tool_action test cases
- Compares expected vs actual target entities
- Validates canonical entity names

### Response Type
- Direct comparison of expected vs actual response types
- Validates tool_action, answer, clarification responses

### Value Parsing
- Tests control_value cases with numeric inputs
- Handles different value types (string vs numeric)
- Validates against expected values

### Ambiguity Handling
- Tests ambiguous input cases
- Validates clarification responses
- Ensures proper handling of incomplete inputs

### Medical Context
- Tests info_definition cases
- Validates medical accuracy in answers
- Checks for expected medical terms

### Typo Robustness
- Tests edge_cases with spelling errors
- Validates system resilience to typos
- Ensures graceful handling of variations

### Complex Phrasing
- Tests natural language variations
- Validates handling of polite requests
- Ensures robustness to different phrasings

### Response Time
- Measures end-to-end processing time
- Targets <500ms for VR interaction
- Provides average, min, max timing statistics

## Success Criteria

### Production Ready
- **Tier 1**: All metrics ≥ 90%
- **Tier 2**: All metrics ≥ 80%
- **Tier 3**: All metrics ≥ 70%

### Development Phase
- **Tier 1**: All metrics ≥ 80%
- **Tier 2**: All metrics ≥ 70%
- **Tier 3**: All metrics ≥ 60%

### Research Phase
- **Tier 1**: All metrics ≥ 70%
- **Tier 2**: All metrics ≥ 60%
- **Tier 3**: All metrics ≥ 50%

## Integration with CI/CD

The evaluation can be integrated into continuous integration:

```yaml
# .github/workflows/evaluation.yml
name: Tiered Evaluation
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
        run: python tests/simple/tiered_evaluation.py
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: evaluation-results
          path: tiered_evaluation_results.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Missing Dependencies**: Install requirements.txt in conda environment
3. **Test Data Issues**: Verify test_data.json format and content
4. **Router Errors**: Check decision_router initialization and configuration

### Debug Mode

Enable debug mode for detailed error information:

```python
# In tiered_evaluation.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When adding new test cases:

1. **Categorize properly**: Use appropriate category tags
2. **Include expected values**: Provide expected_type, expected_target, etc.
3. **Test edge cases**: Include typos, variations, ambiguous inputs
4. **Update documentation**: Document new test categories

## Future Enhancements

- **Automated Test Generation**: Generate test cases from user logs
- **Performance Profiling**: Detailed timing analysis per component
- **A/B Testing**: Compare different system configurations
- **User Study Integration**: Incorporate real user feedback
- **Continuous Monitoring**: Real-time performance tracking
