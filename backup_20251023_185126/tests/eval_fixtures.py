"""
Evaluation fixtures for testing the intelligent intent handling system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any
from app.scene.router import decision_router


def run_eval_fixtures() -> Dict[str, Any]:
    """Run evaluation fixtures and return results."""
    
    test_cases = [
        # Control actions
        {"input": "turn on handles", "expected_type": "tool_action", "expected_tool": "control"},
        {"input": "show me the x-ray", "expected_type": "tool_action", "expected_tool": "control"},
        {"input": "turn off implants", "expected_type": "tool_action", "expected_tool": "control"},
        {"input": "set brightness to 50%", "expected_type": "tool_action", "expected_tool": "control"},
        
        # Information requests
        {"input": "what are handles", "expected_type": "answer", "expected_context": False},
        {"input": "where is the skull", "expected_type": "answer", "expected_context": False},
        {"input": "definition of implants", "expected_type": "answer", "expected_context": False},
        
        # Size requests
        {"input": "give me implant size 4 x 11.5", "expected_type": "tool_action", "expected_tool": "control"},
        {"input": "implant height 4.2 length 12", "expected_type": "tool_action", "expected_tool": "control"},
        
        # Clarification cases
        {"input": "do something", "expected_type": "clarification"},
        {"input": "turn on", "expected_type": "clarification"},
        {"input": "what is", "expected_type": "clarification"},
    ]
    
    results = {
        "total_tests": len(test_cases),
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for i, test_case in enumerate(test_cases):
        try:
            response = decision_router.route(test_case["input"])
            
            # Check response type
            if response.get("type") == test_case["expected_type"]:
                results["passed"] += 1
                status = "PASS"
            else:
                results["failed"] += 1
                status = "FAIL"
            
            # Check specific expectations
            details = {
                "test_id": i + 1,
                "input": test_case["input"],
                "expected_type": test_case["expected_type"],
                "actual_type": response.get("type"),
                "status": status,
                "response": response
            }
            
            if test_case.get("expected_tool"):
                details["expected_tool"] = test_case["expected_tool"]
                details["actual_tool"] = response.get("tool")
            
            if test_case.get("expected_context") is not None:
                details["expected_context"] = test_case["expected_context"]
                details["actual_context"] = response.get("context_used")
            
            results["details"].append(details)
            
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "test_id": i + 1,
                "input": test_case["input"],
                "status": "ERROR",
                "error": str(e)
            })
    
    return results


def print_eval_results(results: Dict[str, Any]) -> None:
    """Print evaluation results in a readable format."""
    print(f"\n=== Evaluation Results ===")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results['passed'] / results['total_tests'] * 100:.1f}%")
    
    print(f"\n=== Detailed Results ===")
    for detail in results["details"]:
        print(f"\nTest {detail['test_id']}: {detail['input']}")
        print(f"  Status: {detail['status']}")
        if detail['status'] == 'PASS':
            print(f"  ✓ Response type: {detail['actual_type']}")
            if 'actual_tool' in detail:
                print(f"  ✓ Tool: {detail['actual_tool']}")
            if 'actual_context' in detail:
                print(f"  ✓ Context used: {detail['actual_context']}")
        elif detail['status'] == 'FAIL':
            print(f"  ✗ Expected: {detail['expected_type']}, Got: {detail['actual_type']}")
        else:
            print(f"  ✗ Error: {detail['error']}")


if __name__ == "__main__":
    results = run_eval_fixtures()
    print_eval_results(results)
