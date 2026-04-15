# SDK Spec Notes

`imgwire-python` follows the server SDK pipeline:

1. acquire raw OpenAPI
2. shape it with `@imgwire/codegen-core` for `target: "python"`
3. generate a disposable base client with OpenAPI Generator
4. apply deterministic post-processing
5. compose handwritten Python ergonomics from `imgwire/`

Generation inputs and outputs are checked in so regeneration stays visible and reproducible.

## Server Scope

The checked-in Python SDK spec is entirely derived from the shared shaping layer. That means:

- `@imgwire/codegen-core` decides which operations are server-safe for the Python target
- `openapi/sdk.openapi.json` is the contract the generator consumes
- expanding the Python server SDK surface starts in the shaping layer, not in `generated/`

## OpenAPI Source

- Local/dev default: `http://localhost:8000/openapi.json`
- Release/default remote source: `https://api.imgwire.dev/openapi.json`
- Override via `OPENAPI_SOURCE`

`scripts/generate.ts` writes both the raw and SDK-shaped specs under `openapi/`.
