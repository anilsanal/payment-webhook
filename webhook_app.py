#!/usr/bin/env python3
"""
Payment Gateway Webhook Receiver
Receives transaction webhooks from Coriunder and stores in PostgreSQL
Updated to use trans_order as unique identifier and include merchant names
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging
from urllib.parse import parse_qs
import os
from contextlib import contextmanager
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('/opt/payment-webhook/.env')

# Create logs directory if it doesn't exist
log_dir = './logs'
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/webhook_receiver.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Payment Webhook Receiver", version="2.1.0")

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'payment_transactions'),
    'user': os.getenv('DB_USER', 'webhook_user'),
    'password': os.getenv('DB_PASSWORD', 'yingyanganil5s'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Slack configuration
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def send_slack_notification(status_code, error_message, webhook_data, request_info):
    """Send error notification to Slack channel"""
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook URL not configured, skipping notification")
        return False

    try:
        # Sanitize sensitive data
        safe_data = webhook_data.copy()
        if 'signature' in safe_data:
            safe_data['signature'] = '***REDACTED***'
        if 'payment_details' in safe_data:
            safe_data['payment_details'] = safe_data['payment_details'][:20] + '...' if safe_data.get('payment_details') else None

        # Build Slack message
        color = "#ff0000" if status_code >= 500 else "#ff9900"  # Red for 500s, orange for 400s

        slack_message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 Webhook Error - {status_code}",
                    "fields": [
                        {
                            "title": "Error Message",
                            "value": f"```{error_message}```",
                            "short": False
                        },
                        {
                            "title": "Trans ID",
                            "value": webhook_data.get('trans_id', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "Trans Order",
                            "value": webhook_data.get('trans_order', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "Reply Code",
                            "value": webhook_data.get('reply_code', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "Merchant ID",
                            "value": webhook_data.get('merchant_id', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "Request Method",
                            "value": request_info.get('method', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "Client IP",
                            "value": request_info.get('client_ip', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "Webhook Data (Sanitized)",
                            "value": f"```{json.dumps(safe_data, indent=2)[:500]}...```",
                            "short": False
                        }
                    ],
                    "footer": "Payment Webhook Monitor",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=slack_message,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )

        if response.status_code == 200:
            logger.info(f"Slack notification sent successfully for {status_code} error")
            return True
        else:
            logger.error(f"Failed to send Slack notification: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}", exc_info=True)
        return False

def determine_status(reply_code):
    """Determine transaction status based on reply_code"""
    if reply_code == '553':
        return 'pending'
    elif reply_code == '000':
        return 'success'
    else:
        return 'declined'

def parse_webhook_data(form_data):
    """Parse and clean webhook form data"""
    data = {}
    for key, value in form_data.items():
        # Get first value if it's a list
        if isinstance(value, list):
            data[key] = value[0] if value else None
        else:
            data[key] = value
        
        # Convert empty strings to None
        if data[key] == '':
            data[key] = None
    
    return data

def log_data_issue(trans_order, trans_id, issue_type, field_name, field_value, error_message, raw_data, cursor):
    """Log data quality issues"""
    try:
        cursor.execute("""
            INSERT INTO webhook_data_issues 
            (trans_order, trans_id, issue_type, field_name, field_value, error_message, raw_webhook_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (trans_order, trans_id, issue_type, field_name, str(field_value), error_message, str(raw_data)))
        logger.warning(f"Data issue logged: {issue_type} for {field_name} in {trans_order}")
    except Exception as e:
        logger.error(f"Failed to log data issue: {e}")

def validate_webhook_data(data, cursor):
    """Validate webhook data and log issues"""
    issues = []
    
    # Required fields
    required_fields = ['trans_order', 'reply_code', 'merchant_id', 'trans_date']
    for field in required_fields:
        if not data.get(field):
            issues.append({
                'issue_type': 'missing_field',
                'field_name': field,
                'field_value': data.get(field),
                'error_message': f'Required field {field} is missing or empty'
            })
    
    # Check if BIN exists in mapping
    cc_bin = data.get('ccBIN')
    if cc_bin:
        cursor.execute("SELECT bin FROM bin_bank_mapping WHERE bin = %s", (cc_bin,))
        if not cursor.fetchone():
            issues.append({
                'issue_type': 'missing_bin_mapping',
                'field_name': 'ccBIN',
                'field_value': cc_bin,
                'error_message': f'BIN {cc_bin} not found in bin_bank_mapping table'
            })
    else:
        issues.append({
            'issue_type': 'missing_optional',
            'field_name': 'ccBIN',
            'field_value': None,
            'error_message': 'BIN field is missing from webhook'
        })
    
    # Check if merchant exists in mapping
    merchant_id = data.get('merchant_id')
    if merchant_id:
        cursor.execute("SELECT merchant_id FROM merchant_mapping WHERE merchant_id = %s", (merchant_id,))
        if not cursor.fetchone():
            issues.append({
                'issue_type': 'missing_merchant_mapping',
                'field_name': 'merchant_id',
                'field_value': merchant_id,
                'error_message': f'Merchant ID {merchant_id} not found in merchant_mapping table'
            })
    
    # Important optional fields
    important_fields = ['client_email', 'client_fullname', 'trans_amount']
    for field in important_fields:
        if not data.get(field):
            issues.append({
                'issue_type': 'missing_optional',
                'field_name': field,
                'field_value': data.get(field),
                'error_message': f'Optional but important field {field} is missing'
            })
    
    # Log all issues
    for issue in issues:
        log_data_issue(
            data.get('trans_order'),
            data.get('trans_id'),
            issue['issue_type'],
            issue['field_name'],
            issue['field_value'],
            issue['error_message'],
            data,
            cursor
        )
    
    return len(issues)

