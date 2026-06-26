# Fide Stack Improvement Plan

## Position In The Stack

FMG-Bench should remain the public benchmark package for faith and moral
guidance evaluation.

It should not become the private evaluation engine, a product launch-readiness
suite, or a hosted certification service. Its value is public inspectability:
dataset, scoring spec, result summaries, paper artifacts, and reproduction
guidance.

## Consolidation Stance

Do not collapse FMG-Bench into Petros or private product evaluation.

FMG-Bench should inform the Fide stack through schemas, taxonomy, scoring
lessons, failure tags, and public benchmark methodology. Product-specific evals
should live in Eval Engine and may reuse FMG-Bench concepts without turning this
repo into product infrastructure.

## Target Capabilities

FMG-Bench should own:

- public dataset and benchmark card;
- scoring specification;
- public runner and smoke tests;
- public result summaries;
- paper and reproduction materials;
- responsible-use and open-benchmark policy.

FMG-Bench should feed:

- Eval Engine adapter and summary workflows;
- Lexicon doctrine/failure taxonomy seeding;
- Gateway escalation and authority-boundary policy examples;
- research-ideas methodology and collaborator calls;
- FideAI.org public artifact pages.

FMG-Bench should not own:

- private run orchestration;
- raw response custody;
- product launch-readiness reports;
- partner deployment evaluation;
- certification or endorsement decisions.

## Petros-Like Product Readiness

A future Petros-like product should not be evaluated directly by FMG-Bench as if
it were a frontier model benchmark. Instead:

1. FMG-Bench informs the taxonomy and measurement principles.
2. Eval Engine runs product-specific launch-readiness suites.
3. Lexicon and Gateway provide source and runtime evidence.
4. Fide AI governance controls any public claims.

## Near-Term Work

1. Keep the public benchmark package reproducible and cleanly scoped.
2. Maintain adapter compatibility with Fide Eval Engine.
3. Document which FMG-Bench taxonomies are safe for reuse by Lexicon, Gateway,
   and product evals.
4. Keep public results separate from private product-readiness findings.
5. Add notes for future benchmark versions without creating hidden leaderboard
   expectations.

## Success Criteria

FMG-Bench is serving the stack when it remains a trusted public benchmark while
other Fide repos can reuse its taxonomy and methodology without confusing public
research findings with product certification.

