# Cutover checklist

1. Export the incumbent customer.io or klaviyo template names and compare their rendered copy with `NotificationPolicy`.
2. Set `INFRAI_API_KEY` in the service environment and send one settled payment to an internal mailbox.
3. Observe the returned `message_id` in the audit log, then enable this path for a small event slice.
4. Promote the path after receipt and review notifications match the approved copy.

## Rollback

If the audit check or copy review fails, disable this worker's event subscription and route new events to the incumbent. Keep the event identifiers unchanged so the next run can be reconciled; re-enable this service after the checklist is green.
