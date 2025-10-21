#!/usr/bin/env python3
"""
Comprehensive Evaluation Framework for Agentic RAG System
Clean tabular output with detailed metrics and failure analysis
"""

import json
import sys
import os
import csv
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.scene.router import decision_router
from app.schemas import validate_response


@dataclass
class EvaluationResult:
    """Result of a single evaluation metric."""
    metric_name: str
    priority: str
    score: float
    max_score: float
    percentage: float
    status: str  # "PASS", "FAIL", "WARNING"
    failures: List[Dict[str, Any]]


class SystemEvaluator:
    """Comprehensive evaluation framework for the agentic RAG system."""
    
    def __init__(self):
        self.results = []
        self.test_cases = self._load_test_cases()
        
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases from JSON file."""
        try:
            with open("tests/simple/test_data.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("test_cases", [])
        except Exception as e:
            print(f"Error loading test data: {e}")
            sys.exit(1)
    
    def evaluate_intent_classification(self) -> EvaluationResult:
        """Evaluate intent classification accuracy."""
        correct = 0
        total = 0
        failures = []
        
        for test_case in self.test_cases:
            input_text = test_case["input"]
            expected_type = test_case["expected_type"]
            
            try:
                response = decision_router.route(input_text)
                actual_type = response.get("type")
                
                # Map response types to intent categories
                intent_mapping = {
                    "tool_action": "control",
                    "answer": "info", 
                    "clarification": "clarification"
                }
                
                expected_intent = intent_mapping.get(expected_type, expected_type)
                actual_intent = intent_mapping.get(actual_type, actual_type)
                
                total += 1
                if expected_intent == actual_intent:
                    correct += 1
                else:
                    failures.append({
                        "input": input_text,
                        "expected": expected_intent,
                        "actual": actual_intent,
                        "category": test_case.get("category", "unknown")
                    })
                    
            except Exception as e:
                total += 1
                failures.append({
                    "input": input_text,
                    "expected": expected_type,
                    "actual": f"ERROR: {str(e)}",
                    "category": test_case.get("category", "unknown")
                })
        
        percentage = (correct / total * 100) if total > 0 else 0
        status = "PASS" if percentage >= 90 else "FAIL"
        
        return EvaluationResult(
            metric_name="Intent Classification",
            priority="Critical",
            score=correct,
            max_score=total,
            percentage=percentage,
            status=status,
            failures=failures
        )
    
    def evaluate_entity_resolution(self) -> EvaluationResult:
        """Evaluate entity resolution accuracy."""
        correct = 0
        total = 0
        failures = []
        
        # Only evaluate tool_action test cases
        tool_cases = [tc for tc in self.test_cases if tc.get("expected_type") == "tool_action"]
        
        for test_case in tool_cases:
            input_text = test_case["input"]
            expected_target = test_case.get("expected_target")
            
            if not expected_target:
                continue
                
            try:
                response = decision_router.route(input_text)
                
                if response.get("type") == "tool_action":
                    actual_target = response.get("arguments", {}).get("target")
                    total += 1
                    
                    if actual_target == expected_target:
                        correct += 1
                    else:
                        failures.append({
                            "input": input_text,
                            "expected": expected_target,
                            "actual": actual_target,
                            "category": test_case.get("category", "unknown")
                        })
                        
            except Exception as e:
                total += 1
                failures.append({
                    "input": input_text,
                    "expected": expected_target,
                    "actual": f"ERROR: {str(e)}",
                    "category": test_case.get("category", "unknown")
                })
        
        percentage = (correct / total * 100) if total > 0 else 0
        status = "PASS" if percentage >= 95 else "FAIL"
        
        return EvaluationResult(
            metric_name="Entity Resolution",
            priority="Critical",
            score=correct,
            max_score=total,
            percentage=percentage,
            status=status,
            failures=failures
        )
    
    def evaluate_response_type(self) -> EvaluationResult:
        """Evaluate response type accuracy."""
        correct = 0
        total = 0
        failures = []
        
        for test_case in self.test_cases:
            input_text = test_case["input"]
            expected_type = test_case["expected_type"]
            
            try:
                response = decision_router.route(input_text)
                actual_type = response.get("type")
                
                total += 1
                if actual_type == expected_type:
                    correct += 1
                else:
                    failures.append({
                        "input": input_text,
                        "expected": expected_type,
                        "actual": actual_type,
                        "category": test_case.get("category", "unknown")
                    })
                    
            except Exception as e:
                total += 1
                failures.append({
                    "input": input_text,
                    "expected": expected_type,
                    "actual": f"ERROR: {str(e)}",
                    "category": test_case.get("category", "unknown")
                })
        
        percentage = (correct / total * 100) if total > 0 else 0
        status = "PASS" if percentage >= 90 else "FAIL"
        
        return EvaluationResult(
            metric_name="Response Type",
            priority="Critical",
            score=correct,
            max_score=total,
            percentage=percentage,
            status=status,
            failures=failures
        )
    
    def evaluate_value_parsing(self) -> EvaluationResult:
        """Evaluate value parsing accuracy."""
        correct = 0
        total = 0
        failures = []
        
        # Only evaluate control_value test cases
        value_cases = [tc for tc in self.test_cases if tc.get("category") == "control_value"]
        
        for test_case in value_cases:
            input_text = test_case["input"]
            expected_value = test_case.get("expected_value")
            
            if not expected_value:
                continue
                
            try:
                response = decision_router.route(input_text)
                
                if response.get("type") == "tool_action":
                    actual_value = response.get("arguments", {}).get("value")
                    total += 1
                    
                    # Handle different value types
                    if isinstance(expected_value, str) and isinstance(actual_value, (int, float)):
                        actual_value = str(actual_value)
                    
                    if actual_value == expected_value:
                        correct += 1
                    else:
                        failures.append({
                            "input": input_text,
                            "expected": expected_value,
                            "actual": actual_value,
                            "category": test_case.get("category", "unknown")
                        })
                        
            except Exception as e:
                total += 1
                failures.append({
                    "input": input_text,
                    "expected": expected_value,
                    "actual": f"ERROR: {str(e)}",
                    "category": test_case.get("category", "unknown")
                })
        
        percentage = (correct / total * 100) if total > 0 else 0
        status = "PASS" if percentage >= 95 else "FAIL"
        
        return EvaluationResult(
            metric_name="Value Parsing",
            priority="Important",
            score=correct,
            max_score=total,
            percentage=percentage,
            status=status,
            failures=failures
        )
    
    def evaluate_ambiguity_handling(self) -> EvaluationResult:
        """Evaluate ambiguity handling."""
        correct = 0
        total = 0
        failures = []
        
        # Only evaluate ambiguous test cases
        ambiguous_cases = [tc for tc in self.test_cases if tc.get("category") == "ambiguous"]
        
        for test_case in ambiguous_cases:
            input_text = test_case["input"]
            expected_type = test_case["expected_type"]
            
            try:
                response = decision_router.route(input_text)
                actual_type = response.get("type")
                
                total += 1
                if actual_type == expected_type:
                    correct += 1
                else:
                    failures.append({
                        "input": input_text,
                        "expected": expected_type,
                        "actual": actual_type,
                        "category": test_case.get("category", "unknown")
                    })
                    
            except Exception as e:
                total += 1
                failures.append({
                    "input": input_text,
                    "expected": expected_type,
                    "actual": f"ERROR: {str(e)}",
                    "category": test_case.get("category", "unknown")
                })
        
        percentage = (correct / total * 100) if total > 0 else 0
        status = "PASS" if percentage >= 80 else "FAIL"
        
        return EvaluationResult(
            metric_name="Ambiguity Handling",
            priority="Important",
            score=correct,
            max_score=total,
            percentage=percentage,
            status=status,
            failures=failures
        )
    
    def evaluate_medical_context(self) -> EvaluationResult:
        """Evaluate medical context accuracy."""
        correct = 0
        total = 0
        failures = []
        
        # Only evaluate info_definition test cases
        definition_cases = [tc for tc in self.test_cases if tc.get("category") == "info_definition"]
        
        for test_case in definition_cases:
            input_text = test_case["input"]
            expected_contains = test_case.get("expected_contains")
            
            if not expected_contains:
                continue
                
            try:
                response = decision_router.route(input_text)
                
                if response.get("type") == "answer":
                    actual_answer = response.get("answer", "")
                    total += 1
                    
                    if expected_contains.lower() in actual_answer.lower():
                        correct += 1
                    else:
                        failures.append({
                            "input": input_text,
                            "expected_contains": expected_contains,
                            "actual_answer": actual_answer,
                            "category": test_case.get("category", "unknown")
                        })
                        
            except Exception as e:
                total += 1
                failures.append({
                    "input": input_text,
                    "expected_contains": expected_contains,
                    "actual_answer": f"ERROR: {str(e)}",
                    "category": test_case.get("category", "unknown")
                })
        
        percentage = (correct / total * 100) if total > 0 else 0
        status = "PASS" if percentage >= 95 else "FAIL"
        
        return EvaluationResult(
            metric_name="Medical Context",
            priority="Important",
            score=correct,
            max_score=total,
            percentage=percentage,
            status=status,
            failures=failures
        )
    
    def evaluate_typo_robustness(self) -> EvaluationResult:
        """Evaluate typo robustness."""
        correct = 0
        total = 0
        failures = []
        
        # Only evaluate edge_cases test cases (which include typos)
        edge_cases = [tc for tc in self.test_cases if tc.get("category") == "edge_cases"]
        
        for test_case in edge_cases:
            input_text = test_case["input"]
            expected_type = test_case["expected_type"]
            
            try:
                response = decision_router.route(input_text)
                actual_type = response.get("type")
                
                total += 1
                if actual_type == expected_type:
                    correct += 1
                else:
                    failures.append({
                        "input": input_text,
                        "expected": expected_type,
                        "actual": actual_type,
                        "category": test_case.get("category", "unknown")
                    })
                    
            except Exception as e:
                total += 1
                failures.append({
                    "input": input_text,
                    "expected": expected_type,
                    "actual": f"ERROR: {str(e)}",
                    "category": test_case.get("category", "unknown")
                })
        
        percentage = (correct / total * 100) if total > 0 else 0
        status = "PASS" if percentage >= 90 else "WARNING"
        
        return EvaluationResult(
            metric_name="Typo Robustness",
            priority="Enhancement",
            score=correct,
            max_score=total,
            percentage=percentage,
            status=status,
            failures=failures
        )
    
    def evaluate_complex_phrasing(self) -> EvaluationResult:
        """Evaluate complex phrasing handling."""
        correct = 0
        total = 0
        failures = []
        
        # Only evaluate complex_phrasing test cases
        complex_cases = [tc for tc in self.test_cases if tc.get("category") == "complex_phrasing"]
        
        for test_case in complex_cases:
            input_text = test_case["input"]
            expected_type = test_case["expected_type"]
            
            try:
                response = decision_router.route(input_text)
                actual_type = response.get("type")
                
                total += 1
                if actual_type == expected_type:
                    correct += 1
                else:
                    failures.append({
                        "input": input_text,
                        "expected": expected_type,
                        "actual": actual_type,
                        "category": test_case.get("category", "unknown")
                    })
                    
            except Exception as e:
                total += 1
                failures.append({
                    "input": input_text,
                    "expected": expected_type,
                    "actual": f"ERROR: {str(e)}",
                    "category": test_case.get("category", "unknown")
                })
        
        percentage = (correct / total * 100) if total > 0 else 0
        status = "PASS" if percentage >= 85 else "WARNING"
        
        return EvaluationResult(
            metric_name="Complex Phrasing",
            priority="Enhancement",
            score=correct,
            max_score=total,
            percentage=percentage,
            status=status,
            failures=failures
        )
    
    def run_evaluation(self) -> List[EvaluationResult]:
        """Run complete evaluation."""
        print("Running Comprehensive System Evaluation")
        print("=" * 60)
        
        results = []
        
        # Critical metrics
        results.append(self.evaluate_intent_classification())
        results.append(self.evaluate_entity_resolution())
        results.append(self.evaluate_response_type())
        
        # Important metrics
        results.append(self.evaluate_value_parsing())
        results.append(self.evaluate_ambiguity_handling())
        results.append(self.evaluate_medical_context())
        
        # Enhancement metrics
        results.append(self.evaluate_typo_robustness())
        results.append(self.evaluate_complex_phrasing())
        
        return results
    
    def export_to_csv(self, results: List[EvaluationResult], filename: str = "evaluation_results.csv"):
        """Export detailed results to CSV format - one row per test case.

        Also records fallback (i.e., cases where structured output would fail
        validation and thus the API would switch to RAG).
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Test_ID', 'Input_Text', 'Category', 'Priority',
                'Expected_Type', 'Actual_Type', 'Expected_Target', 'Actual_Target',
                'Expected_Value', 'Actual_Value', 'Expected_Contains', 'Actual_Answer',
                'Intent_Status', 'Entity_Status', 'Response_Status', 'Value_Status',
                'Ambiguity_Status', 'Medical_Status', 'Typo_Status', 'Phrasing_Status',
                'Overall_Status', 'Fallback', 'Fallback_Reason', 'Error_Message'
            ])
            
            test_id = 1
            # Aggregate fallback stats
            self._fallback_total = 0
            self._fallback_by_category: Dict[str, int] = {}
            self._fallback_reasons: Dict[str, int] = {}
            
            # Process each test case once
            for test_case in self.test_cases:
                input_text = test_case["input"]
                category = test_case.get("category", "unknown")
                expected_type = test_case.get("expected_type", "")
                expected_target = test_case.get("expected_target", "")
                expected_value = test_case.get("expected_value", "")
                expected_contains = test_case.get("expected_contains", "")
                
                # Determine priority
                if category in ["control_on", "control_off", "control_value", "info_definition", "info_location", "size_request"]:
                    priority = "Critical"
                elif category in ["ambiguous"]:
                    priority = "Important"
                else:
                    priority = "Enhancement"
                
                # Get actual values by running the test
                try:
                    response = decision_router.route(input_text)
                    # Validate to detect fallback conditions (invalid structured output)
                    validation = validate_response(response)
                    is_fallback = "error" in validation
                    fallback_reason = validation.get("error", "") if is_fallback else ""

                    actual_type = response.get("type", "")
                    actual_target = response.get("arguments", {}).get("target", "")
                    actual_value = response.get("arguments", {}).get("value", "")
                    actual_answer = response.get("answer", "")
                    error_message = ""

                    # Track fallback stats
                    if is_fallback:
                        self._fallback_total += 1
                        self._fallback_by_category[category] = self._fallback_by_category.get(category, 0) + 1
                        if fallback_reason:
                            self._fallback_reasons[fallback_reason] = self._fallback_reasons.get(fallback_reason, 0) + 1
                except Exception as e:
                    actual_type = "ERROR"
                    actual_target = ""
                    actual_value = ""
                    actual_answer = ""
                    error_message = str(e)
                    is_fallback = True
                    fallback_reason = f"Exception: {error_message}"
                    # Track fallback on exception
                    self._fallback_total += 1
                    self._fallback_by_category[category] = self._fallback_by_category.get(category, 0) + 1
                    self._fallback_reasons[fallback_reason] = self._fallback_reasons.get(fallback_reason, 0) + 1
                
                # Determine status for each metric
                intent_status = "PASS" if actual_type == expected_type else "FAIL"
                entity_status = "PASS" if actual_target == expected_target else "FAIL"
                response_status = "PASS" if actual_type == expected_type else "FAIL"
                value_status = "PASS" if str(actual_value) == str(expected_value) else "FAIL"
                ambiguity_status = "PASS" if actual_type == expected_type else "FAIL"
                
                # Medical status - check if expected text is in actual answer
                if expected_contains:
                    medical_status = "PASS" if expected_contains.lower() in actual_answer.lower() else "FAIL"
                else:
                    medical_status = "PASS"  # No expected content to check
                
                typo_status = "PASS" if actual_type == expected_type else "FAIL"
                phrasing_status = "PASS" if actual_type == expected_type else "FAIL"
                
                # Overall status
                overall_status = "PASS" if intent_status == "PASS" and entity_status == "PASS" and response_status == "PASS" else "FAIL"
                
                writer.writerow([
                    test_id,
                    input_text,
                    category,
                    priority,
                    expected_type,
                    actual_type,
                    expected_target,
                    actual_target,
                    expected_value,
                    actual_value,
                    expected_contains,
                    actual_answer,
                    intent_status,
                    entity_status,
                    response_status,
                    value_status,
                    ambiguity_status,
                    medical_status,
                    typo_status,
                    phrasing_status,
                    overall_status,
                    "YES" if is_fallback else "NO",
                    fallback_reason,
                    error_message
                ])
                test_id += 1
        
        print(f"Detailed results exported to {filename} - {test_id-1} test cases")

    def compute_fallback_summary(self) -> Dict[str, Any]:
        """Return fallback stats collected during CSV export."""
        total_cases = len(self.test_cases)
        fallback_total = getattr(self, "_fallback_total", 0)
        by_category = getattr(self, "_fallback_by_category", {})
        reasons = getattr(self, "_fallback_reasons", {})
        rate = (fallback_total / total_cases * 100.0) if total_cases else 0.0
        return {
            "total_cases": total_cases,
            "fallback_total": fallback_total,
            "fallback_rate": rate,
            "by_category": by_category,
            "reasons": reasons,
        }
    
    def print_tabular_report(self, results: List[EvaluationResult]):
        """Print comprehensive tabular report."""
        print("\n" + "=" * 80)
        print("EVALUATION RESULTS SUMMARY")
        print("=" * 80)
        
        # Overall summary table
        print("\nOVERALL PERFORMANCE:")
        print("-" * 80)
        print(f"{'Metric':<20} {'Priority':<12} {'Score':<10} {'Target':<8} {'Status':<8} {'Details'}")
        print("-" * 80)
        
        critical_total = 0
        critical_max = 0
        important_total = 0
        important_max = 0
        enhancement_total = 0
        enhancement_max = 0
        
        for result in results:
            status_symbol = "PASS" if result.status == "PASS" else "WARN" if result.status == "WARNING" else "FAIL"
            target = "90%" if result.priority == "Critical" else "80%" if result.priority == "Important" else "70%"
            
            print(f"{result.metric_name:<20} {result.priority:<12} {result.score:.0f}/{result.max_score:.0f} {target:<8} {status_symbol:<8} {result.percentage:.1f}%")
            
            # Accumulate totals by priority
            if result.priority == "Critical":
                critical_total += result.score
                critical_max += result.max_score
            elif result.priority == "Important":
                important_total += result.score
                important_max += result.max_score
            else:
                enhancement_total += result.score
                enhancement_max += result.max_score
        
        print("-" * 80)
        
        # Priority summaries
        critical_pct = (critical_total / critical_max * 100) if critical_max > 0 else 0
        important_pct = (important_total / important_max * 100) if important_max > 0 else 0
        enhancement_pct = (enhancement_total / enhancement_max * 100) if enhancement_max > 0 else 0
        
        print(f"{'CRITICAL TOTAL':<20} {'Critical':<12} {critical_total:.0f}/{critical_max:.0f} {'90%':<8} {'PASS' if critical_pct >= 90 else 'FAIL':<8} {critical_pct:.1f}%")
        print(f"{'IMPORTANT TOTAL':<20} {'Important':<12} {important_total:.0f}/{important_max:.0f} {'80%':<8} {'PASS' if important_pct >= 80 else 'FAIL':<8} {important_pct:.1f}%")
        print(f"{'ENHANCEMENT TOTAL':<20} {'Enhancement':<12} {enhancement_total:.0f}/{enhancement_max:.0f} {'70%':<8} {'PASS' if enhancement_pct >= 70 else 'WARN':<8} {enhancement_pct:.1f}%")
        
        # Overall assessment
        overall_total = critical_total + important_total + enhancement_total
        overall_max = critical_max + important_max + enhancement_max
        overall_pct = (overall_total / overall_max * 100) if overall_max > 0 else 0
        
        print("-" * 80)
        print(f"{'OVERALL TOTAL':<20} {'All':<12} {overall_total:.0f}/{overall_max:.0f} {'85%':<8} {'PASS' if overall_pct >= 85 else 'FAIL':<8} {overall_pct:.1f}%")
        
        # Detailed failure analysis
        print("\n" + "=" * 80)
        print("DETAILED FAILURE ANALYSIS")
        print("=" * 80)
        
        for result in results:
            if result.failures:
                print(f"\n{result.metric_name} ({result.priority} Priority):")
                print("-" * 60)
                print(f"{'Input':<25} {'Expected':<15} {'Actual':<15} {'Category'}")
                print("-" * 60)
                
                for i, failure in enumerate(result.failures[:10]):  # Show first 10 failures
                    input_text = failure["input"][:24] if len(failure["input"]) > 24 else failure["input"]
                    expected = str(failure.get("expected", ""))[:14] if len(str(failure.get("expected", ""))) > 14 else str(failure.get("expected", ""))
                    actual = str(failure.get("actual", ""))[:14] if len(str(failure.get("actual", ""))) > 14 else str(failure.get("actual", ""))
                    category = failure.get("category", "unknown")
                    
                    print(f"{input_text:<25} {expected:<15} {actual:<15} {category}")
                
                if len(result.failures) > 10:
                    print(f"... and {len(result.failures) - 10} more failures")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        critical_failed = [r for r in results if r.priority == "Critical" and r.status == "FAIL"]
        important_failed = [r for r in results if r.priority == "Important" and r.status == "FAIL"]
        
        if critical_failed:
            print("CRITICAL ISSUES (Must Fix First):")
            for result in critical_failed:
                print(f"  - {result.metric_name}: {result.percentage:.1f}% (Target: 90%+)")
        
        if important_failed:
            print("\nIMPORTANT ISSUES (Should Address):")
            for result in important_failed:
                print(f"  - {result.metric_name}: {result.percentage:.1f}% (Target: 80%+)")
        
        # Success criteria
        print("\nSUCCESS CRITERIA:")
        print("  Critical Priority: All metrics >= 90%")
        print("  Important Priority: All metrics >= 80%")
        print("  Enhancement Priority: All metrics >= 70%")
        print("  Overall System: >= 85%")
        
        # Final assessment
        print("\n" + "=" * 80)
        if critical_pct >= 90 and important_pct >= 80:
            print("SYSTEM READY FOR PRODUCTION!")
            return 0
        elif critical_pct >= 80:
            print("SYSTEM NEEDS IMPROVEMENT - Focus on Critical metrics")
            return 1
        else:
            print("SYSTEM NOT READY - Critical issues must be resolved")
            return 2


