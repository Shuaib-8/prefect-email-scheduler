# Prefect Email Scheduler

Using Prefect to schedule emails - example of how to use Prefect to schedule emails such as for periodic payment confirmation emails to accounts receivable staff to confirm payroll payments.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Install uv (if not already installed)

```bash
pip install uv
```

### Create virtual environment and install dependencies

```bash
uv sync
```

### Activate the environment

```bash
source .venv/bin/activate
```

Finally, run the main file to verify the environment is working:

```bash
uv run main.py
```

## Project Components

1. **email_flow.py** - The main file that contains the flow for sending the emails.
2. **email_template.py** - Contains the templates for the emails.
3. **deploy.py** - Used to deploy the flow to Prefect Cloud.

## Testing

Install test dependencies and run the test suite:

```bash
uv sync --group test
uv run pytest tests/ -v
```

## Development 

Dev dependencies (ruff, mypy) are included by default with `uv sync`. To install without dev tools:

```bash
uv sync --no-group dev
```

Run linting:

```bash
uvx ruff format . # format code
uvx ruff check --select I --fix && uvx ruff format . # fix import sorting and check code
```
