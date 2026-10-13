import json
from decimal import Decimal

from lifecycle_mail import InfraiEmailClient, Notification, NotificationPolicy, PaymentEvent


def test_policy_sends_receipt_and_suppresses_decline():
    policy = NotificationPolicy()
    settled = PaymentEvent("pay_1", "a@example.com", Decimal("12.50"), "USD", "settled")
    declined = PaymentEvent("pay_2", "a@example.com", Decimal("12.50"), "USD", "declined")

    receipt = policy.build(settled)
    assert receipt is not None
    assert receipt.subject == "Payment receipt"
    assert "pay_1" in receipt.text and "12.50 USD" in receipt.text
    assert policy.build(declined) is None


def test_email_request_uses_contract_body_field():
    requests = []

    class Response:
        status = 200

        def read(self):
            return b'{"ok": true, "data": {"message_id": "test"}}'

    def opener(request, timeout):
        requests.append(request)
        return Response()

    client = InfraiEmailClient(api_key="test", opener=opener)
    assert client.send(Notification("chenhua@changba.com", "Subject", "Message")) == {"message_id": "test"}
    assert json.loads(requests[0].data) == {
        "to": "chenhua@changba.com",
        "subject": "Subject",
        "body": "Message",
    }
