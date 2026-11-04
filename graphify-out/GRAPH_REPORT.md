# Graph Report - APK_2_IPK_Converter  (2026-11-04)

## Corpus Check
- 24 files · ~12,994 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 3, .css 2)

## Summary
- 270 nodes · 623 edges · 14 communities (8 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `311b0132`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- recover.py
- test_converter.py
- parse_manifest
- gui.py
- test_viewer.py
- with
- ConverterTests
- verify_ipk
- apk2ipk
- steps
- check_viewer.js

## God Nodes (most connected - your core abstractions)
1. `convert()` - 33 edges
2. `ConverterTests` - 32 edges
3. `verify_ipk()` - 31 edges
4. `inspect_apk()` - 30 edges
5. `ConversionError` - 23 edges
6. `App` - 15 edges
7. `RecoveryTests` - 15 edges
8. `safe_name()` - 14 edges
9. `main()` - 12 edges
10. `discover_entries()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `check()` --calls--> `verify_ipk()`  [EXTRACTED]
  tools/check_official.py → apk2ipk/package.py
- `check()` --calls--> `convert()`  [EXTRACTED]
  tools/check_official.py → apk2ipk/convert.py
- `convert()` --calls--> `scan_web()`  [EXTRACTED]
  apk2ipk/convert.py → apk2ipk/analyze.py
- `inspect_apk()` --calls--> `APK`  [EXTRACTED]
  apk2ipk/analyze.py → apk2ipk/archive.py
- `inspect_apk()` --calls--> `ConversionError`  [EXTRACTED]
  apk2ipk/analyze.py → apk2ipk/archive.py

## Import Cycles
- None detected.

## Communities (14 total, 6 thin omitted)

### Community 0 - "recover.py"
Cohesion: 0.24
Nodes (5): bootstrap_html(), discover_entries(), html_dependency(), mount_ids(), script_candidate()

### Community 1 - "test_converter.py"
Cohesion: 0.10
Nodes (15): markdown(), write_report(), APK, ConversionError, read_web_directory(), safe_name(), main(), parser() (+7 more)

### Community 2 - "parse_manifest"
Cohesion: 0.19
Nodes (4): _binary(), metadata(), parse_manifest(), binary_manifest()

### Community 3 - "gui.py"
Cohesion: 0.08
Nodes (6): App, launch(), next_output(), smoke_test(), suggested_settings(), DefaultsTests

### Community 4 - "test_viewer.py"
Cohesion: 0.13
Nodes (5): scan_web(), icon_png(), content_kind(), create_content_viewer(), ContentViewerTests

### Community 5 - "with"
Cohesion: 0.08
Nodes (26): jobs, official-package, test, os, python, name, runs-on, steps (+18 more)

### Community 9 - "steps"
Cohesion: 0.06
Nodes (30): runs-on, steps, strategy, concurrency, cancel-in-progress, group, GH_TOKEN, jobs (+22 more)

### Community 13 - "check_viewer.js"
Cohesion: 0.11
Nodes (7): assert, context, document, Element, fs, ids, vm

## Knowledge Gaps
- **1 isolated node(s):** `apk2ipk`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 99 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `convert()` connect `test_converter.py` to `recover.py`, `gui.py`, `test_viewer.py`, `ConverterTests`, `verify_ipk`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **What connects `apk2ipk` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `test_converter.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10275689223057644 - nodes in this community are weakly interconnected._
- **Why does `inspect_apk()` connect `ConverterTests` to `recover.py`, `test_converter.py`, `parse_manifest`, `gui.py`, `test_viewer.py`, `verify_ipk`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Should `gui.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08048780487804878 - nodes in this community are weakly interconnected._
- **Why does `verify_ipk()` connect `verify_ipk` to `recover.py`, `test_converter.py`, `gui.py`, `test_viewer.py`, `ConverterTests`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Should `test_viewer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12648221343873517 - nodes in this community are weakly interconnected._