def get_bank_name(ccbin, cursor):
    """Get bank name from BIN mapping table"""
    if not ccbin:
        return None
    
    try:
        cursor.execute(
            "SELECT bank_name FROM bin_bank_mapping WHERE bin = %s",
            (ccbin,)
        )
        result = cursor.fetchone()
        return result['bank_name'] if result else None
    except Exception as e:
        logger.warning(f"Could not fetch bank name for BIN {ccbin}: {e}")
        return None

def get_merchant_name(merchant_id, cursor):
    """Get merchant name from merchant mapping table"""
    if not merchant_id:
        return None

    try:
        cursor.execute(
            "SELECT merchant_name FROM merchant_mapping WHERE merchant_id = %s",
            (merchant_id,)
        )
        result = cursor.fetchone()
        return result['merchant_name'] if result else None
    except Exception as e:
        logger.warning(f"Could not fetch merchant name for ID {merchant_id}: {e}")
        return None

def get_mid_name(mid_id, cursor):
    """Get terminal name from mid mapping table"""
    if not mid_id:
        return None

    try:
        cursor.execute(
            "SELECT terminal_name FROM mid_mapping WHERE mid_id = %s",
            (mid_id,)
        )
        result = cursor.fetchone()
        return result['terminal_name'] if result else None
    except Exception as e:
        logger.warning(f"Could not fetch terminal name for MidID {mid_id}: {e}")
        return None

def insert_webhook_event(data, status, cursor):
    """Insert webhook event into webhook_events table (audit trail)"""

    insert_query = """
    INSERT INTO webhook_events (
        trans_id, trans_order, reply_code, reply_desc, status,
        trans_date, otrans_amount, trans_amount,
        otrans_currency, trans_currency,
        merchant_id, merchant_name, client_fullname, client_phone, client_email,
        payment_details, exp_month, exp_year, trans_type,
        signature, system_reference,
        debit_company, debrefnum, debrefcode, debit_companyname,
        is3d, is_refund,
        client_address, client_address2, client_zipcode,
        client_country, client_city,
        bin_country, pm, cc_bin, bank_name,
        plid, storage_id, mid_id, mid_name, recon_id, cp26, cp27, cp28, cp29, cp30,
        raw_data
    ) VALUES (
        %(trans_id)s, %(trans_order)s, %(reply_code)s, %(reply_desc)s, %(status)s,
        %(trans_date)s, %(otrans_amount)s, %(trans_amount)s,
        %(otrans_currency)s, %(trans_currency)s,
        %(merchant_id)s, %(merchant_name)s, %(client_fullname)s, %(client_phone)s, %(client_email)s,
        %(payment_details)s, %(exp_month)s, %(exp_year)s, %(trans_type)s,
        %(signature)s, %(system_reference)s,
        %(debit_company)s, %(debrefnum)s, %(debrefcode)s, %(debit_companyname)s,
        %(is3d)s, %(is_refund)s,
        %(client_address)s, %(client_address2)s, %(client_zipcode)s,
        %(client_country)s, %(client_city)s,
        %(bin_country)s, %(pm)s, %(ccBIN)s, %(bank_name)s,
        %(plid)s, %(StorageID)s, %(mid_id)s, %(mid_name)s, %(recon_id)s, %(CP26)s, %(CP27)s, %(CP28)s, %(CP29)s, %(CP30)s,
        %(raw_data)s
    )
    RETURNING id;
    """

    # Get bank name, merchant name, and mid name
    bank_name = get_bank_name(data.get('ccBIN'), cursor)
    merchant_name = get_merchant_name(data.get('merchant_id'), cursor)
    mid_name = get_mid_name(data.get('MidID'), cursor)
    
    params = {
        'trans_id': data.get('trans_id'),
        'trans_order': data.get('trans_order'),
        'reply_code': data.get('reply_code'),
        'reply_desc': data.get('reply_desc'),
        'status': status,
        'trans_date': data.get('trans_date'),
        'otrans_amount': data.get('otrans_amount'),
        'trans_amount': data.get('trans_amount'),
        'otrans_currency': data.get('otrans_currency'),
        'trans_currency': data.get('trans_currency'),
        'merchant_id': data.get('merchant_id'),
        'merchant_name': merchant_name,
        'client_fullname': data.get('client_fullname'),
        'client_phone': data.get('client_phone'),
        'client_email': data.get('client_email'),
        'payment_details': data.get('payment_details'),
        'exp_month': data.get('exp_month'),
        'exp_year': data.get('exp_year'),
        'trans_type': data.get('trans_type'),
        'signature': data.get('signature'),
        'system_reference': data.get('system_reference'),
        'debit_company': data.get('debit_company'),
        'debrefnum': data.get('debrefnum'),
        'debrefcode': data.get('debrefcode'),
        'debit_companyname': data.get('debit_companyname'),
        'is3d': data.get('is3d'),
        'is_refund': data.get('isRefund'),
        'client_address': data.get('client_address'),
        'client_address2': data.get('client_address2'),
        'client_zipcode': data.get('client_zipcode'),
        'client_country': data.get('client_country'),
        'client_city': data.get('client_city'),
        'bin_country': data.get('bin_country'),
        'pm': data.get('pm'),
        'ccBIN': data.get('ccBIN'),
        'bank_name': bank_name,
        'plid': data.get('plid'),
        'StorageID': data.get('StorageID'),
        'mid_id': data.get('MidID'),
        'mid_name': mid_name,
        'recon_id': data.get('ReconID'),
        'CP26': data.get('CP26'),
        'CP27': data.get('CP27'),
        'CP28': data.get('CP28'),
        'CP29': data.get('CP29'),
        'CP30': data.get('CP30'),
        'raw_data': str(data)
    }
    
    cursor.execute(insert_query, params)
    result = cursor.fetchone()
    return result['id']

