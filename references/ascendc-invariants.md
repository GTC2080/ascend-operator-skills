# Ascend C: semantics, memory, tiling and synchronization

## Exact semantics are an implementation constraint

An algebraically equal expression can be observably different in finite precision. As a worked example, consider a geometry predicate whose declared contract is:

```text
y1 = float32(quantized_input_box_y1)
y2 = float32(quantized_input_box_y2)
cy = float32(quantized_input_anchor_y)
s  = round_float32(y2 - y1)
m  = round_float32(s * ratio_float32)
a  = round_float32(m + y1)
b  = round_float32(a + threshold_float32_or_zero)
out = float32(cy > b)
```

Separate FP32 operations, strict `>` and storage quantization are part of this contract. FMA, reassociation, epsilon comparison or replacing `ratio==1` with `y2` can change results. Keep exactly these constraints only for operators with the corresponding contract.

A complete FP32 shortcut counterexample is `y1=-2^25`, `y2=1`, `ratio=1`, `threshold=0`, `cy=1`. Under round-to-nearest-even, `y2-y1=2^25+1` rounds to `2^25`; adding y1 gives zero. The specified predicate returns one, whereas substituting y2 yields `1>1`, which returns zero. Ordinary random values can miss this boundary.

To evaluate an Axpy or other replacement whose contraction is unclear, first capture its actual FP32 intermediate on adversarial operands. Binary outputs can hide different intermediates away from the threshold, and HALF output can hide a one-ULP FP32 difference. Compare fused and separately rounded controls, then rerun the normal complete predicate. A diagnostic intermediate-output kernel must remain outside release artifacts; agreement on a finite corpus is not a full-domain equivalence proof.

Inspect generated operations/flags and use adversarial numerical cases; source expressions and use of `volatile` alone are not a general proof that a compiler preserved the required arithmetic. For matrix routes, accumulator mode and input rounding (including HF32 where applicable) are separate constraints.

## Host and device share one metadata protocol

Check registration, InferShape/InferDataType, legal dtype combinations, optional descriptors, actual allocation bytes and instantiated kernels. Do not repair a metadata mismatch by reinterpreting an output buffer with the wrong dtype.

A host ABI can transport a Float attribute in a C `double` parameter while the operator computes with quantized FP32. Follow the generated signature and explicit conversions; transport width does not redefine arithmetic semantics. For packed float fields, distinguish reinterpreting stored bits from numerically converting an integer field.

Packed tiling protocols need:

- A declared layout, units, bit widths, flag positions and field ranges.
- Consistent Host encode, Init decode, entry-dispatch decode and diagnostic geometry expectations.
- CPU round-trip checks over valid boundary values; rejection of unrepresentable values.
- Verified struct size/alignment and address-space access on the device compiler.
- Actual BlockDim, per-core intervals and platform caps in the run record.

Handle unresolved, negative, zero or unsupported dimensions according to the real contract before unsigned conversion. Use checked sufficiently wide arithmetic for ceil-div, shape products, byte counts, offsets and packed fields. Check overflow and representability before narrowing. A bounded implementation's uint32 arithmetic must not be copied into an unrestricted operator without a range proof.

SDK tiling macros can implement different dynamic-read and static-shape constant semantics. Before replacing them with direct field reads, prove equivalence for the generated template, struct layout and address space. Ordinary host C++ struct copying does not establish legal `__gm__`-to-local aggregate copying. A compiler rejection should not be hidden by erasing address-space qualifiers.

Host tiling may depend on legal metadata and attributes. Changing device tensor contents must be read by the next invocation; do not move them to host cached tiling or a pointer-keyed value cache. Validate workspace-zero behavior against the API rather than assuming a zero-byte allocation returns a usable pointer.

## Prove ownership before tuning core count

For ordinary pointwise stores, write every core/tile's half-open output interval `[start,end)`: the union must cover the logical domain and writable intervals must not overlap. For reductions, scatter or another intentional multiwriter algorithm, define a valid atomic/reduction protocol, partial-output ownership, initialization, synchronization and accumulation-order semantics instead. Distinguish requested core count from actual core count after alignment or topology rules.

Do not shift a writable tail backward without proving legal reads and unique plain-store ownership. With `B=257,T=128`, `min(tile_id*T,B-T)` creates unprotected overlapping `[128,256)` and `[129,257)` writers. Identical outputs do not make that race correct. Unique tile bases with legal tail lengths/padding are a simple solution; backward-aligned reads with correctly owned/masked stores can also be valid.

For a mapping such as `tile_id=u+t*units`, prove each ordinary output tile has one owner and no invalid access. Explicitly guarded inactive cores may be correct; evaluate their launch cost separately. A CPU enumeration is an early design check, not device race/sync validation. After changing a mixed entry to pure vector, reprove core-ID/subblock mapping and launch semantics.

