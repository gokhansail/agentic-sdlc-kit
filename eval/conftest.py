"""Keep pytest out of the eval set: the synthetic repository is data, not code under test."""
collect_ignore_glob = ["repo/*", "repo/**/*"]
