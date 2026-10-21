# NMR T2 结果解释场景检索图谱

用途：后续 Agent 看到模拟或 T2 反演结果后，优先按本表检索“现象 -> 机制 -> 谨慎边界 -> 推荐引用”。报告中可以直接使用 `[@citation_key]` 形式引用，再由 `citation_registry.md` 映射到本地 PDF。

## 短 T2 主峰或短 T2 面积占比高

- **场景 ID**：`short_t2_dominant`
- **触发线索**：`main_peak_ms < 10`；`short_fraction high`；`spectrum shifts to shorter T2`；`simulated decay becomes faster in small pores`
- **解释机制**：优先解释为表面弛豫增强、小孔/高表面积体积比、或受限扩散导致的有效弛豫时间缩短。若样品存在磁化率差异或 echo spacing 较长，也要检查内部梯度造成的附加去相干。
- **谨慎边界**：不能只凭短 T2 就断言孔径小；表面弛豫率、扩散区制、内部梯度和数据采样都会影响峰位。
- **推荐引用**：[@BrownsteinTarr1979] [@MullerPetke2015DiffusionRegimes] [@Mohnke2015TriangularPores] [@Keating2012NMRAssumptions] [@Dunn2002PorousMediaNMR] [@Kleinberg1994RelaxationMechanism] [@KeatingKnight2007IronOxides]
- **报告句式示例**：短 T2 增强通常支持小孔或高表面积/体积比导致表面弛豫增强的解释，但该判断应结合扩散区制和内部梯度影响共同评估 [@BrownsteinTarr1979; @MullerPetke2015DiffusionRegimes].

## 长 T2 尾部或长 T2 面积占比高

- **场景 ID**：`long_t2_tail`
- **触发线索**：`long_fraction high`；`tail extends > 1000 ms`；`peak near upper T2 bound`
- **解释机制**：长 T2 可指示更弱表面弛豫、更大孔隙或更自由流体；但如果峰贴近反演上限，可能是 T2 搜索范围、噪声或正则化造成的边界效应。
- **谨慎边界**：当峰位靠近 t2_max_ms 时，先把它标为边界/不稳定信号，不要直接解释为真实超长孔隙组分。
- **推荐引用**：[@Whittall1991NNLS] [@Coates1999NMRLogging] [@Keating2012NMRAssumptions] [@Hurlimann1998EffectiveGradients]
- **报告句式示例**：长 T2 组分可与较弱表面弛豫或更自由流体有关，但若峰贴近反演搜索上限，应同时考虑逆问题边界效应和正则化敏感性 [@Whittall1991NNLS; @Coates1999NMRLogging].

## 多个预期孔群变成宽峰或合并峰

- **场景 ID**：`broad_or_merged_peaks`
- **触发线索**：`broad peak`；`expected two pore sizes but one spectral peak`；`peaks merge when pores are connected`；`spectrum smoother than pore-size distribution`
- **解释机制**：优先考虑扩散耦合/孔间交换：自旋在不同孔尺度之间扩散，多个局部弛豫环境被平均化。正则化过强也会把相邻峰合并，因此需要同时检查 L-curve 或固定 regularization 设置。
- **谨慎边界**：峰合并不是“只有一个孔群”的充分证据；也可能来自连通性、扩散耦合或反演平滑。
- **推荐引用**：[@Chi2015DiffusionalCoupling] [@Toumelin2003TemperatureDiffusiveCoupling] [@Fraga2013CarbonatePoreCoupling] [@Song2014PoreCouplingReview] [@Ramakrishnan1999Carbonates] [@Fleury2009PoreCoupling] [@Carneiro2014DiffusiveCoupling] [@Alhwety2014RockTypingDiffusiveCoupling] [@Borgia1998UniformPenalty]
- **报告句式示例**：宽峰或峰合并可以由孔间扩散耦合造成，即自旋在不同孔隙尺度间交换后使局部弛豫环境被平均化；这类现象不能简单等同于单一孔群 [@Chi2015DiffusionalCoupling; @Song2014PoreCouplingReview].

## 多峰 T2 谱

