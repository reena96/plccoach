#!/usr/bin/env python3
"""
Domain Validation Script - Story 3.10
Validates all 7 PLC knowledge domains are operational with correct intent routing and retrieval.

Usage:
    python scripts/validate_domains.py [--api-url http://localhost:8000] [--verbose]
"""

import argparse
import json
import sys
from typing import Dict, List
import requests
from datetime import datetime


# Test queries organized by domain
DOMAIN_TESTS = {
    "assessment": [
        "What makes a good common formative assessment?",
        "How do we create quality assessment items?",
        "What's the difference between formative and summative assessment?",
        "How should we grade student work in a PLC?",
        "What are the characteristics of quality rubrics?",
    ],
    "collaboration": [
        "How do we establish effective team norms?",
        "What makes a high-performing collaborative team?",
        "How do we structure effective team meetings?",
        "What protocols help teams make decisions?",
        "How do we build trust among team members?",
    ],
    "leadership": [
        "What is the role of the principal in a PLC?",
        "How do leaders support collaborative teams?",
        "What does loose and tight leadership mean?",
        "How do principals lead change in a PLC?",
        "What are the responsibilities of district leaders?",
    ],
    "curriculum": [
        "What is a guaranteed and viable curriculum?",
        "How do we align curriculum to standards?",
        "What are essential learning outcomes?",
        "How do we prioritize curriculum content?",
        "What is curriculum mapping in a PLC?",
    ],
    "data_analysis": [
        "How do we implement RTI effectively?",
        "What is a multi-tiered system of supports?",
        "How do we use data to identify struggling students?",
        "What interventions work best for Tier 2?",
        "How do we monitor student progress effectively?",
    ],
    "school_culture": [
        "How do we shift to a PLC culture?",
        "What are the three big ideas of a PLC?",
        "How do we build a culture of collaboration?",
        "What are the four critical questions of a PLC?",
        "How do we sustain PLC practices over time?",
    ],
    "student_learning": [
        "How do we increase student engagement?",
        "What strategies improve student motivation?",
        "How do we help students take ownership of learning?",
        "What does student voice look like in practice?",
        "How do we differentiate instruction for all learners?",
    ],
}

CROSS_DOMAIN_TESTS = [
    {
        "query": "How do assessments connect to RTI?",
        "expected_primary": "assessment",
        "expected_secondary": ["data_analysis"],
    },
    {
        "query": "How do leaders support data-driven instruction?",
        "expected_primary": "leadership",
        "expected_secondary": ["data_analysis", "curriculum"],
    },
    {
        "query": "What role does collaboration play in student success?",
        "expected_primary": "collaboration",
        "expected_secondary": ["student_learning"],
    },
    {
        "query": "How do we build a culture of assessment?",
        "expected_primary": "school_culture",
        "expected_secondary": ["assessment"],
    },
]

CLARIFICATION_TESTS = [
    "Tell me about PLCs",
    "How do I improve my school?",
    "What should we do?",
    "Help",
]


