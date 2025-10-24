#!/usr/bin/env python3
"""
Simple test runner for agentic RAG system.
Loads test data and validates system responses.
"""

import json
import sys
import os
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.scene.router import decision_router


def load_test_data(file_path: str = "tests/simple/test_data.json") -> List[Dict[str, Any]]:
    """Load test cases from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("test_cases", [])
    except Exception as e:
        print(f"Error loading test data: {e}")
        sys.exit(1)


def run_test(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single test case."""
    input_text = test_case["input"]
    expected_type = test_case["expected_type"]
    
    try:
        actual_response = decision_router.route(input_text)
        
        # Check basic type
        actual_type = actual_response.get("type")
        passed = actual_type == expected_type
        
        result = {
            "input": input_text,
            "expected_type": expected_type,
            "actual_type": actual_type,
            "passed": passed,
            "category": test_case.get("category", ""),
            "errors": []
        }
        
        if not passed:
            result["errors"].append(f"Expected type '{expected_type}', got '{actual_type}'")
            return result
        
        # Check tool action details
        if expected_type == "tool_action":
            expected_tool = test_case.get("expected_tool")
            expected_target = test_case.get("expected_target")
            expected_operation = test_case.get("expected_operation")
            expected_value = test_case.get("expected_value")
            
            actual_tool = actual_response.get("tool")
            actual_args = actual_response.get("arguments", {})
            actual_target = actual_args.get("target")
            actual_operation = actual_args.get("operation")
            actual_value = actual_args.get("value")
            
            if expected_tool and actual_tool != expected_tool:
                result["errors"].append(f"Expected tool '{expected_tool}', got '{actual_tool}'")
                result["passed"] = False
            
            if expected_target and actual_target != expected_target:
                result["errors"].append(f"Expected target '{expected_target}', got '{actual_target}'")
                result["passed"] = False
            
            if expected_operation and actual_operation != expected_operation:
                result["errors"].append(f"Expected operation '{expected_operation}', got '{actual_operation}'")
                result["passed"] = False
            
            if expected_value and actual_value != expected_value:
                result["errors"].append(f"Expected value '{expected_value}', got '{actual_value}'")
                result["passed"] = False
        
        # Check answer content
        elif expected_type == "answer":
            expected_contains = test_case.get("expected_contains")
            if expected_contains:
                actual_answer = actual_response.get("answer", "")
                if expected_contains.lower() not in actual_answer.lower():
                    result["errors"].append(f"Expected answer to contain '{expected_contains}', got '{actual_answer}'")
                    result["passed"] = False
        
        return result
        
    except Exception as e:
        return {
            "input": input_text,
            "expected_type": expected_type,
            "actual_type": "error",
            "passed": False,
            "category": test_case.get("category", ""),
            "errors": [f"Exception: {str(e)}"]
        }


def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate test metrics."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    # Group by category
    by_category = {}
    for result in results:
        category = result["category"]
        if category not in by_category:
            by_category[category] = {"total": 0, "passed": 0}
        by_category[category]["total"] += 1
        if result["passed"]:
            by_category[category]["passed"] += 1
    
    # Calculate accuracy by category
    category_accuracy = {}
    for category, counts in by_category.items():
        category_accuracy[category] = counts["passed"] / counts["total"] if counts["total"] > 0 else 0
    
    # Group by response type
    by_type = {}
    for result in results:
        response_type = result["expected_type"]
        if response_type not in by_type:
            by_type[response_type] = {"total": 0, "passed": 0}
        by_type[response_type]["total"] += 1
        if result["passed"]:
            by_type[response_type]["passed"] += 1
    
    # Calculate accuracy by type
    type_accuracy = {}
    for response_type, counts in by_type.items():
        type_accuracy[response_type] = counts["passed"] / counts["total"] if counts["total"] > 0 else 0
    
    # Find common failure patterns
    failure_patterns = {}
    for result in results:
        if not result["passed"]:
            for error in result["errors"]:
                if error not in failure_patterns:
                    failure_patterns[error] = 0
                failure_patterns[error] += 1
    
    return {
        "overall": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "accuracy": passed / total if total > 0 else 0
        },
        "by_category": {
            "counts": by_category,
            "accuracy": category_accuracy
        },
        "by_type": {
            "counts": by_type,
            "accuracy": type_accuracy
        },
        "failure_patterns": failure_patterns
    }


def print_report(metrics: Dict[str, Any], results: List[Dict[str, Any]]):
    """Print test report."""
    print("\n" + "="*60)
    print("TEST REPORT")
    print("="*60)
    
    # Overall metrics
    overall = metrics["overall"]
    print(f"\nOVERALL RESULTS:")
    print(f"  Total Tests: {overall['total']}")
    print(f"  Passed: {overall['passed']}")
    print(f"  Failed: {overall['failed']}")
    print(f"  Accuracy: {overall['accuracy']:.2%}")
    
    # By category
    print(f"\nBY CATEGORY:")
    for category, accuracy in metrics["by_category"]["accuracy"].items():
        counts = metrics["by_category"]["counts"][category]
        print(f"  {category}: {counts['passed']}/{counts['total']} ({accuracy:.2%})")
    
    # By response type
    print(f"\nBY RESPONSE TYPE:")
    for response_type, accuracy in metrics["by_type"]["accuracy"].items():
        counts = metrics["by_type"]["counts"][response_type]
        print(f"  {response_type}: {counts['passed']}/{counts['total']} ({accuracy:.2%})")
    
    # Failure patterns
    if metrics["failure_patterns"]:
        print(f"\nCOMMON FAILURE PATTERNS:")
        for error, count in sorted(metrics["failure_patterns"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {count}x: {error}")
    
    # Detailed failures
    failed_results = [r for r in results if not r["passed"]]
    if failed_results:
        print(f"\nDETAILED FAILURES:")
        for result in failed_results:
            print(f"  [FAIL] '{result['input']}'")
            print(f"     Expected: {result['expected_type']}")
            print(f"     Errors: {'; '.join(result['errors'])}")
            print()


def save_results(results: List[Dict[str, Any]], metrics: Dict[str, Any], filename: str = "test_results.json"):
    """Save results to JSON file."""
    results_data = {
        "metrics": metrics,
        "test_results": results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {filename}")


def main():
    """Main test runner."""
    print("Agentic RAG System Test Runner")
    print("="*40)
    
    # Load test data
    test_cases = load_test_data()
    print(f"Loaded {len(test_cases)} test cases")
    
    # Run tests
    print("\nRunning tests...")
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test_case['input']}")
        result = run_test(test_case)
        results.append(result)
        
        if result["passed"]:
            print(f"  [PASS]")
        else:
            print(f"  [FAIL] {'; '.join(result['errors'])}")
    
    # Calculate metrics
    metrics = calculate_metrics(results)
    
    # Print report
    print_report(metrics, results)
    
    # Save results
    save_results(results, metrics)
    
    # Return exit code
    overall_accuracy = metrics["overall"]["accuracy"]
    if overall_accuracy >= 0.9:
        print(f"\n[EXCELLENT] Overall accuracy: {overall_accuracy:.2%}")
        return 0
    elif overall_accuracy >= 0.8:
        print(f"\n[GOOD] Overall accuracy: {overall_accuracy:.2%}")
        return 0
    elif overall_accuracy >= 0.7:
        print(f"\n[FAIR] Overall accuracy: {overall_accuracy:.2%}")
        return 1
    else:
        print(f"\n[POOR] Overall accuracy: {overall_accuracy:.2%}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
