# ANSYS Maxwell PyAEDT Skill

Automate ANSYS Maxwell (2D/3D) and RMxprt motor design on Windows through PyAEDT.

## What it does

This skill provides command-line automation for ANSYS Maxwell electromagnetic simulation and motor design. Instead of clicking through the ANSYS Electronics Desktop GUI, you can create projects, assign geometry, boundaries, windings, setups, solve, and export results — all from the command line.

## Features

### Core Commands

- **`doctor`** — Diagnose Python, PyAEDT, and AEDT/Maxwell installation environment
- **`new-project`** — Create a minimal Maxwell 2D or 3D project with simple geometry, boundaries, setup, and optional solve
- **`analyze-project`** — Open an existing `.aedt` project, modify design variables, re-solve, and export results
- **`list-projects`** — Read-only inspection of an existing project: designs, setups, sweeps, variables, and objects

### Motor-Specific Commands

- **`new-motor-project`** — Create a simple axial-gap motor with stator, rotor, airgap, winding assignment, rotation boundary, adaptive setup, and solve
- **`analyze-motor`** — Modify motor parameters (speed, geometry, variables) and re-solve, export torque/force data
- **`new-rmxprt-project`** — Quick analytical motor analysis using RMxprt (equivalent-circuit tool, no FEA mesh needed)

### Supported Motor Topologies (via RMxprt)

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| `BLDC` | Brushless DC Motor | 无刷直流电机 — trapezoidal back-EMF |
| `PMSM` | Permanent Magnet Synchronous Motor | 永磁同步电机 — sinusoidal back-EMF |
| `IM` | Induction Motor | 感应电机（异步电机）— squirrel-cage or wound rotor |
| `SRM` | Switched Reluctance Motor | 开关磁阻电机 — doubly-salient, no PM |
| `LSSM` | Linear Synchronous Switched Reluctance Motor | 直线同步磁阻电机 — linear motion |
| `ASSM` | Axial Flux Synchronous Motor | 轴向磁通同步电机 — disc-type |
| `PMDC` | Permanent Magnet DC Motor | 永磁直流电机 — brushed DC |
| `DCM` | DC Commutator Motor | 直流换向器电机 — traditional brushed |
| `CPSM` | Claw Pole Synchronous Motor | 爪极同步电机 — automotive alternator |
| `NSSM` | Nested Stator Synchronous Motor | 嵌套定子同步电机 — dual-stator structure |

### Boundary and Excitation Support

Flux-tangential, symmetry (odd/even), zero-H-field, radiation boundary, insulating, resistive sheet, coil terminals, winding assignment (Current/Voltage/Impedance), rotation motion, force and torque monitors

### Maxwell Solver Types

**3D:** Magnetostatic, Transient, Eddy Current, Electrostatic, Magnetodynamic
**2D:** Magnetostatic, TransientZ, Eddy Current, Electrostatic, MagnetodynamicZ

### Export Formats

- Touchstone S-parameter files (`.sNp`)
- Parametric results CSV (torque, force, efficiency vs. time/angle/speed)
- Field results (full field data export)

## Requirements

- Windows
- ANSYS Electronics Desktop with Maxwell installed
- Python 3.10+ with `pyaedt` installed (`pip install pyaedt`)

## Quick Start

### 1. Check Environment

```powershell
py -3.14 scripts/maxwell_workflow.py doctor
py -3.14 scripts/maxwell_workflow.py doctor --json
```

### 2. Create a Minimal Maxwell 3D Project

```powershell
py -3.14 scripts/maxwell_workflow.py new-project ^
  --project C:\temp\maxwell\demo.aedt ^
  --design Maxwell3DDesign1 ^
  --maxwell-type 3D ^
  --geom box ^
  --origin 0mm,0mm,0mm ^
  --size 10mm,10mm,10mm ^
  --material copper ^
  --setup-type Magnetostatic ^
  --solve ^
  --export-touchstone C:\temp\maxwell\demo.s2p
```

### 3. Create a 2D Motor Project

