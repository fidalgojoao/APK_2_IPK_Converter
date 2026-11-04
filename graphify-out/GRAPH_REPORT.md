# Graph Report - APK_2_IPK_Converter  (2026-11-04)

## Corpus Check
- 21 files · ~11,004 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 3, .css 2)

## Summary
- 237 nodes · 561 edges · 13 communities (8 shown, 5 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ca420e24`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- recover.py
- test_converter.py
- parse_manifest
- gui.py
- gui.py
- with
- ConverterTests
- verify_ipk
- apk2ipk
- steps

## God Nodes (most connected - your core abstractions)
1. `ConverterTests` - 34 edges
2. `inspect_apk()` - 30 edges
3. `convert()` - 29 edges
4. `verify_ipk()` - 28 edges
5. `ConversionError` - 24 edges
6. `App` - 15 edges
7. `RecoveryTests` - 15 edges
8. `safe_name()` - 14 edges
9. `main()` - 12 edges
10. `discover_entries()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `ConverterTests` --uses--> `APK`  [INFERRED]
  tests/test_converter.py → apk2ipk/archive.py
- `ConverterTests` --uses--> `ConversionError`  [INFERRED]
  tests/test_converter.py → apk2ipk/archive.py
- `check()` --calls--> `verify_ipk()`  [EXTRACTED]
  tools/check_official.py → apk2ipk/package.py
- `check()` --calls--> `convert()`  [EXTRACTED]
  tools/check_official.py → apk2ipk/convert.py
- `convert()` --calls--> `scan_web()`  [EXTRACTED]
  apk2ipk/convert.py → apk2ipk/analyze.py

## Import Cycles
- None detected.

## Communities (13 total, 5 thin omitted)

### Community 0 - "recover.py"
Cohesion: 0.20
Nodes (5): bootstrap_html(), discover_entries(), html_dependency(), mount_ids(), script_candidate()

### Community 1 - "test_converter.py"
Cohesion: 0.11
Nodes (12): APK, ConversionError, read_web_directory(), safe_name(), convert(), icon_png(), make_ipk(), _tar_files() (+4 more)

### Community 2 - "parse_manifest"
Cohesion: 0.19
Nodes (4): _binary(), metadata(), parse_manifest(), binary_manifest()

### Community 3 - "gui.py"
Cohesion: 0.12
Nodes (4): App, next_output(), suggested_settings(), DefaultsTests

### Community 4 - "gui.py"
Cohesion: 0.13
Nodes (6): markdown(), write_report(), main(), parser(), launch(), smoke_test()

### Community 5 - "with"
Cohesion: 0.08
Nodes (26): jobs, official-package, test, os, python, name, runs-on, steps (+18 more)

### Community 6 - "ConverterTests"
Cohesion: 0.17
Nodes (3): inspect_apk(), scan_web(), ConverterTests

### Community 9 - "steps"
Cohesion: 0.06
Nodes (30): runs-on, steps, strategy, concurrency, cancel-in-progress, group, GH_TOKEN, jobs (+22 more)

## Knowledge Gaps
- **1 isolated node(s):** `apk2ipk`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 83 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `inspect_apk()` connect `ConverterTests` to `recover.py`, `test_converter.py`, `parse_manifest`, `gui.py`, `gui.py`, `verify_ipk`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ConverterTests` (e.g. with `APK` and `ConversionError`) actually correct?**
  _`ConverterTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `apk2ipk` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `test_converter.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1125886524822695 - nodes in this community are weakly interconnected._
- **Why does `convert()` connect `test_converter.py` to `recover.py`, `gui.py`, `gui.py`, `ConverterTests`, `verify_ipk`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Should `gui.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1168091168091168 - nodes in this community are weakly interconnected._
- **Why does `verify_ipk()` connect `verify_ipk` to `recover.py`, `test_converter.py`, `gui.py`, `ConverterTests`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._