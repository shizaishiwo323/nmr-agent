# NMR T2 Result Interpretation Scenario Map

Purpose: after an agent sees a simulation or T2 inversion result, it should look it up in this table first, following the chain "phenomenon -> mechanism -> cautions -> recommended citations". Reports can use the `[@citation_key]` form directly; `citation_registry.md` maps each key to its verified reference and literature note.

## Short T2 main peak or high short-T2 area fraction

- **Scenario ID**: `short_t2_dominant`
- **Trigger cues**: `main_peak_ms < 10`; `short_fraction high`; `spectrum shifts to shorter T2`; `simulated decay becomes faster in small pores`
- **Mechanism**: Interpret first as enhanced surface relaxation, small pores or a high surface-to-volume ratio, or restricted diffusion shortening the effective relaxation time. If the sample has susceptibility contrasts or a long echo spacing, also check for extra dephasing from internal gradients.
- **Cautions**: A short T2 alone does not prove that the pores are small; surface relaxivity, diffusion regime, internal gradients and data sampling all shift the peak position.
- **Recommended citations**: [@BrownsteinTarr1979] [@MullerPetke2015DiffusionRegimes] [@Mohnke2015TriangularPores] [@Keating2012NMRAssumptions] [@Dunn2002PorousMediaNMR] [@Kleinberg1994RelaxationMechanism] [@KeatingKnight2007IronOxides]
- **Example report sentence**: A shortened T2 is usually consistent with small pores or a high surface-to-volume ratio enhancing surface relaxation, but this reading should be weighed against the diffusion regime and internal-gradient effects [@BrownsteinTarr1979; @MullerPetke2015DiffusionRegimes].

## Long T2 tail or high long-T2 area fraction

- **Scenario ID**: `long_t2_tail`
- **Trigger cues**: `long_fraction high`; `tail extends > 1000 ms`; `peak near upper T2 bound`
- **Mechanism**: A long T2 can indicate weaker surface relaxation, larger pores or more free fluid; but if the peak sits against the upper inversion limit, it may be a boundary effect of the T2 search range, noise or regularization.
- **Cautions**: When the peak lies near t2_max_ms, flag it first as a boundary/unstable signal and do not interpret it directly as a real very-long-T2 pore component.
- **Recommended citations**: [@Whittall1991NNLS] [@Coates1999NMRLogging] [@Keating2012NMRAssumptions] [@Hurlimann1998EffectiveGradients]
- **Example report sentence**: A long-T2 component can reflect weaker surface relaxation or more free fluid, but if the peak lies near the upper search limit, inverse-problem boundary effects and regularization sensitivity must be considered as well [@Whittall1991NNLS; @Coates1999NMRLogging].

## Several expected pore populations appear as one broad or merged peak

- **Scenario ID**: `broad_or_merged_peaks`
- **Trigger cues**: `broad peak`; `expected two pore sizes but one spectral peak`; `peaks merge when pores are connected`; `spectrum smoother than pore-size distribution`
- **Mechanism**: Consider diffusive coupling or inter-pore exchange first: spins diffuse between pores of different sizes and the local relaxation environments are averaged. Excessive regularization can also merge neighbouring peaks, so check the L-curve or the fixed regularization setting at the same time.
- **Cautions**: A merged peak is not sufficient evidence for a single pore population; it can also arise from connectivity, diffusive coupling or inversion smoothing.
- **Recommended citations**: [@Chi2015DiffusionalCoupling] [@Toumelin2003TemperatureDiffusiveCoupling] [@Fraga2013CarbonatePoreCoupling] [@Song2014PoreCouplingReview] [@Ramakrishnan1999Carbonates] [@Fleury2009PoreCoupling] [@Carneiro2014DiffusiveCoupling] [@Alhwety2014RockTypingDiffusiveCoupling] [@Borgia1998UniformPenalty]
- **Example report sentence**: A broad or merged peak can result from diffusive coupling between pores, where spins exchange between pore sizes and the local relaxation environments are averaged; such a result should not simply be equated with a single pore population [@Chi2015DiffusionalCoupling; @Song2014PoreCouplingReview].

## Multimodal T2 spectrum

