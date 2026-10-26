# AGENTS.md

> Guidance for AI coding agents working in this repository.

## What this is

`uniswap-universal-router-decoder` is a Python SDK to **decode and encode** transactions sent to the Uniswap
Universal Router (UR), built on [web3.py](https://github.com/ethereum/web3.py). It targets Ethereum Mainnet by default
and works on any chain where the UR is deployed.

Two public surfaces:

- Python API: `RouterCodec` / `AsyncRouterCodec` (the public `encoder` and `decoder` modules).
- Non-Python: the `ur-decode` / `ur-encode` command line tools and the optional `ur-mcp` MCP server. Both speak JSON,
  so shell scripts and agents can drive the codec.

The CLI and MCP tools are **read-only**: they inspect or derive UR data and never sign or broadcast a transaction.

## Layout

- `uniswap_universal_router_decoder/` — the package. Modules prefixed with `_` are private; shared constants live in
  `_constants.py`.
- `uniswap_universal_router_decoder/_command_spec.py`, `_enums.py` — the single home of the command facts, shared by
  the encoder, decoder, CLI and MCP server.
- `tests/` — offline unit tests. `tests/conftest.py` holds the fixtures.
- `integration_tests/` — live-RPC tests.
- `coverage.json` — a tracked, generated artifact (regenerate it before committing).
- `server.json` — metadata for the MCP Registry; **not** a runtime file.

## Dev setup

```bash
pip install -e '.[mcp]' --group dev
```

## Commands that must all pass

```bash
pytest tests                                                          # unit tests
basedpyright                                                          # strict, must be 0 errors
flake8 uniswap_universal_router_decoder
flake8 tests
flake8 integration_tests
isort --check --diff uniswap_universal_router_decoder
isort --check --diff tests
coverage run -m pytest tests && coverage report -m && coverage json   # coverage must stay at 100%
```

`tox` runs all of the above (`tox -e lint-web37`, `tox -e coverage`, ...). See `tox.ini`.

## Ground rules (from CONTRIBUTING.md)

- PEP 8 names; match the formatting of the surrounding code.
- **Coverage must stay at 100%.** Regenerate `coverage.json` (`coverage json`) before committing.
- Put constants in `_constants.py`; do not expose what should stay private.
- A new or changed public API must be documented in its docstring **and** in `README.md`.
- Line length is 120; isort is configured in `tox.ini`.

## Gotchas that will bite you

- **Command bytes.** Never compare a raw command byte against a bare command value — mask it with
  `RouterConstant.COMMAND_TYPE_MASK` first (see `SELECTOR_COMMANDS` in `_enums.py`). Comparing the unmasked byte is a
  real bug that has shipped before.
- **One interchange format.** `decoded_input_to_dict()`'s output *is* `Encoder.function_input()`'s input. Do not add a
  separate "builder vocabulary" plan format — that ABI↔builder mapping is the lossy step that was deliberately removed.
- **Structured commands are decode-only.** `V4_SWAP`, `V4_POSITION_MANAGER_CALL` and `EXECUTE_SUB_PLAN` decode to
  decoded V4 actions / nested command lists, not ABI values, so `function_input()` rejects them (`STRUCTURED_COMMANDS`).
- **`revert_on_fail` polarity.** `True` means the flag is *clear* (the tx must revert on failure); `False` sets `0x80`.
  Only the commands in `NO_REVERT_COMMANDS` honour the flag.
- **RPC tests.** `tests/conftest.py` hardcodes the endpoint (`rpc_endpoint_address`). For offline runs, deselect the
  RPC-dependent `test_decode_transaction` cases **by node id** — a `-k` filter is a substring match and also drops
  unrelated `test_decode_transaction_*` tests.
- **Inert config.** The `[tool.pytest]` section in `pyproject.toml` is inert (pytest reads `[tool.pytest.ini_options]`),
  and there is no `pytest.ini`. Do not assume those options apply.
- **Version lives in more than one file.** `pyproject.toml`'s `[project] version` is the source of truth, but
  `server.json` must repeat it in the *normalized* PEP 440 form (ex: `1.2.3b1`, not `1.2.3-beta.1`).
  `tests/test_version_consistency.py` fails the build if they drift, and also checks the README `mcp-name:` marker
  against `server.json`'s `name`.

## Driving the library without Python

```bash
ur-encode list                          # describe the decoded call format and the commands
ur-encode describe V3_SWAP_EXACT_IN     # describe one command's parameters
ur-decode calldata 0x3593564c...        # decode raw calldata
ur-decode tx 0x... --rpc https://...    # decode a transaction (needs an RPC endpoint)
ur-mcp                                  # MCP server over stdio (needs the [mcp] extra)
```
