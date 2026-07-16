# Training Alpha Airspace

`training_alpha` is a fictional airspace package for testing custom airspace loading.

It is intentionally simple:

- one central navaid: `ALP_VOR`
- four crossing routes
- one polygon TMA boundary
- beginner mixed traffic scenario
- one beginner lesson manifest reference

Validate it:

```bash
python3 scripts/validate_airspace_package.py airspaces/training_alpha
```

Validate only the scenario template:

```bash
python3 scripts/seed_hosted_demo.py \
  --validate-only \
  --airspace airspaces/training_alpha/airspace.v1.json \
  --template airspaces/training_alpha/scenarios/beginner_mix.v1.json
```

Run it:

```bash
python3 scripts/seed_hosted_demo.py \
  --web-base-url http://127.0.0.1:5174 \
  --airspace airspaces/training_alpha/airspace.v1.json \
  --template airspaces/training_alpha/scenarios/beginner_mix.v1.json
```