def main():
    """Main evaluation runner."""
    evaluator = SystemEvaluator()
    results = evaluator.run_evaluation()
    exit_code = evaluator.print_tabular_report(results)
    
    # Export to CSV
    evaluator.export_to_csv(results, "evaluation_results.csv")
    fallback_summary = evaluator.compute_fallback_summary()
    
    # Save results to JSON
    results_data = {
        "overall_performance": {
            "critical_total": sum(r.score for r in results if r.priority == "Critical"),
            "critical_max": sum(r.max_score for r in results if r.priority == "Critical"),
            "important_total": sum(r.score for r in results if r.priority == "Important"),
            "important_max": sum(r.max_score for r in results if r.priority == "Important"),
            "enhancement_total": sum(r.score for r in results if r.priority == "Enhancement"),
            "enhancement_max": sum(r.max_score for r in results if r.priority == "Enhancement"),
        },
        "detailed_results": [
            {
                "metric_name": r.metric_name,
                "priority": r.priority,
                "score": r.score,
                "max_score": r.max_score,
                "percentage": r.percentage,
                "status": r.status,
                "failures": r.failures
            }
            for r in results
        ],
        "fallback_summary": fallback_summary
    }
    
    with open("evaluation_results.json", 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to evaluation_results.json")
    print(f"CSV export completed: evaluation_results.csv")

    # Print fallback summary
    print("\n" + "=" * 80)
    print("FALLBACK SUMMARY (Structured-output validation → RAG)")
    print("=" * 80)
    print(f"Total cases: {fallback_summary['total_cases']}")
    print(f"Fallback total: {fallback_summary['fallback_total']}")
    print(f"Fallback rate: {fallback_summary['fallback_rate']:.1f}%")
    if fallback_summary.get('by_category'):
        print("By category:")
        for cat, cnt in sorted(fallback_summary['by_category'].items()):
            print(f"  {cat}: {cnt}")
    if fallback_summary.get('reasons'):
        print("Top reasons:")
        for reason, cnt in sorted(fallback_summary['reasons'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {cnt} × {reason}")
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
