# Held-Out Scenario Policy

## Purpose
Fide AI maintains held-out scenario sets to reduce benchmark overfitting, preserve evaluation signal quality, and support robust regression testing over time.

## Policy
- Public benchmark documentation may include representative samples, schema definitions, and scoring rules.
- A defined portion of benchmark instances remains private per release cycle.
- Held-out scenarios are rotated on a scheduled basis and when leakage risk is detected.

## Access Controls
- Held-out datasets are restricted to authorized evaluation operations personnel.
- Access is logged and reviewed.
- Related-entity participants do not receive privileged access.

## Leakage and Incident Response
If a held-out scenario leak is suspected:
1. Freeze affected release operations.
2. Run incident triage and scope assessment.
3. Retire or replace compromised items.
4. Publish a release note describing remediation at an appropriate transparency level.

## Research and Transparency Balance
Fide AI publishes sufficient methodology detail for scrutiny and reproducibility while preserving protected test content needed for valid future evaluations.

## Prohibited Participant Conduct
Participants may not:
- solicit held-out content,
- attempt reverse-engineering through abusive probing,
- submit contaminated systems trained directly on non-public benchmark content.

Violations may lead to disqualification or delayed eligibility for future releases.
