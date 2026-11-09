---
citation_key: Hansen1992LCurve
category: 01_core_theory_inversion
tags: [core_theory_inversion, ill_posed, lcurve, regularization, regularization_parameter, regularized_inversion, tikhonov]
pages: 20
doi: 10.1137/1034115
---

# Hansen1992LCurve

- **Title**: Analysis of Discrete Ill-Posed Problems by Means of the L-Curve
- **Suggested citation format**: `[@Hansen1992LCurve]`
- **AGU reference**: Hansen, P. C. (1992). Analysis of discrete ill-posed problems by means of the L-curve. SIAM Review, 34(4), 561–580. https://doi.org/10.1137/1034115
- **Reason for inclusion**: Original methodological reference for the L-curve: the L-shaped curve formed by the residual norm and the (semi)norm of the solution, and the relation of its corner to the choice of the regularization parameter.
- **Role in the T2 agent**: Inversion-method reference: the L-curve concept, Tikhonov regularization and choice of the regularization parameter.

## Conclusions usable by the agent

### L-curve and choice of the regularization parameter
- **When to invoke**: When a report needs to explain what an L-curve plot is, why a smoothing factor near the corner is chosen, or what to do when the L-curve is flat or has no clear corner.
- **Physical/mathematical mechanism**: In discrete ill-posed problems, plotting the (semi)norm of the regularized solution against the residual norm gives an L-shaped curve; near the corner a balance is struck between fitting the data and suppressing oscillations in the solution, and several parameter-selection methods are tied to locating this corner.
- **Citable sentence for reports**: The L-curve places the residual norm and the spectral roughness in a single plot, and a smoothing factor near the corner trades off fitting error against smoothness of the spectrum [@Hansen1992LCurve].
- **Evidence location**: See the evidence anchors below. Check against the original publication before citing.

## Search keywords

`core_theory_inversion`, `ill_posed`, `lcurve`, `regularization`, `regularization_parameter`, `regularized_inversion`, `tikhonov`

## Evidence anchors

- p.1: The abstract states that the residual-versus-solution-norm plot associated with Tikhonov regularization plays a central role, and that several parameter-selection methods are related to locating the L-shaped corner.
- p.2: The outline of the paper indicates a discussion of the L shape and of regularized solutions near the corner.
- p.6: Definition of the corner region.

## Limits of use

- The agent's automatic selection rule is that the reciprocal slope is closest to 0.25 (valid range 0.1–10), which is not the maximum-curvature corner of Hansen's paper; cite this paper only for the L-curve concept, not for this specific rule.
- Do not present this paper as an NMR application reference; it is a general numerical-methods source.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.