- **Scenario ID**: `multimodal_spectrum`
- **Trigger cues**: `two or more peaks`; `multimodal spectrum`; `gaussian peak table has multiple components`
- **Mechanism**: Several peaks can indicate different relaxation environments, pore scales or fluid states; however, the number of peaks depends on regularization, noise, the sampling window and the peak-decomposition model. Gaussian decomposition should be treated as a descriptive tool, not as the only physical classification.
- **Cautions**: Describe the peaks as components in the report; do not claim that every Gaussian peak corresponds to a real pore population.
- **Recommended citations**: [@Whittall1991NNLS] [@Coates1999NMRLogging] [@Grunewald2009PoreCoupling] [@Song2016T2T2] [@WhittallMacKay1989NNLS] [@Borgia1998UniformPenalty]
- **Example report sentence**: A multimodal T2 spectrum suggests that several relaxation environments may be present, but neither the inversion nor the Gaussian decomposition by itself proves the same number of physical pore populations [@Whittall1991NNLS; @Grunewald2009PoreCoupling].

## Peak number, width or position changes markedly with the regularization factor

- **Scenario ID**: `regularization_sensitive`
- **Trigger cues**: `regularization sensitivity`; `alpha change changes peaks`; `lcurve selected alpha`; `roughness_norm high`; `fixed regularization uncertain`
- **Mechanism**: This is the typical signature of the ill-posedness of inverse Laplace / multi-exponential inversion. Weak regularization follows noise more readily and produces sharp spikes; strong regularization is smoother but may merge real peaks.
- **Cautions**: Report the regularization method before interpreting the number of peaks; present the L-curve selection, the residual and the roughness together.
- **Recommended citations**: [@Whittall1991NNLS] [@Coates1999NMRLogging] [@Schwartz2013T2T2Simulation] [@Yu2019T2T2] [@Hansen1992LCurve] [@Borgia1998UniformPenalty] [@WhittallMacKay1989NNLS]
- **Example report sentence**: The spectrum is sensitive to regularization, which means the peak shape contains an inverse-problem stability component; weaker regularization can amplify noise, whereas stronger regularization can smooth or merge neighbouring components [@Whittall1991NNLS; @Schwartz2013T2T2Simulation].

## Oscillating spectrum, noise peaks, or signs of a negative/anomalous fit

- **Scenario ID**: `noisy_oscillatory_or_false_peaks`
- **Trigger cues**: `oscillatory spectrum`; `many narrow peaks`; `large residual`; `poor fit`; `noise amplified`
- **Mechanism**: Check first the signal-to-noise ratio of the input decay, the quality of the early points, the echo-train sampling, the T2 range and the regularization. The NNLS non-negativity constraint avoids negative spectral values but does not guarantee that every peak is physically meaningful.
- **Cautions**: Do not assign a physical mechanism to every narrow noise peak; first suggest re-running the L-curve, increasing smoothing or restricting the T2 range.
- **Recommended citations**: [@Whittall1991NNLS] [@Coates1999NMRLogging] [@EchoTrainSimulation2021] [@WhittallMacKay1989NNLS] [@Borgia1998UniformPenalty]
- **Example report sentence**: An oscillating spectrum or several narrow peaks more likely reflects noise amplification and inversion instability; check the echo-train data quality and the regularization strength before interpreting it [@Whittall1991NNLS; @EchoTrainSimulation2021].

## Peak near the T2 search boundary

- **Scenario ID**: `peak_at_t2_bounds`
- **Trigger cues**: `peak near t2_min_ms`; `peak near t2_max_ms`; `boundary component`; `spectrum mass at limits`
- **Mechanism**: A peak at the boundary usually means that the search-range setting affects the result or that the data do not constrain that time scale. A short-boundary peak may come from insufficient early sampling; a long-boundary peak may come from tail noise or an upper limit that is set too wide.
- **Cautions**: Report it as a boundary-sensitive component and run a sensitivity analysis on the T2 range and the sampling window.
- **Recommended citations**: [@Whittall1991NNLS] [@Coates1999NMRLogging]
- **Example report sentence**: A peak near a boundary should be treated as a result sensitive to both the search range and the data constraints, and should be checked by adjusting the T2 range or the regularization [@Whittall1991NNLS].

## T2 peak position or width changes when the pore geometry changes

- **Scenario ID**: `simulation_geometry_effect`
- **Trigger cues**: `geometry changes spectrum`; `triangular/circular/irregular pore`; `surface-to-volume ratio changed`; `connectivity changed`
- **Mechanism**: Pore shape, surface-to-volume ratio, connectivity and boundary conditions change the diffusion-relaxation eigenmodes, so changes in the T2 spectrum can be explained jointly by geometry and boundary relaxation.
- **Cautions**: Do not reduce the geometric effect to "larger pores give longer T2"; non-spherical pores, corners, partial saturation and connectivity all change the response.
- **Recommended citations**: [@BrownsteinTarr1979] [@Mohnke2015TriangularPores] [@Hagslatt2002RestrictiveGeometries] [@Mohnke2010PoreScaleSimulation]
- **Example report sentence**: Geometry affects the T2 spectrum because restricted diffusion and the surface-relaxation boundary together change the diffusion-relaxation modes, not merely one equivalent pore size [@BrownsteinTarr1979; @Mohnke2015TriangularPores].

