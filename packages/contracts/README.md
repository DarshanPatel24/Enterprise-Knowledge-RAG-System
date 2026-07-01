# Contracts Package Scaffold

## Purpose
Shared cross-engine contract definitions for EKIE, EKRE, and EKCP.

## Standard Layout
1. `src/contracts` for shared contract models
2. `tests` for contract validation and compatibility checks

## Rules
1. Keep one canonical schema definition per payload.
2. Use versioned, backward-compatible evolution.
3. Do not duplicate schema definitions inside service folders.
4. All models are Pydantic v2 with strict typing; no service may fork these schemas locally.
