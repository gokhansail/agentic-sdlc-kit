"""Keep pytest out of the bench: the sandbox project and the hidden tests are data, not code under test.

The sandbox has its own visible suite (run from a copy, see README.md) and each task has hidden tests
that only the known-answer test in tests/test_bench.py runs, inside a temporary copy.
"""
collect_ignore_glob = ["project/*", "project/**/*", "tasks/*", "tasks/**/*"]
