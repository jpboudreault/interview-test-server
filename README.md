# Interview Test Server

Everything for the Points tax calculator take-home:

- [`server/`](server/): the reference tax brackets API, deployed on Fly at `https://{app-name}.fly.dev`. The app name is provided during the interview call.
- [`starter/`](starter/): an optional starting point for candidates, a Python API with a React UI on top.

```
React UI  ──/api──▶  Python API  ──▶  {app-name}.fly.dev
```
