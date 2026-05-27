# Contributing

FMG-Bench is released as a public research benchmark. Contributions should
preserve benchmark clarity, avoid leaking sensitive private materials, and
maintain the responsible-use boundaries described in this repository.

## Good Contributions

- Documentation improvements.
- Reproducibility fixes.
- Runner bug fixes.
- Additional aggregate analyses and reproducibility checks.
- Issues identifying ambiguity in scoring, metadata, or failure tags.

## Do Not Submit

- Raw user logs or private pastoral conversations.
- API keys, provider credentials, local run artifacts, or private reviewer data.
- Model outputs containing sensitive personal information.
- Marketing claims that treat FMG-Bench scores as pastoral endorsement.

## Development Checks

Run tests from the repository root:

```bash
python -m pytest benchmark/tests
```

Run a secret/leakage scan before opening a pull request:

```bash
python tools/release_scan.py
```
