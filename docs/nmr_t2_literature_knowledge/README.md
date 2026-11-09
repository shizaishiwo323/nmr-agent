# NMR T2 Literature Knowledge Base

This directory holds our own literature notes on NMR T2 theory, simulation and inversion, together with verified references, as Markdown and JSON retrieval artifacts. It lets the T2 agent explain simulation and inversion results with citation keys backed by verified references. The notes are written in our own words; they do not reproduce the source papers.

## Files

- `papers/`: one Markdown literature note per paper.
- `result_interpretation_scenarios.md`: human-readable scenario map from result patterns to mechanisms and citations.
- `result_interpretation_scenarios.json`: machine-readable version for Agent retrieval.
- `citation_registry.md`: citation key to verified reference and note mapping.
- `literature_manifest.json`, `literature_manifest.csv`: citation keys, categories and the reason each paper is included.
- `literature_manifest.enriched.json`: the manifest plus curated concepts, retrieval tags and Crossref-verified AGU references (read by `t2_agent/literature.py`).

## Scope

The knowledge base prioritizes theory, pore-scale simulation, inversion regularization, surface relaxation, diffusive coupling, restricted diffusion, FEM/FVM/LBM/matrix methods, internal gradients, CPMG sampling, Gaussian decomposition cautions, and T2-T2 interpretation.

## Use in reports

Use citation keys such as `[@BrownsteinTarr1979]` or combined citations such as `[@Whittall1991NNLS; @Coates1999NMRLogging]`. Keep interpretation probabilistic and data-aware.
