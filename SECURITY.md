# Security

## Report a vulnerability

Do not publish credentials, exploit details, or sensitive research output in a public issue. Report
security concerns privately to the repository owner through the contact method listed on the GitHub
profile for `AdenCJM`.

## Trust model

Parallel Research sends the requested topic to selected third-party model providers and stores their
responses locally. Retrieved webpages and provider output are untrusted data. The Claude Code skill
must not execute instructions, read paths, expose secrets, or make external changes because raw
research asks it to do so.

The application redacts common credential patterns from stored errors, but this is not a substitute
for keeping secrets out of prompts and logs. Add `.research/` to consuming projects' `.gitignore`
unless publication is intentional.

Provider SDKs and models change independently. Run the locked dependency audit and review current
provider data controls before processing sensitive material.