## Random-walk forward result versus inverted T2 spectrum

- **Scenario ID**: `random_walk_forward_model`
- **Trigger cues**: `random walk simulation`; `Monte Carlo decay`; `forward simulated echo decay`; `compare simulated pore geometry with inverted spectrum`
- **Mechanism**: A random walk converts pore geometry, diffusion coefficient, surface relaxivity and field inhomogeneity into an echo decay; the same inversion workflow then yields a T2 spectrum, which makes it suitable for testing the mechanism chain from structure to spectrum.
- **Cautions**: The inverted spectrum still depends on the inversion parameters; do not expect a one-to-one match between the true forward parameters and the recovered spectrum.
- **Recommended citations**: [@Toumelin2007GeneralRandomWalk] [@Toumelin2003GeneralRandomWalk] [@Toumelin2002MonteCarloNMR] [@LucasOliveira2018RestrictedDiffusion] [@Liebig1993RandomWalk] [@Noetinger2016DiffusionRandomWalk] [@SCA2008PoreScaleNMRSimulation]
- **Example report sentence**: A random-walk forward model establishes a testable mechanism chain from pore structure, diffusion and surface relaxation to the echo decay and T2 spectrum [@Toumelin2007GeneralRandomWalk; @Toumelin2002MonteCarloNMR].

## Interpreting FEM/FVM/COMSOL mesh-model results

- **Scenario ID**: `fem_fvm_mesh_model`
- **Trigger cues**: `finite element simulation`; `finite volume simulation`; `COMSOL model`; `mesh boundary condition`; `PDE diffusion relaxation`
- **Mechanism**: Mesh methods solve the diffusion-relaxation equation and thus treat complex geometry, boundary surface relaxation and internal gradients explicitly. The interpretation should report the boundary conditions, mesh resolution, diffusion coefficient and surface relaxivity.
- **Cautions**: The credibility of a numerical solution depends on the mesh and the boundary conditions; if the result differs from a random walk, check the discretization and the boundary implementation first.
- **Recommended citations**: [@Tandon2018FiniteVolumeInternalGradients] [@Mitchell2019FiniteElementNMR] [@Ghomeshi2018FEMNMR] [@Oliveira2021COMSOLNMRGuide] [@Mohnke2010PoreScaleSimulation]
- **Example report sentence**: FEM/FVM forward modelling places complex pore geometry, surface-relaxation boundaries and internal gradients in one diffusion-relaxation framework, and is therefore suited to interpreting geometry-controlled T2 responses [@Tandon2018FiniteVolumeInternalGradients; @Mitchell2019FiniteElementNMR].

## Internal gradients or field inhomogeneity shorten T2

- **Scenario ID**: `internal_gradient_shortening`
- **Trigger cues**: `internal gradients enabled`; `field inhomogeneity`; `echo spacing changes T2`; `susceptibility contrast`; `long T2 suppressed`
- **Mechanism**: Internal field gradients acting together with diffusion cause additional dephasing, which can shorten the whole T2 spectrum or suppress the long-T2 components. The more the data depend on echo spacing, the more the gradient term should be considered.
- **Cautions**: Do not attribute every T2 shortening to smaller pores; internal gradients are an important candidate for the mismatch between simulation and experiment.
- **Recommended citations**: [@Tandon2018FiniteVolumeInternalGradients] [@Gonzalez2020FieldInhomogeneities] [@Keating2012NMRAssumptions] [@Mohnke2010PoreScaleSimulation] [@KleinbergHorsfield1990TransverseRelaxation] [@Hurlimann1998EffectiveGradients] [@KeatingKnight2007IronOxides]
- **Example report sentence**: If the model includes internal gradients or field inhomogeneity, a shortened T2 may come from diffusion-induced dephasing and not only from smaller pores or enhanced surface relaxation [@Tandon2018FiniteVolumeInternalGradients; @Gonzalez2020FieldInhomogeneities].

## Effect of CPMG sampling, early points and trim-from-peak on the inversion

