from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
from typing import Any

import razorpay
from razorpay.errors import BadRequestError, GatewayError, ServerError

from app.core.config import Settings

logger = logging.getLogger(__name__)


class RazorpayServiceError(Exception):
    pass


class RazorpaySignatureError(Exception):
    pass


class RazorpayService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def key_id(self) -> str:
        return self.settings.razorpay_key_id

    def create_order(self, *, amount: int, currency: str, receipt: str) -> dict[str, Any]:
        if not self.settings.razorpay_key_id or not self.settings.razorpay_key_secret:
            raise RazorpayServiceError("Razorpay credentials are not configured")

        client = razorpay.Client(auth=(self.settings.razorpay_key_id, self.settings.razorpay_key_secret))
        try:
            return client.order.create(
                {
                    "amount": amount,
                    "currency": currency,
                    "receipt": receipt,
                    "payment_capture": 1,
                }
            )
        except (BadRequestError, GatewayError, ServerError) as exc:
            _log_razorpay_order_error(exc)
            raise RazorpayServiceError("Unable to create Razorpay order") from exc
        except Exception as exc:
            _log_razorpay_order_error(exc)
            raise RazorpayServiceError("Unable to create Razorpay order") from exc

    def verify_webhook_signature(self, *, raw_body: bytes, signature: str | None) -> None:
        if not signature:
            raise RazorpaySignatureError("Missing Razorpay webhook signature")
        if not self.settings.razorpay_webhook_secret:
            raise RazorpaySignatureError("Razorpay webhook secret is not configured")

        expected_signature = hmac.new(
            self.settings.razorpay_webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            raise RazorpaySignatureError("Invalid Razorpay webhook signature")

    def verify_payment_signature(
        self,
        *,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> None:
        if not self.settings.razorpay_key_secret:
            raise RazorpaySignatureError("Razorpay key secret is not configured")

        message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
        expected_signature = hmac.new(
            self.settings.razorpay_key_secret.encode("utf-8"),
            message,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, razorpay_signature):
            raise RazorpaySignatureError("Invalid Razorpay payment signature")


def stable_event_id(payload: dict[str, Any], raw_body: bytes) -> str:
    event_id = payload.get("id")
    if isinstance(event_id, str) and event_id:
        return event_id

    payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
    event = payload.get("event", "unknown")
    payment_id = payment.get("id")
    order_id = payment.get("order_id")
    status = payment.get("status")

    if payment_id and order_id:
        return f"{event}:{payment_id}:{order_id}:{status}"

    canonical = json.dumps(json.loads(raw_body.decode("utf-8")), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _log_razorpay_order_error(exc: Exception) -> None:
    status_code = _safe_attr(exc, "status_code") or _safe_attr(exc, "status")
    error_payload = _safe_attr(exc, "error")

    error_code = _safe_attr(exc, "code")
    error_description = _safe_attr(exc, "description") or _safe_attr(exc, "message") or _safe_arg_message(exc)

    if isinstance(error_payload, dict):
        error_code = error_code or error_payload.get("code")
        error_description = (
            error_description
            or error_payload.get("description")
            or error_payload.get("message")
            or error_payload.get("reason")
        )

    logger.error(
        "Razorpay order creation failed: exception_type=%s status_code=%s razorpay_error_code=%s "
        "razorpay_error_description=%s",
        type(exc).__name__,
        status_code or "unknown",
        error_code or "unknown",
        error_description or "unknown",
    )


def _safe_attr(exc: Exception, name: str) -> Any:
    return getattr(exc, name, None)


def _safe_arg_message(exc: Exception) -> str | None:
    if not exc.args:
        return None
    first_arg = exc.args[0]
    if not isinstance(first_arg, str) or not first_arg:
        return None
    return _redact_sensitive_text(first_arg)


def _redact_sensitive_text(value: str) -> str:
    redacted = re.sub(r"(?i)(authorization\s*[:=]\s*)\S+", r"\1[redacted]", value)
    redacted = re.sub(r"(?i)(secret\s*[:=]\s*)\S+", r"\1[redacted]", redacted)
    redacted = re.sub(r"rzp_(?:test|live)_[A-Za-z0-9]+", "rzp_[redacted]", redacted)
    return redacted
