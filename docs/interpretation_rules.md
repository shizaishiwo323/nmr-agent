# Interpretation rules

The interpretation tool (`interpret_results`, implemented in
`t2_agent/literature.py`) applies the 20 rules below. Each rule is evaluated
only when the quantity it rests on has been computed for the current run, and
each statement it writes cites the listed references. Full AGU references are
given at the end of this page. The literature library behind the rules is in
`docs/nmr_t2_literature_knowledge/`: one note per paper in `papers/` (64 notes)
and the verified references in `literature_manifest.enriched.json`.

`tests/test_rule_list.py` checks that this list matches the rules in the code.

## Measured decays

| # | Rule ID | Applied when | What the agent reports | References |
|---|---|---|---|---|
| 1 | `soil_water_state_classes` | Measured decay of a sample described as soil, peat or organic-rich | Signal shares below 60 ms, 60–300 ms and above 300 ms (micropore/tightly bound, mesopore/loosely bound, macropore/bulk water), and the share above 1 s compared with extracted pore water | Bayer et al. (2010); Jaeger et al. (2010); Costabel & Stange (2025) for organic samples |
| 2 | `two_water_populations` | Soil sample with two resolved Gaussian components | Position and area of each component and the water environment it corresponds to | Jaeger et al. (2010); Costabel & Stange (2025) and Mashhadi et al. (2025) for organic samples |
| 3 | `short_t2_dominant` | Measured decay of a sample not described as soil | Fast-diffusion reading of the spectrum: T2 follows the surface-to-volume ratio, and pore sizes need the surface relaxivity | Brownstein & Tarr (1979); Kleinberg et al. (1994) |
| 4 | `echo_spacing_lower_bound` | First echo time known | Amplitude lost before the first echo by short-T2 water; bound-water fractions are lower bounds | Peng et al. (2023) and Jaeger et al. (2010) for soils; Coates et al. (1999) otherwise |
| 5 | `cpmg_sampling_trim` | Early-time misfit larger than 1% of the signal | Effect of early echoes and of trimming the decay on the short-T2 part of the spectrum | Whittall et al. (1991) |
| 6 | `acquisition_window_too_short_for_long_t2` | Decay ends above 5% of its initial amplitude | Long-T2 components are not fully sampled | Coates et al. (1999) |

## Built-in dual-pore geometry

| # | Rule ID | Applied when | What the agent reports | References |
|---|---|---|---|---|
| 7 | `uncoupled_peaks_match_pores` | Pore pair without a throat | Each peak compared with the fast-diffusion estimate of its pore | Brownstein & Tarr (1979); Zhou & Zhang (2025) for the built-in pore pair |
| 8 | `pore_coupling_exchange` | Pore pair joined by a throat | Fast-exchange limit, exchange time and the small-pore water merged into one peak; loss of coupling as saturation falls | McCall et al. (1991); Fleury & Soualem (2009); Grunewald & Knight (2009); Zhou et al. (2026); Zhou & Zhang (2025) for the built-in pore pair |
| 9 | `partial_saturation_capacity` | At least one pore partially saturated | Capacity check: the short-T2 signal compared with the water the smaller pore can hold | Zhou & Zhang (2025); Mohnke et al. (2015) |
| 10 | `bulk_dominated` | Main peak above half of T2,bulk | Share of the relaxation rate due to surface relaxation; T2 is insensitive to pore size | Brownstein & Tarr (1979); Kleinberg et al. (1994) |

## Segmented CT slices

| # | Rule ID | Applied when | What the agent reports | References |
|---|---|---|---|---|
| 11 | `ct_porosity_and_water_regions` | 2D porosity, water saturation and spectral peak available | Porosity, saturation, the main peak, and the disconnected water regions that form the short-T2 tail | Brownstein & Tarr (1979), when water regions are reported |
| 12 | `sv_first_moment_check` | Mesh boundary lengths available | Harmonic-mean T2 compared with the meshed S/V of the water domain | Brownstein & Tarr (1979) |
| 13 | `rho_calibration_conditioning` | Mesh boundary lengths available | Amplification of T2 errors in a relaxivity calibration when bulk relaxation dominates | Brownstein & Tarr (1979); Kleinberg et al. (1994) |
| 14 | `saturation_wall_coverage` | Water saturation below 1 | Fraction of the pore wall covered by water and its effect on S/V and T2 | Mohnke et al. (2015); Falzone & Keating (2016); Behroozmand et al. (2015) |
| 15 | `area_above_bulk_t2` | More than 1% of the spectral area above T2,bulk | Area that is a smoothing or time-window artefact rather than water | Borgia et al. (1998); Coates et al. (1999) |

## All workflows

| # | Rule ID | Applied when | What the agent reports | References |
|---|---|---|---|---|
| 16 | `unresolved_gaussian_components` | More Gaussian components than spectral maxima | Components that the spectrum cannot resolve | Borgia et al. (1998) |
| 17 | `multimodal_spectrum` | Measured spectrum with two or more peaks and no Gaussian fit | The number of peaks depends on the regularization | Whittall & MacKay (1989) |
| 18 | `peak_at_t2_bounds` | Amplitude above 5% of the maximum near the upper end of the T2 grid | Possible truncation artefact; extend the grid and invert again | Whittall et al. (1991); Coates et al. (1999) |
| 19 | `gaussian_overfit_or_bad_residual` | Gaussian components below 2% of the area | Components within the non-uniqueness of the inversion | Whittall & MacKay (1989); Borgia et al. (1998) |
| 20 | `regularization_sensitive` | Every inversion | Basis of the inversion: fixed α, or α from the L-curve slope or maximum-curvature criterion | Whittall & MacKay (1989); Borgia et al. (1998) for fixed α; Zou et al. (2016) or Hansen (1992) for the L-curve |