- **Scenario ID**: `cpmg_sampling_trim`
- **Trigger cues**: `early rise before decay`; `trim_from_peak true/false`; `missing early echoes`; `echo spacing large`; `CPMG artifacts`
- **Mechanism**: The inversion knows only the input echo train: the early points determine whether short T2 can be recovered, tail noise affects long T2, and trim-from-peak changes the effective starting point and the amplitude normalization.
- **Cautions**: If the raw simulated data first rise and then decay, trimming is a reasonable preprocessing step; for a clean real decay that starts at its maximum, excessive trimming can discard short-T2 information.
- **Recommended citations**: [@Whittall1991NNLS] [@EchoTrainSimulation2021] [@Tan2012T2T1Simulation] [@Toumelin2007GeneralRandomWalk]
- **Example report sentence**: T2 inversion is first limited by the echo-train sampling window and the quality of the early points, so trim-from-peak, echo spacing and tail noise should all be considered when judging the stability of the spectral shape [@Whittall1991NNLS; @EchoTrainSimulation2021].

## A 1D T2 spectrum cannot be interpreted uniquely; multidimensional NMR or extra evidence is needed

- **Scenario ID**: `need_multidimensional_validation`
- **Trigger cues**: `ambiguous component assignment`; `pore coupling suspected`; `fluid type unclear`; `T2 peaks overlap`; `exchange suspected`
- **Mechanism**: A 1D T2 spectrum is a projection of several mechanisms. T2-T2 or T1-T2 can supply information on exchange, coupling and the correlation of different fluid or pore environments, and is a useful complement for complex interpretations.
- **Cautions**: Do not over-distinguish fluid types or pore populations from a 1D T2 result; use "suggests" rather than "proves".
- **Recommended citations**: [@Song2012MRPM] [@Schwartz2013T2T2Simulation] [@Song2016T2T2] [@Song2008T2T2] [@Johnson2014T2T2] [@Monteilhet2006T2T2] [@Guo2016MultidimensionalNMRSimulation] [@Kleinberg1994RelaxationMechanism]
- **Example report sentence**: For complex samples with pronounced coupling or exchange, the 1D T2 peak positions and areas are not enough to assign pore populations or fluid types uniquely, and multidimensional NMR can provide stronger correlation constraints [@Song2012MRPM; @Song2016T2T2].

## Eigenmode interpretation of multi-exponential decay

- **Scenario ID**: `matrix_mode_interpretation`
- **Trigger cues**: `matrix diagonalization`; `eigenvalue modes`; `multiple exponential modes`; `semi-analytical forward model`
- **Mechanism**: A multi-exponential decay can be understood as the superposition of several eigenmodes of the diffusion-relaxation operator. The eigenvalues depend on pore geometry, boundary relaxation, saturation history and connectivity.
- **Cautions**: A mode need not equal a discrete physical pore population; it is a response determined jointly by the mathematical representation and the physical structure.
- **Recommended citations**: [@Chang2000MatrixDiagonalization] [@Chang2001DrainageSaturationHistory] [@MatrixDiagonalization2002NMR] [@McCall1991RestrictedDiffusion]
- **Example report sentence**: A multi-exponential decay can also be understood through the eigenmodes of the diffusion-relaxation operator, whose weights and decay rates are controlled jointly by geometry and boundary conditions [@Chang2000MatrixDiagonalization; @McCall1991RestrictedDiffusion].

## Interpreting LBM pore-scale simulation

- **Scenario ID**: `lbm_modeling`
- **Trigger cues**: `LBM simulation`; `lattice Boltzmann`; `voxel pore image`; `complex boundaries`
- **Mechanism**: The lattice Boltzmann method simulates diffusion in complex boundaries on a discrete lattice and can be used to forward-model the NMR response from a digital pore structure.
- **Cautions**: LBM results depend on the lattice resolution, the boundary implementation and the surface-relaxation parameters; cross-check them against FEM or random-walk results.
- **Recommended citations**: [@Mohnke2014LBMNMR] [@Guyer2000LBMDiffusion]
- **Example report sentence**: LBM can serve as a pore-scale forward method from a digital pore structure to the NMR decay response, and is particularly suited to diffusion problems with complex boundaries [@Mohnke2014LBMNMR; @Guyer2000LBMDiffusion].

## Unclear L-curve or unstable automatic regularization selection

