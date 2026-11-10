"""Forward and inverse calculations of the controlled-pore cases in the paper.

Ported from the paper code package (2026-09-30) so that the agent can run the
same calculations as Sections 3 and 5 of the manuscript:

* equal-area pore shapes (circle, equilateral and 30-60-90 triangles);
* corner water at a given saturation and contact angle in an equilateral pore;
* T2 (consistent-mass FEM, generalized Lanczos), D-T2 (narrow-pulse PFG) and
  T1-T2 (saturation recovery) forward responses on pyGIMLi triangular meshes;
* the effective two-compartment exchange model of the dual-pore case;
* the finite-volume pixel-grid solver used for the segmented CT slice;
* the regularized nonnegative 1D and 2D inversions.

Default parameters follow Table 1 of the manuscript.
"""

from .settings import PaperSettings, DT2Acquisition, T1T2Acquisition, InversionGrids

__all__ = ["PaperSettings", "DT2Acquisition", "T1T2Acquisition", "InversionGrids"]
