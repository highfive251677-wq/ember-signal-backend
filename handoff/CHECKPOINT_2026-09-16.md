# Checkpoint — 2026-09-16

## Current stage

The duplicate institution workflow has been generated locally as a candidate queue. No institution has been merged, deleted, remapped, or approved automatically.

## Duplicate queue

The local database currently contains 357 institutions, 79 duplicate candidate pairs, 79 pending candidates, and 0 human decisions. The candidate generator uses normalized names, name similarity, city, township, and institution type. The queue is a review aid, not a merge decision.

The next gated step is to review the high-confidence candidates manually. No AI auto-merge is permitted.

## Railway checks

The following public Railway endpoints returned HTTP 200 during this checkpoint:

- `/api/health`
- `/api/dashboard`
- `/api/methodology`
- `/api/signals`

A Railway CLI or Railway token is not available in this session, so internal deployment logs were not retrieved. Public endpoint health is therefore verified, but internal log inspection remains pending until Railway access is available.

## GitHub checks

The repository currently has no GitHub issues and no pull requests in the queried history. The duplicate workflow code is pushed on commit `5eb516b`.

## Safety gates

- No automatic merge.
- No source or evidence foreign-key remapping.
- No production database write.
- No public signal release from unreviewed evidence.
- Connector analysis is report-only.
- Stop immediately if a material data-integrity, access-control, privacy, or provenance error is found.

## Next step

Use one connector as an independent operational auditor over the collected status facts. Then inspect the high-confidence candidate list one human decision at a time. Only after recorded human decisions exist should an approved merge implementation be designed.