- **场景 ID**：`multimodal_spectrum`
- **触发线索**：`two or more peaks`；`multimodal spectrum`；`gaussian peak table has multiple components`
- **解释机制**：多峰可作为不同弛豫环境、孔尺度或流体状态的提示；但峰数受正则化、噪声、采样窗口和分峰模型影响。Gaussian 分峰应作为描述性解释工具，而不是唯一物理分类。
- **谨慎边界**：报告中用“component/组分”描述即可，不要宣称每个 Gaussian 峰必然对应一个真实孔群。
- **推荐引用**：[@Whittall1991NNLS] [@Coates1999NMRLogging] [@Grunewald2009PoreCoupling] [@Song2016T2T2] [@WhittallMacKay1989NNLS] [@Borgia1998UniformPenalty]
- **报告句式示例**：多峰 T2 谱提示样品中可能存在多个弛豫环境，但反演与 Gaussian 分峰本身并不能唯一证明相同数量的物理孔群 [@Whittall1991NNLS; @Grunewald2009PoreCoupling].

## 正则化因子改变后峰数、峰宽或峰位明显变化

- **场景 ID**：`regularization_sensitive`
- **触发线索**：`regularization sensitivity`；`alpha change changes peaks`；`lcurve selected alpha`；`roughness_norm high`；`fixed regularization uncertain`
- **解释机制**：这是逆 Laplace/多指数反演病态性的典型表现。弱正则化更容易追随噪声并产生尖峰，强正则化更平滑但可能合并真实峰。
- **谨慎边界**：解释峰数前先报告正则化方法；推荐把 L-curve 选择、残差和粗糙度一起呈现。
- **推荐引用**：[@Whittall1991NNLS] [@Coates1999NMRLogging] [@Schwartz2013T2T2Simulation] [@Yu2019T2T2] [@Hansen1992LCurve] [@Borgia1998UniformPenalty] [@WhittallMacKay1989NNLS]
- **报告句式示例**：该谱对正则化敏感，说明峰形包含反问题稳定性因素；较小正则化可能放大噪声，较大正则化则可能平滑或合并相邻组分 [@Whittall1991NNLS; @Schwartz2013T2T2Simulation].

## 谱线振荡、噪声峰或负/异常拟合迹象

- **场景 ID**：`noisy_oscillatory_or_false_peaks`
- **触发线索**：`oscillatory spectrum`；`many narrow peaks`；`large residual`；`poor fit`；`noise amplified`
- **解释机制**：优先检查输入衰减信噪比、早期点质量、echo train 采样、T2 范围和正则化。NNLS 非负约束可以避免负谱值，但不能自动保证峰都具有物理意义。
- **谨慎边界**：不要给每个窄噪声峰分配物理机制；先建议重跑 L-curve、增加平滑或限制 T2 范围。
- **推荐引用**：[@Whittall1991NNLS] [@Coates1999NMRLogging] [@EchoTrainSimulation2021] [@WhittallMacKay1989NNLS] [@Borgia1998UniformPenalty]
- **报告句式示例**：振荡谱或多个窄峰更可能反映噪声放大和反演不稳定性，解释前应检查 echo train 数据质量和正则化强度 [@Whittall1991NNLS; @EchoTrainSimulation2021].

## 峰贴近 T2 搜索边界

- **场景 ID**：`peak_at_t2_bounds`
- **触发线索**：`peak near t2_min_ms`；`peak near t2_max_ms`；`boundary component`；`spectrum mass at limits`
- **解释机制**：峰贴近边界通常表示搜索范围设置影响结果，或数据中没有足够信息约束该时间尺度。短边界峰可能来自早期采样不足；长边界峰可能来自尾部噪声或上限过宽。
- **谨慎边界**：报告为“边界敏感组分”，建议调整 T2 范围和采样窗口做敏感性分析。
- **推荐引用**：[@Whittall1991NNLS] [@Coates1999NMRLogging]
- **报告句式示例**：边界附近峰应视为搜索范围和数据约束共同作用下的敏感结果，需要通过调整 T2 范围或正则化进行复核 [@Whittall1991NNLS].

## 改变孔隙几何后 T2 谱峰位或峰宽改变

