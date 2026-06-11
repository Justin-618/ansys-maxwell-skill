# Local Environment Checklist

## Expected Baseline

- OS: Windows
- Local AEDT installation with Maxwell (ANSYS Electronics Desktop)
- Working Python launcher such as `py`
- PyAEDT installed in the interpreter used by the skill

## Quick Checks

- Confirm PyAEDT import:
  ```powershell
  py -3.14 -c "from ansys.aedt.core import Maxwell3d, Maxwell2d, Rmxprt; print('OK')"
  ```
  > **注意**: PyAEDT 类名是小写结尾的 `Maxwell3d` / `Maxwell2d`，不是 `Maxwell3D`。

- Confirm the skill can inspect the environment:
  ```powershell
  py -3.14 scripts/maxwell_workflow.py doctor
  ```

- Confirm local AEDT install folders exist:
  - `C:\Program Files\AnsysEM`
  - `C:\Program Files\ANSYS Inc`
  - `D:\Ansys\AnsysEM`  (your installation path)
  - `D:\Ansys\ANSYS Inc`

## Known Installation Paths

For this workstation, ANSYS is installed under `D:\Ansys`:
```
D:\Ansys\
├── ANSYS Inc\
│   └── v241\
├── AnsysEM\
│   └── v241\
├── Motor-CAD\
└── ...
```

The script `_find_aedt_installs()` searches these standard roots plus `D:\Ansys`.

## Maxwell-Specific Notes

- Maxwell is part of ANSYS Electronics Desktop (AEDT). There is no standalone Maxwell installer.
- Your installation appears to be **ANSYS Student** edition. Use `--student-version` / `student_version=True` when launching.
- The AEDT version on this machine is v241 (2024 R1).
- Student edition has limitations:
  - Maximum mesh count limit
  - Cannot use HPC (cluster) solving
  - Some features may be disabled
- Maxwell licensing may differ from HFSS licensing. If solve fails with a licensing error, verify that your license server includes Maxwell modules.
- Maxwell 2D assumes geometry in the XY plane (Z = 0 by default).

## Implications

- Prefer an explicit Python launcher such as `py -3.14` when running bundled scripts.
- Confirm licensing and GUI launch behavior before adding fragile high-level workflows.
- If a different Python version is the active PyAEDT environment, use that interpreter consistently.
