# Decoupled Composite Bayesian Optimisation for Catalyst Discovery

## 1. Project Overview

### Research objective

Develop and evaluate a Bayesian optimisation (BO) framework that reduces the number of expensive atomistic calculations required to identify promising heterogeneous catalysts.

The central idea is that catalytic performance often depends on the adsorption energies of multiple reaction intermediates. Conventional screening approaches may calculate every relevant intermediate on every candidate surface, even when some calculations contribute relatively little information to the final catalyst selection.

We propose using **decoupled, composite multi-objective Bayesian optimisation** to select which catalyst surface and adsorption intermediate should be evaluated next.

The acquisition function should consider:

- How an adsorption-energy measurement contributes to the final catalytic objectives.
- The uncertainty in adsorption-energy predictions.
- Statistical correlations between different adsorption intermediates.
- The computational cost of evaluating each intermediate.
- Whether a catalyst surface has already been relaxed and can be reused.

The primary goal is to demonstrate that selective evaluation of adsorption intermediates can recover promising catalysts and their Pareto front using fewer DFT calculations than conventional coupled screening.

### Research novelty

We are **not necessarily aiming to develop a new BO algorithm**.

Instead, the intended contribution is applying and evaluating established decoupled/composite BO principles for computational catalysis, where multiple adsorption energies contribute to coupled catalytic objectives.

Existing work includes conventional catalyst BO, multi-objective catalyst optimisation, active learning of adsorption energies, composite BO and decoupled BO.

Our specific application is:

**Cost-aware selection of individual adsorption intermediates to efficiently optimise composite catalytic objectives over candidate catalyst surfaces.**

We have not yet established that this exact application is absent from the literature. A systematic literature review will be needed before claiming it as the first demonstration.

A potential later extension is acquisition of individual adsorption sites, rather than entire surface–adsorbate evaluations.

---

## 2. Catalytic System and Dataset

### Selected system

We will initially study **CO₂ reduction on transition-metal nitride (TMN) surfaces**, using the DFT dataset associated with:

