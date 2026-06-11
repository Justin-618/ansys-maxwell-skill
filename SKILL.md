---
name: ansys-maxwell
description: Automate ANSYS Maxwell tasks on Windows through PyAEDT. Use when the user needs to inspect the local Maxwell environment, create or modify Maxwell 2D/3D projects, set design variables, build simple geometry, assign excitations and boundaries (flux-tangential, symmetry, zero-H, radiation), create adaptive setups and sweeps, run analyses, and export Touchstone or parametric results from `.aedt` projects. Also supports motor-specific workflows: create simple axial-gap motors with stator/rotor/winding/rotation boundaries, and quick analytical motor analysis via RMxprt.
---

# ANSYS Maxwell PyAEDT Skill

## Overview

Use this skill to perform scripted Maxwell work through local PyAEDT instead of hand-driving the ANSYS Electronics Desktop GUI. Prefer it for repeatable Maxwell 2D/3D setup, geometry automation, environment diagnostics, and simple simulation-to-export workflows.

This skill ships one stable entrypoint: [scripts/maxwell_workflow.py](./scripts/maxwell_workflow.py). Start with `doctor`, then use `new-project` or `analyze-project`. For motor design, use `new-motor-project` or `new-rmxprt-project`.

## Workflow

1. Run the environment check before touching Maxwell:
   ```powershell
   py -3.14 scripts/maxwell_workflow.py doctor
   ```
2. Read [references/local-environment.md](./references/local-environment.md) if version or Python path discovery matters.
3. For a brand new automation smoke test, create a minimal project with `new-project`.
4. For an existing `.aedt` project, use `analyze-project` to set variables, rerun a setup, and optionally export Touchstone.
5. For motor design, use `new-motor-project` to create a stator+rotor+winding+rotation setup, or `new-rmxprt-project` for quick analytical screening.
6. Use `list-projects` to inspect designs, setups, and variables without solving.
7. Save outputs outside the repository when they are large or binary-heavy.

## Command Guide

### Doctor

```powershell
py -3.14 scripts/maxwell_workflow.py doctor
py -3.14 scripts/maxwell_workflow.py doctor --json
```

### Create A Minimal Maxwell Project

```powershell
py -3.14 scripts/maxwell_workflow.py new-project `
  --project C:\temp\maxwell\demo.aedt `
  --design Maxwell3DDesign1 `
  --maxwell-type 3D `
  --geom box `
  --origin 0mm,0mm,0mm `
  --size 10mm,10mm,10mm `
  --material copper `
  --setup-type Magnetostatic `
  --solve `
  --export-touchstone C:\temp\maxwell\demo.s2p
```

Notes:
- `--maxwell-type` supports `3D` (default) and `2D`.
- `--setup-type` is a **string**, not a number. Maxwell examples: `"Magnetostatic"`, `"Transient"`, `"Eddy Current"`, `"Electrostatic"`, `"Magnetodynamic"`.
- `--set-variable NAME=VALUE` is repeatable.
- `--non-graphical` is available, but prefer graphical mode until local licensing is proven stable.

### Analyze An Existing Project

```powershell
py -3.14 scripts/maxwell_workflow.py analyze-project `
  --project C:\temp\maxwell\demo.aedt `
  --design Maxwell3DDesign1 `
  --setup-name Setup1 `
  --set-variable L=12mm `
  --export-touchstone C:\temp\maxwell\demo.s2p
```

### List Projects (Read-Only)

```powershell
py -3.14 scripts/maxwell_workflow.py list-projects `
  --project C:\temp\maxwell\demo.aedt `
  --design Maxwell3DDesign1 `
  --maxwell-type 3D
```

Outputs: design name, solution type, setup names, sweep names, variables, and object list.

## Motor-Specific Commands

### new-motor-project: Simple Axial-Gap Motor

Creates a motor with stator cylinder, rotor cylinder, airgap region, winding assignment, rotation boundary, and adaptive setup.

```powershell
py -3.14 scripts/maxwell_workflow.py new-motor-project `
  --project C:\temp\maxwell\motor.aedt `
  --design Maxwell2DDesign1 `
  --maxwell-type 2D `
  --stator-od 100mm `
  --rotor-od 60mm `
  --stack-length 80mm `
  --air-gap 0.5mm `
  --stator-material M19_24G `
  --rotor-material M19_24G `
  --pole-pairs 4 `
  --stator-slots 36 `
  --rotor-slots 40 `
  --solution-type Transient `
  --setup-type Transient `
  --assign-motion `
  --angular-velocity 1500rpm `
  --winding-type Current `
  --winding-current 5 `
  --symmetry-mode `
  --solve `
  --export-torque-csv C:\temp\maxwell\torque.csv
```

### new-rmxprt-project: Quick Analytical Motor Analysis

Uses RMxprt (equivalent-circuit analytical tool) for rapid motor concept screening. No geometry, no FEA mesh — pure analytical calculation.

```powershell
py -3.14 scripts/maxwell_workflow.py new-rmxprt-project `
  --project C:\temp\maxwell\motor_rmxprt.aedt `
  --rmxprt-topology BLDC `
  --stator-od 100mm `
  --rotor-od 60mm `
  --stack-length 80mm `
  --air-gap 0.5mm `
  --pole-pairs 4 `
  --stator-slots 36 `
  --rotor-slots 40 `
  --angular-velocity 3000rpm `
  --rated-power 1kW `
  --rated-voltage 400V `
  --solve `
  --export-results C:\temp\maxwell\motor_params.csv
```

Supported RMxprt topologies: `BLDC`, `PMSM`, `IM`, `SRM`, `LSSM`, `ASSM`, `PMDC`, `DCM`, `CPSM`, `NSSM`.

## Maxwell Solver Types

### 3D Solver Types
| Type | Use Case |
|------|----------|
| `Magnetostatic` | Permanent magnets, inductors, actuators (steady-state) |
| `Transient` | Rotating machines, time-varying excitations, torque ripple |
| `Eddy Current` | High-frequency induction, heating, eddy current losses |
| `Electrostatic` | Capacitors, sensors, insulation breakdown |
| `Magnetodynamic` | Low-frequency rotating machines (quasi-static) |

### 2D Solver Types
Same as 3D but with Z-suffix for planar: `TransientZ`, `MagnetodynamicZ`, etc.

## Working Rules

- Prefer explicit file paths for `.aedt` outputs and exported files.
- Treat PyAEDT API behavior as version-sensitive. If a method fails, inspect the current method signature before patching.
- Keep first-pass automations narrow and verifiable. Add one new Maxwell operation at a time.
- When a user asks for motor, transformer, or cable-specific flows, extend the script or add a new one rather than overloading prompts with unchecked assumptions.
- If Maxwell launch or solve fails, rerun `doctor`, confirm installed AEDT paths, and capture the exact error.
- Maxwell licensing may differ from HFSS licensing. Always test with graphical mode first.
- For motor design, **2D Transient** is the most common choice. 3D is needed for end-effect modeling, skew analysis, or complex 3D windings.

## References

- [references/workflow-recipes.md](./references/workflow-recipes.md): command examples and Codex prompt patterns
- [references/local-environment.md](./references/local-environment.md): local AEDT and Python findings
