import pytest
from benchmark import run_benchmark

def test_benchmark_accuracy_and_fnr():
    """Verify that the compliance benchmark meets safety-critical thresholds (>95% accuracy, 0% FNR)."""
    accuracy, fnr, fpr, latency = run_benchmark()
    assert accuracy >= 95.0, f"Accuracy {accuracy}% is below target 95%"
    assert fnr == 0.0, f"False Negative Rate {fnr}% must be 0.0% for compliant filings"
    assert fpr == 0.0, f"False Positive Rate {fpr}% must be 0.0% for illegal filings"
    assert latency < 5.0, f"Mean latency {latency}ms exceeds 5ms requirement"