- **Scenario ID**: `lcurve_flat_or_unstable`
- **Trigger cues**: `lcurve corner unclear`; `flat lcurve`; `selected alpha at search bound`; `multiple comparable alpha values`; `regularization choice unstable`
- **Mechanism**: Automatic L-curve selection is an algorithmic decision of this tool. If the curve has no clear corner or the selected value lies near the search boundary, the trade-off between data fit and smoothing is not stable enough; treat the result as an exploratory interpretation and try adjusting the alpha range, the T2 range or the data preprocessing.
- **Cautions**: The local knowledge base contains no paper that specifically establishes the current L-curve rule; these references support the need for regularization in the inversion and must not be written as "a paper proposed this tool's L-curve selection criterion".
- **Recommended citations**: [@Whittall1991NNLS] [@Coates1999NMRLogging] [@Hansen1992LCurve]
- **Example report sentence**: When the L-curve lacks a clear corner or the selected regularization lies near the search boundary, the inverted spectrum should be treated as regularization-sensitive; this reflects the stability trade-off between fit accuracy and smoothness that multi-exponential inversion requires [@Whittall1991NNLS; @Coates1999NMRLogging].

## Gaussian decomposition overfits or leaves a large residual

- **Scenario ID**: `gaussian_overfit_or_bad_residual`
- **Trigger cues**: `gaussian residual high`; `too many gaussian peaks`; `components overlap strongly`; `peak count changes interpretation`; `fit improves but components become unphysical`
- **Mechanism**: A Gaussian decomposition is only an empirical approximation of the log-T2 spectral shape. If adding peaks improves only the numerical residual but leads to strong overlap, unstable area fractions or peak positions without physical interpretation, reduce the number of peaks or label the result as a descriptive fit.
- **Cautions**: Whittall and Coates support the need for caution when interpreting inverted spectra and components; they are not the source of the Gaussian decomposition method.
- **Recommended citations**: [@Whittall1991NNLS] [@Coates1999NMRLogging] [@Grunewald2009PoreCoupling]
- **Example report sentence**: A Gaussian decomposition can help describe the T2 spectral shape, but the number of peaks and the area assignment depend on the stability of the inverted spectrum, noise and pore coupling; when peaks overlap strongly or the residual is abnormal, each peak should not be interpreted directly as an independent physical pore population [@Whittall1991NNLS; @Grunewald2009PoreCoupling].

## Changing surface relaxivity shifts the T2 peaks systematically

- **Scenario ID**: `surface_relaxivity_sensitivity`
- **Trigger cues**: `surface relaxivity changes peak`; `rho_s sensitivity`; `same geometry different T2`; `surface relaxation parameter sweep`
- **Mechanism**: Surface relaxivity controls how strongly magnetization decays at the boundary. In models with identical geometry, raising the surface relaxivity usually shortens the effective T2 and strengthens the short-T2 components.
- **Cautions**: A change in surface relaxivity and a change in pore size can produce similar spectral shapes; separate them with a parameter sweep or independent constraints.
- **Recommended citations**: [@BrownsteinTarr1979] [@Mohnke2010PoreScaleSimulation] [@MullerPetke2015DiffusionRegimes] [@Kleinberg1994RelaxationMechanism] [@Foley1996ParamagneticIons] [@KeatingKnight2007IronOxides]
- **Example report sentence**: For fixed geometry, a higher surface relaxivity strengthens boundary relaxation and shortens the effective T2, so a shift of the T2 peak does not necessarily represent only a change in pore size [@BrownsteinTarr1979; @Mohnke2010PoreScaleSimulation].

## Mesh resolution or boundary conditions change the simulation result

- **Scenario ID**: `mesh_resolution_boundary_condition_sensitivity`
- **Trigger cues**: `mesh sensitivity`; `boundary condition sensitivity`; `FEM result changes with mesh`; `finite volume discretization changes decay`
- **Mechanism**: FEM/FVM models solve the diffusion-relaxation equation explicitly; the mesh resolution, the implementation of the surface-relaxation boundary and the internal-gradient term all affect the numerical decay. The simulation interpretation should report these settings and include a sensitivity check.
- **Cautions**: If a change in mesh or boundary conditions changes the T2 spectrum, treat it first as numerical sensitivity and not as a change in physical mechanism.
- **Recommended citations**: [@Tandon2018FiniteVolumeInternalGradients] [@Mitchell2019FiniteElementNMR] [@Oliveira2021COMSOLNMRGuide] [@Mohnke2010PoreScaleSimulation]
- **Example report sentence**: The T2 response of a mesh-based forward model depends not only on the physical parameters but also on the mesh resolution and the implementation of the boundary conditions, so FEM/FVM results should be interpreted together with numerical sensitivity checks [@Tandon2018FiniteVolumeInternalGradients; @Oliveira2021COMSOLNMRGuide].

## Acquisition window too short for a reliable long T2