def upsert_transaction(data, status, cursor):
    """
    Insert or update transaction in transactions table based on trans_order.
    This keeps only the latest status for each transaction.
    """
    
    upsert_query = """
    INSERT INTO transactions (
        trans_order, trans_id, reply_code, reply_desc, status,
        trans_date, otrans_amount, trans_amount,
        otrans_currency, trans_currency,
        merchant_id, merchant_name, client_fullname, client_phone, client_email,
        payment_details, exp_month, exp_year, trans_type,
        system_reference,
        debit_company, debrefnum, debrefcode, debit_companyname,
        is3d, is_refund,
        client_address, client_address2, client_zipcode,
        client_country, client_city,
        bin_country, pm, cc_bin, bank_name,
        mid_id, mid_name, recon_id,
        first_seen_at, last_updated_at
    ) VALUES (
        %(trans_order)s, %(trans_id)s, %(reply_code)s, %(reply_desc)s, %(status)s,
        %(trans_date)s, %(otrans_amount)s, %(trans_amount)s,
        %(otrans_currency)s, %(trans_currency)s,
        %(merchant_id)s, %(merchant_name)s, %(client_fullname)s, %(client_phone)s, %(client_email)s,
        %(payment_details)s, %(exp_month)s, %(exp_year)s, %(trans_type)s,
        %(system_reference)s,
        %(debit_company)s, %(debrefnum)s, %(debrefcode)s, %(debit_companyname)s,
        %(is3d)s, %(is_refund)s,
        %(client_address)s, %(client_address2)s, %(client_zipcode)s,
        %(client_country)s, %(client_city)s,
        %(bin_country)s, %(pm)s, %(ccBIN)s, %(bank_name)s,
        %(mid_id)s, %(mid_name)s, %(recon_id)s,
        NOW(), NOW()
    )
    ON CONFLICT (trans_order) DO UPDATE SET
        trans_id = EXCLUDED.trans_id,
        reply_code = EXCLUDED.reply_code,
        reply_desc = EXCLUDED.reply_desc,
        status = EXCLUDED.status,
        system_reference = EXCLUDED.system_reference,
        trans_date = EXCLUDED.trans_date,
        merchant_name = EXCLUDED.merchant_name,
        mid_id = EXCLUDED.mid_id,
        mid_name = EXCLUDED.mid_name,
        recon_id = EXCLUDED.recon_id,
        last_updated_at = NOW();
    """

    # Get bank name, merchant name, and mid name
    bank_name = get_bank_name(data.get('ccBIN'), cursor)
    merchant_name = get_merchant_name(data.get('merchant_id'), cursor)
    mid_name = get_mid_name(data.get('MidID'), cursor)
    
    params = {
        'trans_order': data.get('trans_order'),
        'trans_id': data.get('trans_id'),
        'reply_code': data.get('reply_code'),
        'reply_desc': data.get('reply_desc'),
        'status': status,
        'trans_date': data.get('trans_date'),
        'otrans_amount': data.get('otrans_amount'),
        'trans_amount': data.get('trans_amount'),
        'otrans_currency': data.get('otrans_currency'),
        'trans_currency': data.get('trans_currency'),
        'merchant_id': data.get('merchant_id'),
        'merchant_name': merchant_name,
        'client_fullname': data.get('client_fullname'),
        'client_phone': data.get('client_phone'),
        'client_email': data.get('client_email'),
        'payment_details': data.get('payment_details'),
        'exp_month': data.get('exp_month'),
        'exp_year': data.get('exp_year'),
        'trans_type': data.get('trans_type'),
        'system_reference': data.get('system_reference'),
        'debit_company': data.get('debit_company'),
        'debrefnum': data.get('debrefnum'),
        'debrefcode': data.get('debrefcode'),
        'debit_companyname': data.get('debit_companyname'),
        'is3d': data.get('is3d'),
        'is_refund': data.get('isRefund'),
        'client_address': data.get('client_address'),
        'client_address2': data.get('client_address2'),
        'client_zipcode': data.get('client_zipcode'),
        'client_country': data.get('client_country'),
        'client_city': data.get('client_city'),
        'bin_country': data.get('bin_country'),
        'pm': data.get('pm'),
        'ccBIN': data.get('ccBIN'),
        'bank_name': bank_name,
        'mid_id': data.get('MidID'),
        'mid_name': mid_name,
        'recon_id': data.get('ReconID')
    }
    
    cursor.execute(upsert_query, params)

