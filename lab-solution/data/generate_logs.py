"""Script tạo và làm mới dữ liệu file log thực tế cho bài Lab Log Analyzer."""

import os
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent
LOG_FILE = DATA_DIR / "app.log"

SAMPLE_LOG_ENTRIES = [
    # (relative_minutes_ago, level, service, trace_id, message, traceback_str)
    (55, "INFO", "api-gateway", "req-001a8f", "Incoming GET /api/v1/health from 10.0.0.12 - 200 OK (2ms)", None),
    (50, "INFO", "auth-service", "req-002bc3", "User usr_1042 successfully authenticated via OAuth2", None),
    (48, "INFO", "order-service", "req-003de4", "Creating new order ORD-2026-9901 for user usr_1042 (total: $149.99)", None),
    (45, "WARNING", "inventory-service", "req-004f5a", "Low stock warning for SKU-8841 (Remaining: 2 units)", None),
    (42, "INFO", "payment-service", "req-005a1b", "Initiating Stripe payment charge for order ORD-2026-9901", None),
    (40, "ERROR", "payment-service", "req-005a1b", "PaymentGatewayError: 502 Bad Gateway from upstream endpoint https://api.stripe.com/v1/charges", 
     """Traceback (most recent call last):
  File "/app/services/payment.py", line 84, in process_charge
    response = httpx.post(STRIPE_ENDPOINT, json=payload, timeout=5.0)
  File "/app/vendor/httpx/_client.py", line 1024, in post
    return self.request("POST", url, data=data, json=json)
httpx.HTTPStatusError: 502 Server Error: Bad Gateway for url: https://api.stripe.com/v1/charges"""),
    (38, "INFO", "payment-service", "req-006c7d", "Retrying payment charge for order ORD-2026-9901 (attempt 2/3)", None),
    (37, "INFO", "payment-service", "req-006c7d", "Payment charge succeeded on retry for order ORD-2026-9901", None),
    (32, "WARNING", "auth-service", "req-007e8f", "Rate limit exceeded (429) for IP 192.168.1.99 - 100 requests/minute", None),
    (28, "ERROR", "auth-service", "req-008f9a", "AuthenticationFailedException: Invalid signature on JWT bearer token for user_id=usr_8492",
     """Traceback (most recent call last):
  File "/app/services/auth.py", line 112, in verify_jwt
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
  File "/app/vendor/jwt/api_jwt.py", line 156, in decode
    raise InvalidSignatureError("Signature verification failed")
jwt.exceptions.InvalidSignatureError: Signature verification failed"""),
    (25, "INFO", "order-service", "req-009a2b", "Batch job archive_completed_orders started (processing 450 orders)", None),
    (20, "ERROR", "order-service", "req-010b3c", "psycopg2.OperationalError: Connection to database host db-postgres:5432 timed out after 30000ms",
     """Traceback (most recent call last):
  File "/app/db/connection.py", line 45, in get_db_cursor
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
  File "/app/vendor/psycopg2/__init__.py", line 122, in connect
    dsn = _ext.make_dsn(dsn, **kwargs)
psycopg2.OperationalError: could not connect to server: Connection timed out
\tIs the server running on host "db-postgres" (10.0.4.15) and accepting
\tTCP/IP connections on port 5432?"""),
    (18, "WARNING", "order-service", "req-011c4d", "Database pool fallback to read-replica db-replica-01 enabled", None),
    (15, "INFO", "inventory-service", "req-012d5e", "Inventory cache refreshed (total SKUs indexed: 14,200)", None),
    (10, "CRITICAL", "worker-service", "req-013e6f", "MemoryLimitExceededError: Worker process exceeded hard limit of 2048MB (current RSS: 2150MB), trigger OOM-kill",
     """Traceback (most recent call last):
  File "/app/workers/memory_monitor.py", line 67, in check_health
    raise MemoryLimitExceededError(f"Process {os.getpid()} exceeded threshold: {mem_mb}MB")
workers.exceptions.MemoryLimitExceededError: Worker process 4812 exceeded threshold: 2150MB"""),
    (8, "WARNING", "worker-service", "req-014f7a", "Spawning new replacement worker process (pid: 5920)", None),
    (5, "ERROR", "api-gateway", "req-015a8b", "SchemaValidationError: Missing required field 'customer_email' in payload for POST /api/v1/checkout",
     """Traceback (most recent call last):
  File "/app/middleware/validator.py", line 32, in validate_body
    schema.validate(body)
  File "/app/vendor/pydantic/main.py", line 521, in validate
    raise ValidationError("Field 'customer_email' is required but missing")
pydantic.error_wrappers.ValidationError: 1 validation error for CheckoutPayload
customer_email
  Field required (type=value_error.missing)"""),
    (2, "INFO", "api-gateway", "req-016b9c", "Incoming GET /api/v1/metrics from Prometheus scraper - 200 OK (5ms)", None),
    (1, "INFO", "api-gateway", "req-017c0d", "Heartbeat check PASSED for all 6 microservices", None),
]


def generate_logs(output_path: Path = LOG_FILE) -> None:
    """Tạo file app.log với timestamp thời gian thực dựa trên thời điểm chạy."""
    now = datetime.now()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for mins_ago, level, service, trace_id, msg, tb in SAMPLE_LOG_ENTRIES:
        timestamp = (now - timedelta(minutes=mins_ago)).strftime("%Y-%m-%d %H:%M:%S")
        log_header = f"[{timestamp}] [{level:<8}] [{service:<17}] [{trace_id}] {msg}"
        lines.append(log_header)
        if tb:
            # Ghi stacktrace thụt lề rõ ràng
            for tb_line in tb.strip().splitlines():
                lines.append(f"    {tb_line}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ Đã tạo thành công file log thực tế tại: {output_path} ({len(lines)} dòng)")


if __name__ == "__main__":
    generate_logs()