- **Scenario ID**: `acquisition_window_too_short_for_long_t2`
- **Trigger cues**: `decay does not reach baseline`; `short acquisition window`; `long T2 beyond max time`; `tail poorly sampled`; `few late echoes`
- **Mechanism**: Long-T2 components need a sufficiently long echo train to be constrained stably. If the sampling window is too short or the tail noise is large, the inversion may express the unconstrained long time scales as a boundary peak or a long tail.
- **Cautions**: Before interpreting a long tail, check the maximum sampling time, the tail signal-to-noise ratio and t2_max_ms; resample or narrow the T2 upper limit if necessary.
- **Recommended citations**: [@Whittall1991NNLS] [@Coates1999NMRLogging] [@EchoTrainSimulation2021]
- **Example report sentence**: If the echo train does not cover a sufficiently long part of the decay tail, the long-T2 components are strongly constrained by the sampling window and noise, and a long tail at the boundary should be interpreted with caution [@Whittall1991NNLS; @Coates1999NMRLogging].

## Fast-diffusion assumption fails or the mean pore-size estimate is unreliable

- **Scenario ID**: `fast_diffusion_assumption_breakdown`
- **Trigger cues**: `outside fast diffusion regime`; `large pore with slow diffusion`; `surface relaxivity high`; `pore-size estimate inconsistent`; `T2-pore mapping breaks down`
- **Mechanism**: Many T2-to-pore-size conversions rely on the fast-diffusion approximation; when the diffusion length, pore scale, surface relaxivity or connected structure makes that approximation invalid, the mean pore-size estimate departs from the true pore structure.
- **Cautions**: Do not convert a T2 distribution directly into a pore-size distribution before the fast-diffusion assumption has been verified.
- **Recommended citations**: [@MullerPetke2015DiffusionRegimes] [@Keating2012NMRAssumptions] [@Ramakrishnan1999Carbonates] [@BrownsteinTarr1979] [@Kleinberg1994RelaxationMechanism]
- **Example report sentence**: The direct correspondence between T2 and pore size usually relies on the fast-diffusion approximation; when the sample is in a non-fast-diffusion regime or strongly coupled, the pore-size distribution inferred from T2 may deviate from the real structure [@MullerPetke2015DiffusionRegimes; @Keating2012NMRAssumptions].

## Iron-bearing or paramagnetic minerals shorten T2 overall

- **Scenario ID**: `paramagnetic_mineral_shortening`
- **Trigger cues**: `iron-bearing soil or sand`; `red or weathered geomaterial`; `T2 shorter than expected for known pore size`; `clay or iron oxide coating`; `same geometry different sample chemistry`
- **Mechanism**: Paramagnetic ions (Fe3+, Mn2+) and iron oxides on the pore wall markedly raise the surface relaxivity, giving a shorter T2 at the same pore size; strongly magnetic minerals such as magnetite also introduce internal gradients.
- **Cautions**: Do not convert a short T2 in an iron-bearing sample directly into small pores; a known or calibrated surface relaxivity, or another pore-size measurement, is needed as a constraint.
- **Recommended citations**: [@Kleinberg1994RelaxationMechanism] [@Foley1996ParamagneticIons] [@KeatingKnight2007IronOxides] [@Keating2012NMRAssumptions]
- **Example report sentence**: Iron-bearing minerals raise the surface relaxivity markedly, so a short T2 in iron-bearing geomaterials does not necessarily mean smaller pores [@KeatingKnight2007IronOxides; @Foley1996ParamagneticIons].

## Water-state classes for soil and organic-matter samples

- **Scenario ID**: `soil_water_state_classes`
- **Trigger cues**: `measured decay`; `user describes a soil, peat or organic-rich sample`
- **Mechanism**: Following the empirical classification of Bayer et al. (2010, p. 18), compute the fractions with T2 < 60 ms (micropore / tightly bound water), 60-300 ms (mesopore / loosely bound water) and > 300 ms (macropore / bulk water); compare with the T2B of about 2 s for pore water extracted from peat (Jaeger et al., 2010, p. 35) to judge whether free water is present; organic matter (hydrogel effect, paramagnetic centres) shortens T2 (Costabel & Stange, 2025).
- **Cautions**: The class boundaries are empirical and differ slightly between studies; the classes describe the state of the water and are not a pore-size distribution.
- **Recommended citations**: [@Bayer2010SoilNMR] [@Jaeger2010PeatSwelling] [@CostabelStange2025Peat]
- **Example report sentence**: About X% of the signal comes from water bound in fine pores or by the matrix, so the water is predominantly in a bound state [@Bayer2010SoilNMR; @Jaeger2010PeatSwelling].

