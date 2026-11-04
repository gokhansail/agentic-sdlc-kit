# Evidence

What is this file? The measured numbers for this kit, how they were counted, how far they can be trusted, and how to rerun them. The numbers are descriptive. They do not show that the process caused any change. The method itself is in `PLAYBOOK.md`; decisions are in `DECISIONS.md` (DEC-xxx).

## What this is

Nine metrics were counted by script from the record files of three sources. The script is in `tools/metrics/`. Every number in the result tables comes from a JSON file in `evidence/`. No number was typed by hand into the tables.

The tables are the only place for metric results. Outside the tables this file holds method dates, thresholds and the numbers in the limits section, each with its source named.

## Sources and periods

There are two periods. Version 1 (v1) of the process is the work before 2026-10-25. Version 2 (v2) of the process is the work from 2026-10-25. A record belongs to a period by the date in its entry or heading. A heading without a date takes the period of its two dated neighbours when both agree. Otherwise it is counted as undated.

Three sources:

- Project A, a game project. v1 commits run from 2026-10-10 to 2026-10-24: 15 days, 36 commits. v2 commits run from 2026-10-25 to 2026-11-03: 10 days, 33 commits.
- Project B, a game project. v1 commits run from 2025-11-02 to 2026-10-17: 350 days, 103 commits. Its changelog has dated headings only from 2026-10-06 to 2026-10-18. It has no v2 commits.
- This repository (the kit). v2 only: 2026-10-29 to 2026-11-03, 6 days, 20 commits.

The day and commit counts come from the commit dates in the snapshots, computed on 2026-11-04. The snapshot date is 2026-11-03 for all three sources. For Project A it ends the v2 series, before the kit is used on that project in phase 3 (DEC-024).

Project A and Project B appear only under these labels (DEC-006). Their names and record text are not in this repository.

## Metrics and counting rules

Each metric is counted per source and per period. A metric with no record in a source shows "no data", never 0. A cell with fewer than 5 items shows the count and no rate (DEC-025).

- M1, reverted versions: version headings that mark a revert, over all version headings. Reverted items inside a version are counted separately (DEC-028).
- M2, versions marked to be tested: version headings with the to-be-tested marker, over all version headings. Headings marked as no behaviour change are counted apart.
- M3, test attributes: the count of test attributes in source files at the last commit of each ISO week. The cell shows the count of the last week in the period.
- M5, review rounds per task: the share of tasks with 0, 1, 2 and 3 or more review rounds, from the per-task metric lines in the work log.
- M6, questions back and out-of-scope files: the share of tasks with at least one question back, and the share with at least one file outside the contract. Each share is over the tasks that carry that field.
- M8, audit findings: findings per report by severity, their latest status in a re-verify report, and the days until the first closed status.
- M9, decisions with an outcome: decision entries whose outcome field is filled, over all entries.
- M12, commits and versions per week: commits per ISO week by author date, and versions per ISO week by changelog heading date.
- M13, tasks by size tag: tasks by the size tags E, M and H. The share of hard tasks tests the 30% rule in Appendix F of `PLAYBOOK.md`. A task is placed in a period by its done date.

## Results

<!-- metrics:begin -->
M1: Reverted versions

| Source | v1 | v2 |
|---|---|---|
| project-a | 1 of 62 (2%); item reverts 1 | 0 of 17 (0%); item reverts 0 |
| project-b | no data | no data |
| kit | no data | no data |

M2: Versions marked to be tested

| Source | v1 | v2 |
|---|---|---|
| project-a | 39 of 62 (63%); no change 0 | 11 of 17 (65%); no change 6 |
| project-b | no data | no data |
| kit | no data | no data |

M3: Test attributes at the last commit of the last week

| Source | v1 | v2 |
|---|---|---|
| project-a | 0 in 2026-W42; 2 weeks | 120 in 2026-W45; 3 weeks |
| project-b | 0 in 2026-W42; 4 weeks | no items |
| kit | no data | no data |

M5: Review rounds per task

| Source | v1 | v2 |
|---|---|---|
| project-a | no items | 0: 2 (11%); 1: 11 (61%); 2: 4 (22%); 3+: 1 (6%); n 18 |
| project-b | no data | no data |
| kit | no items | 0: 7 (44%); 1: 4 (25%); 2: 5 (31%); 3+: 0 (0%); n 16 |

