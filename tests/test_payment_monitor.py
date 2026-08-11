"""
Tests for services/payment_monitor.py business logic.

No live database is required for these tests: check_route_health takes a
cursor as an argument, so a fake cursor stands in for it. The other
functions under test are pure.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import payment_monitor as pm


class FakeCursor:
    """Stands in for a psycopg2 RealDictCursor: .execute() is a no-op,
    .fetchone() returns whatever dict was configured."""

    def __init__(self, fetchone_result):
        self._fetchone_result = fetchone_result

    def execute(self, *args, **kwargs):
        pass

    def fetchone(self):
        return self._fetchone_result


# ---------------------------------------------------------------------------
# should_exclude_mid
# ---------------------------------------------------------------------------

def test_should_exclude_mid_by_id():
    assert pm.should_exclude_mid('43110201461', 'Anything') is True


def test_should_exclude_mid_by_name_case_insensitive():
    assert pm.should_exclude_mid('999', 'Timesaver Terminal') is True
    assert pm.should_exclude_mid('999', 'TIMESAVER') is True
    assert pm.should_exclude_mid('999', 'Some Networxpay MID') is True


def test_should_exclude_mid_normal_mid_not_excluded():
    assert pm.should_exclude_mid('4141119152227', 'Sendsco - LIVE - Mastercard 8') is False


def test_should_exclude_mid_handles_none():
    assert pm.should_exclude_mid(None, None) is False


# ---------------------------------------------------------------------------
# should_exclude_decline
# ---------------------------------------------------------------------------

def test_should_exclude_decline_insufficient_funds():
    assert pm.should_exclude_decline('Insufficient Funds') is True
    assert pm.should_exclude_decline('insufficient fund') is True


def test_should_exclude_decline_risk_management():
    assert pm.should_exclude_decline("Transaction didn't pass risk management system") is True


def test_should_exclude_decline_normal_reason_not_excluded():
    assert pm.should_exclude_decline('Invalid card number') is False


def test_should_exclude_decline_handles_empty():
    assert pm.should_exclude_decline(None) is False
    assert pm.should_exclude_decline('') is False


# ---------------------------------------------------------------------------
# check_route_health
# ---------------------------------------------------------------------------

def test_check_route_health_disabled_always_alerts():
    original = pm.SMART_FILTER_CONFIG['enabled']
    pm.SMART_FILTER_CONFIG['enabled'] = False
    try:
        result = pm.check_route_health(FakeCursor(None), 'mid', 'bank')
        assert result == {'should_alert': True, 'reason': 'smart_filtering_disabled'}
    finally:
        pm.SMART_FILTER_CONFIG['enabled'] = original


def test_check_route_health_insufficient_data():
    # total_7d below min_transactions_for_analysis (10)
    stats = {'success_24h': 1, 'total_24h': 2, 'success_7d': 3, 'total_7d': 5}
    result = pm.check_route_health(FakeCursor(stats), 'mid', 'bank')
    assert result['should_alert'] is True
    assert result['reason'] == 'insufficient_data'


def test_check_route_health_healthy_route():
    # >10% success in 24h -> healthy, should alert on failures
    stats = {'success_24h': 5, 'total_24h': 20, 'success_7d': 20, 'total_7d': 100}
    result = pm.check_route_health(FakeCursor(stats), 'mid', 'bank')
    assert result['should_alert'] is True
    assert result['reason'] == 'healthy_route'


def test_check_route_health_regression():
    # >10% in 7d but <=10% in 24h -> regression, critical
    stats = {'success_24h': 0, 'total_24h': 15, 'success_7d': 20, 'total_7d': 100}
    result = pm.check_route_health(FakeCursor(stats), 'mid', 'bank')
    assert result['should_alert'] is True
    assert result['reason'] == 'regression'
    assert result['severity_upgrade'] == 'CRITICAL'


def test_check_route_health_dead_route_suppressed():
    # <=10% in both windows -> dead route, suppress
    stats = {'success_24h': 0, 'total_24h': 15, 'success_7d': 2, 'total_7d': 50}
    result = pm.check_route_health(FakeCursor(stats), 'mid', 'bank')
    assert result['should_alert'] is False
    assert result['reason'] == 'dead_route'
    assert result['suppression_reason'] == 'low_success_rate'


def test_check_route_health_dead_route_zero_success_ever():
    stats = {'success_24h': 0, 'total_24h': 15, 'success_7d': 0, 'total_7d': 50}
    result = pm.check_route_health(FakeCursor(stats), 'mid', 'bank')
    assert result['should_alert'] is False
    assert result['suppression_reason'] == 'dead_route'


def test_check_route_health_null_stats_treated_as_zero():
    # postgres COUNT(*) FILTER can return NULL rather than 0 for empty groups
    stats = {'success_24h': None, 'total_24h': None, 'success_7d': None, 'total_7d': None}
    result = pm.check_route_health(FakeCursor(stats), 'mid', 'bank')
    assert result['should_alert'] is True
    assert result['reason'] == 'insufficient_data'


# ---------------------------------------------------------------------------
# escape_html
# ---------------------------------------------------------------------------

def test_escape_html_escapes_special_characters():
    assert pm.escape_html('<b>Test & "quotes"</b>') == '&lt;b&gt;Test &amp; "quotes"&lt;/b&gt;'


def test_escape_html_handles_none():
    assert pm.escape_html(None) is None