## Two distinguishable Gaussian water populations

- **Scenario ID**: `two_water_populations`
- **Trigger cues**: `two Gaussian components`; `spectrum has two maxima`; `R² of the Gaussian fit available`
- **Mechanism**: Report the centres, areas and separation factor of the two components and interpret them by water-state class: the short-T2 population corresponds to confined water (in peat, water with T2 < 30 ms has a reduced diffusion coefficient, Jaeger et al., 2010, p. 37), and the long-T2 population to water in more open pores or inside intact plant cells (Mashhadi et al., 2025, Section 5.1).
- **Cautions**: Treat them as two water populations only if the spectrum really shows two maxima.
- **Recommended citations**: [@Jaeger2010PeatSwelling] [@CostabelStange2025Peat] [@Mashhadi2025SDRPeat]
- **Example report sentence**: The spectrum is well described by two Gaussian components separated by a factor of N, which are two distinguishable water populations [@Jaeger2010PeatSwelling].

## Short-T2 water that has already decayed before the first echo

- **Scenario ID**: `echo_spacing_lower_bound`
- **Trigger cues**: `measured decay with known first echo time`
- **Mechanism**: Components with T2 below about 3 x TE have mostly decayed before the first echo; water adsorbed on clay has T2 of about 0.05-0.13 ms (Peng et al., 2023) and unfrozen bound water in peat about 0.3 ms (Jaeger et al., 2010, p. 39), so the bound-water fraction is therefore a lower bound.
- **Cautions**: This only states the direction (a lower bound) of the short-T2 fraction and does not estimate the missing amount.
- **Recommended citations**: [@Peng2023Bentonite] [@Jaeger2010PeatSwelling] [@Coates1999NMRLogging]
- **Example report sentence**: The bound-water fraction is a lower bound, because hydration water with T2 below about 3 x TE has decayed before the first echo [@Peng2023Bentonite].

## Coupled pore pair: fast-exchange limit and exchange time

- **Scenario ID**: `pore_coupling_exchange`
- **Trigger cues**: `ideal structure with throat`
- **Mechanism**: From the geometry compute the fast-exchange limit given by the S/V of the whole water-filled domain, the throat exchange time tau = 1/k_ex (k_ex = D*w/L*(1/A_L + 1/A_S)) and the ratio of k_ex to the difference between the surface-relaxation rates of the two pores, to judge whether the two pores behave as one (McCall et al., 1991; Fleury & Soualem, 2009); report the amount of small-pore water merged into the single peak and the equivalent side length obtained from a single-pore reading (Grunewald & Knight, 2009); reduced saturation weakens coupling (Zhou et al., 2026).
- **Cautions**: The exchange criterion is an order-of-magnitude judgement; the throat conductance estimate neglects the diffusive resistance of the pore mouth.
- **Recommended citations**: [@McCall1991RestrictedDiffusion] [@Fleury2009PoreCoupling] [@Grunewald2009PoreCoupling] [@Zhou2026GRLExchange] [@Zhou2025WRRUnsaturated]
- **Example report sentence**: The throat exchange time is about 1/N of T2, so the two pores behave as one pore, and a single peak does not mean a single pore population [@McCall1991RestrictedDiffusion; @Grunewald2009PoreCoupling].

## Uncoupled pore pair: peaks correspond to the individual pores

- **Scenario ID**: `uncoupled_peaks_match_pores`
- **Trigger cues**: `ideal structure without throat`
- **Mechanism**: Compare each inverted peak with the fast-diffusion estimate for each pore (valid when rho*r/D << 1, Brownstein & Tarr, 1979), and compare the small-pore peak area with its water-volume fraction.
- **Cautions**: When the estimates for the two pores are identical they fall on the same peak.
- **Recommended citations**: [@BrownsteinTarr1979] [@Zhou2025WRRUnsaturated]
- **Example report sentence**: The two pores are not connected, and the peak positions agree with the respective fast-diffusion estimates to within 10% [@BrownsteinTarr1979].

## Partial saturation: attribution of the short T2 and capacity check

- **Scenario ID**: `partial_saturation_capacity`
- **Trigger cues**: `ideal structure with Sw < 1`
- **Mechanism**: A partially saturated large pore and a saturated small pore have the same T2 when the water volume and wetted area are the same; compare the fraction of the saturated total signal with T2 below the geometric midpoint of the two pores' saturated estimates against the saturation capacity of the small pore, and if it is exceeded the short T2 cannot be attributed to the small pore alone (Zhou & Zhang, 2025, Sections 4.2 and 7; Mohnke et al., 2015).
- **Cautions**: The saturated volume of each pore must be known; this applies to built-in structures or samples with a saturated reference spectrum.
- **Recommended citations**: [@Zhou2025WRRUnsaturated] [@Mohnke2015TriangularPores]
- **Example report sentence**: This short-T2 signal exceeds the saturation capacity of the small pore and cannot be attributed to the small pore alone [@Zhou2025WRRUnsaturated].

