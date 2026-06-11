# Maxwell PyAEDT Recipes

## Quick Checks

- Environment doctor:
  ```powershell
  py -3.14 scripts/maxwell_workflow.py doctor
  ```
- JSON doctor output:
  ```powershell
  py -3.14 scripts/maxwell_workflow.py doctor --json
  ```

## Maxwell 3D: Create Minimal Project

```powershell
py -3.14 scripts/maxwell_workflow.py new-project `
  --project C:\temp\maxwell\demo3d.aedt `
  --design Maxwell3DDesign1 `
  --maxwell-type 3D `
  --geom box `
  --origin 0mm,0mm,0mm `
  --size 10mm,10mm,10mm `
  --material copper `
  --setup-type Magnetostatic `
  --solve
```

## Maxwell 2D: Create Minimal Project

```powershell
py -3.14 scripts/maxwell_workflow.py new-project `
  --project C:\temp\maxwell\demo2d.aedt `
  --design Maxwell2DDesign1 `
  --maxwell-type 2D `
  --geom rectangle `
  --origin 0mm,0mm,0mm `
  --size 10mm,10mm,0mm `
  --material copper `
  --setup-type TransientZ `
  --solve
```

## Maxwell Project with Boundaries

```powershell
py -3.14 scripts/maxwell_workflow.py new-project `
  --project C:\temp\maxwell\boundaries.aedt `
  --design Maxwell3DDesign1 `
  --maxwell-type 3D `
  --geom box `
  --material iron `
  --assign-flux-tangential `
  --flux-tangential-objects FluxCore `
  --assign-radiation `
  --setup-type Magnetostatic `
  --solve
```

## Inspect Project Without Solving

```powershell
py -3.14 scripts/maxwell_workflow.py list-projects `
  --project C:\temp\maxwell\demo3d.aedt `
  --design Maxwell3DDesign1 `
  --maxwell-type 3D
```

## Motor: New Transient Motor Project (2D)

```powershell
py -3.14 scripts/maxwell_workflow.py new-motor-project `
  --project C:\temp\maxwell\pmsm.aedt `
  --design Maxwell2DDesign1 `
  --maxwell-type 2D `
  --stator-od 120mm `
  --rotor-od 70mm `
  --stack-length 90mm `
  --air-gap 0.5mm `
  --stator-material M19_24G `
  --rotor-material M19_24G `
  --pole-pairs 4 `
  --stator-slots 48 `
  --rotor-slots 36 `
  --solution-type Transient `
  --setup-type Transient `
  --assign-motion `
  --angular-velocity 1500rpm `
  --winding-type Current `
  --winding-current 10 `
  --coil-conductors 20 `
  --symmetry-mode `
  --percent-error 0.1 `
  --stop-time 0.04s `
  --time-step 1e-5s `
  --solve `
  --export-torque-csv C:\temp\maxwell\torque.csv
```

## Motor: Analyze with Modified Speed

```powershell
py -3.14 scripts/maxwell_workflow.py analyze-motor `
  --project C:\temp\maxwell\pmsm.aedt `
  --design Maxwell2DDesign1 `
  --setup-name Setup1 `
  --angular-velocity 3000rpm `
  --solve `
  --export-torque-csv C:\temp\maxwell\torque_3000.csv
```

## Motor: RMxprt Quick Analysis (BLDC)

```powershell
py -3.14 scripts/maxwell_workflow.py new-rmxprt-project `
  --project C:\temp\maxwell\bldc_rmxprt.aedt `
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
  --rated-voltage 48V `
  --solve `
  --export-results C:\temp\maxwell\bldc_params.csv
```

## Prompt Patterns For Codex

- `Use $ansys-maxwell to diagnose whether PyAEDT and Maxwell are ready on this Windows machine.`
- `Use $ansys-maxwell to create a minimal Maxwell 3D project at C:\temp\maxwell\demo.aedt with a 10mm copper box and Magnetostatic setup.`
- `Use $ansys-maxwell to create a 2D BLDC motor project with 36 stator slots, 4 pole pairs, 1500rpm.`
- `Use $ansys-maxwell to open this motor project, set speed to 3000rpm, re-solve, and export torque data.`
- `Use $ansys-maxwell to do a quick RMxprt analysis of a PMSM motor with 4 pole pairs.`
- `Use $ansys-maxwell to inspect the setups and variables in C:\temp\maxwell\demo.aedt.`
