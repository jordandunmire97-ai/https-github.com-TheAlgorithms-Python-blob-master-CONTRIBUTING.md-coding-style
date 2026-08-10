# Enhanced Idealization Platform

This repository now contains a Python MVP for an enhanced idealization platform.
It helps users define success, model constraints, generate multiple candidate
futures, stress test them across scenarios, and receive ranked recommendations
with confidence, tradeoffs, and reasoning traces.

## What it does

- captures goals, criteria, constraints, and context in a structured request
- generates multiple candidate strategies from a baseline or explicit blueprints
- adapts scoring based on user profiles and weighted success criteria
- simulates candidate performance under future scenarios
- explains why one recommendation outranks another
- compares the current recommendation against previous runs

## Project layout

- `/enhanced_idealization/models.py` - data models and request parsing
- `/enhanced_idealization/engine.py` - candidate generation, simulation, scoring
- `/enhanced_idealization/reporting.py` - plain-text recommendation rendering
- `/enhanced_idealization/__main__.py` - command-line entry point
- `/examples/product_strategy.json` - sample input
- `/tests/test_engine.py` - automated tests

## Run the sample

```bash
cd /path/to/enhanced-idealization
python -m enhanced_idealization examples/product_strategy.json --profile enterprise_ops
```

Use `--format json` for machine-readable output, `--output report.json` to write a
report to a file, and `--save-result previous.json` to persist a result for later
comparison. Criteria may use `"target": "minimize"` when lower metric values are
preferred. Requests require at least one criterion, and constraints must define a
minimum or maximum.

## Run the tests

```bash
cd /path/to/enhanced-idealization
python -m unittest discover -s tests
```
