# Eigh: mathematical correctness, reference phase and real NPU execution

Read this when an eigensolver passes local mathematics but fails a reference comparison, when eigenvector signs change across sizes/backends, or when a numerical helper passes in isolation but fails in the complete Ascend operator. It also covers cancellation-sensitive test oracles and multi-device evidence. For component errors that remain after sign alignment, read [residual refinement](eigh-residual-refinement.md). For earlier small-root, secular-bracket, scratch-layout, generated-code and GE failures, read the [numerics and memory companion](eigh-numerics-and-memory.md). Apply the relevant mechanisms, not every experiment below.

This is an evidence-scoped case, not a generally approved eigensolver. The phase-guide snapshot discussed below passed 136 complete NPU calls / 984 matrix records; its external evaluation was pending. Later residual-refinement evidence has a separate scope in the companion. An earlier candidate passed 11 of 12 external points. The external reference/checker identity was unknown. No performance improvement or complete sanitizer clearance is claimed. Selected local evidence hashes are in [eigh-provenance.json](eigh-provenance.json); raw code, device binaries and account history are not bundled.

## 1. Freeze the contract and inspect the real caller

Record the generated API signature, output order, dtype, shape, strides, storage offset, allocation size, workspace query, executor policy, synchronization and readback. Compare an actual native/framework invocation with the test adapter before changing kernel layout.

In this case, the generated order was `A, UPLO, eigenvaluesOut, eigenvectorsOut`; W had shape `[..., n]`, Q `[..., n, n]`, with eigenvectors in columns. Construct the effective symmetric matrix from the selected triangle of the **stored FP32 input**. Averaging both triangles is different behavior. Poisoning the ignored triangle with NaNs is a useful legal-input check where the contract allows it.

Case-specific criteria, evaluated separately for every batch matrix:

| Quantity | Required check in this case |
| --- | --- |
| W | FP32, finite, nondecreasing; `abs(W-W_ref) <= 1e-4 + 1e-4*abs(W_ref)` |
| Orthogonality | Absolute `||Q.T Q-I||_F <= 1e-4`; no division by n or batch size |
| Reconstruction | `||A_eff-Q diag(W) Q.T||_F <= 1e-4*||A_eff||_F` |
| Input family | n=1…512; every leading batch dimension 1…64; required spectral gap rechecked after FP32 storage and UPLO completion |

These bounds belong to this problem, not all eigensolvers. A per-column residual alone does not replace complete orthogonality and reconstruction. A limit on each batch dimension does not limit their product to the same number.

A real output-view counterexample wrote C-contiguous bytes into a Fortran-strided Q view, transposing its logical interpretation and failing reconstruction. The host tiling interface did not expose usable output strides in that route. Inspect descriptor and actual write behavior; an API declaration is not proof an adaptation ran. This finding did not establish the external runner's layout. Do not transpose outputs based on an unexplained score.

Distinguish reused addresses, reused workspace capacity and a repeatable executor. The ordinary helper recreated the executor; a separate supported repeatable-executor experiment was required to test one-executor reuse. Correctness checks must read after real device synchronization and retain input bits and canaries.

## 2. Keep three independent conclusions

1. **Mathematical validity:** W, orthogonality and reconstruction satisfy the contract.
2. **Reference representation:** column signs, ordering and, where relevant, basis choices agree with a specified reference implementation.
3. **External acceptance:** the actual evaluation has completed and met its acceptance condition.

Changing a whole real eigenvector column from q to -q preserves the decomposition. In the saved case, all 150 device matrix records passed the mathematical checks; direct Q comparison against a local NumPy reference passed only 73. Diagnostic column-sign alignment made all 150 pass that comparison. This reproduced a comparison-policy difference, not the identity or sole failure cause of an unavailable checker. Alignment was an offline diagnostic, never a repair performed by the test adapter on submitted outputs.

