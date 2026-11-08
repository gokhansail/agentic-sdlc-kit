> **What is this file?** The written security check of the 10-tool read-only MCP server (T-44): findings with severity, status and test, the checks per input, the C-26 endpoint standard, and what the check does not cover. Checked 2026-11-08 on Windows 10, Python 3.10.4, git 2.35.1, mcp 2.3.0.

# Method and scale
Read of `server/`, `tools/lookup.py`, `tools/records.py`, `tools/events.py` and the guard functions the server calls, then measured probes and tests. The threat is a crafted project folder (links, huge or hostile files, a hostile `.git/config`) opened by someone who trusts the tools. High: a tool can read or leak data outside the root, reach the network or run code. Medium: a resource or input limit is missing that a crafted repository or argument can abuse. Low: description, documentation or hardening gap. Open High: 0.

# Findings
| ID | Severity | Status | What and test |
|---|---|---|---|
| S-1 | High | FIXED | `.sdlc/project.md`, `active-contract.md` and `metrics.jsonl` were read through a link or junction out of the root and their lines returned. Now resolved inside the root, regular file, size limit. `test_the_sdlc_folder_as_a_link_pointing_outside_is_never_read`, `test_a_control_file_that_is_a_link_pointing_outside_is_refused` |
| S-2 | High | FIXED | `git status` started the program named by `core.fsmonitor` in `.git/config` (measured). `_git` passes `-c core.fsmonitor=false`. `test_a_repository_config_cannot_start_a_program_through_core_fsmonitor` (has a control run), `test_git_is_started_with_the_file_system_monitor_off` |
| S-3 | High | FIXED | `git status` ran a clean filter named in `.git/config` when only a file time changed (measured). `changed_outside` now refuses a config with `[filter` or `[include`, and a `.git` that is a file or a link. `test_a_clean_filter_in_the_repository_config_is_not_run_by_changed_outside` (control run), `test_changed_outside_does_not_start_git_for_a_config_with_a_filter_or_include` |
| S-4 | Low | ACCEPTED | S-3 reads only the config of the repository at or above the root. Submodule configs, system and global git config are not read; the owner controls the last two. Git LFS repositories are refused by S-3. No test. |
| S-5 | Medium | FIXED | `git status` can rewrite `.git/index`, so a read-only tool wrote. `GIT_OPTIONAL_LOCKS=0` for the call. `test_changed_outside_leaves_the_git_index_alone` (control run), `test_changed_outside_asks_git_not_to_take_optional_locks` |
| S-6 | Medium | FIXED | `tools/scope_guard._HEADING` backtracked cubically: 800 blanks took 0.9 s, 2,000 took 13 s. T-44a replaced it with `heading_text`, one pass over the line. The stopgap in `server/inputs.py` (refuse a run over 16 blanks or `#`) is removed; the 256,000-byte limit on a control file stays. `test_a_heading_with_a_long_run_is_parsed_by_the_guard_without_a_refusal` (server), `test_the_heading_parse_gives_the_regex_answer_on_generated_lines`, `test_a_control_file_over_the_size_limit_is_refused_and_one_at_the_limit_is_read` |
| S-7 | Medium | FIXED | The hook ran the same pattern on the same files, and a hook timeout lets a write through (V-6). Closed by the S-6 change in `tools/scope_guard.py`: a heading of 200,000 blanks now parses in under 0.5 s (the test limit; measured 0.5 ms for 1,000,000), against a 30 s hook timeout. `test_a_heading_with_a_2000_blank_run_is_parsed_in_bounded_time`, `test_a_contract_with_long_field_lines_is_parsed_in_bounded_time` |
| S-8 | Medium | FIXED | `glob_to_regex` patterns with several `**/` or `*` groups backtracked without a bound: 9 `**/` against 30 segments took 4.6 s, 50 patterns of `*a*a*b` against a 500-character path took 1.6 s. `matches` now keeps the reachable path positions as one integer and moves it token by token: O(pattern length x path length / word size). `glob_to_regex` stays as the reference. `test_nine_globstars_against_thirty_segments_are_matched_in_bounded_time`, `test_fifty_patterns_against_a_500_character_path_are_matched_in_bounded_time`, `test_a_decision_on_a_crafted_contract_is_made_in_bounded_time`, `test_the_linear_matcher_gives_the_regex_answer_on_generated_pairs`, `test_the_linear_matcher_gives_the_regex_answer_for_every_string_in_the_tests` |
| S-9 | Medium | FIXED | Record files had a 5 MB limit and were read in full; a device name (`NUL`, `CON`) could be named in the map. Now 2,000,000 bytes, bounded read, regular files only. `test_a_record_file_over_2_mb_is_an_error_answer_and_one_of_2_mb_is_read`, `test_a_device_name_in_the_map_is_an_error_answer_and_does_not_hang` |
| S-10 | Medium | FIXED | The audits folder had no entry or total limit. Now 200 entries, 10,000,000 bytes per call, 1,000 findings or rows per report. `test_an_audits_folder_with_200_entries_is_read_and_one_with_201_is_an_error_answer`, `test_a_report_over_2_mb_is_counted_unreadable_and_not_read`, `test_one_call_reads_at_most_the_byte_budget_of_reports`, `test_a_report_with_too_many_findings_or_rows_is_unreadable` |
| S-11 | Medium | FIXED | Quadratic work: `named_by` compared every decision with every later one (10,000 entries took 3.4 s, so 30,000 take about 31 s), and the heading pattern was quadratic in blank runs (20,000 blanks took 1.8 s). Now linear. `test_naming_decisions_is_fast_and_capped_for_a_file_of_30000_entries`, `test_a_heading_with_a_very_long_blank_run_is_read_in_linear_time`, `test_the_record_map_parses_long_blank_runs_in_linear_time` |
| S-12 | Medium | FIXED | An answer was as large as its file (up to 2 MB). Now titles 200 characters, 30 fields per entry, 150,000 characters per answer (`truncated` is true), IDs of 1 to 20 letters and 1 to 9 digits; `status` and `contract` give 500 patterns and 40 record names of 200 characters (`cut` is true). `test_an_answer_is_cut_to_the_answer_limit`, `test_status_and_contract_answers_are_bounded`, `test_an_entry_has_at_most_30_fields_in_an_answer`, `test_a_long_title_is_cut_to_200_characters`, `test_an_id_longer_than_the_id_shape_is_an_unreadable_heading_not_a_key` |
| S-13 | Medium | FIXED | The event file was read with no limit. Now 8,000,000 bytes, regular file, inside the root. `test_an_event_file_over_the_limit_is_an_error_answer_and_one_at_the_limit_is_read` |
| S-14 | Low | FIXED | OS and git messages carried the root (backslashes doubled in an OS message) or the home folder. `scrub` removes both in three forms. `test_scrub_removes_the_root_and_the_home_folder_in_every_form`, `test_an_error_text_from_the_guard_carries_no_root_path`, `test_no_tool_answer_holds_the_root_or_a_home_path` (all 10 tools, two fixtures) |
| S-15 | Low | FIXED | A `scope_check` path had no length limit. Now 500 characters. `test_scope_check_limits_one_path_to_500_characters` |
| S-16 | Low | FIXED | Descriptions did not say that the tool only reads, or that answers carry project text. Now each starts with "Read only:", the five record tools end with "the text returned is project data", the server instructions say it too. `test_tool_descriptions_are_one_plain_sentence_each` |
| S-17 | Low | ACCEPTED | The `mcp` dependency set is not scanned for known vulnerabilities: no network call is allowed here. Versions are in `docs/toolchain.md`. No test. |

