# GC Collectors Troubleshooting Notes

This note is a collector-specific troubleshooting layer for Apache Ignite
incident analysis. It complements `ignite-troubleshooting-tree.yaml` and should
not be read as a universal tuning recipe.

The key rule: first identify the collector and the failure mode, then choose
collector-specific actions. G1, Shenandoah, and ZGC all react differently to
allocation pressure, live-set pressure, and latency targets.

## Sources

- Oracle HotSpot GC Tuning Guide, G1:
  https://docs.oracle.com/en/java/javase/21/gctuning/garbage-first-garbage-collector-tuning.html
- Oracle HotSpot GC Tuning Guide, ZGC:
  https://docs.oracle.com/en/java/javase/21/gctuning/z-garbage-collector.html
- OpenJDK Shenandoah wiki:
  https://wiki.openjdk.org/display/Shenandoah
- OpenJDK ZGC wiki:
  https://wiki.openjdk.org/pages/viewpage.action?pageId=35455041
- Oracle JFR troubleshooting guide:
  https://docs.oracle.com/en/java/javase/11/troubleshoot/troubleshoot-performance-issues-using-jfr.html

## First Pass

Collect these before changing collector-specific flags:

- Effective JVM flags: `jcmd <pid> VM.flags`, `jcmd <pid> VM.command_line`.
- GC logs with timestamps and phase detail.
- JFR for the incident window when available.
- Heap size, live-set trend, allocation rate, direct/off-heap usage, and OS
  memory pressure.
- Ignite workload context: put/load/query/tx/rebalance/checkpoint/WAL activity.
- Collector version: JDK major, vendor, and whether ZGC is generational.

Classify the problem before tuning:

- Long stop-the-world pauses.
- High allocation rate.
- Large live set or heap occupancy that never drops.
- Allocation stalls or back-to-back concurrent cycles.
- Full GC, degenerated GC, evacuation failure, or allocation failure.
- OS memory pressure, swap, or dirty-page/writeback pressure.
- Ignite persistence pressure: WAL fsync, checkpoint, page writes.

## Common Evidence

Useful cross-collector signals:

- `Pause Young`, `Pause Full`, `Full GC`, `Allocation Failure`,
  `Evacuation Failure`, `Concurrent Mark`, `Concurrent Relocate`,
  `Allocation Stall`, `Degenerated GC`.
- JFR `GarbageCollection`, `GCPhasePause*`, `AllocationRequiringGC`,
  `ObjectAllocation*`, `ThreadAllocationStatistics`, `CPULoad`,
  `ExecutionSample`, `ThreadPark`, `JavaMonitorEnter`, `SocketRead`,
  `FileWrite`, and safepoint events.
- Heap after GC and old/live set trend, not only max heap.
- Frequency of explicit `System.gc()` and whether `-XX:+DisableExplicitGC`
  is set.

Common actions that are not collector-specific:

- Reduce allocation pressure in the application path that dominates JFR or GC
  allocation samples.
- Reduce live data retained by caches, query results, queues, metrics,
  marshalling buffers, or transaction state.
- Make `-Xms` and `-Xmx` equal for latency-sensitive nodes if memory footprint
  allows it.
- Use `-XX:+AlwaysPreTouch` when startup cost is acceptable and page-fault
  hiccups matter.
- Check OS memory and swap before assuming the collector is the only cause.

## G1

### Implementation Model

G1 is a region-based collector with young collections, concurrent marking, and
mixed collections that reclaim selected old regions. It has a pause-time goal
and chooses collection work based on region cost estimates.

G1-specific words in evidence:

- Young GC, mixed GC, concurrent mark, remark, cleanup.
- Humongous objects or humongous regions.
- Evacuation failure, to-space exhausted, Full GC.
- Remembered set, update remembered set, scan remembered set.
- Termination time, worker imbalance, old region selection.

### G1-Specific Actions

If young or mixed pauses are too long:

- Inspect phase breakdown before changing flags. Check evacuation, remembered
  set update/scan, reference processing, and termination.
- Relax or validate `-XX:MaxGCPauseMillis`; making it too aggressive can reduce
  young size and increase GC frequency.
- Check whether `ParallelGCThreads` is too high on large CPU hosts. For Ignite
  nodes on high-core machines, too many GC workers can hurt termination and
  scheduling. Validate with GC phase data before lowering it.
- If remembered-set work dominates, inspect write-heavy paths, dirty cards, and
  cross-region pointer churn before touching `G1RSetUpdatingPauseTimePercent`.

If Full GC, evacuation failure, or to-space exhaustion appears:

