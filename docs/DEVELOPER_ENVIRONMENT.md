# Developer Environment

This project is split into a FastAPI backend and a Next.js frontend. The normal path is to use a local Python virtual environment and Node 22.

## Runtime Versions

- Python: 3.11 or newer
- Node: 22, pinned in `.node-version`
- Frontend package manager: npm or pnpm from the `frontend/` directory

The real frontend lockfile is `frontend/package-lock.json`. The repository root does not need a `package-lock.json` because there is no root package.

## Codex Desktop Runtime Workaround

Some Codex desktop shells do not expose plain `npm` or `python` on `PATH`. When that happens, use the bundled runtime binaries directly:

```powershell
$Runtime = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies"
$env:PATH = "$Runtime\node\bin;$env:PATH"
& "$Runtime\bin\pnpm.cmd" --dir frontend install --ignore-scripts
& "$Runtime\bin\pnpm.cmd" --dir frontend build
& "$Runtime\python\python.exe" scripts\smoke_check.py
```

If pnpm prompts for build-script approval, approve only packages you trust for the current project. The frontend currently builds without custom application build scripts.

## Common Tasks

PowerShell aliases are available through `scripts/tasks.ps1`:

```powershell
.\scripts\tasks.ps1 backend-tests
.\scripts\tasks.ps1 frontend-build
.\scripts\tasks.ps1 frontend-ui
.\scripts\tasks.ps1 smoke
.\scripts\tasks.ps1 cleanup
```

The cleanup task removes generated caches, frontend build output, Python bytecode, and temporary SQLite databases. To preview cleanup first:

```powershell
python scripts\cleanup_workspace.py --dry-run
```

To also remove frontend dependency folders:

```powershell
python scripts\cleanup_workspace.py --include-dependencies
```