class DomainValidator:
    """Validates domain coverage and intent routing."""

    def __init__(self, api_url: str, verbose: bool = False):
        self.api_url = api_url.rstrip("/")
        self.verbose = verbose
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "domains": {},
        }

    def _test_query(self, query: str, expected_domain: str = None) -> Dict:
        """Send a query to the coach API and return the classification result."""
        try:
            response = requests.post(
                f"{self.api_url}/api/coach/query",
                json={"query": query},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if self.verbose:
                print(f"\nQuery: {query}")
                print(f"Primary Domain: {data.get('primary_domain', 'N/A')}")
                print(f"Confidence: {data.get('confidence', 0):.2f}")
                if data.get("chunks"):
                    print(f"Chunks Retrieved: {len(data['chunks'])}")

            return {
                "success": True,
                "query": query,
                "primary_domain": data.get("primary_domain"),
                "secondary_domains": data.get("secondary_domains", []),
                "needs_clarification": data.get("needs_clarification", False),
                "confidence": data.get("confidence", 0),
                "num_chunks": len(data.get("chunks", [])),
                "books_cited": self._extract_books(data.get("chunks", [])),
            }

        except requests.RequestException as e:
            if self.verbose:
                print(f"\nError testing query '{query}': {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
            }

    def _extract_books(self, chunks: List[Dict]) -> List[str]:
        """Extract unique book titles from chunks."""
        books = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            book_title = metadata.get("book_title")
            if book_title:
                books.add(book_title)
        return list(books)

    def test_domain(self, domain: str, queries: List[str]) -> Dict:
        """Test all queries for a specific domain."""
        print(f"\n{'='*60}")
        print(f"Testing Domain: {domain.upper()}")
        print(f"{'='*60}")

        domain_results = {
            "queries_tested": len(queries),
            "passed": 0,
            "failed": 0,
            "tests": [],
        }

        for query in queries:
            result = self._test_query(query, expected_domain=domain)
            self.results["total_tests"] += 1

            # Check if correct domain identified
            if result.get("success"):
                if result["primary_domain"] == domain:
                    domain_results["passed"] += 1
                    self.results["passed"] += 1
                    status = "✓ PASS"
                else:
                    domain_results["failed"] += 1
                    self.results["failed"] += 1
                    status = f"✗ FAIL (got: {result['primary_domain']})"
            else:
                domain_results["failed"] += 1
                self.results["failed"] += 1
                status = "✗ ERROR"

            domain_results["tests"].append(result)

            # Print result
            print(f"  {status}: {query[:60]}...")
            if self.verbose and result.get("books_cited"):
                print(f"    Books: {', '.join(result['books_cited'])}")

        # Summary
        pass_rate = (
            domain_results["passed"] / domain_results["queries_tested"] * 100
        )
        print(f"\nDomain Pass Rate: {pass_rate:.1f}% ({domain_results['passed']}/{domain_results['queries_tested']})")

        self.results["domains"][domain] = domain_results
        return domain_results

    def test_cross_domain(self) -> Dict:
        """Test cross-domain queries."""
        print(f"\n{'='*60}")
        print("Testing Cross-Domain Queries")
        print(f"{'='*60}")

        cross_results = {"queries_tested": len(CROSS_DOMAIN_TESTS), "passed": 0, "failed": 0, "tests": []}

        for test in CROSS_DOMAIN_TESTS:
            query = test["query"]
            expected_primary = test["expected_primary"]
            expected_secondary = test.get("expected_secondary", [])

            result = self._test_query(query)
            self.results["total_tests"] += 1

            # Check primary and secondary domains
            primary_match = result.get("primary_domain") == expected_primary
            secondary_match = any(
                domain in result.get("secondary_domains", [])
                for domain in expected_secondary
            )

            if result.get("success") and primary_match:
                cross_results["passed"] += 1
                self.results["passed"] += 1
                status = "✓ PASS"
                if not secondary_match:
                    status += " (secondary domains differ)"
            else:
                cross_results["failed"] += 1
                self.results["failed"] += 1
                status = f"✗ FAIL (got: {result.get('primary_domain')})"

            cross_results["tests"].append(result)
            print(f"  {status}: {query[:60]}...")
            if self.verbose:
                print(f"    Expected: {expected_primary} + {expected_secondary}")
                print(
                    f"    Got: {result.get('primary_domain')} + {result.get('secondary_domains', [])}"
                )

        self.results["cross_domain"] = cross_results
        return cross_results

    def test_clarification(self) -> Dict:
        """Test clarification prompts for vague queries."""
        print(f"\n{'='*60}")
        print("Testing Clarification Prompts")
        print(f"{'='*60}")

        clarification_results = {
            "queries_tested": len(CLARIFICATION_TESTS),
            "passed": 0,
            "failed": 0,
            "tests": [],
        }

        for query in CLARIFICATION_TESTS:
            result = self._test_query(query)
            self.results["total_tests"] += 1

            # Check if needs_clarification is True
            if result.get("success") and result.get("needs_clarification"):
                clarification_results["passed"] += 1
                self.results["passed"] += 1
                status = "✓ PASS (clarification triggered)"
            else:
                clarification_results["failed"] += 1
                self.results["failed"] += 1
                status = "✗ FAIL (no clarification)"

            clarification_results["tests"].append(result)
            print(f"  {status}: {query}")

        self.results["clarification"] = clarification_results
        return clarification_results

    def run_all_tests(self):
        """Run all validation tests."""
        print("\n" + "="*60)
        print("PLC COACH DOMAIN VALIDATION - Story 3.10")
        print("="*60)
        print(f"API URL: {self.api_url}")
        print(f"Timestamp: {self.results['timestamp']}")

        # Test each domain
        for domain, queries in DOMAIN_TESTS.items():
            self.test_domain(domain, queries)

        # Test cross-domain
        self.test_cross_domain()

        # Test clarification
        self.test_clarification()

        # Final summary
        self.print_summary()

    def print_summary(self):
        """Print final test summary."""
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)

        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ({pass_rate:.1f}%)")
        print(f"Failed: {failed}")

        # Per-domain summary
        print("\nPer-Domain Results:")
        for domain, results in self.results.get("domains", {}).items():
            domain_pass_rate = (
                results["passed"] / results["queries_tested"] * 100
            )
            print(
                f"  {domain:20s}: {results['passed']}/{results['queries_tested']} ({domain_pass_rate:.1f}%)"
            )

        # Success threshold
        if pass_rate >= 90:
            print(f"\n✅ SUCCESS: {pass_rate:.1f}% pass rate (threshold: 90%)")
            return 0
        else:
            print(f"\n⚠️  BELOW THRESHOLD: {pass_rate:.1f}% pass rate (threshold: 90%)")
            return 1

    def save_results(self, output_file: str):
        """Save results to JSON file."""
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate PLC Coach domain coverage (Story 3.10)"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print detailed test output"
    )
    parser.add_argument(
        "--output",
        default="docs/testing/domain-validation-results.json",
        help="Output file for test results (JSON)",
    )

    args = parser.parse_args()

    validator = DomainValidator(api_url=args.api_url, verbose=args.verbose)

    try:
        validator.run_all_tests()
        validator.save_results(args.output)
        return validator.print_summary()
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nValidation failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
