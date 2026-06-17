# SA-Exoscale_fs

`SA-Exoscale_fs` is a Splunk add-on for collecting Exoscale audit events and normalizing them into CIM-oriented sourcetypes for security and compliance use cases.

The add-on provides:

- A modular input that calls the Exoscale API and ingests audit events.
- Account configuration for Exoscale API credentials.
- Checkpointing via Splunk KV Store to avoid re-reading already fetched events.
- Sourcetype routing from raw `exoscale:event` data into:
  - `exoscale:audittrail:auth`
  - `exoscale:audittrail:mutation`
- Field extractions, aliases, tags, and event types for CIM-style searches.
- Prebuilt Splunk views shipped in the package.

## What It Does

The main ingestion logic lives in [`SA-Exoscale_fs/package/bin/exoscale_audit_helper.py`](SA-Exoscale_fs/package/bin/exoscale_audit_helper.py). For each configured input, the add-on:

1. Reads the configured Exoscale account credentials from Splunk's secure storage.
2. Loads the last checkpoint from KV Store.
3. Calls Exoscale `list_events()` for the requested time window.
4. Writes each event into Splunk with sourcetype `exoscale:event`.
5. Updates the checkpoint after the run completes.

If no checkpoint exists, the add-on starts from the configured `Start From` date. If that field is empty, it defaults to the last 30 days.

## Splunk Configuration

The add-on UI definition is stored in [`SA-Exoscale_fs/globalConfig.json`](SA-Exoscale_fs/globalConfig.json).

### Account Configuration

The configuration page defines an account with at least:

- `name`
- `ms_api_zones`
- `api_key`
- `api_secret`

### Data Input

The shipped input is `Exoscale Audit` and supports:

- `interval`
- `index`
- `account`
- `date` (`Start From`)
- `reset_checkpoint`

`reset_checkpoint` forces the add-on to fetch again from the configured start point or the default 30-day lookback. It should be turned off after the backfill run.

## Data Model and Routing

Raw events are initially written as `exoscale:event`. Splunk transforms in [`SA-Exoscale_fs/package/default/transforms.conf`](SA-Exoscale_fs/package/default/transforms.conf) then route them into normalized sourcetypes:

- Authentication handlers such as `authenticate`, `create session`, and `revoke session` become `exoscale:audittrail:auth`.
- Other handlers are routed to `exoscale:audittrail:mutation`.

Normalization is implemented in [`SA-Exoscale_fs/package/default/props.conf`](SA-Exoscale_fs/package/default/props.conf), including:

- Timestamp parsing
- JSON field extraction
- Field aliases such as `src` and `src_ip`
- Derived values such as `action`, `result`, `object_category`, and `object_id`

Supporting Splunk knowledge objects are defined in:

- [`SA-Exoscale_fs/package/default/eventtypes.conf`](SA-Exoscale_fs/package/default/eventtypes.conf)
- [`SA-Exoscale_fs/package/default/tags.conf`](SA-Exoscale_fs/package/default/tags.conf)

## Local Development

This repository is Python-based and declares dependencies in [`pyproject.toml`](pyproject.toml). The project currently depends on:

- `exoscale`
- `solnlib`
- `splunk-sdk`
- `splunktaucclib`

Development tooling includes:

- `pytest`
- `ruff`
- `pre-commit`
- `yamllint`
- `splunk-add-on-ucc-framework`

Typical local setup with `uv`:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```

## Installation Notes

The packaged Splunk app content is under [`SA-Exoscale_fs/package`](SA-Exoscale_fs/package). To use the add-on in Splunk:

1. Build or package the app according to your internal Splunk app release process.
2. Install the resulting app into Splunk.
3. Create an Exoscale account in the add-on configuration UI.
4. Create an `Exoscale Audit` input and assign an index.
5. Verify that events are arriving under `exoscale:audittrail:auth` and `exoscale:audittrail:mutation`.

This repository does not currently document a complete release command sequence in the root project files, so packaging steps should follow the process your team already uses for Splunk UCC-based add-ons.

## Dashboards and Views

The app ships Splunk UI views under [`SA-Exoscale_fs/package/default/data/ui/views`](SA-Exoscale_fs/package/default/data/ui/views), including dashboards for inputs, configuration, and Exoscale data overview.

## License

This repository is licensed under Apache 2.0. See [`LICENSE`](LICENSE).