## Harmonic-mean T2 of a CT-derived simulated spectrum versus S/V

- **Scenario ID**: `sv_first_moment_check`
- **Trigger cues**: `CT simulation with mesh boundary lengths`
- **Mechanism**: Integrating the diffusion-relaxation equation over the water-filled domain gives an initial decay rate of 1/T2B + rho*S/V that is independent of the diffusion regime, so the amplitude-weighted harmonic-mean T2 of the spectrum is set by S/V; comparing it with the peak position shows which statistic should be used when comparing with measured spectra or back-calculating rho; the difference between the S/V of the pixel boundary and of the mesh boundary enters the rho calibration.
- **Cautions**: The initial magnetization must be uniform; comparison with measurements requires the early echoes to be complete.
- **Recommended citations**: [@BrownsteinTarr1979]
- **Example report sentence**: The harmonic-mean T2 of the spectrum agrees with the prediction from the mesh S/V, so the simulated spectrum is fully determined by the geometry [@BrownsteinTarr1979].

## Error amplification in the rho calibration when bulk relaxation dominates

- **Scenario ID**: `rho_calibration_conditioning`
- **Trigger cues**: `CT simulation`; `harmonic-mean T2 close to T2B`
- **Mechanism**: The share of the rate due to surface relaxation is s = 1 - T2/T2B; a relative error in T2 is amplified by a factor of about 1/s when rho is back-calculated.
- **Cautions**: T2B must be measured separately on the same fluid.
- **Recommended citations**: [@BrownsteinTarr1979] [@Kleinberg1994RelaxationMechanism]
- **Example report sentence**: Bulk relaxation contributes most of the rate, so a 5% error in T2 is amplified to N% in rho [@BrownsteinTarr1979].

## Pore-wall wetted fraction in a partially saturated CT slice

- **Scenario ID**: `saturation_wall_coverage`
- **Trigger cues**: `CT simulation with air phase`
- **Mechanism**: From the label image compute the fraction of pore wall covered by water and the change in S/V when the pores are completely filled; when the gas phase occupies the pore body while the wall stays wet, T2 hardly changes with saturation and the saturation should be read from the signal amplitude (Mohnke et al., 2015; Falzone & Keating, 2016); calibrating rho with the total pore-wall area biases it low (Behroozmand et al., 2015).
- **Cautions**: Based on a two-dimensional pixel-face count.
- **Recommended citations**: [@Mohnke2015TriangularPores] [@Falzone2016Saturation] [@Behroozmand2015Review]
- **Example report sentence**: Water still covers most of the pore wall, T2 hardly changes with saturation, and the saturation should be read from the signal amplitude [@Mohnke2015TriangularPores; @Falzone2016Saturation].

## Spectral area above T2B

- **Scenario ID**: `area_above_bulk_t2`
- **Trigger cues**: `simulated spectrum with area above the bulk T2`
- **Mechanism**: Relaxation slower than bulk water is physically impossible and results from smoothing broadening (Borgia et al., 1998); if the simulation duration is too short, the width, the upper edge and the component fractions should be recomputed with a duration of about 5 times T2 (Coates et al., 1999).
- **Cautions**: The harmonic-mean T2 is unaffected.
- **Recommended citations**: [@Borgia1998UniformPenalty] [@Coates1999NMRLogging]
- **Example report sentence**: X% of the spectral area lies above T2B, which is broadening caused by smoothing [@Borgia1998UniformPenalty].

## Unresolvable Gaussian components

- **Scenario ID**: `unresolved_gaussian_components`
- **Trigger cues**: `more Gaussian components than spectral maxima`; `components less than three times apart`
- **Mechanism**: When two components are less than about a factor of 3 apart and the spectrum has only one maximum, they describe the shape of one asymmetric peak and not two water populations (Borgia et al., 1998).
- **Cautions**: The fractions change with the smoothing factor and the simulation duration.
- **Recommended citations**: [@Borgia1998UniformPenalty]
- **Example report sentence**: The two Gaussian components are only a factor of N apart and describe the shape of one peak, not two water populations [@Borgia1998UniformPenalty].