## UB: logical length, physical access and capacity differ

Maintain this table for each relevant dtype/tile/stage:

| Region | Offset in bytes | Element dtype/count | Half-open physical bytes | Writer → reader | Defined range |
| --- | --- | --- | --- | --- | --- |
| Input staging | derived | input dtype | derived | MTE2 → V | DMA plus required pad |
| Extracted fields | derived | compute dtype | derived | Gather/Cast → arithmetic | all subsequently read lanes |
| Compare predicate | derived | packed bits/storage type | derived | Compare → Select | complete downstream read width |
| Output staging | derived | output dtype | derived | V/S → MTE3 | complete transfer read width |
| SDK scratch | version contract | version-specific | reserved interval | helper internal | contract-specific |

Check alignment, aliasing, maximum live end address, per-stage multiplicity and platform capacity. Update the host guard when inserting alignment gaps or new regions. A sum of logical buffer sizes can underestimate the highest occupied address. Different `TPosition` labels do not by themselves prove disjoint physical storage: use actual byte intervals and allocator contracts.

Important counterexamples:

- Initializing only `n` valid scalar results does not define all lanes read by a padded vector operation.
- FP16 staging and FP32 fields are different regions. Clearing the latter does not define staging padding before Cast.
- If an operation physically reads a 32-byte unit, four logical FP32 values still require all eight staging lanes to be defined; write back only legal logical output bytes.
- A conversion layout may expand a 32-byte HALF row into a 64-byte FLOAT row. Recompute output capacity and stride from its actual helper, not the input width.
- Public SDK scratch reservations remain the supported contract even if one installed helper internally requests less. Inspect the installed overload and the version-matched [Select contract](sources.md#api-and-diagnostic-references).

Query temporary requirements and UB capacity for the actual target and overload. Never rely on spare memory elsewhere in physical UB to justify a read outside the buffer's allocated and defined region.

## Capacity stairs and bank-layout hypotheses

For each workload record valid rows `n`, allocated/padded rows `P`, field stride and actual elements processed by Cast/clear/Compare. For three fields per row, processing all `3P` values can cost much more than `3n`. An intermediate capacity or reduced physical extent is a performance hypothesis. Recompute every region and tail read before changing that extent, then measure the correct full path.

The [official A2/A3 bank-conflict example](sources.md#api-and-diagnostic-references) uses a model such as `BG=(address/32)%16`: FP32 field strides of 1024/2048 bytes map to the same group under that model. Derive addresses on the actual target before treating a changed stride as a remedy. Bank grouping suggests an experiment; it does not identify the dominant bottleneck or establish a speedup. If three field arrays change spacing from `P` to `R=P+64` floats, old contiguous `3P` initialization no longer covers the new layout. Update allocation, offsets, highest address, conversion mapping and every readable tail.

## Audit DMA from address formulas

For every copy, derive GM and UB first/last addresses and the increment for each row/repeat. Write the unit beside each parameter: element, byte, block, 32-byte unit, or repeat. Inspect the installed helper's parameter order. Unary and Binary repeat parameter fields are not interchangeable.

Review AoS/SoA extraction, block count, valid byte count, source/destination stride, padding and expansion/contraction. The meaning of a DSL's singleton dimension is not proof of a contiguous copy. A shape-correct output can still read every eighth float if a helper interprets the stride in 32-byte units.

No core may DMA beyond its legal GM input/output interval, even if another allocation often follows it. For offset/canary testing, preserve required API alignment and test valid offsets deliberately; do not redefine the public alignment contract.

An aligned ordinary-copy specialization needs two independent proofs: every actual source/destination start address satisfies the selected API's alignment, and every transferred byte count satisfies its granularity. Derive base plus core/tile/row offsets for each dtype; a divisible n alone is insufficient. Use the supported padded/tail route otherwise. For a tiny metadata payload, DMA setup and MTE-to-scalar publication can cost more than direct supported field loads; fewer source loads do not establish a win.

## Vector masks and Compare/Select

For each API call, establish Normal/Counter mode, mask payload width, `isSetMask` behavior, repeat count, repeat stride and tail semantics. A placeholder mask argument does not identify the mode: the external vector state and implementation do.

Read the actual count overload. If its implementation computes only full repeats as `count*sizeof(T)/256`, FP32 lengths below 64 give zero repeats unless another path handles the tail. Inspect both paths; the word count is not a guarantee of arbitrary tail support.

As a worked width calculation, suppose the verified target processes 256 bytes per vector repeat. FP32 comparison pads n to `R=64*ceil(n/64)`, while a HALF-output Select can need `S=128*ceil(n/128)`. Its predicate and HALF-ones operands must define all S lanes/bits, including the zero predicate tail `[R,S)`. Reusing an FP32 R-element buffer for HALF ones needs the byte proof `2*S <= 4*R`, plus alignment, ownership and lifetime; it does not follow from equal logical n. The actual overload's scratch contract still applies.

Packed predicate writes and Select reads can have different widths. Writing all valid comparison bits does not initialize the full storage read by Select. Preserve complete mask initialization when required, including unused high bits/bytes. Use mixed 0/1 cases and sanitizer to expose hidden reads.

Do not assume that changing count syntax changes Counter execution: ordinary count arithmetic may internally use Counter mode. Inspect the selected overload and external vector state. An explicit Normal repeat/tail path can isolate a mode-dependent warning, but still requires correct scratch allocation, initialization and lifetime.

`isSetMask=false` is only valid where the installed API supports it. CANN9 Select marked that parameter reserved; optimization rules from other arithmetic APIs must not be transferred mechanically. Restore state at genuine boundaries and kernel exit as required; do not rely on another dtype branch's incidental Cast to restore it.

Check whether the installed release supports the chosen GatherMask overload and whether it is deprecated. Do not generate a new implementation from an old signature without that check. A tile-gather byte-index interface is also not a synonym for GatherMask.

## Synchronization follows producers and consumers

Construct a dependency graph, including helper internals:

| Producer | Consumer | Typical reason |
| --- | --- | --- |
| MTE2 input load | V Gather/Cast | avoid reading unfinished input |
| V initialization | MTE2 write to overlapping bytes | avoid conflicting writes |
| Gather/Cast or prior V operation | raw vector arithmetic | protect entry RAW dependency |
| V output/convert | MTE3 | avoid premature writeback |
| Scalar UB output | MTE3 | protect scalar-produced staging |
| MTE3 | buffer reuse or return | complete the last writeback |

Choose the actual event/barrier for the installed architecture and API, not from this illustrative table alone. Record event-ID ownership, stage reuse and allocator-reserved state. A helper can enforce dependencies that a raw C replacement does not.

Do not assume source order on the same vector pipe proves result availability: preserve the target-required V-to-V dependency between dependent instructions. Conversely, `MTE2_V` makes a transfer available to a vector consumer, not automatically to a scalar `GetValue`; HALF Cast-to-scalar use also needs the appropriate V-to-S boundary. Inspect generated code and the installed synchronization contract for each real consumer.

Reserve caller event IDs together with IDs used inside generated copy/padding helpers and allocators. Verify set/wait counts and ownership for zero, one and multiple loop iterations; a balanced busy path can leave an inactive core or empty loop waiting forever. Replacing a broad barrier with a precise one is valid only after covering every dependency it used to protect.

When replacing a wrapper with raw intrinsics, protect the caller-to-first-operation Cast/Gather RAW boundary as well as dependencies inside the new arithmetic sequence. Internal barriers cannot repair a missing entry dependency. If strided DMA diagnostics report a redundant wait, first prove whether initialization and DMA writes overlap; delete an event only after revising that dependency graph and revalidating. Last-store completion remains required.

Never trade a missing dependency for a smaller device binary. If corruption persists after a completion barrier, continue isolating address, lifetime, physical width and producer/consumer order. Calling it a cache bug without evidence does not identify a fix.
## Specialize tiny operators by proven metadata regimes

For low-arithmetic-intensity vector work, measure fixed setup, metadata decoding, transfer descriptors, Gather/Cast, masks and final drain separately from useful arithmetic. Duplicating a larger pipeline may add work when each core handles only one tile. Reducing source API calls or enabling a vectorized threshold broadcast does not by itself reduce total duration.

A useful candidate can make input/output handling compile-time fixed for one legal dtype combination while retaining a validated dynamic route for the others. Guard dispatch using complete dtype, presence and shape metadata. Do not infer threshold/output dtype from coordinates, specialize on actual tensor values or reuse stale pointer-keyed values.

After proving each path, sweep a bounded set of rows per core, tile sizes and active-core counts. Smaller workloads can benefit from fewer rows per core, while the next smaller grain can regress; neither core count nor row grain has a linear latency rule. Compare actual geometry and preserve independent input/oracle checks for each arm.

Combine only confirmed scoped mechanisms. A dtype-specific I/O win and a small-shape grain win need a new complete regression and paired measurement together. Preserve exact bits on intentionally untouched paths, true same-address updates, required scratch/mask state and final-store completion. An unchanged generated device program is not a new kernel optimization, and a locally measured gain does not establish the same gain through a different caller or device.
