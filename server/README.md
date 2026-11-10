# Reference server

The tax brackets API candidates call, deployed on Fly at `https://{app-name}.fly.dev`. Candidates get the app name during the interview call.

- `/` landing page for candidates
- `/deck` the assignment brief
- `GET /tax-calculator/tax-year/{year}` brackets for 2019 to 2023. It waits 0 to 5 s, fails 1 call in 4 with a 500, and returns a 404 for other years.

## Run locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python app.py      # http://localhost:5001
pytest
```

## Deploy

From this folder, with the app name in `FLY_APP`:

```bash
fly deploy --app "$FLY_APP"
```

`static/deck.html` is a static export of the "Income Tax 101" slides. Re-export it when the deck changes.
