# Graph Report - APK_2_IPK_Converter  (2026-11-04)

## Corpus Check
- 18 files · ~8,885 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .css 1)

## Summary
- 206 nodes · 465 edges · 10 communities (7 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dd3d3d83`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- check_official.py
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
4. `verify_ipk()` - 22 edges
5. `ConversionError` - 21 edges
6. `App` - 14 edges
7. `APK` - 12 edges
8. `parse_manifest()` - 12 edges
9. `safe_name()` - 12 edges
10. `main()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `ConverterTests` --uses--> `APK`  [INFERRED]
  tests/test_converter.py → apk2ipk/archive.py
- `ConverterTests` --uses--> `ConversionError`  [INFERRED]
  tests/test_converter.py → apk2ipk/archive.py
- `check()` --calls--> `convert()`  [EXTRACTED]
  tools/check_official.py → apk2ipk/convert.py
- `check()` --calls--> `verify_ipk()`  [EXTRACTED]
  tools/check_official.py → apk2ipk/package.py
- `main()` --calls--> `launch()`  [EXTRACTED]
  apk2ipk/cli.py → apk2ipk/gui.py

## Import Cycles
- None detected.

## Communities (10 total, 3 thin omitted)

### Community 1 - "test_converter.py"
Cohesion: 0.14
Nodes (11): scan_web(), APK, ConversionError, read_web_directory(), safe_name(), convert(), icon_png(), make_ipk() (+3 more)

### Community 2 - "parse_manifest"
Cohesion: 0.19
Nodes (4): _binary(), metadata(), parse_manifest(), binary_manifest()

### Community 3 - "gui.py"
Cohesion: 0.09
Nodes (6): App, launch(), next_output(), smoke_test(), suggested_settings(), DefaultsTests

### Community 4 - "cli.py"
Cohesion: 0.19
Nodes (5): markdown(), write_report(), main(), parser(), create()

### Community 5 - "with"
Cohesion: 0.08
Nodes (26): jobs, official-package, test, os, python, name, runs-on, steps (+18 more)

### Community 6 - "ConverterTests"
Cohesion: 0.17
Nodes (3): inspect_apk(), verify_ipk(), ConverterTests

### Community 9 - "steps"
Cohesion: 0.06
Nodes (30): runs-on, steps, strategy, concurrency, cancel-in-progress, group, GH_TOKEN, jobs (+22 more)

## Knowledge Gaps
- **1 isolated node(s):** `apk2ipk`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 73 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `inspect_apk()` connect `ConverterTests` to `test_converter.py`, `parse_manifest`, `gui.py`, `cli.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ConverterTests` (e.g. with `APK` and `ConversionError`) actually correct?**
  _`ConverterTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `apk2ipk` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `test_converter.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13658536585365855 - nodes in this community are weakly interconnected._
- **Why does `ConverterTests` connect `ConverterTests` to `test_converter.py`, `parse_manifest`, `cli.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Should `gui.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08636977058029689 - nodes in this community are weakly interconnected._
- **Why does `verify_ipk()` connect `ConverterTests` to `check_official.py`, `test_converter.py`, `gui.py`, `cli.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._