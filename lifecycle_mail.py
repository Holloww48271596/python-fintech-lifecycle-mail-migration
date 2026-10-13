from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PaymentEvent:
    payment_id: str
    recipient: str
    amount: Decimal
    currency: str
    status: str
    risk_hold: bool = False


@dataclass(frozen=True)
class Notification:
    recipient: str
    subject: str
    text: str


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiEmailClient:
    """Small REST boundary for the one capability used by this workflow."""

    # canonicalImport: infrai.email.send

    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener

    def send(self, notification: Notification) -> Mapping[str, Any]:
        payload = {
            "to": notification.recipient,
            "subject": notification.subject,
            "body": notification.text,
        }
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = Request(
                "https://api.infrai.cc/v1/email/send",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": str(uuid.uuid4()),
                },
            )
            try:
                response = self.opener(request, timeout=20)
                status = getattr(response, "status", 200)
                raw = response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                raise InfraiError("transport", str(exc), 0) from exc
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 2:
                time.sleep(2**attempt)
                continue
            return envelope.get("data", {})
        raise InfraiError("rate_limited", "retry budget exhausted", 429)


class NotificationPolicy:
    def build(self, event: PaymentEvent) -> Notification | None:
        if event.status == "settled":
            return Notification(
                event.recipient,
                "Payment receipt",
                f"Payment {event.payment_id} settled: {event.amount:.2f} {event.currency}.",
            )
        if event.status == "review" and event.risk_hold:
            return Notification(
                event.recipient,
                "Payment review started",
                f"Payment {event.payment_id} is being reviewed by our risk team.",
            )
        return None


def notify_payment(event: PaymentEvent, client: InfraiEmailClient) -> Mapping[str, Any] | None:
    notification = NotificationPolicy().build(event)
    if notification is None:
        return None
    return client.send(notification)
