import pytest

from models import Check,LatencyRule, StatusCode, ContentRule, Endpoint
from client import build_reports

# ---------------------------------------------------------
#       Endpoints.rules   TEST
# ---------------------------------------------------------

#       Latency Test
def test_latency_rule_passes_when_fast():
    rule = LatencyRule(500)
    fast = Check(latency=100, status_code=200, body="{}")
    assert rule.check(fast) is True
    
    
def test_latency_rule_fails_when_slow():
    rule = LatencyRule(500)
    slow = Check(latency=900, status_code=200, body="{}")
    assert rule.check(slow) is False
    
#       Code Test
def test_status_code_rule_passes_when_200():
    rule = StatusCode({200})
    code_200 = Check(latency=100, status_code=200, body="{}")
    assert rule.check(code_200) is True

def test_status_code_rule_fail_when_no_200():
    rule = StatusCode({200})
    code_400 = Check(latency=100, status_code=400, body="{}")
    assert rule.check(code_400) is False
    
#       Body Test
# - with no content rules, just check parseable JSON
def test_content_rule_passes_when_is_json():
    rule = ContentRule()
    text_json = Check(latency=100, status_code=200, body='{"msg":"body-test-rule"}')
    assert rule.check(text_json) is True

def test_content_rule_fails_when_not_json():
    rule = ContentRule()
    garbage = Check(latency=100, status_code=200, body="this is not json")
    assert rule.check(garbage) is False

# - with content rules
def test_content_rule_passes_with_match():
    rule = ContentRule("body-test-rule")
    body_test = Check(latency=100, status_code=200, body='{"msg":"body-test-rule"}')
    assert rule.check(body_test) is True

def test_content_rule_fail_with_no_match():
    rule = ContentRule("body-test-rule")
    body_test = Check(latency=100, status_code=200, body='{"msg":"no-match-here"}')
    assert rule.check(body_test) is False
    
    
    
# ---------------------------------------------------------
#       build_reports   TEST
# ---------------------------------------------------------

@pytest.fixture
def endpoint():
    return Endpoint(name="test", url="x", rules=[LatencyRule(500), StatusCode({200})])

# HEALTHY -> all pass
def test_report_is_healthy_when_all_pass(endpoint):
    check = Check(latency=100, status_code=200, body="{}")
    reports = build_reports([(endpoint, check)])       
    assert reports[0].state == "healthy"

# DEGRADED -> latency != latencyRule
def test_report_is_degraded_when_slow(endpoint):
    check = Check(latency=800, status_code=200, body="{}")
    reports = build_reports([(endpoint, check)])
    assert reports[0].state == "degraded"
    
# DOWN -> status code fails
def test_report_is_down_when_status_fails(endpoint):
    check = Check(latency=100, status_code=400, body="{}")
    reports = build_reports([(endpoint, check)])
    assert reports[0].state == "down"
    
# DOWN -> check is None (No respose)
def test_report_is_down_when_no_response(endpoint):
    check = None
    reports = build_reports([(endpoint, check)])
    assert reports[0].state == "down"