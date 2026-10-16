# Ascend C: semantics, memory, tiling and synchronization

## Exact semantics are an implementation constraint

An algebraically equal expression can be observably different in finite precision. In the geometry case, for each row:

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

Inspect generated operations/flags and use adversarial numerical cases; source expressions and use of `volatile` alone are not a general proof that a compiler preserved the required arithmetic. For matrix routes, accumulator mode and input rounding (including HF32 where applicable) are separate constraints.

## Host and device share one metadata protocol

Check registration, InferShape/InferDataType, legal dtype combinations, optional descriptors, actual allocation bytes and instantiated kernels. Do not repair a metadata mismatch by reinterpreting an output buffer with the wrong dtype.

Packed tiling protocols need:

- A declared layout, units, bit widths, flag positions and field ranges.
- Consistent Host encode, Init decode, entry-dispatch decode and diagnostic geometry expectations.
- CPU round-trip checks over valid boundary values; rejection of unrepresentable values.
- Verified struct size/alignment and address-space access on the device compiler.
- Actual BlockDim, per-core intervals and platform caps in the run record.

Handle unresolved, negative, zero or unsupported dimensions according to the real contract before unsigned conversion. Use checked sufficiently wide arithmetic for ceil-div, shape products, byte counts, offsets and packed fields. Check overflow and representability before narrowing. The small bounded geometry case does not justify copying its uint32 arithmetic into an unrestricted operator.

The case's dynamic two-field 8-byte tiling read was tested only in its dynamic template. SDK macros can also implement static-shape constant semantics; bypassing them is not generally equivalent. Ordinary host C++ struct copying does not establish legal `__gm__`-to-local aggregate copying. A compiler rejection should not be hidden by erasing address-space qualifiers.

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

Check alignment, aliasing, maximum live end address, per-stage multiplicity and platform capacity. Update the host guard when inserting alignment gaps or new regions. A sum of logical buffer sizes can underestimate the highest occupied address.

Important counterexamples:

- Initializing only `n` valid scalar results does not define all lanes read by a padded vector operation.
- FP16 staging and FP32 fields are different memory regions. Clearing the latter does not define unread staging padding before Cast.
- Four logical floats may still require a fully defined eight-float/32-byte staging unit before the relevant transfer. Initialize the physical read width; write only legal logical output bytes.
- In one HALF→FLOAT strided layout, a 32-byte source row becomes a 64-byte output row. Capacity and stride must be recomputed, not copied from the input.
- Public SDK scratch reservations remain the supported contract even if one installed helper internally uses less. In the studied CANN9/C220 Select path, a small internal request did not supersede the documented 8KiB reservation.

Temporary addresses and UB capacities in the casebook are observations for that release; query a new target. Never rely on spare memory elsewhere in physical UB to justify a read outside the buffer's defined region.

## Capacity stairs and bank-layout hypotheses

For each workload record valid rows `n`, allocated/padded rows `P`, field stride and the actual number of elements processed by Cast/clear/Compare. In the early case, capacity64/256/512 meant FP16 B65 converted768 fields for195 useful values; B257 converted1536 for771. An intermediate capacity or effective padded extent was a reasonable hypothesis, not an established speedup. Recompute every region and tail read when changing that extent.

The early bank-conflict hypothesis used the official A2/A3 example model `BG=(address/32)%16`: FP32 field strides1024/2048B map to the same group. A proposed256B stride offset would change the grouping. This was a layout inference, not proof of the operator's dominant bottleneck or a measured benefit. Query the actual target and validate independently. If field spacing becomes `R=P+64` floats, old contiguous `3P` initialization does not cover the new `3R` layout; update allocation, offsets, maximum address and every readable tail. The original FP16 continuous Cast also depends on the old layout and cannot inherit this change mechanically.

## Audit DMA from address formulas

For every copy, derive GM and UB first/last addresses and the increment for each row/repeat. Write the unit beside each parameter: element, byte, block, 32-byte unit, or repeat. Inspect the installed helper's parameter order. Unary and Binary repeat parameter fields are not interchangeable.

Review AoS/SoA extraction, block count, valid byte count, source/destination stride, padding and expansion/contraction. The meaning of a DSL's singleton dimension is not proof of a contiguous copy. A shape-correct output can still read every eighth float if a helper interprets the stride in 32-byte units.

No core may DMA beyond its legal GM input/output interval, even if another allocation often follows it. For offset/canary testing, preserve required API alignment and test valid offsets deliberately; do not redefine the public alignment contract.

## Vector masks and Compare/Select

For each API call, establish Normal/Counter mode, mask payload width, `isSetMask` behavior, repeat count, repeat stride and tail semantics. A placeholder mask argument does not identify the mode: the external vector state and implementation do.

Read the actual count overload. In the studied CANN9/C220 packed Compare implementation, `count*sizeof(T)/256` determined full repeats; FP32 lengths below64 yielded zero repeats on that path. This is a counterexample to “count always handles a tail,” not a rule about every count API.

Packed predicate writes and Select reads can have different widths. Writing all valid comparison bits does not initialize the full storage read by Select. Preserve complete mask initialization when required, including unused high bits/bytes. Use mixed 0/1 cases and sanitizer to expose hidden reads.

Do not assume that changing count syntax changes Counter execution: ordinary count arithmetic may internally use Counter mode. In this case an explicit Normal repeat/tail comparison was needed to isolate the diagnostic behavior. Conversely, Normal alone did not resolve a later HALF scalar Select scratch read.

`isSetMask=false` is only valid where the installed API supports it. CANN9 Select marked that parameter reserved; optimization rules from other arithmetic APIs must not be transferred mechanically. Restore state at genuine boundaries and kernel exit as required; do not rely on another dtype branch's incidental Cast to restore it.

The no-retained-count GatherMask overload used in the historical case was deprecated and tested only on CANN9.0. Do not generate code for a different release from that old signature. A tile-gather byte-index interface is also not a synonym for GatherMask.

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

The raw C arithmetic experiment failed 38 FP16 cases until a barrier covered the Cast/Gather→first raw operation boundary. Internal four-step barriers were insufficient. A strided DMA experiment produced redundant-wait diagnostics; removing a wait became justified only after initialization and DMA writes were made nonoverlapping. Last-store completion was still required.

Never trade a missing dependency for a smaller device binary. Do not name unexplained output corruption a cache bug: the scalar GM experiment remained incorrect after an additional completion barrier, with its root cause unresolved.