- **场景 ID**：`simulation_geometry_effect`
- **触发线索**：`geometry changes spectrum`；`triangular/circular/irregular pore`；`surface-to-volume ratio changed`；`connectivity changed`
- **解释机制**：孔形、表面积/体积比、连通性和边界条件会改变扩散-弛豫特征模态，因此 T2 谱变化可以从几何和边界弛豫共同解释。
- **谨慎边界**：不要把几何影响简化为“孔越大 T2 越长”；非球形孔、角点、部分饱和和连通性都会改变响应。
- **推荐引用**：[@BrownsteinTarr1979] [@Mohnke2015TriangularPores] [@Hagslatt2002RestrictiveGeometries] [@Mohnke2010PoreScaleSimulation]
- **报告句式示例**：几何改变影响 T2 谱，是因为受限扩散和表面弛豫边界共同改变扩散-弛豫模态，而非仅仅改变一个等效孔径 [@BrownsteinTarr1979; @Mohnke2015TriangularPores].

## 随机游走正演结果与反演 T2 谱对应

- **场景 ID**：`random_walk_forward_model`
- **触发线索**：`random walk simulation`；`Monte Carlo decay`；`forward simulated echo decay`；`compare simulated pore geometry with inverted spectrum`
- **解释机制**：随机游走可把孔隙几何、扩散系数、表面弛豫率和场不均匀转化为 echo decay；再用同一反演流程得到 T2 谱，适合验证从结构到谱的机制链。
- **谨慎边界**：反演谱仍受反演参数影响；正演真实参数和反演恢复谱之间不应期待完全一一对应。
- **推荐引用**：[@Toumelin2007GeneralRandomWalk] [@Toumelin2003GeneralRandomWalk] [@Toumelin2002MonteCarloNMR] [@LucasOliveira2018RestrictedDiffusion] [@Liebig1993RandomWalk] [@Noetinger2016DiffusionRandomWalk] [@SCA2008PoreScaleNMRSimulation]
- **报告句式示例**：随机游走正演为孔隙结构、扩散和表面弛豫到 echo decay/T2 谱之间建立了可检验的机制链 [@Toumelin2007GeneralRandomWalk; @Toumelin2002MonteCarloNMR].

## FEM/FVM/COMSOL 网格模型结果解释

- **场景 ID**：`fem_fvm_mesh_model`
- **触发线索**：`finite element simulation`；`finite volume simulation`；`COMSOL model`；`mesh boundary condition`；`PDE diffusion relaxation`
- **解释机制**：网格法通过求解扩散-弛豫方程显式处理复杂几何、边界表面弛豫和内部梯度。结果解释应报告边界条件、网格分辨率、扩散系数和表面弛豫率。
- **谨慎边界**：数值解的可信度依赖网格和边界条件；若结果与随机游走不同，先检查离散化和边界实现。
- **推荐引用**：[@Tandon2018FiniteVolumeInternalGradients] [@Mitchell2019FiniteElementNMR] [@Ghomeshi2018FEMNMR] [@Oliveira2021COMSOLNMRGuide] [@Mohnke2010PoreScaleSimulation]
- **报告句式示例**：FEM/FVM 正演可把复杂孔隙几何、表面弛豫边界和内部梯度纳入同一扩散-弛豫方程框架，因此适合解释几何控制的 T2 响应 [@Tandon2018FiniteVolumeInternalGradients; @Mitchell2019FiniteElementNMR].

## 内部梯度或场不均匀导致 T2 缩短

- **场景 ID**：`internal_gradient_shortening`
- **触发线索**：`internal gradients enabled`；`field inhomogeneity`；`echo spacing changes T2`；`susceptibility contrast`；`long T2 suppressed`
- **解释机制**：内部磁场梯度与扩散共同造成附加去相干，可能使 T2 谱整体变短或压低长 T2 组分。echo spacing 越敏感，越应考虑梯度项。
- **谨慎边界**：不要把所有 T2 缩短都归因于孔径变小；内部梯度是模拟和实验偏差的重要候选机制。
- **推荐引用**：[@Tandon2018FiniteVolumeInternalGradients] [@Gonzalez2020FieldInhomogeneities] [@Keating2012NMRAssumptions] [@Mohnke2010PoreScaleSimulation] [@KleinbergHorsfield1990TransverseRelaxation] [@Hurlimann1998EffectiveGradients] [@KeatingKnight2007IronOxides]
- **报告句式示例**：若模型包含内部梯度或场不均匀，T2 缩短可能来自扩散诱导去相干，而不只是孔径变小或表面弛豫增强 [@Tandon2018FiniteVolumeInternalGradients; @Gonzalez2020FieldInhomogeneities].

