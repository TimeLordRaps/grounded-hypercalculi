# Security Policy

## Supported Releases

Only the latest tagged public release on the `main` branch is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

Do not disclose security vulnerabilities, exploit primitives, or secret material in public GitHub issues.

Please report sensitive security issues via GitHub Private Vulnerability Reporting:

`https://github.com/TimeLordRaps/grounded-hypercalculi/security/advisories/new`

If the private advisory route is temporarily unavailable, contact the project maintainer securely.

## Operational Boundaries

`grounded-hypercalculi` provides mathematical and formal execution abstractions.
It does not execute unsanitized external shell processes or download untrusted remote code.
Never commit secret tokens, API keys, credentials, or personal email addresses.
