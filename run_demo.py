from decimal import Decimal
import os

from lifecycle_mail import InfraiEmailClient, PaymentEvent, notify_payment


recipient = os.environ.get("DEMO_EMAIL_TO")
if not recipient:
    raise SystemExit("DEMO_EMAIL_TO is required")

event = PaymentEvent(
    payment_id="pay_demo_1042",
    recipient=recipient,
    amount=Decimal("49.90"),
    currency="USD",
    status="settled",
)
result = notify_payment(event, InfraiEmailClient())
print("receipt sent:", result.get("message_id") if result else None)
