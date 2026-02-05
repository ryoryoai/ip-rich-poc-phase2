# Patent Infringement Investigation – Prompt Set (v1)

This ZIP contains a set of ready-to-use prompts to implement the pipeline discussed:
- Fetch/Store/Normalize (facts capture)
- Search/Discovery (candidate generation & ranking)
- Analyze (claim -> elements -> evidence -> assessments -> claim/case decisions)

All prompts are designed to output JSON only.

## Files
- 00_common_system_prompt.txt
- A_fetch_store_normalize/*.txt
- B_discovery/*.txt
- C_analyze/*.txt

## Notes
- Replace {{variables}} with your runtime inputs.
- Enforce "JSON only" at the caller level as well (e.g., schema validation + retry).
- Do not output raw payloads verbatim to end users; keep raw responses internal.