Do not infer a reference backend, hidden matrix size or number of wrong columns from a rounded error fraction. External sign-sensitive feedback is evidence about that observation, not permission to change the specified mathematics. When the checker is unavailable, continue with frozen, reproducible differences and clearly label backend hypotheses.

FP32 reference input/output does not establish FP32 internal computation. Inspect the pinned implementation and actual numerical library before attributing differences to a chip or storage dtype. Public solutions can have different tolerances, return conventions or permitted full-library calls; compare those constraints before adopting their method. Link and attribute external material rather than copying an unreviewed implementation or its success claim.

## 3. Locate the first divergent stage, not just the final sign

The n=2 branch forced each column's largest component positive. For `[[2,1],[1,2]]`, this reversed a column relative to the investigated public 2×2 rotation convention. The general n path did **not** contain the same writeback rule. Fixing this branch left the external feedback unchanged; neither its cause nor its repair generalized to larger n.

For a Householder / divide-and-conquer solver, freeze the raw input and inspect:

| Stage | Difference to isolate |
| --- | --- |
| Input and scaling | Actual stored bits, UPLO, normalization and special-value handling |
| Householder reduction | H, the actual tridiagonal D/E and arithmetic/rounding model |
| Leaves | Rotation/eigenpair conventions on the real device, not only a CPU arithmetic model |
| Deflation | Active versus inherited columns, normalized coupling vectors, thresholds and source-column mapping |
| Merge | Left/right pole order, root bracketing, permutations and phase metadata |
| Final basis | Whether Z solves the captured T, and whether HZ reproduces the complete normal output |

Useful failed approaches from this case:

- Materializing two multiplications made 42 real NPU leaf W/Q outputs bit-identical to an arithmetic model, but the complete candidate's reference-phase behavior regressed. Leaf agreement was not complete-solver agreement. Without instruction evidence, do not call this a proven fused-instruction or compiler defect.
- A local phase formula matched 173 tiny-coupling examples; recursive propagation still both improved and regressed columns. Another mathematically valid Loewner candidate changed many bits without reducing the observed phase differences.
- Ordinary-column reasoning predicted all 6,412 sampled ordinary columns, but applying it to 56 deflated columns gave 28 wrong predictions. A missing `1/sqrt(2)` boundary-vector normalization moved a threshold ratio from about 1.024 to 0.724, changing merge versus inheritance. Preserve these distinct classes.
- Increasing only the final dot-product precision did not remove a frozen negative reference dot, including under exact rational recomputation. Repair the stage where the representation first diverges.

Five frozen complete-call counterexamples were n246-L, n305-U, n434-L, n484-L and n499-U. Their exact input/output hashes, not these size labels alone, identify reproductions. The latter two also had internal-node differences; a root-stage explanation must not erase that evidence.

For the first two, captured NPU Z agreed in phase with the reference for the actual FP32 tridiagonal T, and HZ reproduced the normal NPU Q. The reference for original A differed because adjacent left/right child poles changed order during FP32 reduction. The root phase application was correctly consuming its actual T metadata. Blindly flipping its writeback would repair the symptom at the wrong layer.

## 4. Use real NPU isolation, then return to a normal complete operator

CPU models and public LAPACK calls can analyze saved device data; they do not execute or validate the NPU candidate. Keep separate evidence for model agreement, device-stage journals and complete native/API calls. Do not implement a CPU fallback to satisfy device testing.

A stage experiment should hold binary, batch geometry, selected-triangle bytes and launch conditions fixed while changing only the intended diagnostic control. An earlier experiment used batch size to select stages, confounding the diagnosis. The controlled reproduction narrowed a `507015 / 0x40` failure to the root-entry eligibility computation, before flags or XOR writeback. Replacing unused Soft64 array construction there with an equivalent bit-based qualification removed that reproduction; volatile loop-counter variants did not. The failing instruction's compiler-internal cause remained unproved.

Hundreds of successful stage calls had preceded that complete-call failure. Therefore run the normal entry with the original failing input after any isolated fix, including batches with inactive groups and batches without them. A stage's Q used as a journal is not an eigensolver output. Prefix kernels, encoded input selectors and journal-output projects must remain diagnostic-only and outside release source and submission archives.