M6: Tasks with questions back and with out-of-scope files

| Source | v1 | v2 |
|---|---|---|
| project-a | no items | questions back 0 of 17 (0%); out of scope 2 of 17 (12%) |
| project-b | no data | no data |
| kit | no items | questions back 6 of 16 (38%); out of scope 0 of 16 (0%) |

M8: Audit findings

| Source | v1 | v2 |
|---|---|---|
| project-a | 30 findings; severity critical 3, high 8, medium 10, low 6, unrated 3; latest closed 0, partial 0, open 0, deferred 0, none 30; days to closed 0 0, 1-3 0, 4-7 0, 8+ 0 | 12 findings; severity critical 0, high 2, medium 6, low 3, unrated 1; latest closed 0, partial 0, open 0, deferred 0, none 12; days to closed 0 0, 1-3 0, 4-7 0, 8+ 0 |
| project-b | 25 findings; severity critical 0, high 5, medium 9, low 8, unrated 3; latest closed 0, partial 0, open 0, deferred 0, none 25; days to closed 0 0, 1-3 0, 4-7 0, 8+ 0 | no items |
| kit | no items | 15 findings; severity critical 0, high 1, medium 4, low 9, unrated 1; latest closed 14, partial 0, open 0, deferred 0, none 1; days to closed 0 14, 1-3 0, 4-7 0, 8+ 0 |

M9: Decisions with an outcome filled

| Source | v1 | v2 |
|---|---|---|
| project-a | 14 of 34 (41%) | 2 of 9 (22%) |
| project-b | no data | no data |
| kit | no items | 1 of 29 (3%) |

M12: Commits and versions per ISO week

| Source | v1 | v2 |
|---|---|---|
| project-a | commits 36 (12.00 per week); versions 61 (20.33 per week); 3 weeks | commits 33 (11.00 per week); versions 17 (5.67 per week); 3 weeks |
| project-b | commits 103 (2.02 per week); versions 35 (0.69 per week); 51 weeks | no items |
| kit | no items | commits 20 (10.00 per week); 2 weeks |

M13: Tasks by size tag

| Source | v1 | v2 | undated |
|---|---|---|---|
| project-a | no items | no items | hard 1 of 16 (6%); E 10, M 5, H 1; done 15 |
| project-b | no data | no data | no data |
| kit | no items | hard 2 of 4; E 1, M 1, H 2; done 4 | hard 1 of 11 (9%); E 3, M 7, H 1; done 9 |
<!-- metrics:end -->

## How to read the results

The kit has no v1 data, so it is a third series and not a before/after pair. The comparison that exists is Project A v1 against Project A v2.

- M1: a lower share means fewer versions were taken back. Reverts are rare in the Project A series, so no direction can be read.
- M2: a lower share means fewer versions are left waiting for a test. The v2 share is about the same as the v1 share. M2 did not improve.
- M3: a higher count means more test attributes. In Project A the count rose from v1 to v2. It says nothing about whether the tests pass.
- M5: more tasks in the 0 and 1 columns mean fewer review rounds. The meaning of the number differs between entries (limit 11). M5 has v2 data only, so there is no before/after comparison.
- M6: lower shares mean fewer questions back to the lead and fewer files outside the contract. M6 has v2 data only, so there is no before/after comparison.
- M8: more findings with the status closed, and fewer days to closed, mean faster closure. Only the kit has closure data, so the metric shows no trend over time.
- M9: a higher share means more decisions have a recorded result. In Project A the v2 share is lower than the v1 share. Newer entries have had less time to get an outcome. The kit cells are young (limit 13).
- M12: higher values mean more commits or versions per week. In Project A the versions per week fell from v1 to v2. Commits per week are close in the two periods. Project B per-week figures are spread over a long span (limit 14).
- M13: the 30% rule in `PLAYBOOK.md` is a ceiling, not a direction. If hard tasks pass 30% of all tasks, the contracts are too big and are split. Project A has no dated tasks, so there is no before/after comparison. Most tasks have no done date and sit in the undated column (limit 12).

## Limits