# Inputs
Path inputs. `scope_check.paths`: text rule `relative_to_root`, never opened. Record map entries `decisions`, `lessons`, `tasks`, `log`, `audits`: text rule, then resolved on disk inside the root, regular file, size. Other map entries (`status`, `changelog`, `developer_rules`, extras) are returned as written and never opened. Fixed files (`.sdlc/project.md`, `.sdlc/active-contract.md`, `.sdlc/metrics.jsonl`, `.git/config`): resolved inside the root (`.git/config` may sit in a parent repository and is only scanned). Root: `CLAUDE_PROJECT_DIR` or the start folder, fixed at start. Tests for `..`, absolute outside, UNC (`\\host\share`, `//?/`), drive-relative (`C:x`), NUL byte, device names and a junction: `test_root_lock_denies`, `test_a_map_entry_outside_the_root_gives_an_error_answer*`, `test_a_device_name_in_the_map_*`, `test_root_lock_denies_a_link_pointing_outside`, S-1.

| Tool.argument | Type | Limit |
|---|---|---|
| `scope_check.paths` | list of text | 50 entries, 500 characters each |
| `scope_check.actor` | text | exactly `sub-agent` or `main` |
| `guard_events.task` | text or none | 40 characters |
| `decisions.id`, `tasks.id` | text or none | 40 characters, letters, hyphen, digits |
| `decisions.query`, `lessons.query`, `findings.report` | text or none | 100 characters |
| `findings.status` | text or none | `open`, `closed`, `partial`, `deferred`, `none` |
| `log.count` | whole number | 1 to 20, a boolean is refused |
`status`, `contract`, `changed_outside` take none. Tests: `test_every_argument_of_every_tool_has_a_limit_that_refuses` (fails when an argument has no row), `test_each_argument_accepts_its_limit`.

# C-26 public endpoint standard
Not applicable while the server is stdio only. The source line (C-26) lists 9 items, so there is no item j.
| Item | Reason it does not apply |
|---|---|
| a write-only endpoint | No endpoint takes data; every tool only reads (`test_server_has_no_write_call`). |
| b fail closed without a key | A child process of the host, no listener, no key; a bad root exits 1. |
| c validate input | No untrusted caller on a socket; the arguments are still validated (table above). |
| d escape formulas | No spreadsheet or CSV output; answers are JSON. |
| e cheap checks before locks | No locks; argument and size checks run before any file is read. |
| f rate and volume limits | One caller over stdio; volume is limited per file, folder and answer (S-9 to S-13). |
| g minimal permission | No service identity; the process reads only (S-5). |
| h a closing path | Nothing to close; the process ends when the host closes stdin. |
| i local tests with mutation checks | No endpoint to test; the filter, fsmonitor and index tests each run the unguarded call first and skip if it is harmless. |

# Limits of this check
- No network vulnerability scan (S-17). Importing `mcp` loads `httpx2`, `starlette`, `uvicorn` and `ssl`; no socket is opened (`test_every_tool_runs_with_socket_creation_blocked`).
- A file can change between the check and the read; an attacker would need write access to the folder.
- Answers carry project text. The server labels it as data; it cannot stop a model from following text inside it.
- A `git.exe` in the working folder was not started on this machine (1 trial); other Windows settings were not tried.
- Link tests for single files skip without symlink rights (5 skips here); the junction tests ran. Not run on Linux or macOS.
- The new matcher equals the regex on 6,000 generated pairs (fixed seed, case folding on and off) and on every short string in `tests/*.py` as a pattern. A pair outside that corpus is not proven equal; the case rule for one character is taken from `re` itself.
- The guard's other patterns (`_FIELD`, `_TICKED`, `_TASK_ID`) were measured on lines of 100,000 blanks, backticks or digits (each under 20 ms); they have no proof of a bound.