## References cited by the rules (21)

- Bayer, J. V., Jaeger, F., & Schaumann, G. E. (2010). Proton Nuclear Magnetic Resonance (NMR) Relaxometry in Soil Science Applications. The Open Magnetic Resonance Journal, 3(1), 15–26. https://doi.org/10.2174/1874769801003010015
- Behroozmand, A. A., Keating, K., & Auken, E. (2015). A Review of the Principles and Applications of the NMR Technique for Near-Surface Characterization. Surveys in Geophysics, 36(1), 27–85. https://doi.org/10.1007/s10712-014-9304-0
- Borgia, G. C., Brown, R. J. S., & Fantazzini, P. (1998). Uniform-Penalty Inversion of Multiexponential Decay Data. Journal of Magnetic Resonance, 132(1), 65–77. https://doi.org/10.1006/jmre.1998.1387
- Brownstein, K. R., & Tarr, C. E. (1979). Importance of classical diffusion in NMR studies of water in biological cells. Physical Review A, 19(6), 2446–2453. https://doi.org/10.1103/physreva.19.2446
- Coates, G. R., Xiao, L., & Prammer, M. G. (1999). NMR logging: Principles and applications. Houston, TX: Halliburton Energy Services.
- Costabel, S., & Stange, C. F. (2025). Nuclear magnetic resonance relaxometry to characterise the decomposition degree of peat soils. Geoderma, 456, 117244. https://doi.org/10.1016/j.geoderma.2025.117244
- Falzone, S., & Keating, K. (2016). A laboratory study to determine the effect of pore size, surface relaxivity, and saturation on NMR T2 relaxation measurements. Near Surface Geophysics, 14(1), 57–69. https://doi.org/10.3997/1873-0604.2016001
- Fleury, M., & Soualem, J. (2009). Quantitative analysis of diffusional pore coupling from T2-store-T2 NMR experiments. Journal of Colloid and Interface Science, 336(1), 250–259. https://doi.org/10.1016/j.jcis.2009.03.051
- Grunewald, E., & Knight, R. (2009). A laboratory study of NMR relaxation times and pore coupling in heterogeneous media. Geophysics, 74(6), E215–E221. https://doi.org/10.1190/1.3223712
- Hansen, P. C. (1992). Analysis of Discrete Ill-Posed Problems by Means of the L-Curve. SIAM Review, 34(4), 561–580. https://doi.org/10.1137/1034115
- Jaeger, F., Shchegolikhina, A., Van As, H., & Schaumann, G. E. (2010). Proton NMR Relaxometry as a Useful Tool to Evaluate Swelling Processes in Peat Soils. The Open Magnetic Resonance Journal, 3(1), 27–45. https://doi.org/10.2174/1874769801003010027
- Kleinberg, R. L., Kenyon, W. E., & Mitra, P. P. (1994). Mechanism of NMR Relaxation of Fluids in Rock. Journal of Magnetic Resonance, Series A, 108(2), 206–214. https://doi.org/10.1006/jmra.1994.1112
- Mashhadi, S. R., Keating, K., Petersen, R. J., Parra, A. O., Costabel, S., Beisembina, G., Hiller, T., & Grombacher, D. (2025). Hydraulic conductivity estimation by NMR data in unconsolidated geological materials: insights from SDR model calibrations. Journal of Hydrology, 662, 134060. https://doi.org/10.1016/j.jhydrol.2025.134060
- McCall, K. R., Johnson, D. L., & Guyer, R. A. (1991). Magnetization evolution in connected pore systems. Physical Review B, 44(14), 7344–7355. https://doi.org/10.1103/physrevb.44.7344
- Mohnke, O., Jorand, R., Nordlund, C., & Klitzsch, N. (2015). Understanding NMR relaxometry of partially water-saturated rocks. Hydrology and Earth System Sciences, 19(6), 2763–2773. https://doi.org/10.5194/hess-19-2763-2015
- Peng, L., Zhang, F., Dong, Y., & Zhang, C. (2023). Water partitioning and migration in unsaturated bentonites by low‐field NMR characterization. Vadose Zone Journal, 22(6), e20284. https://doi.org/10.1002/vzj2.20284
- Whittall, K. P., & MacKay, A. L. (1989). Quantitative interpretation of NMR relaxation data. Journal of Magnetic Resonance, 84(1), 134–152. https://doi.org/10.1016/0022-2364(89)90011-5
- Whittall, K. P., Bronskill, M. J., & Henkelman, R. M. (1991). Investigation of analysis techniques for complicated NMR relaxation data. Journal of Magnetic Resonance, 95(2), 221–234. https://doi.org/10.1016/0022-2364(91)90213-d
- Zhou, J., & Zhang, C. (2025). How Does Pore Structure Affect the NMR Relaxation in Unsaturated Porous Media: A Simulation Study. Water Resources Research, 61(2), e2024WR038139. https://doi.org/10.1029/2024wr038139
- Zhou, J., Schröer, L., Cnudde, V., & Zhang, C. (2026). How Does Fluid Exchange Between Pores in Unsaturated Porous Media? Geophysical Research Letters, 53(5), e2025GL120450. https://doi.org/10.1029/2025gl120450
- Zou, Y.-L., Xie, R.-H., & Arad, A. (2016). Numerical estimation of choice of the regularization parameter for NMR T2 inversion. Petroleum Science, 13(2), 237–246. https://doi.org/10.1007/s12182-016-0093-6
