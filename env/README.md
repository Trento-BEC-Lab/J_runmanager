# Shared development environment

All six repositories use `~/.local/share/mamba/envs/labscript_test_v1` and the
same authoritative snapshot in `../env/` (relative to each repository).
Each repository's own `env/` contains Git-tracked copies of the two dependency
files, not an independent environment definition.

Run through **Terminal → Run Task**:

- **Env: Snapshot** exports the current conda package URLs/builds and ordinary
  pip requirements to the shared folder, then copies both files to every existing
  participating repository. Editable installs are excluded.
- **Env: Sync from lock** reads the shared snapshot. If conda differs it stops
  without package changes and asks for a rebuild. Otherwise it synchronizes
  ordinary pip packages, removing extras, while preserving editable registrations.
- **Env: Rebuild from lock** reads the shared snapshot and requires typing
  `rebuild`. Close applications using the environment first. It prefetches conda
  packages, removes and recreates the environment, then installs pip dependencies.
  All editable registrations are removed, but source checkouts remain intact.
  Reinstall your chosen editable projects manually afterward.
- **Env: Copy local snapshot to shared** replaces the shared snapshot with the
  current repository's saved copy and distributes it to all participating folders.
  This does not export or modify the installed environment. Use it to promote a
  committed snapshot after a Git checkout/pull, then run Sync or Rebuild as needed.

Participants: `J_labscript`, `J_labscript-devices`, `J_labscript-utils`, `J_blacs`,
`J_runmanager`, and `J_runviewer`, located beside one another. Missing repositories
are silently skipped. Distribution reports each repository copied; real write
errors fail the task. Only `conda-linux-64.lock` and `pip-requirements.txt` are
copied, preserving READMEs and other files. Commits remain manual.

On first Sync/Rebuild, if both shared snapshot files are absent, they are
initialized from the current repository and distributed. An incomplete shared
snapshot is an error; use Copy local snapshot to shared to restore it. Existing
shared files always take precedence over local copies. A Snapshot or copy task
can therefore modify tracked files in every participating repository. Run these
shared-environment tasks one at a time.

The tasks use system Python to orchestrate micromamba. Network access is needed
for uncached dependencies. Rebuild is not transactional: failure after removal
can leave an incomplete environment; rerun Rebuild to recover.

Pip uses `--no-deps`; dependencies must be captured separately. Pip versions are
pinned but artifacts are not hash-locked. Direct-URL/local non-editable pip
installs are rejected by Snapshot rather than converted to inaccurate pins.
Sync/Rebuild verify both inventories; `pip check` issues are advisory. Actual
installation errors or inventory mismatches still fail the task.

Editable projects and their Git revisions remain under your control. Ordinary
Python source changes take effect after restart; metadata/entry-point changes
or compiled extensions can require reinstalling. For a manual editable install:

```bash
~/.local/share/mamba/envs/labscript_test_v1/bin/python -m pip install --no-deps -e .
```
