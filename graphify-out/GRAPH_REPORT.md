# Graph Report - APK_2_IPK_Converter  (2026-11-04)

## Corpus Check
- 17 files · ~7,788 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .css 1)

## Summary
- 184 nodes · 416 edges · 10 communities (6 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- package.py
- test_converter.py
- parse_manifest
- gui.py
- cli.py
- with
- ConverterTests
- apk2ipk
- steps

## God Nodes (most connected - your core abstractions)
1. `ConverterTests` - 34 edges
2. `convert()` - 25 edges
3. `inspect_apk()` - 24 edges
4. `ConversionError` - 21 edges
5. `verify_ipk()` - 20 edges
6. `main()` - 13 edges
7. `APK` - 12 edges
8. `App` - 12 edges
9. `parse_manifest()` - 12 edges
10. `safe_name()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `ConverterTests` --uses--> `APK`  [INFERRED]
  tests/test_converter.py → apk2ipk/archive.py
- `ConverterTests` --uses--> `ConversionError`  [INFERRED]
  tests/test_converter.py → apk2ipk/archive.py
- `check()` --calls--> `convert()`  [EXTRACTED]
  tools/check_official.py → apk2ipk/convert.py
- `check()` --calls--> `verify_ipk()`  [EXTRACTED]
  tools/check_official.py → apk2ipk/package.py
- `field()` --indirect_call--> `main()`  [INFERRED]
  apk2ipk/gui.py → apk2ipk/cli.py

## Import Cycles
- None detected.

## Communities (10 total, 4 thin omitted)

### Community 0 - "package.py"
Cohesion: 0.29
Nodes (3): icon_png(), _tar_files(), tar_gz()

### Community 1 - "test_converter.py"
Cohesion: 0.21
Nodes (9): inspect_apk(), scan_web(), APK, ConversionError, read_web_directory(), safe_name(), convert(), make_ipk() (+1 more)

### Community 2 - "parse_manifest"
Cohesion: 0.19
Nodes (4): _binary(), metadata(), parse_manifest(), binary_manifest()

### Community 3 - "gui.py"
Cohesion: 0.11
Nodes (7): markdown(), write_report(), main(), parser(), App, field(), launch()

### Community 5 - "with"
Cohesion: 0.08
Nodes (26): jobs, official-package, test, os, python, name, runs-on, steps (+18 more)

### Community 9 - "steps"
Cohesion: 0.08
Nodes (24): runs-on, steps, strategy, jobs, build, os, name, on (+16 more)

## Knowledge Gaps
- **1 isolated node(s):** `apk2ipk`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 63 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ConverterTests` connect `ConverterTests` to `package.py`, `test_converter.py`, `parse_manifest`, `gui.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ConverterTests` (e.g. with `APK` and `ConversionError`) actually correct?**
  _`ConverterTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `apk2ipk` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `gui.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Why does `inspect_apk()` connect `test_converter.py` to `parse_manifest`, `gui.py`, `cli.py`, `ConverterTests`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Should `with` be split into smaller, more focused modules?**
  _Cohesion score 0.08262108262108261 - nodes in this community are weakly interconnected._
- **Why does `convert()` connect `test_converter.py` to `package.py`, `gui.py`, `cli.py`, `ConverterTests`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._