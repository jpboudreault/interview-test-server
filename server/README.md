# Reference server

The tax brackets API candidates call, deployed on Fly at `https://{app-name}.fly.dev`. Candidates get the app name during the interview call.

- `/` landing page for candidates
- `/deck` the assignment brief
- `/starter.zip` the optional starter. Rebuild it with `./build_starter_zip.sh` after committing changes to `starter/`; a test fails if it's out of date.
- `/docs` OpenAPI docs for the baseline endpoint (spec at `/openapi.json`)
- `GET /tax-calculator/tax-year/{year}` brackets for 2019 to 2023. It waits 0 to 5 s, fails 1 call in 4 with a 500, and returns a 404 for other years.

## Feature endpoints

Used for the follow-up features in the interview. They aren't listed on the landing page. All of them return a 404 for unsupported years and fail 1 call in 4 with a 500.

| Feature | Endpoint | Behaviour |
|---|---|---|
| F3 rate limit | `GET /tax-calculator/rate-limited/tax-year/{year}` | 2 calls per 3 s per client, then `429` with `Retry-After` (1 to 3 s). No added latency. |
| F4 auth | `GET /tax-calculator/secure/tax-year/{year}` | Needs `X-API-Key` matching `TAX_API_KEY`: `401` if missing, `403` if wrong. |
| F5 schema v2 | `GET /tax-calculator/v2/tax-year/{year}` | `{"tax_year", "brackets": [{"lower", "upper", "rate_percent"}]}`, with `upper` null on the top bracket. |
| F6 credits | `GET /tax-calculator/tax-year/{year}/credits` | RRSP deduction cap and a flat basic personal credit, in dollars, per year. |
| F7 correlation | every endpoint | Echoes `X-Correlation-ID` and logs it. |

`/docs/full` (spec at `/openapi-full.json`) documents every endpoint. It isn't linked anywhere, so share it when you introduce a feature. Both specs come from `static/openapi.json`.

## Run locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
TAX_API_KEY=dev-key python app.py      # http://localhost:5001
pytest
```

## Deploy to Fly.io

Install `flyctl` and run `fly auth login` first. Then, from this folder, with the app name in `FLY_APP`:

```bash
TAX_API_KEY=$(openssl rand -hex 16); echo "$TAX_API_KEY"   # save this value
fly secrets set TAX_API_KEY="$TAX_API_KEY" --app "$FLY_APP"   # once; triggers a restart
fly deploy --app "$FLY_APP"
fly scale count 1 --app "$FLY_APP"   # rate-limit counters are in memory
fly secrets list --app "$FLY_APP"    # shows TAX_API_KEY is set, not its value
```

Fly can't show the key again after it's set, so save the printed value. You'll give it to the candidate for F4. Without it, the secure endpoint returns `503`. To rotate the key, run `fly secrets set` again.

`static/deck.html` is a static export of the "Income Tax 101" slides. Re-export it when the deck changes.