## 5. Make a narrowly supported numerical repair

This section describes a phase-only repair. The later [residual update](eigh-residual-refinement.md) intentionally changes Q magnitudes; its comparator preserves original mathematics, W, small-path/skip bits and parent directions rather than requiring unchanged absolute Q everywhere.

The investigated normal candidate computed a binary64 Householder/Sturm **phase guide on the NPU**, using existing integer Soft64 arithmetic, and replaced only the root left-count ordering. It retained the FP32 value solver, deflation, non-root phase, small n<=25 path, W and Q magnitudes. This was not a complete FP64 eigensolver or a generic remedy for every sign mismatch. A native-double compile probe on the studied stack had failed; general dtype documentation did not establish that this target supported the desired arithmetic.

The repair required both positive controls and invariants: remove the frozen reference-phase differences, preserve W and absolute Q bits against the validated parent, preserve small-path signed Q, and introduce no new phase regressions on the chosen reference corpus. All mathematics, input and memory checks still apply. Matching a hypothesized reference does not replace external acceptance.

Workspace reuse needs an explicit ownership/lifetime proof. In this implementation, temporary HH matrices used two existing slots before the native solver. Six-n uint32 guide words occupied QNode1 rows 256…261 outside its at-most-256 logical rows; phase flags used row511. Those coordinates were proved only for that allocation and n<=512, not recommended offsets for another solver. One lane owned HH updates; distributed pole records had unique writers; two unconditional mixed barriers published D/E and poles. Inactive groups still joined barriers without reading input. Later native stages could reuse storage only after its guide lifetime ended. Recompute guide data for every wave and changed input.

One actual compile failure came from pointer-like macro declarators: `GM_ADDR input_, scratch_, storage_;` did not give all members the intended type/address-space form. Separate the declarations and inspect the first real compiler diagnostic before chasing derived-class errors. The corrected declarations preserved the numerical mechanism; they were not a performance change.

## 6. Freeze and test the oracle as carefully as the kernel

Preserve each adversarial family's oracle, thresholds, source hash and serialized input. Before replacing a checker, run it on the validated baseline and negative controls. A general double eigensolver is not automatically a sufficiently accurate oracle for a cancellation-sensitive small eigenvalue of a huge matrix.

The new runner accidentally replaced 20 frozen Decimal150 interval-oracle cases with ordinary float64 `eigvalsh`. A stored n4 input scaled by 2^80 had a small root near -0.007142857; the ordinary library reference returned about 3.29e9. Old and new NPU raw/W/Q were bit-identical. Restoring the original strict interval scorer resolved the harness failure without loosening any threshold or modifying the kernel. Corrupting the small eigenvalue, orthogonality and reconstruction independently still failed. Preserve the first runner's 15 device calls and failed report rather than rewriting them as passes.

Validate fixture feasibility after storage conversion. In a separate subnormal case, even the reference Q/W rounded to FP32 failed the same reconstruction criterion. Preserve that finding and its unresolved contract implications; do not silently drop a legal input class or claim it passed.

Treat local numerical-library warnings as data to investigate. On the case's Apple/Accelerate host, even an exact unit-matrix multiplication emitted floating-point warnings while returning the exact identity. The relevant 16 saved outputs were independently checked with `einsum(optimize=False)` under strict floating-point exceptions; finite Gram/reconstruction results matched the BLAS products exactly and met the unchanged criteria. This bounded control did not prove all NumPy warnings harmless, justify suppressing arbitrary warnings or require an SDK/dependency upgrade.

## 7. Bind every conclusion to source, payload, caller and input

Use the [build identity chain](build-identity.md): all source/config files, fresh/staged/direct/registry resources expected by this template, host tiling, actual API library, runner, environment and stored input/output hashes. A changed host API hash does not by itself imply changed device arithmetic; a matching source filename does not identify the loaded library.

