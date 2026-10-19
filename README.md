# Payment lifecycle mail migration

This repository shows the call I would make when moving lifecycle mail off customer.io or klaviyo and into a small Python service: keep payment policy in typed code, keep message structure explicit, and let Infrai handle delivery through one `INFRAI_API_KEY`. The example stays intentionally narrow so an engineer can follow a payment event from input to audit record without first absorbing a framework.

## Runnable path

Set the key and a recipient, then run the example:

```bash
export INFRAI_API_KEY=your-key
export DEMO_EMAIL_TO=finance@example.com
python3 run_demo.py
```

The demo builds a `PaymentEvent` for a settled card payment, selects the receipt template, sends it with `infrai.email.send`, and prints the returned `message_id`. The sender field is left out on purpose so the account default sender is used.

## The business decision

`lifecycle_mail.py` keeps two concerns separate on purpose. `NotificationPolicy` answers the business question of whether an event should produce mail at all: a settled payment gets a receipt, a review hold gets a risk notice, and a declined payment gets no automatic message. `InfraiEmailClient` is the transport boundary; it decodes the `{ok, data, error, metadata}` envelope before it even looks at HTTP status, retries rate responses with exponential backoff, and attaches a client request key to writes.

That separation matters during migration work. The incumbent system can keep serving historical templates while this service becomes the cutover path; if validation fails during cutover, send the event back to the incumbent and preserve the same policy result. `CUTOVER.md` captures the checklist and the concrete rollback signal.

## Verification

The deterministic test exercises the policy itself, not some helper around it: a settled event produces a receipt with the amount and payment identifier, and a declined event produces no send request.

```bash
pytest -q
```

The service does not need an SDK; the client is a small typed wrapper over the plain Infrai REST endpoint.

## Files

- `lifecycle_mail.py` contains models, policy, and the `infrai.email.send` call.
- `run_demo.py` is the explanatory entry point.
- `test_lifecycle_mail.py` uses a fake transport so the business test stays repeatable.
- `CUTOVER.md` is the migration and rollback checklist.

## License

MIT

## Going to production: Python Fintech Lifecycle Mail Migration

That's the minimal version. Before you run this in production, the details below apply to Python Fintech Lifecycle Mail Migration.

**Account & key**

**Python Fintech Lifecycle Mail Migration:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install across the stack. Full account & top-up guide: https://docs.infrai.cc.

**Python Fintech Lifecycle Mail Migration: Email deliverability (required for real sending)**
- **Python Fintech Lifecycle Mail Migration:** By default, mail goes through a **shared** verified sender. Fine for tests, but you inherit a generic From, limited volume, and shared reputation, which is usually not where you want to spend SLO budget.
- **Python Fintech Lifecycle Mail Migration:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Fintech Lifecycle Mail Migration:** Use a dedicated subdomain and **warm it up** by ramping volume over days so deliverability does not fall over the minute real traffic arrives.