1. One maintainer (n = 1). The results are descriptive and carry no causal claim (DEC-010).
2. The process and the maintainer changed at the same time. A difference between v1 and v2 cannot be assigned to either.
3. Project B has v1 data for M3, M8 and M12 only. M1 and M2 exist for Project A only. The kit has no version data (M1, M2) and no test attribute history (M3). M5 and M6 have v2 data only. Project A M13 is entirely undated.
4. Period lengths differ: 15, 10, 350 and 6 days (see sources and periods). Entries per column are in the tables.
5. M5, M6 and M13 are written by the role being measured. M8 is the only series written by an independent role.
6. Project A's records entered git just before the cutoff. The v1 record text is today's text.
7. The snapshot date is 2026-11-03 for all sources. Project A and Project B were snapshotted with uncommitted changes in the source (`input.dirty` true in the result files). The kit snapshot was clean.
8. Cells shown as counts only: M13 kit v2. The threshold 5 is a judgment, not derived from data.
9. Four metrics were dropped: M4, M7, M10 and M11. The reasons are in DEC-021: a hand list with a very small n, a hand label needed, specific to the source domain, and no source.
10. The Project B audit folder is not tracked in git (DEC-029). The snapshot hash pins the text, but its history cannot be checked in git.
11. The source records use two meanings of the review round number, so 0 and 1 are not comparable across all entries. The script takes the number as written (DEC-030).
12. Undated tasks in M13. Project A has 22 task headings with no size tag, which M13 does not count. Its 16 tagged tasks are all undated. The kit has 2 untagged headings, and 11 of its 15 tagged tasks are undated (result file warnings). Project A M12 also has 1 version without a date (`m12_undated_version`).
13. M8 closure data exists for the kit only. In Project A and Project B every finding shows status "none". This means the reports carry no status the parser can follow. It does not show that findings stayed open. M9 for the kit is young: decisions are recent and outcomes are written later, and the data stops at the snapshot.
14. M12 for Project B: the commit span is 350 days, while the dated changelog headings cover 13 days. Its per-week figures are spread over a long span.
15. M2 is a state at snapshot time, not a history. It cannot tell "tested, marker left" from "never tested". M3 counts test attributes, not passing tests.
16. Parse coverage (log 2026-11-03, entries 6 and 7). Project A: 20 v2 log entries carry task numbers and 19 were parsed. One was not parsed because it holds two conflicting free-text round numbers. One of the 19 has no round number, so the M5 n is 18. The M6 n is 17 per field, because 2 entries miss each field (result file warnings). Kit: 20 loose matches, 16 counted, and the other 4 are prose lines, not metric lines, so the gap is 0. Project B has no metric lines.
17. The kit counts every metric line as a task, including the lead's plan and audit entries.
18. File hashes are taken over raw bytes, so they depend on line endings. In a check by the technical lead on 2026-11-04, the kit was snapshotted again from a fresh clone at the commit in `input.head`, on one Windows machine. 5 of 7 snapshot files had different hashes and the same text once line endings were normalized. Metrics and warnings matched `evidence/kit.json` exactly.

## How to rerun

Only the kit can be rerun by a stranger. The Project A and Project B snapshots are private and ignored by git. For those two, the result files and the hashes are committed, and the source records are not.

A fresh clone holds no snapshot, because `evidence/raw/` is ignored by git. To rerun the kit:

1. Clone the repository.
2. Make a second checkout at the commit in `input.head` of `evidence/kit.json`.
3. From the first clone, run the snapshot command below with `--source` pointing at the second checkout.

Expected result: `metrics`, `warnings` and `input.head` match `evidence/kit.json`. `kit_commit` differs, because it records the commit of the tools. File hashes can differ with line endings (limit 18). This was tested on one Windows machine on 2026-11-04.

To take a snapshot and count, from the repository root:

```
python -m tools.metrics --source <dir> --profile tools/metrics/profiles/<label>.json --label <label> --out evidence/<label>.json --snapshot
```

The label is `project-a`, `project-b` or `kit`. The snapshot copies the record files into `evidence/raw/<label>/` and writes a manifest with a SHA-256 hash per file.

To rerun from an existing snapshot, leave out `--snapshot` and `--source`. The run reads the copies only. The JSON is byte-identical only on a machine that holds the snapshot in `evidence/raw/`:

```
python -m tools.metrics --profile tools/metrics/profiles/<label>.json --label <label> --out evidence/<label>.json
```

To rewrite the tables in this file:

```
python -m tools.metrics.render --doc EVIDENCE.md evidence/project-a.json evidence/project-b.json evidence/kit.json
```

A second render leaves the file unchanged.