## CPMG 采样、早期点和 trim-from-peak 对反演的影响

- **场景 ID**：`cpmg_sampling_trim`
- **触发线索**：`early rise before decay`；`trim_from_peak true/false`；`missing early echoes`；`echo spacing large`；`CPMG artifacts`
- **解释机制**：反演只知道输入的 echo train；早期点决定短 T2 可恢复性，尾部噪声影响长 T2，trim-from-peak 会改变有效起点和幅值归一化。
- **谨慎边界**：如果原始模拟数据先上升后衰减，trim 是合理前处理；但对真实实验中从最大值开始的干净衰减，过度 trim 可能丢失短 T2 信息。
- **推荐引用**：[@Whittall1991NNLS] [@EchoTrainSimulation2021] [@Tan2012T2T1Simulation] [@Toumelin2007GeneralRandomWalk]
- **报告句式示例**：T2 反演首先受 echo train 采样窗口和早期点质量限制，因此 trim-from-peak、echo spacing 和尾部噪声都应作为解释谱形稳定性的因素 [@Whittall1991NNLS; @EchoTrainSimulation2021].

## 一维 T2 谱无法唯一解释，需要多维 NMR 或额外证据

- **场景 ID**：`need_multidimensional_validation`
- **触发线索**：`ambiguous component assignment`；`pore coupling suspected`；`fluid type unclear`；`T2 peaks overlap`；`exchange suspected`
- **解释机制**：一维 T2 是多个机制投影后的结果。T2-T2/T1-T2 可提供交换、耦合和不同流体/孔隙环境的相关信息，适合作为复杂解释的补充。
- **谨慎边界**：不要在一维 T2 结果上过度区分流体类型或孔群；用“提示”而非“证明”。
- **推荐引用**：[@Song2012MRPM] [@Schwartz2013T2T2Simulation] [@Song2016T2T2] [@Song2008T2T2] [@Johnson2014T2T2] [@Monteilhet2006T2T2] [@Guo2016MultidimensionalNMRSimulation] [@Kleinberg1994RelaxationMechanism]
- **报告句式示例**：对于耦合或交换明显的复杂样品，一维 T2 峰位和面积不足以唯一分配孔群或流体类型，多维 NMR 可提供更强的相关约束 [@Song2012MRPM; @Song2016T2T2].

## 多指数衰减的特征模态解释

- **场景 ID**：`matrix_mode_interpretation`
- **触发线索**：`matrix diagonalization`；`eigenvalue modes`；`multiple exponential modes`；`semi-analytical forward model`
- **解释机制**：多指数衰减可理解为扩散-弛豫算子的多个特征模态叠加。特征值受孔隙几何、边界弛豫、饱和历史和连通性影响。
- **谨慎边界**：模态不必等同于离散物理孔群；它是数学表示与物理结构共同决定的响应。
- **推荐引用**：[@Chang2000MatrixDiagonalization] [@Chang2001DrainageSaturationHistory] [@MatrixDiagonalization2002NMR] [@McCall1991RestrictedDiffusion]
- **报告句式示例**：多指数衰减也可从扩散-弛豫算子的特征模态角度理解，模态权重和衰减率受几何与边界条件共同控制 [@Chang2000MatrixDiagonalization; @McCall1991RestrictedDiffusion].

## LBM 孔尺度模拟解释

- **场景 ID**：`lbm_modeling`
- **触发线索**：`LBM simulation`；`lattice Boltzmann`；`voxel pore image`；`complex boundaries`
- **解释机制**：LBM 适合在离散格点上模拟复杂边界中的扩散过程，可用于从数字孔隙结构正演 NMR 响应。
- **谨慎边界**：LBM 结果依赖格点分辨率、边界实现和表面弛豫参数；需要与 FEM/随机游走结果交叉检查。
- **推荐引用**：[@Mohnke2014LBMNMR] [@Guyer2000LBMDiffusion]
- **报告句式示例**：LBM 可作为数字孔隙结构到 NMR 衰减响应的孔尺度正演方法，尤其适合复杂边界扩散问题 [@Mohnke2014LBMNMR; @Guyer2000LBMDiffusion].

