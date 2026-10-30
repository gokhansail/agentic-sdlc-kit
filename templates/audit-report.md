# Audit report

What is this file? The report of one audit. The auditor fills it at a gate. The auditor reads documents, code, history and logs, checks every claim, counts what can be counted and puts evidence first. The auditor fixes nothing and never closes its own finding.

## Audit <gate or audit ID>
- Read: <documents, code, history and logs that were read>

## Findings
One block per finding.

### <prefix>-<number> <short title>
- Type: <process, design, code or role; this is the prefix of the ID>
- Severity: <critical, high, medium or low, by threat and recurring cost>
- Claim: <the statement that was checked>
- Evidence: <file and line, command output or count that shows the result>

## Verdict line
<accept, conditional or reject>: <one sentence with the reason>

Sources: [C-42, C-43, C-44]