```powershell
py -3.14 scripts/maxwell_workflow.py new-motor-project ^
  --project C:\temp\maxwell\motor.aedt ^
  --design Maxwell2DDesign1 ^
  --maxwell-type 2D ^
  --stator-od 100mm ^
  --rotor-od 60mm ^
  --stack-length 80mm ^
  --air-gap 0.5mm ^
  --stator-material M19_24G ^
  --rotor-material M19_24G ^
  --pole-pairs 4 ^
  --stator-slots 36 ^
  --rotor-slots 40 ^
  --solution-type Transient ^
  --setup-type Transient ^
  --assign-motion ^
  --angular-velocity 1500rpm ^
  --winding-type Current ^
  --winding-current 5 ^
  --symmetry-mode ^
  --solve ^
  --export-torque-csv C:\temp\maxwell\torque.csv
```

### 4. Quick RMxprt Analysis (BLDC)

```powershell
py -3.14 scripts/maxwell_workflow.py new-rmxprt-project ^
  --project C:\temp\maxwell\bldc.aedt ^
  --rmxprt-topology BLDC ^
  --stator-od 100mm ^
  --rotor-od 60mm ^
  --stack-length 80mm ^
  --air-gap 0.5mm ^
  --pole-pairs 4 ^
  --stator-slots 36 ^
  --rotor-slots 40 ^
  --angular-velocity 3000rpm ^
  --rated-power 1kW ^
  --rated-voltage 48V ^
  --solve ^
  --export-results C:\temp\maxwell\bldc_params.csv
```

### 5. Re-solve with New Parameters

```powershell
py -3.14 scripts/maxwell_workflow.py analyze-motor ^
  --project C:\temp\maxwell\motor.aedt ^
  --setup-name Setup1 ^
  --angular-velocity 3000rpm ^
  --solve ^
  --export-torque-csv C:\temp\maxwell\torque_3000.csv
```

### 6. Inspect Existing Project (No Solve)

```powershell
py -3.14 scripts/maxwell_workflow.py list-projects ^
  --project C:\temp\maxwell\motor.aedt ^
  --design Maxwell2DDesign1 ^
  --maxwell-type 2D
```

## Full Command Reference

### `doctor`

Diagnoses the local Python, PyAEDT, and AEDT/Maxwell installation.

| Flag | Description |
|------|-------------|
| `--json` | Output machine-parseable JSON |

### `new-project`

Creates a minimal Maxwell project with geometry, boundaries, setup, and optional solve.

| Flag | Description | Default |
|------|-------------|---------|
| `--project` | Output `.aedt` file path (required) | — |
| `--design` | Design name | `Maxwell3DDesign1` |
| `--maxwell-type` | Solver type | `3D` |
| `--version` | AEDT version | auto-detect |
| `--non-graphical` | Run without GUI | false |
| `--set-variable` | Set design variable (repeatable) | — |
| `--geom` | Geometry primitive | `box` (3D) / `rectangle` (2D) |
| `--origin` | Origin x,y,z | `0mm,0mm,0mm` |
| `--size` | Size sx,sy,sz (2D: sx,sy) | `10mm,10mm,1mm` |
| `--material` | Material name | `vacuum` |
| `--assign-flux-tangential` | Assign flux-tangential boundary | false |
| `--assign-symmetry` | Assign symmetry boundary | false |
| `--assign-zero-h` | Assign zero tangential H-field | false |
| `--assign-radiation` | Assign radiation boundary | false |
| `--assign-insulating` | Assign insulating boundary | false |
| `--assign-resistive-sheet` | Assign resistive sheet | false |
| `--setup-type` | Setup type string | `None` |
| `--max-passes` | Max adaptive passes | `20` |
| `--min-passes` | Min adaptive passes | `2` |
| `--percent-error` | Convergence criterion | `2.0` |
| `--solve` | Solve after creation | false |
| `--export-touchstone` | Output `.sNp` path | — |
| `--export-parametric-results` | Output CSV path | — |

### `analyze-project`

Re-opens an existing project, updates variables, re-solves, exports results. Same flags as `new-project` minus geometry options.

### `list-projects`