## L-curve 不清晰或自动正则化选择不稳定

- **场景 ID**：`lcurve_flat_or_unstable`
- **触发线索**：`lcurve corner unclear`；`flat lcurve`；`selected alpha at search bound`；`multiple comparable alpha values`；`regularization choice unstable`
- **解释机制**：L-curve 自动选参是项目中的算法决策；若曲线没有明显折角或选中值贴近搜索边界，说明数据拟合与平滑之间的折中不够稳定，应把结果作为探索性解释，并尝试调整 alpha 范围、T2 范围或数据预处理。
- **谨慎边界**：本地知识库中没有专门证明当前 L-curve 规则的论文；这些引用支撑的是反演/正则化必要性，不应写成“某论文提出本项目 L-curve 选择准则”。
- **推荐引用**：[@Whittall1991NNLS] [@Coates1999NMRLogging] [@Hansen1992LCurve]
- **报告句式示例**：当 L-curve 缺少清晰折角或选中正则化贴近搜索边界时，反演谱应被视为正则化敏感结果；这反映了多指数反演需要在拟合精度和平滑性之间做稳定性折中 [@Whittall1991NNLS; @Coates1999NMRLogging].

## Gaussian 分峰过拟合或残差仍较大

- **场景 ID**：`gaussian_overfit_or_bad_residual`
- **触发线索**：`gaussian residual high`；`too many gaussian peaks`；`components overlap strongly`；`peak count changes interpretation`；`fit improves but components become unphysical`
- **解释机制**：Gaussian 分峰只是 log T2 谱形的经验近似。若增加峰数只改善数值残差但导致高度重叠、面积分数不稳定或峰位缺乏物理解释，应降低峰数或把该结果标为描述性拟合。
- **谨慎边界**：Whittall/Coates 支撑的是反演谱与组分解释需要谨慎，不是 Gaussian decomposition 方法来源。
- **推荐引用**：[@Whittall1991NNLS] [@Coates1999NMRLogging] [@Grunewald2009PoreCoupling]
- **报告句式示例**：Gaussian 分峰可帮助描述 T2 谱形，但峰数和面积分配会受反演谱稳定性、噪声和孔耦合影响；高度重叠或残差异常时不宜把每个峰直接解释为独立物理孔群 [@Whittall1991NNLS; @Grunewald2009PoreCoupling].

## 表面弛豫率改变导致 T2 峰位系统移动

- **场景 ID**：`surface_relaxivity_sensitivity`
- **触发线索**：`surface relaxivity changes peak`；`rho_s sensitivity`；`same geometry different T2`；`surface relaxation parameter sweep`
- **解释机制**：表面弛豫率控制边界处磁化衰减强度。在几何相同的模型中，提高表面弛豫率通常会使有效 T2 缩短并增强短 T2 组分。
- **谨慎边界**：表面弛豫率变化与孔径变化可能产生相似谱形，需要通过参数扫掠或独立约束区分。
- **推荐引用**：[@BrownsteinTarr1979] [@Mohnke2010PoreScaleSimulation] [@MullerPetke2015DiffusionRegimes] [@Kleinberg1994RelaxationMechanism] [@Foley1996ParamagneticIons] [@KeatingKnight2007IronOxides]
- **报告句式示例**：在几何不变时，表面弛豫率升高会增强边界弛豫并使有效 T2 缩短，因此 T2 峰位移动不一定只代表孔径变化 [@BrownsteinTarr1979; @Mohnke2010PoreScaleSimulation].

## 网格分辨率或边界条件改变影响模拟结果