- Increase heap headroom or reduce live set/allocation spikes.
- Start concurrent marking earlier after evidence, for example by validating
  `InitiatingHeapOccupancyPercent` or disabling adaptive IHOP only when GC logs
  show marking starts too late.
- Increase reserve cautiously with `G1ReservePercent` when evacuation failures
  occur, and raise heap accordingly because reserve reduces usable space.
- Look for Ignite spikes: rebalance, checkpoint, large SQL result materializing,
  binary marshalling bursts, and DataStreamer load.

If humongous allocations appear:

- Identify classes and allocation sites in JFR or heap histogram.
- Reduce large arrays/buffers, split payloads, or reuse buffers when safe.
- Consider `-XX:G1HeapRegionSize` only after confirming object sizes. G1 treats
  objects larger than half a region as humongous, so region size can change
  classification. This is a startup-time structural choice, not a generic fix.

If mixed collections are ineffective:

- Check old live percent and whether mixed GC selects useful old regions.
- Consider `G1MixedGCLiveThresholdPercent`, `G1HeapWastePercent`, or
  `G1MixedGCCountTarget` only after logs show old-region selection is the
  problem.
- If old occupancy is mostly truly live Ignite data, tuning mixed collection
  policy will not solve it; reduce retained data or add capacity.

### G1 Avoid List

- Do not tune many G1 flags at once. The ergonomics are interdependent.
- Do not treat every long G1 pause as a pause-target problem; it may be OS,
  safepoint, reference processing, humongous allocation, or Full GC.
- Do not hide live-set pressure by only increasing `MaxGCPauseMillis`.
- Do not use fixed young-gen sizing unless there is strong evidence that G1
  ergonomics are failing for this workload.

## Shenandoah

### Implementation Model

Shenandoah is a low-pause collector that performs most work concurrently,
including evacuation/compaction. Its key operational question is whether
concurrent GC keeps up with allocation pressure.

Shenandoah-specific words in evidence:

- Concurrent marking, evacuation, update references.
- Pacing delay.
- Degenerated GC.
- Full GC upgraded from degenerated GC.
- Cancelled cycle, allocation failure.
- Heuristics decisions.

### Shenandoah-Specific Actions

If normal pauses look low but end-to-end latency is high:

- Check pacing. Shenandoah pacing can delay allocating threads and may not look
  like stop-the-world pause time.
- Enable or inspect `-Xlog:gc+stats` and `-Xlog:gc+ergo` to see pacing,
  heuristics decisions, successful cycles, degenerated cycles, and Full GC.
- Correlate pacing with Ignite request latency, not only JVM pause metrics.

If Degenerated GC appears:

- Treat it as a signal that concurrent GC failed to keep up or started too late.
- Increase heap headroom if possible.
- Reduce allocation pressure from the dominant JFR allocation sites.
- Reduce live set so concurrent cycles finish faster.
- Tune heuristics to start cycles earlier only after logs show late starts.
  Candidate knobs depend on selected heuristics, for example
  `ShenandoahMinFreeThreshold`, `ShenandoahInitFreeThreshold`, and
  `ShenandoahAllocSpikeFactor`.

If Full GC appears:

- Check whether it was upgraded from Degenerated GC or caused by allocation
  failure.
- First fix headroom, live set, or allocation spikes. Full GC means the
  graceful degradation ladder was exhausted.
- Check explicit `System.gc()` and consider `-XX:+DisableExplicitGC` if a
  library triggers it.

If GC CPU steals too much from the application:

- Inspect `ConcGCThreads`. Too many concurrent GC threads can compete with
  Ignite worker pools; too few can fail to keep up.
- Do not switch to aggressive/compact heuristics for production latency without
  proving that continuous collection is acceptable for throughput.

If root scanning or final marks are long:

- Inspect thread count, JNI/VM roots, class unloading, and reference processing.
- Compare pause phases with JFR safepoint/thread data; not every long final mark
  is caused by heap size.

### Shenandoah Avoid List

- Do not judge Shenandoah only by stop-the-world pause logs; pacing can be the
  real request-latency cost.
- Do not disable pacing to make latency graphs prettier. It may convert hidden
  per-thread delay into Degenerated or Full GC.
- Do not use diagnostic/aggressive heuristics as a production fix without a
  controlled benchmark.
- Do not expect G1-style pause target tuning. Shenandoah is driven by
  concurrent-cycle timing, pacing, and heuristics.

## ZGC

### Implementation Model

ZGC is a low-latency collector that performs most work concurrently and is
primarily tuned by heap headroom. Modern JDKs include generational ZGC; always
record whether the deployment uses non-generational or generational ZGC.

ZGC-specific words in evidence:

