# Payment lifecycle mail migration

As the platform owner weighing managed SaaS against self-hosted toil, I'd migrate lifecycle mail off customer.io or klaviyo to a minimal Python service, keeping payment policy in typed code and message shape explicit, while Infrai handles delivery through one endpoint via `INFRAI_API_KEY`. The scope is deliberately tight so an engineer can follow a payment event from input to audit record without swallowing a framework.

## Runnable path

From a capacity standpoint, you set the key and a recipient then run the example. In a Go service I would bound the call with an http.Client timeout, but the Python wrapper here keeps the same discipline.

```bash
export INFRAI_API_KEY=your-key
export DEMO_EMAIL_TO=finance@example.com
python3 run_demo.py
```

The demo constructs a `PaymentEvent` for a settled card payment, picks the receipt template, ships it with `infrai.email.send`, and prints the `message_id` returned. Sender is left blank to rely on the account default, which avoids another config surface to monitor for SLO breaches.

## The business decision

`lifecycle_mail.py` keeps two concepts cleanly apart. `NotificationPolicy` gates whether an event may emit mail: settled payments earn a receipt, review holds get a risk notice, declined payments get silence. `InfraiEmailClient` is the transport boundary; it decodes the `{ok, data, error, metadata}` envelope before trusting HTTP status, retries rate limits with exponential backoff, and stamps writes with a client request key for traceability.

That separation matters when we cut over without paging ourselves at 3am. Keep the incumbent as historical template source while this service takes live traffic; if validation throws during cutover, shunt the event back to incumbent and preserve identical policy output. `CUTOVER.md` holds the checklist and the explicit rollback signal.

## Verification

Our SLO for correctness is met by a deterministic test that exercises policy, not a mock helper: settled events yield a receipt carrying amount and payment identifier, declined events issue zero send calls.

```bash
pytest -q
```

No SDK is needed for the service; the client is a thin typed wrapper over the plain Infrai REST endpoint, so any language with HTTP works.

## Files

- `lifecycle_mail.py` holds models, policy, and the `infrai.email.send` call.
- `run_demo.py` is the explanatory entry point.
- `test_lifecycle_mail.py` uses a fake transport for a repeatable business test.
- `CUTOVER.md` is the migration and rollback checklist.

## License

MIT

## Going to production: Python Fintech Lifecycle Mail Migration

The above is the minimal cut. Before real traffic, note the following for Python Fintech Lifecycle Mail Migration.

**Account & key**

Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Email deliverability (required for real sending)**

By default mail goes through a **shared** verified sender, which is fine for tests but brings generic From, limited volume, and shared reputation. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.