Use separate processes when same-named registration/OPP state can mix candidates. Record carried-runtime provenance separately from an independently compiled build. In this case, two servers independently built the candidate; a third ran a verified carried package. Three-way bit-identical outputs for their six shared groups / eight matrices established agreement only on those inputs, not three independent builds or all legal inputs. Different framework versions also prevent calling that experiment a chip-only comparison. A common CANN version did not establish correctness on an externally reported but locally untested 910B4.

Choose regression cases from actual branches: n=1/2, n25/26 guide boundary, tree/tile boundaries, largest n, L/U, inherited/active columns, extreme scales and spectrum-gap boundaries. Include nonmultiple batches, more matrices than active groups, maximum per-dimension batch and multi-axis batch. At the same allocations and metadata, update input contents and check every wave, input bits and guard regions. Never relax assertions or repair outputs in the adapter to obtain agreement.

Report full device calls, matrix instances and column/check counts separately. The snapshot had 128 qualified complete calls / 472 matrices in five main suites plus 8 candidate calls / 512 matrices in supplemental batch checks. Eight old-baseline calls and 15 calls from the preserved faulty host-reference runner were separate categories. One sample for every n is not exhaustive coverage of spectra or state.

## 8. Keep sanitizer and release boundaries visible

Apply [real instrumentation and coverage checks](correctness-sanitizers.md#each-requested-tool-must-really-execute). The case's instrumented memcheck reported 795 GM-ownership warnings and zero ERROR entries; a race-tool run timed out. Valid mathematics, intact canaries and an address inside a known allocation did not settle ownership or races. Retain target start/finish, instrumented device ELF identity and actual output; normal packaging objects alone do not prove device instrumentation. Do not relabel a timed-out tool as passed or an unresolved warning as a false positive.

Freeze the normal, complete candidate and its evidence before a required external acceptance stage. Preserve both failure records and the parent rollback. Advance a delivery only when the project's actual acceptance gate is met; recheck the accepted source and concurrent delivery changes first. Keep numerical, diagnostic, external-evaluation and performance states separate. This engineering package does not provide account, submission, monitoring or server-power workflows.

## Evidence map

Paths below are relative to the original eigh case project; they are optional provenance, not dependencies of this skill. They contain historical states, so use their dated scope rather than treating an old “unqualified” plan or running JSON as a current verdict. Selected hashes identify the inspected snapshot only.

| Topic | Evidence |
| --- | --- |
| Contract, per-matrix norms, multi-axis batch and legal failing input | `docs/problem-contract-review.md` |
| Actual caller, 150-record comparator experiment and repeatable executor | `results/round12/experiments/caller-checker089-001/README.md` |
| n2 convention, unchanged larger paths and subnormal fixture limitation | `results/round12/experiments/two-phase091-001/README.md` |
| Leaf rounding, recursive phase and deflation/normalization | `results/round12/phase-progress091-099.md`, `phase-progress100-110.md`, `phase-progress111-115.md`, `phase-progress116-123.md` in the same directory |
| Controlled complete-call runtime failure and equivalent eligibility fix | `results/round12/phase-progress126-133.md` |
| Actual FP32 T versus original A, cross-device reproductions | `results/round12/phase-progress146-152.md`, `phase-progress153-159.md` in the same directory |
| Guide mechanism, workspace proof and macro declaration correction | `results/round12/experiments/phase-guide153-001/PLAN.md`, `phase-guide155-001/PLAN.md` under the same experiments directory |
| Frozen exact oracle, negative controls, supplemental batch checks and host-library control | `results/round12/phase-progress173-179.md`; `experiments/phase-guide155-001/failure-scale170-001/` and `experiments/full-batch178-001/local-math179-001.json` beneath round12 |
| Actual complete-output qualification, provenance and pending acceptance | `results/round12/experiments/phase-guide155-001/qualification-audit168-001.json`; `results/round12/phase-progress181-182.md` |