Yohannes et al. (2023), *ACS Catalysis*, 13, 9007–9017. DOI: [10.1021/acscatal.3c01249](https://doi.org/10.1021/acscatal.3c01249).

The data are available through CatHub and contain adsorption/reaction energies for four intermediates:

| Intermediate | CatHub label |
|---|---|
| *CO | CO |
| *CHO | CHO |
| *OH | HO / OH |
| *H | H |

The dataset includes different TMN compositions, crystal facets, surface terminations and adsorption configurations.

### Dataset processing completed

The original dataset contained approximately:

| Quantity | Original dataset |
|---|---:|
| Unique adsorbed structures | 8,307 |
| Unique clean slabs | 166 |
| Unique Materials Project bulk structures | 59 |

We reconstructed unrelaxed clean slabs from Materials Project bulk crystal structures using pymatgen.

Important aspects of the reconstruction:

- Use primitive-standard bulk structures rather than conventional cells, to preserve the relevant Miller-index interpretation.
- Generate (100) and (110) slabs, including different terminations and thicknesses.
- Orthogonalise the slab's out-of-plane lattice vector.
- Generate suitable lateral supercells.
- Match the generated slabs against relaxed CatHub clean slabs using composition, cell geometry and atomic positions.
- Retain high-confidence geometric matches.

This process retained 110 of 166 clean slabs, representing 47 of the original 59 bulk structures.

### Energy filtering

Some adsorption calculations had extremely exothermic reaction energies, including values below −10 eV.

Visual inspection showed that at least some of these configurations undergo major surface reconstruction, with one OH example suggesting lattice nitrogen expulsion and molecular N₂ formation.

These calculations may represent physically meaningful surface decomposition rather than ordinary adsorption on an intact nitride surface.

To maintain consistency with the original study, we applied an initial filter:

**−5 eV ≤ reaction energy ≤ +5 eV**

This filter changed the minimum recorded adsorption energy for only 16 surface–adsorbate combinations.

The excluded calculations are preserved separately. We should not assume every outlier is numerically invalid; additional geometry-based quality control may be useful.

### Current filtered dataset

| Quantity | Filtered dataset |
|---|---:|
| Clean slabs | 110 |
| Bulk structures | 47 |
| Adsorption calculations | 5,284 |
| Surfaces with all four intermediates | 104 |
| Bulk structures in complete-surface subset | 46 |
| Calculations in complete-surface subset | 5,209 |

The **104 complete surfaces** form the proposed primary BO benchmark.

The six incomplete surfaces will remain available for later investigations of missing observations.

The dataset retains reasonably balanced representation of the four adsorbates and crystal facets.

There are many nearly degenerate adsorption energies, potentially because distinct starting configurations relaxed to equivalent final states. These require further geometric investigation.

---

## 3. Optimisation Problem

### Design variables

The candidate designs are catalyst surfaces, denoted by \(S\).

Each surface has four relevant adsorption-energy quantities:

\[
\mathbf{E}(S)=
\begin{bmatrix}
E_{\mathrm{CO}}(S)\\
E_{\mathrm{CHO}}(S)\\
E_{\mathrm{OH}}(S)\\
E_{\mathrm H}(S)
\end{bmatrix}
\]

Initially, each energy is defined as the minimum recorded energy across the available adsorption configurations:

\[
E_a(S)=\min_{s\in\mathcal S_{S,a}} E_a(S,s)
\]

where \(a\) denotes the adsorbate and \(s\) is an adsorption configuration.

These are minima over the **available CatHub calculations**, not guaranteed global adsorption minima.

### Catalytic objectives

The ultimate optimisation problem is multi-objective:

\[
\max_S\mathbf f(S)
\]

where

\[
\mathbf f(S)=g(\mathbf E(S))
\]

The function \(g\) converts adsorption energies into catalytic screening objectives.

Our intended objectives are based on three competing catalytic properties:

1. **Activity:** Favourable CO₂-to-CO reduction activity, represented by an adsorption-energy-based limiting-potential or activity descriptor.
2. **Selectivity:** Preference for the desired CO₂ reduction pathway relative to competing hydrogen evolution.
3. **Resistance to poisoning:** Avoidance of strongly bound unwanted intermediates, particularly *OH.

The precise thermodynamic definitions, signs and targets must be finalised using the original study before the main BO experiments.

For early methodological tests, synthetic objectives constructed from the real DFT energies are acceptable, provided they are clearly identified as illustrative screening utilities rather than experimentally validated catalytic activities.

An important requirement is that the objectives depend on multiple adsorption energies and that some adsorption energies contribute to more than one objective.

For example, if the CO limiting potential depends on *CO and *CHO, those two intermediates may influence activity, selectivity and resistance simultaneously.

This creates the shared dependency structure that our acquisition strategy should exploit.

---

## 4. Bayesian Optimisation Formulation

### Decoupled evaluations

Instead of selecting a surface and evaluating all four adsorption intermediates, the algorithm selects:

\[
(S^*,a^*)=\arg\max_{S,a}\alpha(S,a)
\]

where:

- \(S\) is the selected catalyst surface.
- \(a\) is the selected adsorbate.
- \(\alpha(S,a)\) is a cost-aware acquisition function.

A query of \((S,a)\) evaluates that adsorbate across the available adsorption configurations on the selected surface.

The minimum energy is then obtained from those calculations.

Importantly, the query also provides individual site-specific energies, which can be used to train the surrogate.

### Why this is composite BO

The expensive underlying calculations predict adsorption energies:

\[
\mathbf E(S)
\]

The catalytic objectives are known functions of those energies:

\[
\mathbf f(S)=g(\mathbf E(S))
\]

This is a composite optimisation problem: rather than modelling the final objectives directly, we model the intermediate physical quantities and transform them through known functions.

Our formulation is also **decoupled**, because only selected components of the adsorption-energy vector are evaluated.

Using the known objective functions should not inherently compromise optimal decision-making. A correctly constructed value-of-information acquisition can use them directly to estimate the expected benefit of a calculation.

### Uncertainty propagation

The GP provides a posterior distribution over adsorption energies:

\[
p(\mathbf E\mid\mathcal D)
\]

We propagate this uncertainty through the objective functions using Monte Carlo sampling:

1. Draw joint adsorption-energy samples from the surrogate.
2. Determine the minimum adsorption energy across sites for each adsorbate.
3. Calculate the catalytic objectives for every sample.
4. Use the resulting objective samples to evaluate acquisition candidates.

It is important to sample jointly.

In general:

\[
\mathbb E[g(\mathbf E)]\neq g(\mathbb E[\mathbf E])
\]

Likewise, taking the minimum of predicted mean site energies does not correctly represent uncertainty in the lowest adsorption energy.

### Acquisition function

Our preferred acquisition strategy is a **cost-aware composite hypervolume value-of-information method**, potentially based on hypervolume knowledge gradient (HVKG).

Conceptually:

\[
\alpha(S,a)=
\frac{
\text{Expected improvement in Pareto decision quality}
}{
\text{Cost of evaluating }(S,a)
}
\]

The acquisition should consider the expected consequences of observing the selected adsorption energy, including changes to other predicted adsorption energies and to the final multi-objective Pareto front.

This may favour *CO or *CHO calculations because they affect several objectives, but it should not be hard-coded to prefer them.

For example, a less influential intermediate might be selected if it is much more uncertain, cheaper to evaluate, or particularly important for distinguishing promising candidates.

**Implementation status:** This acquisition is proposed, not yet implemented. Existing BoTorch components provide useful foundations, but selecting underlying adsorption-energy tasks for nonlinear composite objectives may require custom acquisition logic.

For development, we may first use a simpler Thompson-sampling or uncertainty-aware strategy before implementing full composite HVKG.

---

## 5. Surrogate Model

### Preferred approach: site-level prediction

Although the BO algorithm selects an entire **surface–adsorbate pair**, the surrogate can operate at the **adsorption-site level**.

This avoids the difficulty of representing a chemically heterogeneous surface with a single global feature vector.

The model predicts:

\[
E_a(S,s)
\]

where \(s\) denotes a local adsorption environment.

A surface–adsorbate query reveals the results for all available configurations belonging to that pair.

The model is updated using those individual energies.

The resulting surface-level adsorption energy is:

\[
E_a(S)=\min_s E_a(S,s)
\]

The site-level surrogate therefore provides the physical predictions, while the BO algorithm makes surface-level decisions.

### Structural featurisation

Candidate inputs include:

- DSTAR / m-DSTAR site descriptors.
- SOAP descriptors.
- Local atomic composition.
- Metal coordination environments.
- Nearest- and next-nearest-neighbour species.
- Subsurface atomic environments.
- Potentially surface-level context such as facet or termination.

Descriptors should be generated from **unrelaxed clean-slab geometries**, since these are intended to be available before expensive DFT calculations.

This avoids using information from the relaxed adsorbate structure as a predictive feature when that information would not be available before evaluation.

### Correlated multi-task GP

Our preferred primary surrogate is a multi-task Gaussian process predicting the four adsorbates jointly.

A simple covariance model is:

\[
\operatorname{Cov}
[E_a(\mathbf x),E_b(\mathbf x')]
=
k(\mathbf x,\mathbf x')B_{ab}
\]

where \(B_{ab}\) describes the correlations between adsorbates.

A correlated model may transfer information from one adsorbate to another, allowing a *CO evaluation to reduce uncertainty in *CHO predictions, for example.

However, this advantage is not guaranteed.

Different intermediates may respond differently to local chemistry, and an overly restrictive multi-task model may produce negative transfer.

We will therefore compare:

- **Correlated multi-task GP:** Primary candidate.
- **Independent GPs:** Baseline and ablation study.

The comparison should include adsorption-energy prediction accuracy, uncertainty calibration and BO performance.

Correlations between adsorption energies are distinct from the deterministic dependencies introduced by the composite objective functions. Both mechanisms may contribute to the efficiency of decoupled BO.

### Site matching limitation

CatHub's `site1`, `site2`, etc. labels appear to be ordered by reaction energy rather than identifying consistent geometric adsorption sites.

Consequently, these labels cannot be used directly as physical site descriptors.

We need to map adsorbed DFT structures to geometric environments on the reconstructed unrelaxed slabs.

Potential complications include:

- Surface reconstruction during adsorption.
- Migration between initial and final adsorption sites.
- Equivalent starting configurations converging to the same final geometry.
- Multiple binding geometries for an adsorbate.
- Dissociation or surface decomposition.
- Difficulty inferring the initial adsorption site from a relaxed final structure.

This is a significant remaining technical task.

A final-state geometric assignment must not be treated as an unquestionably known pre-calculation site. We will need confidence measures and appropriate filtering.

If reliable matching proves impractical, the initial aggregate surface–adsorbate benchmark can proceed without a site-resolved surrogate.

---

## 6. Computational Cost Model

Unlike a standard BO benchmark, evaluations have different costs.

The cost depends on:

1. Whether the clean slab has already been relaxed.
2. How many adsorption configurations must be evaluated.
3. Potential differences in the costs of individual adsorption calculations.

A suitable formulation is:

\[
c(S,a\mid\mathcal D)=
c_{\mathrm{slab}}(S)
\mathbb{1}_{\text{slab not yet relaxed}}
+
\sum_{s\in\mathcal S_{S,a}}c_{\mathrm{ads}}(S,a,s)
\]

The clean-slab relaxation is a shared cost, paid only once per surface.

For example:

- The first adsorbate evaluated on a new surface incurs clean-slab relaxation plus adsorption calculations.
- Subsequent adsorbates on that surface reuse the relaxed clean slab.
- Surfaces with fewer candidate adsorption configurations may be cheaper to investigate.

### Initial cost approximation

Initially, use:

- One cost unit per adsorption calculation.
- One additional cost unit for the clean-slab relaxation.
- The number of recorded adsorption calculations as a proxy for the cost of evaluating all sites.

We may later refine these costs using DFT wall times, atom counts or actual computational resources.

**Important:** Cost estimates should account for attempted calculations, including those excluded from the final training data by the energy-quality filter. An excluded calculation still incurred computational cost.

We must also distinguish the total number of recorded CatHub calculations from the number of distinct geometric sites. Different starting configurations may converge to the same final adsorption state.

The retrospective benchmark assumes the query cost is known or estimable before evaluation, but the energies themselves remain hidden.

---

## 7. Benchmark Design

### Primary evaluation

Use the filtered dataset as a finite DFT oracle.

The true stored adsorption energies are hidden from the optimiser until the corresponding query is selected.

At every iteration:

1. Fit or update the surrogate using previously observed calculations.
2. Predict adsorption energies for the candidate library.
3. Propagate uncertainty through adsorption-site minima and composite objectives.
4. Calculate the cost-aware acquisition values.
5. Select a surface and adsorbate.
6. Reveal all available site energies for that pair.
7. Update the dataset and computational budget.
8. Evaluate progress towards identifying the reference Pareto-optimal surfaces.

The underlying benchmark is retrospective: no new DFT calculations are initially required.

### Primary baseline methods

| Method | Strategy |
|---|---|
| Coupled BO | Select a surface and evaluate all four adsorbates |
| Random decoupled | Select a random unevaluated surface–adsorbate pair |
| Uncertainty-based decoupled BO | Select informative or uncertain intermediate measurements |
| Composite-aware decoupled BO | Select measurements based on their expected effect on the final catalytic objectives |
| Optional adapted Thompson sampling | Select promising surfaces from posterior samples, then choose individual measurements |

For a fair comparison, baselines should use comparable surrogate models, initial observations and computational budgets.

The effect of correlated versus independent GP modelling should be tested separately from the effect of the acquisition function.

### Evaluation metrics

Primary metrics:

- **Reference Pareto hypervolume recovery versus cumulative calculation cost.**
- **Hypervolume regret versus cumulative calculation cost.**
- **Cost required to reach a specified fraction of the reference Pareto hypervolume.**

Secondary metrics:

- Recovery of true Pareto-optimal surfaces.
- Ranking quality among promising candidates.
- Adsorbate-selection frequencies.
- Number of unique surfaces studied.
- Allocation of computational budget between clean slabs and adsorption calculations.
- Adsorption-energy predictive performance and uncertainty calibration.

We should evaluate posterior-recommended catalysts using the hidden reference oracle for benchmarking, while preventing the acquisition from accessing those unrevealed values.

Repeat optimisation campaigns using different initial observations and random seeds to establish statistical reliability.

### Ablation studies

Potential experiments include:

1. Correlated multi-task GP versus independent GPs.
2. Coupled versus decoupled evaluations.
3. Composite-aware acquisition versus uncertainty-based acquisition.
4. Uniform evaluation costs versus realistic heterogeneous costs.
5. Shared clean-slab costs versus independent evaluation costs.
6. Aggregate adsorption-minimum surrogate versus site-level surrogate.
7. Sensitivity to the objective definitions and energy filtering.

The central objective is to isolate whether **selectively evaluating adsorption intermediates improves catalyst-discovery efficiency**, rather than attributing every improvement to the acquisition function.

---

## 8. Implementation Strategy

We will develop the project incrementally.

### Stage 1 — Aggregate surface–adsorbate benchmark

**Priority: first working BO experiment.**

Use the minimum retained adsorption energy for each of the four intermediates on the 104 complete surfaces.

Each surface–adsorbate pair is treated as a single selectable task.

Tasks are initially evaluated through a lookup table rather than through a site-level surrogate.

Required steps:

- Construct a table of the four adsorption-energy minima for each surface.
- Finalise the three catalytic objective functions.
- Produce inexpensive surface-level descriptors for a first surrogate.
- Implement independent and correlated GP models.
- Implement coupled and simple decoupled baselines.
- Implement an initial composite-aware acquisition strategy.
- Compare Pareto recovery against an aggregate evaluation budget.

This stage validates the decoupled composite BO framework without requiring geometric adsorption-site matching.

It is a methodological prototype: revealing a minimum directly is an abstraction of the underlying site-search process.

### Stage 2 — Introduce realistic costs

Replace uniform task costs with the estimated cost of evaluating all available adsorption configurations for a surface–adsorbate pair.

Include the shared clean-slab relaxation cost.

Evaluate whether cost-aware intermediate selection improves computational efficiency.

### Stage 3 — Site-level surrogate

Complete adsorption-site matching and site featurisation.

Train a multi-task GP on individual site-specific reaction energies.

For every candidate surface and adsorbate, use joint posterior samples across sites to estimate the distribution of its minimum adsorption energy.

Retain the same surface–adsorbate-level acquisition decision.

When queried, reveal all corresponding site energies, rather than only the minimum.

This stage provides a more realistic physical surrogate and makes use of the full dataset.

### Possible Stage 4 — Site-resolved acquisition

Extend the selectable query from:

\[
(S,a)
\]

to:

\[
(S,a,s)
\]

The algorithm would then choose individual adsorption sites, avoiding exhaustive evaluation of every configuration.

This introduces an additional optimisation problem: deciding which local adsorption configurations are most likely to change the estimated surface-level minima and final composite objectives.

**This is a possible extension, not a requirement for the initial project.**

---

## 9. Relevant Literature and Tools

### Catalysis dataset

**Yohannes et al. (2023)**  
*ACS Catalysis*, 13, 9007–9017.  
[DOI: 10.1021/acscatal.3c01249](https://doi.org/10.1021/acscatal.3c01249)

Source of the transition-metal nitride dataset and adsorption-energy-based catalytic screening objectives.

### Composite Bayesian optimisation

**Guilhoto and Perdikaris (2024)**  
*Scientific Reports*.  
[Article](https://www.nature.com/articles/s41598-024-79621-7)

Demonstrates composite BO where expensive intermediate predictions are transformed by known functions. Its NEON framework is designed for high-dimensional function outputs and is more sophisticated than our initial problem requires.

### Decoupled multi-objective BO

**Renganathan and Bachman (2026)**  
[arXiv:2609.32632](https://arxiv.org/abs/2609.32632)

Introduces qPOTS-DOE, combining Pareto-optimal Thompson sampling and correlation-aware selection of which objectives to evaluate.

Relevant because it demonstrates that partial evaluation of correlated tasks can improve optimisation efficiency.

Our problem differs because we measure underlying adsorption energies rather than directly observing the final multi-objective outputs.

### Software

- **BoTorch / GPyTorch:** GP modelling, posterior sampling, multi-task modelling and BO components.
- **ASE:** Atomistic structures and geometry analysis.
- **pymatgen:** Slab generation and adsorption-site enumeration.
- **Materials Project API:** Bulk crystal structures.
- **CatHub:** DFT adsorption structures and reaction energies.
- **DScribe / DSTAR:** Candidate structural descriptors for site-level surrogate modelling.

Existing implementations will be preferred over custom reimplementations where possible.

---

## 10. Main Scientific Questions

The project will investigate:

**Q1.** Can selective evaluation of adsorption intermediates identify Pareto-optimal catalysts more efficiently than coupled screening?

**Q2.** Does explicitly accounting for the known dependence of catalytic objectives on adsorption energies improve acquisition decisions?

**Q3.** Does modelling correlations between adsorption intermediates improve predictive performance and BO sample efficiency?

**Q4.** How much benefit is obtained by considering heterogeneous evaluation costs and reuse of previously relaxed slabs?

**Q5.** Does replacing surface-level adsorption-minimum predictions with a site-level surrogate improve optimisation efficiency?

**Q6.** Which intermediates does the acquisition preferentially evaluate, and how does this depend on their uncertainty, cost and influence on the catalytic objectives?

---

## 11. Limitations and Assumptions

The initial work is a finite-library, retrospective BO benchmark. Generalisation to completely unseen catalyst systems is not its primary aim.

Key limitations include:

- Only 104 complete surfaces in the primary benchmark.
- Several surfaces share the same bulk crystal, so observations are not chemically independent.
- The true global adsorption minimum may not be included among the recorded DFT configurations.
- Synthetic adsorption-energy-based objectives may not correspond to experimental catalytic activity.
- Realistic thermodynamic screening requires consistent adsorption-energy references and carefully defined operating conditions.
- Some DFT calculations may involve surface reconstruction or different chemical processes.
- CatHub site labels are not reliable geometric site identifiers.
- Initial aggregate tasks obscure the site-search process and require an approximate cost model.
- The preferred site-level surrogate depends on successful geometric matching of the existing DFT results.
- A more sophisticated acquisition function may be computationally expensive without providing significant improvements over simpler alternatives.

These limitations should be examined explicitly rather than concealed.

---

## 12. Current Status and Immediate Next Steps

### Completed

- [x] Select TMN CO₂ reduction as the demonstration system.
- [x] Retrieve and process the CatHub reaction dataset.
- [x] Identify the four relevant adsorption intermediates.
- [x] Reconstruct unrelaxed clean slabs from Materials Project structures.
- [x] Match reconstructed slabs against the CatHub clean slabs.
- [x] Filter high-confidence geometric matches.
- [x] Investigate extreme reaction-energy outliers.
- [x] Apply the initial ±5 eV reaction-energy filter.
- [x] Audit adsorbate coverage and dataset completeness.
- [x] Identify 104 surfaces suitable for the primary four-intermediate benchmark.
- [x] Establish the basic decoupled composite MOBO formulation.
- [x] Decide to begin with surface–adsorbate acquisition rather than individual-site acquisition.

### Next steps

- [ ] Finalise the mathematical definitions of activity, selectivity and poisoning resistance.
- [ ] Construct the surface–adsorbate minimum-energy oracle.
- [ ] Implement inexpensive surface-level descriptors for the initial benchmark.
- [ ] Evaluate independent and correlated GP surrogates.
- [ ] Implement coupled BO and simple decoupled baselines.
- [ ] Implement a composite-aware, cost-aware acquisition function.
- [ ] Define the reference Pareto front and evaluation metrics.
- [ ] Run repeated BO experiments and quantify computational savings.
- [ ] Develop and validate geometric adsorption-site matching.
- [ ] Introduce site-level structural descriptors and a site-level multi-task surrogate.
- [ ] Repeat the optimisation benchmark with site-level predictions and realistic calculation costs.
- [ ] Complete a systematic literature review to establish application-level novelty.

---

## 13. Proposed Project Contribution

The project aims to demonstrate that **Bayesian optimisation can exploit the shared dependence of catalytic objectives on multiple adsorption intermediates to reduce the computational cost of catalyst discovery**.

Rather than evaluating every intermediate for every candidate material, a decoupled acquisition strategy selects the most valuable calculations using surrogate uncertainty, correlations, known objective relationships and evaluation costs.

The methodology will initially be benchmarked on DFT adsorption data for transition-metal nitride catalysts, with a subsequent extension to site-level surrogate modelling.

The intended contribution is a scientifically grounded application and quantitative evaluation of existing BO methodology for computational catalysis, with particular emphasis on **efficient allocation of expensive atomistic calculations**.

The principal measure of success will be whether the proposed framework recovers high-quality Pareto-optimal catalyst candidates at a lower computational cost than conventional coupled screening.