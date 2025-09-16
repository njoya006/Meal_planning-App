Billing Backend Checklist — ChopSmo

This one-pager lists exactly what the frontend needs from the backend to implement billing and subscriptions.

Priority: ascending order (lowest -> highest) as requested.

1) Repo artifacts (low)
- OpenAPI (YAML): `docs/billing-openapi.yaml` (provided)
- Plans fixtures: `docs/plans.json` (provided)
- Webhook sample payloads: `docs/webhook-samples.json` (provided)
- Test user tokens fixtures: `docs/test_user_tokens.json` (provided)

2) Configuration (medium)
- Staging API base URL and Production API base URL (e.g., https://staging.api.example.com, https://api.example.com)
- CORS rules for frontend origins (list of allowed origins)
- Env vars to set in staging/production:
  - STRIPE_SECRET_KEY (secret)
  - STRIPE_WEBHOOK_SECRET (secret)
  - STRIPE_SUCCESS_URL, STRIPE_CANCEL_URL
  - DJANGO_DEBUG (False in staging/production)

3) Provider details (high)
- Provider name (Stripe/PayPal): preferred: Stripe
- Staging publishable key (pk_test_...) and staging secret key (sk_test_...) for backend
- Webhook signing secret for staging
- List of provider test card numbers (e.g., Stripe test cards)

4) API endpoints (highest)
- GET /api/plans (public)
- GET /api/plans/{plan_id} (public)
- POST /api/checkout/create (auth required) — returns checkoutUrl and sessionId
- POST /api/purchase/complete (auth) — optional client callback
- GET /api/me/subscription (auth) — current subscription
- POST /api/subscription/cancel (auth) — cancel subscription
- POST /api/test/grant-entitlement (auth/admin) — grant entitlements for QA
- POST /api/webhooks/stripe/ — webhook endpoint, accepts provider events and verifies signature

5) Data shapes (highest) — sample JSON
- See `docs/plans.json` for plan schema
- Checkout create response: {"checkoutUrl":"...","sessionId":"..."}
- Subscription shape: {"subscription_id":"sub_...","plan_id":"pro_monthly","status":"active","current_period_end":"ISO8601","cancel_at_period_end":false,"entitlements":[]}

6) Operational notes (highest)
- Webhook processing must be idempotent. Use event idempotency keys and track processed events.
- Use provider SDKs on the server; never expose secret keys to frontend.
- Document if prices are decimal (e.g., 9.99) or minor units (e.g., 999). Frontend expects decimal by default.
- Define proration rules and trial handling.
- Provide test users or an endpoint to seed test states.

7) Handover deliverables (final)
- Postman collection or OpenAPI export (YAML) — completed
- Staging base URL + CORS rules — backlog
- Staging provider test keys + webhook signing secret — backlog (secrets)
- Plan fixtures and test user tokens — completed
- Short runbook for webhook troubleshooting (how to replay events) — backlog

If you'd like, I will:
- Create a PR with the above docs + billing app (I already added a minimal billing app).
- Implement full Stripe webhook handlers and mapping to `Subscription` model.
- Add unit tests and CI job for webhook idempotency.

Which next step should I run: "create PR", "implement webhook handlers", or "add tests"?
