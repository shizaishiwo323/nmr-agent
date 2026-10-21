# Agent Retrieval Guide for NMR T2 Literature Knowledge

## Recommended retrieval order

1. Start from `result_interpretation_scenarios.json` if the user asks what a result means. Match by trigger fields and scenario id.
2. Open the cited cards under `papers/` for the mechanism, cautious wording, and citation key.
3. Use `citation_registry.md` to map `[@key]` to PDF/card.
4. Use `_extracted_text/` only when stronger source grounding or exact page-level checking is needed.

## Citation style

- Use `agent_citation_key` / `citation_key` from the enriched manifest; these keys are unique.
- In generated reports, write scientific explanations with citation keys, for example: `短 T2 增强通常支持小孔或高表面积/体积比导致的表面弛豫增强 [@BrownsteinTarr1979; @MullerPetke2015DiffusionRegimes].`
- Use cautious verbs: `提示`, `支持`, `可能`, `与...一致`; avoid `证明` unless external validation is available.
- Prefer 2 citations per explanation: one foundational paper and one method/scenario-specific paper.
- Do not cite Whittall/Coates as Gaussian decomposition method papers; use them only for inversion/relaxation spectrum interpretation caution.
- Do not cite BrownsteinTarr1979 for regularization or L-curve; use it for surface relaxation, restricted diffusion, and geometry/eigenmode mechanisms.
- Cite Hansen1992LCurve for the L-curve concept only. The agent selects the factor whose slope reciprocal is closest to 0.25, which is not Hansen's maximum-curvature corner; do not attribute that rule to Hansen.
- Cite Borgia1998UniformPenalty as a warning about fixed-smoothing artefacts; the agent does not implement uniform-penalty (UPEN) inversion.
- Hurlimann1998EffectiveGradients and KleinbergHorsfield1990TransverseRelaxation explain measured data only; the agent's 2D forward model has no internal-gradient term.
- Each new card carries a `reference_agu` entry in the enriched manifest for the reference list.

## High-priority foundational citations

- Surface relaxation and restricted diffusion: [@BrownsteinTarr1979], [@MullerPetke2015DiffusionRegimes], [@Mohnke2015TriangularPores].
- Inversion/regularization: [@Whittall1991NNLS], [@WhittallMacKay1989NNLS], [@Hansen1992LCurve], [@Borgia1998UniformPenalty], [@Coates1999NMRLogging].
- Relaxation mechanism and mineralogy: [@Kleinberg1994RelaxationMechanism], [@Foley1996ParamagneticIons], [@KeatingKnight2007IronOxides].
- Echo spacing and internal gradients in measured data: [@KleinbergHorsfield1990TransverseRelaxation], [@Hurlimann1998EffectiveGradients].
- Diffusive pore coupling: [@Chi2015DiffusionalCoupling], [@Song2014PoreCouplingReview], [@Fraga2013CarbonatePoreCoupling], [@Fleury2009PoreCoupling].
- Random-walk simulation: [@Toumelin2007GeneralRandomWalk], [@Toumelin2002MonteCarloNMR], [@Liebig1993RandomWalk], [@Noetinger2016DiffusionRandomWalk].
- FEM/FVM/internal gradients: [@Tandon2018FiniteVolumeInternalGradients], [@Mitchell2019FiniteElementNMR], [@Gonzalez2020FieldInhomogeneities].
- Multidimensional NMR/T2-T2: [@Song2012MRPM], [@Schwartz2013T2T2Simulation], [@Song2016T2T2], [@Guo2016MultidimensionalNMRSimulation].