- Allocation Stall.
- Concurrent Mark, Concurrent Relocate.
- Warmup or proactive cycles.
- Soft Max Capacity / SoftMaxHeapSize.
- Uncommit / commit activity.
- Relocation set.
- Generational ZGC young/old activity on JDKs that support it.

### ZGC-Specific Actions

If Allocation Stall appears:

- Treat it as the core ZGC failure mode: allocation outpaced concurrent
  reclamation.
- Increase `-Xmx` or reduce live set/allocation rate.
- Check `-XX:SoftMaxHeapSize`. A soft max that is too low can force ZGC to work
  harder and may allow growth only when needed to avoid stalls.
- Check whether the process has enough CPU for concurrent GC threads and
  application threads.

If GC runs back-to-back:

- Increase heap headroom or reduce allocation pressure.
- Inspect whether live set is close to `SoftMaxHeapSize` or `Xmx`.
- Use JFR allocation sites and GC logs to find bursts from Ignite rebalance,
  binary marshalling, query materialization, or WAL/checkpoint buffers.

If OS memory commit/uncommit causes latency:

- Check whether ZGC uncommit is active.
- Consider `-XX:-ZUncommit` or tune `ZUncommitDelay` only when commit/uncommit
  churn correlates with latency and the node can afford committed memory.
- Remember that setting `-Xms` equal to `-Xmx` prevents shrinking below `Xms`.

If using generational ZGC:

- Separate young-generation allocation churn from old-generation live-set
  pressure.
- Check promotion/tenuring-like behavior in available logs/JFR events for the
  JDK version.
- Do not copy non-generational ZGC conclusions blindly; generational ZGC changes
  the meaning of young allocation pressure.

### ZGC Avoid List

- Do not search for a G1-like pause target knob. ZGC tuning is mostly heap
  headroom, allocation rate, CPU for concurrent work, and memory commit policy.
- Do not set `SoftMaxHeapSize` too close to the live set without validating
  allocation stalls.
- Do not diagnose ZGC only from pause duration. Allocation stalls and concurrent
  cycle frequency are often more important.
- Do not ignore non-Java memory. Ignite off-heap, direct buffers, mmap, native
  agents, and OS page cache still compete with Java heap for RAM.

## Collector Choice For Ignite Incidents

Use this as a diagnostic framing, not as a migration recommendation:

- G1 is usually the baseline choice for throughput plus manageable pauses. It
  gives rich phase detail and mature ergonomics, but large live sets, humongous
  allocations, or evacuation failures need G1-specific handling.
- Shenandoah is useful when low pause time matters and pacing/degenerated cycles
  are acceptable signals to monitor. It needs analysis of hidden per-thread
  pacing latency.
- ZGC is useful for very low pause requirements and large heaps, but allocation
  stalls, heap headroom, `SoftMaxHeapSize`, and memory uncommit policy become
  the implementation-specific focus.

## Output Facts For The Troubleshooting Tree

Suggested facts an analyzer or agent can set:

- `signal.gc.long_pause`: long stop-the-world pauses in logs or JFR.
- `signal.gc.large_live_set`: after-GC heap remains high or live histogram is
  dominated by retained objects.
- `signal.gc.high_allocation_rate`: allocation rate is high for the selected
  collector and heap headroom.
- `signal.gc.slow_termination`: G1 worker termination is disproportionately
  long.
- `signal.jfr.gc_pause_impact`: JFR GC events show high total pause impact.
- `signal.jfr.cpu_hot_methods`: JFR samples concentrate in collector-affected
  application paths, such as marshalling, page memory, query/index work.
- `signal.jfr.thread_stalling_high`: Shenandoah pacing-like or ZGC allocation
  stall-like latency is visible as thread delay.
- `signal.ignite.region_pressure`: Ignite data region/off-heap pressure is
  close to limits and must be separated from Java heap pressure.

## Minimal Collector-Specific Cheat Sheet

| Collector | Main failure mode | First evidence | Collector-specific action |
| --- | --- | --- | --- |
| G1 | Long STW pause, Full GC, evacuation failure, humongous allocation | GC phase logs, JFR GC phases, heap histogram | Tune pause/live-set/humongous handling; consider IHOP, reserve, region size, worker count only after evidence |
| Shenandoah | Pacing, Degenerated GC, Full GC after allocation failure | `gc+stats`, `gc+ergo`, JFR latency, GC log | Increase headroom, reduce allocation/live set, tune heuristics/pacing carefully |
| ZGC | Allocation Stall, back-to-back concurrent cycles, commit/uncommit churn | GC log, JFR, heap headroom, SoftMaxHeapSize | Increase heap headroom, reduce allocation/live set, validate SoftMaxHeapSize and uncommit policy |
