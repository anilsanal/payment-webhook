"""
Tests for app/webhook_app.py business logic.

CAVEAT: importing app.webhook_app opens a real ThreadedConnectionPool to
Postgres at module import time (see the `_db_pool = ...` line near the top
of webhook_app.py) - that's existing production behavior, not something
these tests introduce. As a result, these tests can only run on a machine
with access to the configured database (e.g. this server), not in an
isolated/DB-less CI runner. The lookup_* functions themselves don't touch
the DB directly - they read from the in-memory _mapping_cache dict, which
we monkeypatch below instead of relying on the real cache contents.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import webhook_app as wa


# ---------------------------------------------------------------------------
# determine_status
# ---------------------------------------------------------------------------

def test_determine_status_pending():
    assert wa.determine_status('553') == 'pending'


def test_determine_status_success():
    assert wa.determine_status('000') == 'success'


def test_determine_status_declined_for_anything_else():
    assert wa.determine_status('005-39') == 'declined'
    assert wa.determine_status(None) == 'declined'


# ---------------------------------------------------------------------------
# parse_webhook_data
# ---------------------------------------------------------------------------

def test_parse_webhook_data_takes_first_list_value():
    result = wa.parse_webhook_data({'trans_id': ['123', '456']})
    assert result['trans_id'] == '123'


def test_parse_webhook_data_empty_list_becomes_none():
    result = wa.parse_webhook_data({'trans_id': []})
    assert result['trans_id'] is None


def test_parse_webhook_data_empty_string_becomes_none():
    result = wa.parse_webhook_data({'client_email': ''})
    assert result['client_email'] is None


def test_parse_webhook_data_scalar_value_passes_through():
    result = wa.parse_webhook_data({'reply_code': '000'})
    assert result['reply_code'] == '000'


# ---------------------------------------------------------------------------
# lookup_bank_name / lookup_merchant_name / lookup_mid_name
# ---------------------------------------------------------------------------

def _with_cache(bins=None, merchants=None, mids=None):
    original = {k: dict(v) for k, v in wa._mapping_cache.items()}
    wa._mapping_cache['bins'] = bins or {}
    wa._mapping_cache['merchants'] = merchants or {}
    wa._mapping_cache['mids'] = mids or {}
    return original


def _restore_cache(original):
    wa._mapping_cache.update(original)


def test_lookup_bank_name_hit():
    original = _with_cache(bins={'123456': 'Test Bank'})
    try:
        assert wa.lookup_bank_name('123456') == 'Test Bank'
    finally:
        _restore_cache(original)


def test_lookup_bank_name_miss_returns_none():
    original = _with_cache(bins={'123456': 'Test Bank'})
    try:
        assert wa.lookup_bank_name('999999') is None
    finally:
        _restore_cache(original)


def test_lookup_bank_name_handles_empty_input():
    assert wa.lookup_bank_name(None) is None
    assert wa.lookup_bank_name('') is None


def test_lookup_merchant_name_hit():
    original = _with_cache(merchants={'1885994': 'Panelix [LIVE]'})
    try:
        assert wa.lookup_merchant_name('1885994') == 'Panelix [LIVE]'
    finally:
        _restore_cache(original)


def test_lookup_mid_name_hit():
    original = _with_cache(mids={'414622153451': 'Sendsco - LIVE - Mastercard 26'})
    try:
        assert wa.lookup_mid_name('414622153451') == 'Sendsco - LIVE - Mastercard 26'
    finally:
        _restore_cache(original)