@app.api_route("/webhook", methods=["GET", "POST"])
async def receive_webhook(request: Request):
    """
    Endpoint to receive webhooks from Coriunder payment gateway
    Accepts both GET (query parameters) and POST (form data) requests
    Uses trans_order as the unique identifier for transaction lifecycle
    """
    # Capture request information for error notifications
    request_info = {
        'method': request.method,
        'client_ip': request.client.host if request.client else 'unknown'
    }
    data = {}

    try:
        # Parse data based on request method
        if request.method == "GET":
            # Parse query parameters for GET requests
            data = parse_webhook_data(dict(request.query_params))
        else:
            # Parse form data for POST requests
            form_data = await request.form()
            data = parse_webhook_data(dict(form_data))
        
        logger.info(f"Received webhook for trans_order: {data.get('trans_order')}, trans_id: {data.get('trans_id')}, reply_code: {data.get('reply_code')}")

        # Use trans_id as fallback if trans_order is missing
        if not data.get('trans_order') and data.get('trans_id'):
            logger.warning(f"trans_order missing, using trans_id as fallback: {data.get('trans_id')}")
            data['trans_order'] = f"TXID_{data.get('trans_id')}"

        # Validate required fields - trans_order (or trans_id) is the key identifier
        if not data.get('trans_order') or not data.get('reply_code'):
            error_msg = "Missing required fields: trans_order/trans_id and reply_code"
            logger.error(f"Response sent (400): {error_msg}")
            send_slack_notification(400, error_msg, data, request_info)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Determine status
        status = determine_status(data.get('reply_code'))

        # Store in database
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Validate data and log issues (but don't fail the webhook)
                issues_count = validate_webhook_data(data, cursor)
                if issues_count > 0:
                    logger.warning(f"Webhook has {issues_count} data quality issues")

                # Insert into webhook_events (audit trail - keeps all webhooks)
                event_id = insert_webhook_event(data, status, cursor)
                logger.info(f"Inserted webhook event with id: {event_id}")

                # Upsert into transactions (latest status only - keyed by trans_order)
                upsert_transaction(data, status, cursor)
                logger.info(f"Updated transaction table for trans_order: {data.get('trans_order')} with status: {status}")

        response_data = {
            "status": "success",
            "message": "Webhook processed successfully",
            "trans_order": data.get('trans_order'),
            "trans_id": data.get('trans_id'),
            "status_determined": status
        }
        logger.info(f"Response sent (200): {response_data}")
        return JSONResponse(status_code=200, content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"Internal server error: {str(e)}"
        logger.error(f"Response sent (500): {error_detail}", exc_info=True)
        send_slack_notification(500, error_detail, data, request_info)
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Payment Gateway Webhook Receiver",
        "version": "2.1.0",
        "status": "running",
        "features": [
            "trans_order based transaction lifecycle tracking",
            "Bank name lookup from BIN",
            "Merchant name lookup from merchant_id",
            "Support for both GET and POST webhook requests",
            "MidID and ReconID field support"
        ],
        "endpoints": {
            "webhook": "/webhook (GET, POST)",
            "health": "/health (GET)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