Read-only inspection. Outputs: design name, solution type, setup names, sweep names, variables, and object list.

| Flag | Description | Default |
|------|-------------|---------|
| `--project` | Existing `.aedt` file (required) | — |
| `--design` | Design name | auto-detect |
| `--maxwell-type` | Solver type | `3D` |
| `--version` | AEDT version | auto-detect |
| `--non-graphical` | Run without GUI | false |

### `new-motor-project`

Creates a motor with stator, rotor, airgap, winding, rotation boundary, and setup.

| Flag | Description | Default |
|------|-------------|---------|
| `--project` | Output `.aedt` file path (required) | — |
| `--maxwell-type` | `2D` recommended for motors | `2D` |
| `--stator-od` | Stator outer diameter | `100mm` |
| `--rotor-od` | Rotor outer diameter | `60mm` |
| `--stack-length` | Magnetic stack length | `80mm` |
| `--air-gap` | Air gap length | `0.5mm` |
| `--stator-material` | Stator core material | `M19_24G` |
| `--rotor-material` | Rotor core material | `M19_24G` |
| `--stator-name` | Stator object name | `Stator` |
| `--rotor-name` | Rotor object name | `Rotor` |
| `--pole-pairs` | Number of pole pairs | `4` |
| `--stator-slots` | Number of stator slots | `36` |
| `--rotor-slots` | Number of rotor slots | `40` |
| `--solution-type` | Maxwell solution type | `Transient` |
| `--winding-type` | Winding type | `Current` |
| `--winding-current` | Winding current (A) | `1.0` |
| `--winding-voltage` | Winding voltage (V) | `0` |
| `--winding-phase` | Phase angle (degrees) | `0` |
| `--assign-motion` | Assign rotation to rotor | false |
| `--rotation-axis` | Rotation axis | `Z` |
| `--angular-velocity` | Motor speed | `1500rpm` |
| `--symmetry-mode` | Apply symmetry boundary | false |
| `--setup-type` | Setup type | `Transient` |
| `--stop-time` | Transient stop time | `0.1s` |
| `--time-step` | Transient time step | `0.0001s` |
| `--solve` | Solve | false |
| `--export-torque-csv` | Torque/force CSV output | — |
| `--export-results` | Field results export folder | — |

### `new-rmxprt-project`

Quick analytical motor analysis without FEA mesh.

| Flag | Description | Default |
|------|-------------|---------|
| `--project` | Output `.aedt` file path (required) | — |
| `--rmxprt-topology` | Motor topology | `BLDC` |
| `--stator-od` | Stator outer diameter | `100mm` |
| `--rotor-od` | Rotor inner diameter | `60mm` |
| `--stack-length` | Stack length | `80mm` |
| `--air-gap` | Air gap | `0.5mm` |
| `--pole-pairs` | Pole pairs | `4` |
| `--stator-slots` | Stator slots | `36` |
| `--rotor-slots` | Rotor slots | `40` |
| `--angular-velocity` | Rated speed | `3000rpm` |
| `--rated-power` | Rated power | `1kW` |
| `--rated-voltage` | Rated voltage | `400V` |
| `--stator-material` | Stator material | `M19_24G` |
| `--rotor-material` | Rotor material | `M19_24G` |
| `--solve` | Solve | false |
| `--export-results` | Motor parameters CSV | — |

## Project Structure

```
maxwell-skill/
├── SKILL.md                     # Claude/Codex skill instructions
├── README.md                    # This file
├── scripts/
│   └── maxwell_workflow.py      # Main automation script (~1000 lines)
├── references/
│   ├── local-environment.md     # Environment checklist
│   └── workflow-recipes.md      # Command examples and prompt patterns
└── agents/
    └── openai.yaml              # Agent UI metadata
```

## Installation (as a Claude/Codex Skill)

Copy the `maxwell-skill` folder into your Claude skills directory:

```powershell
xcopy /E /I maxwell-skill %USERPROFILE%\.claude\skills\ansys-maxwell
```

Claude will then automatically recognize the `ansys-maxwell` skill and invoke it when you describe Maxwell-related tasks.

## License

MIT
