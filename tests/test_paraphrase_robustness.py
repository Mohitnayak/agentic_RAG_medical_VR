#!/usr/bin/env python3
"""
Test script to verify robustness against phrasing variations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scene.router import decision_router


def test_paraphrase_robustness():
    """Test various phrasings of the same intent."""
    
    test_cases = [
        # Control ON variations
        {
            "category": "control_on",
            "queries": [
                "turn on handles",
                "activate the handles", 
                "enable handles",
                "switch on the handles",
                "start the handles",
                "show me the handles",
                "bring up the handles",
                "could you turn on handles",
                "please activate handles",
                "I need the handles on"
            ],
            "expected_type": "tool_action",
            "expected_tool": "control"
        },
        
        # Control OFF variations  
        {
            "category": "control_off",
            "queries": [
                "turn off handles",
                "deactivate handles",
                "disable the handles",
                "switch off handles", 
                "stop the handles",
                "hide handles",
                "turn down the handles",
                "could you turn off handles",
                "please deactivate handles",
                "I need handles off"
            ],
            "expected_type": "tool_action", 
            "expected_tool": "control"
        },
        
        # Info definition variations
        {
            "category": "info_definition",
            "queries": [
                "what are sinuses",
                "what is a sinus",
                "tell me about sinuses",
                "explain sinuses",
                "describe sinuses",
                "information on sinuses",
                "what do you know about sinuses",
                "can you explain what sinuses are",
                "I want to know about sinuses"
            ],
            "expected_type": "answer",
            "expected_context_used": False
        },
        
        # Info location variations
        {
            "category": "info_location", 
            "queries": [
                "where is the skull",
                "where are the skulls",
                "which side is the skull",
                "what side is skull on",
                "skull location",
                "where can I find the skull",
                "position of skull",
                "skull is where"
            ],
            "expected_type": "answer",
            "expected_context_used": False
        },
        
        # Size request variations
        {
            "category": "size_request",
            "queries": [
                "give me the implant",
                "provide me with implants", 
                "I need implants",
                "show me implants",
                "get me some implants",
                "can I have implants",
                "implant please",
                "I want implants"
            ],
            "expected_type": "clarification"
        }
    ]
    
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for test_case in test_cases:
        category = test_case["category"]
        queries = test_case["queries"]
        expected_type = test_case["expected_type"]
        
        print(f"\n=== Testing {category} ===")
        
        for query in queries:
            results["total_tests"] += 1
            
            try:
                response = decision_router.route(query)
                
                # Check response type
                actual_type = response.get("type")
                if actual_type == expected_type:
                    results["passed"] += 1
                    status = "PASS"
                else:
                    results["failed"] += 1
                    status = "FAIL"
                
                # Check specific expectations
                details = {
                    "category": category,
                    "query": query,
                    "expected_type": expected_type,
                    "actual_type": actual_type,
                    "status": status,
                    "response": response
                }
                
                if "expected_tool" in test_case:
                    details["expected_tool"] = test_case["expected_tool"]
                    details["actual_tool"] = response.get("tool")
                
                if "expected_context_used" in test_case:
                    details["expected_context_used"] = test_case["expected_context_used"]
                    details["actual_context_used"] = response.get("context_used")
                
                results["details"].append(details)
                
                print(f"  {status}: '{query}' -> {actual_type}")
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "category": category,
                    "query": query,
                    "status": "ERROR",
                    "error": str(e)
                })
                print(f"  ERROR: '{query}' -> {str(e)}")
    
    return results


def print_summary(results):
    """Print test summary."""
    print("\n" + "="*60)
    print("PARAPHRASE ROBUSTNESS TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['passed']/results['total_tests']*100:.1f}%")
    
    # Group by category
    categories = {}
    for detail in results["details"]:
        cat = detail["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0}
        categories[cat]["total"] += 1
        if detail["status"] == "PASS":
            categories[cat]["passed"] += 1
    
    print("\nBy category:")
    for cat, stats in categories.items():
        rate = stats["passed"]/stats["total"]*100
        print(f"  {cat}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")


if __name__ == "__main__":
    results = test_paraphrase_robustness()
    print_summary(results)
