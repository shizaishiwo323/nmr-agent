---
citation_key: KleinbergHorsfield1990TransverseRelaxation
category: 05_relaxation_mechanism_mineralogy
tags: [cpmg, echo_spacing, internal_gradient, relaxation_mechanism, restricted_diffusion, surface_relaxation, susceptibility_contrast]
pages: 11
doi: 10.1016/0022-2364(90)90104-H
---

# KleinbergHorsfield1990TransverseRelaxation

- **Title**: Transverse relaxation processes in porous sedimentary rock
- **Suggested citation format**: `[@KleinbergHorsfield1990TransverseRelaxation]`
- **AGU reference**: Kleinberg, R. L., & Horsfield, M. A. (1990). Transverse relaxation processes in porous sedimentary rock. Journal of Magnetic Resonance, 88, 9–19. https://doi.org/10.1016/0022-2364(90)90104-H
- **Reason for inclusion**: Measured T2 as a function of static field strength and CPMG pulse spacing: surface relaxation dominates at low field and short spacing, whereas diffusion in field gradients appears at high field and long spacing.
- **Role in the T2 agent**: Mechanism reference: distinguishing surface relaxation from internal-gradient diffusion, and echo-spacing dependence.

## Conclusions usable by the agent

### When T2 is dominated by surface relaxation
- **When to invoke**: When it is necessary to argue that T2 at low field and short echo spacing can be treated as controlled by surface relaxation, or to explain why results depend on instrument field strength and echo spacing.
- **Physical/mathematical mechanism**: At the lowest field strength and shortest pulse spacing, T2 is controlled mainly by relaxation at the fluid-solid interface; as the field strength increases and the spacing lengthens, a clear contribution from diffusion in magnetic-field gradients appears, the gradient arising from the susceptibility difference between grains and pore fluid. The total relaxation rate is not a simple sum of the rates of the individual processes.
- **Citable sentence for reports**: At low field and short echo spacing T2 mainly reflects surface relaxation; at higher field strength or longer echo spacing, the gradient-diffusion contribution caused by susceptibility differences must be considered [@KleinbergHorsfield1990TransverseRelaxation].
- **Evidence location**: See the evidence anchors below. Check against the original publication before citing.

## Search keywords

`cpmg`, `echo_spacing`, `internal_gradient`, `relaxation_mechanism`, `restricted_diffusion`, `surface_relaxation`, `susceptibility_contrast`

## Evidence anchors

- p.1: The abstract gives the comparison between field strength and pulse spacing, and attributes the gradients to susceptibility differences.
- p.1: Restricted diffusion is most pronounced in small-pore samples; in the theory the total relaxation rate is not a simple sum over processes.

## Limits of use

- The samples are water-bearing sedimentary rocks; when interpreting experimental data, check whether the user's instrument field strength and echo spacing are comparable to the conditions in the paper.
- The agent's two-dimensional forward model has no internal-gradient term, so this paper cannot be used to explain gradient effects in simulation results.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.
