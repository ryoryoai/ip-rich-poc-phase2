# gBizINFO API (v2) integration notes

This system uses gBizINFO to enrich company master data.
The gBizINFO Swagger UI is the source of truth for endpoints and parameters.

## Official references
- API usage page (gBizINFO v2, access token required)
- Swagger UI (v2) and JSON spec
- Swagger operation manual
- FAQ: where to find the API specification

## Access prerequisites
- gBizINFO account
- API usage application approved
- Access token issued (required for API calls)

## Configuration (Phase2)
Set the following in `.env`:

- `GBIZINFO_API_BASE_URL`
  - Set this to the corporate-number lookup endpoint shown in Swagger UI (v2).
  - The client supports either:
    - A base endpoint that ends with `/{corporate_number}`, or
    - A template URL containing `{corporate_number}`.
- `GBIZINFO_API_KEY`
  - Your access token (never commit or log this).
- `GBIZINFO_API_KEY_HEADER`
  - Header name defined in the Swagger spec (code default is used if blank).
- `GBIZINFO_FIELD_MAP`
  - JSON mapping file for field extraction.
  - Example: `./docs/gbizinfo_field_map.example.json`

## Usage (CLI)

```bash
python -m app.cli company-enrich-gbiz \
  --corporate-number 1234567890123 \
  --field-map-file ./docs/gbizinfo_field_map.example.json
```

## Verification checklist
- Confirm the base URL and header name in Swagger UI (v2).
- Use Swagger UI "Authorize" to validate the token.
- If Swagger UI is under maintenance, retry later and keep the base URL/header as provisional.
