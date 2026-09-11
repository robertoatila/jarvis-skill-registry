# Phase 14 — n8n Adapter

Status: PASS_WITH_WARNINGS

Inspected: adapters/n8n.py, schemas/n8n-adapter.schema.json, test_agentic_n8n.py

Changed: None (Verified existing implementation)

Reused: N8nWorkflowAdapter, webhook payload formatting, execution contract

Deprecated: None

Commands Executed: `C:\Users\Ad\AppData\Local\Programs\Python\Python312\python.exe -B -m unittest tests.test_agentic_n8n -v` (exit 0 in 0.152s).

Results: Test suite executed with exit code 0. All unit and integration assertions satisfied.

Tests Passed: All tests in test_agentic_n8n.py passed.
Tests Failed: 0
Tests Not Executed: External linters/typecheckers NOT_EXECUTED (absent in local Python environment).

Compatibility Notes: Adapter handles webhook schema conversion without requiring live external network.

Known Risks: Live webhook delivery requires configured n8n endpoint.

Remaining Uncertainty: External network services remain outside local sovereign boundary.

Evidence: phase-14-n8n.json
