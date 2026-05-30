# Project snapshot — download & reassemble

`mphinance-jules-ready-20260530.zip` is a full snapshot of this branch
(`claude/reproduction-case-CgpHJ`) with the Jules-ready updates. It's 102MB,
which exceeds GitHub's 100MB per-file push limit, so it's split into parts here.

## Download

Grab all three parts from this `dist/` folder:

- `mphinance-jules-ready.zip.part-00`
- `mphinance-jules-ready.zip.part-01`
- `mphinance-jules-ready.zip.part-02`

## Reassemble

**macOS / Linux:**
```bash
cat mphinance-jules-ready.zip.part-* > mphinance-jules-ready.zip
shasum -a 256 mphinance-jules-ready.zip
# expect: 9eb314693f30e5dcecc099d1e27d0d669112dcbbf3a3f698de708b9ba23ebcb7
unzip mphinance-jules-ready.zip -d mphinance
```

**Windows (PowerShell):**
```powershell
cmd /c copy /b mphinance-jules-ready.zip.part-00+mphinance-jules-ready.zip.part-01+mphinance-jules-ready.zip.part-02 mphinance-jules-ready.zip
Get-FileHash mphinance-jules-ready.zip -Algorithm SHA256
# expect: 9EB314693F30E5DCECC099D1E27D0D669112DCBBF3A3F698DE708B9BA23EBCB7
Expand-Archive mphinance-jules-ready.zip -DestinationPath mphinance
```

Then follow the run steps in [`JULES.md`](../JULES.md) (use a venv + `setup.sh`).

> Note: these zip parts are large binaries committed only for download
> convenience on this throwaway branch. Don't merge them into `main`.