- **场景 ID**：`mesh_resolution_boundary_condition_sensitivity`
- **触发线索**：`mesh sensitivity`；`boundary condition sensitivity`；`FEM result changes with mesh`；`finite volume discretization changes decay`
- **解释机制**：FEM/FVM 模型显式求解扩散-弛豫方程，网格分辨率、边界表面弛豫实现和内部梯度项都会影响数值衰减。模拟解释应报告这些设置并做敏感性检查。
- **谨慎边界**：若网格或边界条件改变导致 T2 谱变化，先视为数值敏感性，不要直接解释为物理机制变化。
- **推荐引用**：[@Tandon2018FiniteVolumeInternalGradients] [@Mitchell2019FiniteElementNMR] [@Oliveira2021COMSOLNMRGuide] [@Mohnke2010PoreScaleSimulation]
- **报告句式示例**：网格型正演的 T2 响应不仅取决于物理参数，也受网格分辨率和边界条件实现影响，因此 FEM/FVM 结果应配合数值敏感性检查解释 [@Tandon2018FiniteVolumeInternalGradients; @Oliveira2021COMSOLNMRGuide].

## 采集窗口过短导致长 T2 不可靠

- **场景 ID**：`acquisition_window_too_short_for_long_t2`
- **触发线索**：`decay does not reach baseline`；`short acquisition window`；`long T2 beyond max time`；`tail poorly sampled`；`few late echoes`
- **解释机制**：长 T2 组分需要足够长的 echo train 才能被稳定约束。若采样窗口太短或尾部噪声大，反演可能把未被约束的长时间尺度表现为边界峰或长尾。
- **谨慎边界**：长尾解释前先检查最大采样时间、尾部信噪比和 t2_max_ms；必要时重采样或缩窄 T2 上限。
- **推荐引用**：[@Whittall1991NNLS] [@Coates1999NMRLogging] [@EchoTrainSimulation2021]
- **报告句式示例**：若 echo train 未覆盖足够长的衰减尾部，长 T2 组分会受到采样窗口和噪声的强约束，边界长尾应谨慎解释 [@Whittall1991NNLS; @Coates1999NMRLogging].

## 快扩散假设失效或平均孔径估计不可靠

- **场景 ID**：`fast_diffusion_assumption_breakdown`
- **触发线索**：`outside fast diffusion regime`；`large pore with slow diffusion`；`surface relaxivity high`；`pore-size estimate inconsistent`；`T2-pore mapping breaks down`
- **解释机制**：许多 T2-孔径换算依赖快扩散近似；当扩散长度、孔尺度、表面弛豫率或连通结构使该近似不成立时，平均孔径估计会偏离真实孔径结构。
- **谨慎边界**：不要在快扩散假设未验证时把 T2 分布直接换算为孔径分布。
- **推荐引用**：[@MullerPetke2015DiffusionRegimes] [@Keating2012NMRAssumptions] [@Ramakrishnan1999Carbonates] [@BrownsteinTarr1979] [@Kleinberg1994RelaxationMechanism]
- **报告句式示例**：T2 与孔径的直接对应通常依赖快扩散近似；当样品处于非快扩散区制或存在强耦合时，T2 推断的孔径分布可能偏离真实结构 [@MullerPetke2015DiffusionRegimes; @Keating2012NMRAssumptions].

## 含铁/顺磁矿物导致 T2 整体偏短

- **场景 ID**：`paramagnetic_mineral_shortening`
- **触发线索**：`iron-bearing soil or sand`；`red or weathered geomaterial`；`T2 shorter than expected for known pore size`；`clay or iron oxide coating`；`same geometry different sample chemistry`
- **解释机制**：孔壁上的顺磁离子（Fe3+、Mn2+）和铁氧化物会显著提高表面弛豫率，使同样孔径下的 T2 更短；磁铁矿等强磁性矿物还会引入内部梯度。
- **谨慎边界**：不要把含铁样品的短 T2 直接换算为小孔；需要已知或标定的表面弛豫率，或用其他孔径测量约束。
- **推荐引用**：[@Kleinberg1994RelaxationMechanism] [@Foley1996ParamagneticIons] [@KeatingKnight2007IronOxides] [@Keating2012NMRAssumptions]
- **报告句式示例**：含铁矿物会显著提高表面弛豫率，因此含铁岩土材料中 T2 偏短不一定代表孔径更小 [@KeatingKnight2007IronOxides; @Foley1996ParamagneticIons].
