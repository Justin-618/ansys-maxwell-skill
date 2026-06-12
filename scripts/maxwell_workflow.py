#!/usr/bin/env python3
"""
ANSYS Maxwell automation entrypoint for the ansys-maxwell skill.

Targets ANSYS Maxwell (2D and 3D) via PyAEDT's Maxwell2d / Maxwell3d classes.
Also includes a dedicated motor-workflow path with rotor geometry, winding,
rotation boundary, torque/force monitors, and Rmxprt quick-analysis.

Workflows:
1. doctor            - inspect local PyAEDT and AEDT/Maxwell availability
2. new-project         - create a minimal Maxwell project with simple geometry
3. analyze-project     - open existing .aedt, update variables, solve, export
4. list-projects       - read-only: list designs, setups, variables
5. new-motor-project   - create a simple axial-gap motor (stator+rotor+winding+motion)
6. analyze-motor       - open motor project, set variables, solve, export torque/power
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_pyaedt():
    """Import PyAEDT Maxwell classes. Case-sensitive: Maxwell3d, Maxwell2d."""
    try:
        from ansys.aedt.core import Maxwell3d, Maxwell2d  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "PyAEDT is not importable. Install it with `py -3.14 -m pip install pyaedt` "
            "and confirm that AEDT/Maxwell is installed locally."
        ) from exc
    return Maxwell3d, Maxwell2d


def _parse_triplet(raw: str) -> list[str]:
    parts = [item.strip() for item in raw.split(",")]
    if len(parts) != 3 or any(not item for item in parts):
        raise argparse.ArgumentTypeError(
            f"Expected three comma-separated values, got: {raw!r}"
        )
    return parts


def _parse_pair(raw: str) -> list[str]:
    """Parse a simple 'key=value' pair."""
    if "=" not in raw:
        raise argparse.ArgumentTypeError(
            f"Expected NAME=VALUE, got: {raw!r}"
        )
    name, value = raw.split("=", 1)
    return [name.strip(), value.strip()]


def _parse_variable_overrides(items: Iterable[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        parts = _parse_pair(item)
        result[parts[0]] = parts[1]
    return result


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _find_aedt_installs() -> list[str]:
    roots = [
        Path(r"C:\Program Files\AnsysEM"),
        Path(r"C:\Program Files\ANSYS Inc"),
        Path(r"D:\Ansys\AnsysEM"),
        Path(r"D:\Ansys\ANSYS Inc"),
    ]
    found: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir():
                found.append(str(child))
    return found


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    data: dict = {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "aedt_install_dirs": _find_aedt_installs(),
    }
    try:
        import ansys.aedt.core  # type: ignore
        data["pyaedt_version"] = getattr(ansys.aedt.core, "__version__", "unknown")
        data["pyaedt_import"] = True
    except Exception as exc:
        data["pyaedt_import"] = False
        data["pyaedt_error"] = str(exc)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print("ANSYS Maxwell PyAEDT Doctor")
        for key, value in data.items():
            print(f"- {key}: {value}")
    return 0


# ---------------------------------------------------------------------------
# Context builder (fixes: Maxwell3d/Maxwell2d lowercase + no maxwell_type param)
# ---------------------------------------------------------------------------

def _build_maxwell_context(args: argparse.Namespace):
    """Return an open Maxwell3d or Maxwell2d context manager.

    Important: PyAEDT class names are Maxwell3d / Maxwell2d (lowercase 'd'),
    NOT Maxwell3D / Maxwell2D.  There is no 'maxwell_type' keyword — the
    solution type is passed separately via 'solution_type' to the Hfss-style
    init, or the design_type parameter for Maxwell.
    """
    Maxwell3d, Maxwell2d = _require_pyaedt()
    if args.maxwell_type == "2D":
        cls = Maxwell2d
        print("Using Maxwell2d (2D solver)")
    else:
        cls = Maxwell3d
        print("Using Maxwell3d (3D solver)")

    # Build kwargs carefully: Maxwell2d/3d accept 'solution_type' but NOT
    # 'maxwell_type'.  We also add 'student_version' for Student edition.
    kwargs = dict(
        project=args.project,
        design=args.design,
        version=args.version,
        non_graphical=args.non_graphical,
        new_desktop=True,
        close_on_exit=True,
        student_version=True,  # your installation appears to be ANSYS Student
    )
    return cls(**kwargs)


# ---------------------------------------------------------------------------
# new-project: create a minimal Maxwell project
# ---------------------------------------------------------------------------

def cmd_new_project(args: argparse.Namespace) -> int:
    project_path = Path(args.project).expanduser().resolve()
    _ensure_parent_dir(project_path)

    variable_overrides = _parse_variable_overrides(args.set_variable)

    with _build_maxwell_context(args) as maxwell:
        # Set user-specified variables first
        for name, value in variable_overrides.items():
            maxwell[name] = value

        # ------------------------------------------------------------------
        # Geometry: create a simple primitive
        # ------------------------------------------------------------------
        if args.maxwell_type == "2D":
            if args.geom == "rectangle":
                maxwell.modeler.create_rectangle(
                    points=args.origin,
                    sizes=args.size,
                    name=args.geom_name,
                    material=args.material,
                )
            elif args.geom == "circle":
                maxwell.modeler.create_circle(
                    center=args.origin,
                    radius=args.radius,
                    name=args.geom_name,
                    material=args.material,
                )
            elif args.geom == "arc":
                maxwell.modeler.create_arc(
                    center=args.origin,
                    radius=args.radius,
                    start_angle=args.start_angle,
                    end_angle=args.end_angle,
                    name=args.geom_name,
                    material=args.material,
                )
            else:
                raise ValueError(f"Unsupported geometry type for 2D: {args.geom}")
        else:
            if args.geom == "box":
                maxwell.modeler.create_box(
                    origin=args.origin,
                    sizes=args.size,
                    name=args.geom_name,
                    material=args.material,
                )
            elif args.geom == "sphere":
                maxwell.modeler.create_sphere(
                    center=args.origin,
                    radius=args.radius,
                    name=args.geom_name,
                    material=args.material,
                )
            elif args.geom == "cylinder":
                maxwell.modeler.create_cylinder(
                    axis_start=args.origin,
                    axis_end=(
                        args.origin[0],
                        args.origin[1],
                        args.origin[2] + float(args.length.replace("mm", "")) * 1e-3,
                    ),
                    radius=args.radius,
                    name=args.geom_name,
                    material=args.material,
                )
            else:
                raise ValueError(f"Unsupported geometry type for 3D: {args.geom}")

        # ------------------------------------------------------------------
        # Boundary assignments
        # ------------------------------------------------------------------
        if args.assign_flux_tangential:
            objects = args.flux_tangential_objects or [args.geom_name]
            maxwell.assign_flux_tangential(
                assignment=objects,
                flux_name=args.flux_tangential_name or "FluxTangent1",
            )

        if args.assign_symmetry:
            maxwell.assign_symmetry(
                assignment=args.symmetry_objects or [args.geom_name],
                symmetry_name=args.symmetry_name or "Symmetry1",
                is_odd=args.symmetry_odd,
            )

        if args.assign_zero_h:
            objects = args.zero_h_objects or [args.geom_name]
            maxwell.assign_zero_tangential_h_field(
                assignment=objects,
            )

        if args.assign_radiation:
            maxwell.assign_radiation(
                assignment=[args.geom_name],
                radiation=args.radiation_name or "Radiation1",
            )

        if args.assign_insulating:
            maxwell.assign_insulating(
                assignment=args.geom_name,
            )

        if args.assign_resistive_sheet:
            objects = args.resistive_sheet_objects or [args.geom_name]
            maxwell.assign_resistive_sheet(
                assignment=objects,
                resistance=args.resistive_resistance or "1ohm",
                name="ResistiveSheet1",
            )

        # ------------------------------------------------------------------
        # Setup — Maxwell create_setup uses setup_type string, NOT properties
        # ------------------------------------------------------------------
        if args.setup_name:
            setup = maxwell.create_setup(
                name=args.setup_name,
                setup_type=args.setup_type,  # e.g. "Magnetostatic", "Transient"
                MaximumPasses=args.max_passes,
                MinPasses=args.min_passes,
                PercentError=args.percent_error,
                PercentRefinement=args.percent_refinement,
            )

        # ------------------------------------------------------------------
        # Frequency / time sweep (for applicable setups)
        # ------------------------------------------------------------------
        if args.sweep_name:
            maxwell.create_linear_count_sweep(
                setup=args.setup_name,
                name=args.sweep_name,
                units=args.sweep_units,
                start_frequency=args.sweep_start,
                stop_frequency=args.sweep_stop,
                num_of_freq_points=args.sweep_count,
            )

        # ------------------------------------------------------------------
        # Solve
        # ------------------------------------------------------------------
        if args.solve:
            print("Solving ...")
            if args.setup_name:
                success = maxwell.analyze(setup=args.setup_name)
            else:
                success = maxwell.analyze()
            if not success:
                raise RuntimeError("Maxwell analyze() returned False.")
            print("Solve complete.")

        # ------------------------------------------------------------------
        # Export
        # ------------------------------------------------------------------
        if args.export_touchstone:
            output_path = Path(args.export_touchstone).expanduser().resolve()
            _ensure_parent_dir(output_path)
            exported_file = maxwell.export_touchstone(
                setup=args.setup_name,
                sweep=args.sweep_name,
                output_file=str(output_path),
            )
            if exported_file:
                print(f"Exported Touchstone: {exported_file}")

        if args.export_parametric_results:
            output_path = Path(args.export_parametric_results).expanduser().resolve()
            _ensure_parent_dir(output_path)
            if maxwell.export_parametric_results(
                setup=args.setup_name,
                output_file=str(output_path),
            ):
                print(f"Exported parametric results: {output_path}")

        # ------------------------------------------------------------------
        # Save
        # ------------------------------------------------------------------
        saved = maxwell.save_project(file_name=str(project_path), overwrite=True)
        if not saved:
            raise RuntimeError(f"Failed to save project to {project_path}")

    print(f"Created Maxwell project: {project_path}")
    return 0


# ---------------------------------------------------------------------------
# analyze-project
# ---------------------------------------------------------------------------

def cmd_analyze_project(args: argparse.Namespace) -> int:
    project_path = Path(args.project).expanduser().resolve()
    if not project_path.exists():
        raise FileNotFoundError(f"Project file does not exist: {project_path}")

    variable_overrides = _parse_variable_overrides(args.set_variable)

    with _build_maxwell_context(args) as maxwell:
        for name, value in variable_overrides.items():
            maxwell[name] = value

        print("Solving ...")
        if args.setup_name:
            success = maxwell.analyze(setup=args.setup_name)
        else:
            success = maxwell.analyze()
        if not success:
            raise RuntimeError("Maxwell analyze() returned False.")
        print("Solve complete.")

        if args.export_touchstone:
            output_path = Path(args.export_touchstone).expanduser().resolve()
            _ensure_parent_dir(output_path)
            exported_file = maxwell.export_touchstone(
                setup=args.setup_name,
                sweep=args.sweep_name,
                output_file=str(output_path),
            )
            if exported_file:
                print(f"Exported Touchstone: {exported_file}")

        if args.export_parametric_results:
            output_path = Path(args.export_parametric_results).expanduser().resolve()
            _ensure_parent_dir(output_path)
            if maxwell.export_parametric_results(
                setup=args.setup_name,
                output_file=str(output_path),
            ):
                print(f"Exported parametric results: {output_path}")

        saved = maxwell.save_project(file_name=str(project_path), overwrite=True)
        if not saved:
            raise RuntimeError(f"Failed to save project to {project_path}")

    print(f"Analyzed Maxwell project: {project_path}")
    return 0


# ---------------------------------------------------------------------------
# list-projects
# ---------------------------------------------------------------------------

def cmd_list_projects(args: argparse.Namespace) -> int:
    """Read-only: list designs, setups, variables of an existing project."""
    project_path = Path(args.project).expanduser().resolve()
    if not project_path.exists():
        raise FileNotFoundError(f"Project file does not exist: {project_path}")

    Maxwell3d, Maxwell2d = _require_pyaedt()
    cls = Maxwell3d if args.maxwell_type == "3D" else Maxwell2d

    with cls(
        project=str(project_path),
        design=args.design,
        version=args.version,
        non_graphical=args.non_graphical,
        new_desktop=False,
        close_on_exit=True,
        student_version=True,
    ) as maxwell:
        print(f"Design: {maxwell.design_name}")
        print(f"Solution type: {maxwell.solution_type}")

        # Setup names
        try:
            setups = maxwell.get_setups()
            print(f"Setups: {setups}")
        except Exception:
            print("Setups: (unable to query)")

        # Sweeps
        try:
            sweeps = maxwell.get_sweeps()
            print(f"Sweeps: {sweeps}")
        except Exception:
            print("Sweeps: (unable to query)")

        # Variables
        try:
            vars_dict = maxwell.get_variables_dict()
            print(f"Variables: {vars_dict}")
        except Exception:
            print("Variables: (unable to query)")

        # Material list
        try:
            mat_names = maxwell.get_all_conductors_names() + maxwell.get_all_dielectrics_names()
            if mat_names:
                print(f"Objects: {mat_names}")
            else:
                print("Objects: (none)")
        except Exception:
            print("Objects: (unable to query)")

    return 0


# ===========================================================================
# MOTOR-SPECIFIC WORKFLOW
# ===========================================================================
# The following commands are tailored for motor design using Maxwell 2D/3D
# or the analytical tool RMxprt.  They assume the user has a basic
# understanding of motor terminology (stator, rotor, poles, slots).
# ===========================================================================


# ---------------------------------------------------------------------------
# Motor geometry helpers — these use variables, not hard-coded geometry,
# so that the user can drive everything from the CLI.
# ---------------------------------------------------------------------------

def _setup_motor_variables(maxwell, args):
    """Set all motor-related design variables."""
    motor_vars = {
        "StatorOD": args.stator_od,
        "RotorOD": args.rotor_od,
        "StackLength": args.stack_length,
        "AirGap": args.air_gap,
        "StatorSlots": str(args.stator_slots),
        "RotorSlots": str(args.rotor_slots),
        "PolePairs": str(args.pole_pairs),
        "SlotDepth": args.slot_depth,
        "RotorThickness": args.rotor_thickness,
    }
    for name, value in motor_vars.items():
        if value is not None:
            maxwell[name] = str(value)
    # Also apply user-supplied overrides
    var_overrides = _parse_variable_overrides(args.set_variable) if args.set_variable else {}
    for name, value in var_overrides.items():
        maxwell[name] = value


def _setup_motor_boundary(maxwell, args):
    """Assign flux-tangential outer boundary and rotation to rotor."""
    # Outer boundary: flux tangential on stator OD (Maxwell 2D uses oeditor)
    stator_obj = (args.stator_name + "_outer") if args.maxwell_type == "2D" else (args.stator_name or "Stator")
    try:
        oedt = maxwell.modeler.oeditor
        oedt.ChangeProperty(operation="assignfluxtangential", scope=stator_obj,
                            tab="Flux Tangential", props=[
                                {"Name": "Name", "Value": args.boundary_name or "FluxTangent1"}])
    except Exception:
        pass  # skip if not applicable
    # Symmetry (optional): divide by pole pairs
    if args.symmetry_mode:
        rotor_obj = (args.rotor_name + "_outer") if args.maxwell_type == "2D" else (args.rotor_name or "Rotor")
        try:
            maxwell.assign_symmetry(
                assignment=[rotor_obj],
                symmetry_name=args.symmetry_name or "Symmetry1",
                is_odd=args.symmetry_odd,
            )
        except Exception:
            pass  # skip symmetry if object selection fails

    # Rotation motion on rotor (2D Transient / Magnetodynamic only)
    if args.assign_motion:
        maxwell.assign_rotate_motion(
            assignment=args.rotor_name or "Rotor",
            axis=args.rotation_axis,
            angular_velocity=args.angular_velocity,
            start_position=args.start_angle,
            has_rotation_limits=False,
        )


# ---------------------------------------------------------------------------
# new-motor-project: create a simple motor skeleton
# ---------------------------------------------------------------------------

def cmd_new_motor_project(args: argparse.Namespace) -> int:
    """Create a minimal motor project: stator + rotor cylinders,
    winding coil assignment, rotation boundary, magnetostatic or transient setup.
    """
    project_path = Path(args.project).expanduser().resolve()
    _ensure_parent_dir(project_path)

    print(f"Creating motor project: {project_path}")

    with _build_maxwell_context(args) as maxwell:
        maxwell.solution_type = args.solution_type

        # --- Variables ---
        _setup_motor_variables(maxwell, args)

        # --- Geometry: stator outer cylinder + rotor inner cylinder ---
        stator_name = args.stator_name or "Stator"
        rotor_name = args.rotor_name or "Rotor"
        airgap_name = args.airgap_name or "AirGap"

        if args.maxwell_type == "2D":
            # 2D: concentric circles — outer stator, inner rotor, airgap region
            # The circles are drawn in order; Maxwell boolean merge handles overlaps.
            # We create three circles: stator ring (outer), airgap ring, rotor (inner).
            # The airgap circle fills the gap between rotor OD and stator OD.
            stator_od_half = float(args.stator_od.replace("mm", "")) / 2.0
            rotor_od_half = float(args.rotor_od.replace("mm", "")) / 2.0
            airgap_od_half = (stator_od_half + rotor_od_half) / 2.0

            # Outer circle: stator ring
            maxwell.modeler.create_circle(
                origin=[0, 0],
                radius=stator_od_half,
                name=stator_name + "_outer",
                material=args.stator_material,
            )
            # Middle circle: airgap region (will be merged or overridden by material)
            maxwell.modeler.create_circle(
                origin=[0, 0],
                radius=airgap_od_half,
                name=airgap_name + "_outer",
                material="vacuum",
            )
            # Inner circle: rotor
            maxwell.modeler.create_circle(
                origin=[0, 0],
                radius=rotor_od_half,
                name=rotor_name + "_outer",
                material=args.rotor_material,
            )
        else:
            # 3D: cylinders
            maxwell.modeler.create_cylinder(
                axis_start=[0, 0, 0],
                axis_end=[0, 0, float(args.stack_length.replace("mm", "")) * 1e-3],
                radius=float(args.stator_od.replace("mm", "")) / 2000.0,
                name=stator_name,
                material=args.stator_material,
            )
            maxwell.modeler.create_cylinder(
                axis_start=[0, 0, 0],
                axis_end=[0, 0, float(args.stack_length.replace("mm", "")) * 1e-3],
                radius=float(args.rotor_od.replace("mm", "")) / 2000.0,
                name=rotor_name,
                material=args.rotor_material,
            )

        # --- Material override for regions ---
        # In 2D mode, object names have "_outer" suffix; in 3D mode they match stator_name/rotor_name
        stator_obj = stator_name + "_outer" if args.maxwell_type == "2D" else stator_name
        rotor_obj = rotor_name + "_outer" if args.maxwell_type == "2D" else rotor_name
        maxwell.assign_material(assignment=stator_obj, material=args.stator_material)
        maxwell.assign_material(assignment=rotor_obj, material=args.rotor_material)

        # --- Boundary: flux-tangential on stator outer ---
        stator_obj = stator_name + "_outer" if args.maxwell_type == "2D" else stator_name
        try:
            oedt = maxwell.modeler.oeditor
            oedt.ChangeProperty(operation="assignfluxtangential", scope=stator_obj,
                                tab="Flux Tangential", props=[
                                    {"Name": "Name", "Value": args.boundary_name or "FluxTangent1"}])
        except Exception:
            pass  # skip if not applicable
    # Symmetry (optional): divide by pole pairs
    if args.symmetry_mode:
        rotor_obj = rotor_name + "_outer" if args.maxwell_type == "2D" else rotor_name
        try:
            maxwell.assign_symmetry(
                assignment=[rotor_obj],
                symmetry_name=args.symmetry_name or "Symmetry1",
                is_odd=args.symmetry_odd,
            )
        except Exception:
            pass  # skip symmetry if object selection fails

        # --- Winding assignment (for 2D Transient / Magnetodynamic) ---
        if args.winding_type:
            # Create a coil terminal on the rotor
            coil_name = maxwell.assign_coil(
                assignment=[rotor_name + "_outer" if args.maxwell_type == "2D" else rotor_name],
                conductors_number=args.coil_conductors,
                polarity=args.coil_polarity,
                name=args.coil_name,
            )
            # Create winding from coil
            winding = maxwell.assign_winding(
                assignment=None,
                winding_type=args.winding_type,
                current=args.winding_current,
                voltage=args.winding_voltage,
                resistance=args.winding_resistance,
                phase=args.winding_phase,
                name=args.winding_name,
            )
            if winding and coil_name:
                maxwell.add_winding_coils(
                    assignment=args.winding_name or "Winding1",
                    coils=[coil_name.name if hasattr(coil_name, "name") else str(coil_name)],
                )

        # --- Setup ---
        setup = maxwell.create_setup(
            name=args.setup_name,
            setup_type=args.setup_type,  # "Magnetostatic" or "Transient"
            MaximumPasses=args.max_passes,
            MinPasses=args.min_passes,
            PercentError=args.percent_error,
            StopTime=args.stop_time,  # for Transient
            TimeStep=args.time_step,
        )

        # --- Motion parameters (after setup creation — required for Transient) ---
        rotor_obj = rotor_name + "_outer" if args.maxwell_type == "2D" else rotor_name
        if args.angular_velocity:
            try:
                maxwell.assign_rotate_motion(
                    assignment=rotor_obj,
                    axis=args.rotation_axis,
                    angular_velocity=str(args.angular_velocity),
                    start_position=args.start_angle,
                    has_rotation_limits=not args.assign_motion,
                )
                print(f"Rotation assigned to {rotor_obj}: {args.angular_velocity}")
            except Exception as e:
                print(f"Rotation assign note: {e}")
            # Also set angular velocity in setup
            try:
                setup.change_property(
                    aedt_object=setup.name if hasattr(setup, "name") else args.setup_name,
                    tab_name="Analysis",
                    property_object="Setup",
                    property_name="AngularVelocity",
                    property_value=str(args.angular_velocity),
                )
            except Exception as e:
                print(f"Setup AngularVelocity note: {e}")

        # --- Solve ---
        if args.solve:
            print("Solving motor ...")
            success = maxwell.analyze(setup=args.setup_name)
            if not success:
                raise RuntimeError("Motor solve failed.")
            print("Motor solve complete.")

        # --- Export: torque, force, results ---
        if args.export_torque_csv:
            output_path = Path(args.export_torque_csv).expanduser().resolve()
            _ensure_parent_dir(output_path)
            # Export parametric results (includes torque vs. time/angle)
            maxwell.export_parametric_results(
                setup=args.setup_name,
                output_file=str(output_path),
                export_units=True,
            )
            print(f"Exported torque/force data: {output_path}")

        if args.export_results:
            output_path = Path(args.export_results).expanduser().resolve()
            _ensure_parent_dir(output_path)
            maxwell.export_results(export_folder=str(output_path))
            print(f"Exported field results to: {output_path}")

        # --- Save ---
        saved = maxwell.save_project(file_name=str(project_path), overwrite=True)
        if not saved:
            raise RuntimeError(f"Failed to save motor project to {project_path}")

    print(f"Created motor project: {project_path}")
    return 0


# ---------------------------------------------------------------------------
# analyze-motor: re-solve motor project with new parameters
# ---------------------------------------------------------------------------

def cmd_analyze_motor(args: argparse.Namespace) -> int:
    """Open a motor project, modify variables, re-solve, export torque/power."""
    project_path = Path(args.project).expanduser().resolve()
    if not project_path.exists():
        raise FileNotFoundError(f"Project file does not exist: {project_path}")

    print(f"Analyzing motor project: {project_path}")

    with _build_maxwell_context(args) as maxwell:
        # Update motor variables
        motor_vars = {
            "StatorOD": args.stator_od,
            "RotorOD": args.rotor_od,
            "StackLength": args.stack_length,
            "AirGap": args.air_gap,
            "PolePairs": str(args.pole_pairs) if args.pole_pairs else None,
            "AngularVelocity": args.angular_velocity,
        }
        for name, value in motor_vars.items():
            if value is not None:
                maxwell[name] = str(value)
        for name, value in args.set_variable.items():
            maxwell[name] = value

        # Solve
        print("Solving ...")
        success = maxwell.analyze(setup=args.setup_name)
        if not success:
            raise RuntimeError("Motor solve failed.")
        print("Solve complete.")

        # Export
        if args.export_torque_csv:
            output_path = Path(args.export_torque_csv).expanduser().resolve()
            _ensure_parent_dir(output_path)
            maxwell.export_parametric_results(
                setup=args.setup_name,
                output_file=str(output_path),
                export_units=True,
            )
            print(f"Exported torque/force data: {output_path}")

        if args.export_results:
            output_path = Path(args.export_results).expanduser().resolve()
            _ensure_parent_dir(output_path)
            maxwell.export_results(export_folder=str(output_path))
            print(f"Exported results to: {output_path}")

        saved = maxwell.save_project(file_name=str(project_path), overwrite=True)
        if not saved:
            raise RuntimeError(f"Failed to save project to {project_path}")

    print(f"Analyzed motor project: {project_path}")
    return 0


# ---------------------------------------------------------------------------
# new-rmxprt-project: quick analytical motor analysis
# ---------------------------------------------------------------------------

def cmd_new_rmxprt_project(args: argparse.Namespace) -> int:
    """Create a quick motor analysis using RMxprt (analytical motor tool).

    RMxprt is a 2D equivalent-circuit motor design tool built into AEDT.
    It does NOT build 3D geometry — it uses analytical equations for
    torque, efficiency, power, etc.  Ideal for rapid concept screening.
    """
    project_path = Path(args.project).expanduser().resolve()
    _ensure_parent_dir(project_path)

    from ansys.aedt.core import Rmxprt  # type: ignore

    print(f"Creating RMxprt project: {project_path}")

    app = Rmxprt(
        project=str(project_path),
        design=args.rmxprt_design or "RMxprtDesign1",
        version=args.version,
        new_desktop=True,
        close_on_exit=True,
        student_version=True,
    )

    # Set motor topology
    app["Topology"] = args.rmxprt_topology  # "BLDC", "PMSM", "IM", "SRM", etc.

    # Set key motor parameters as variables
    motor_params = {
        "StatorOuterRadius": args.stator_od,
        "StatorInnerRadius": args.rotor_od,
        "StackLength": args.stack_length,
        "AirGapLength": args.air_gap,
        "NumberPolePairs": str(args.pole_pairs),
        "NumberStatorSlots": str(args.stator_slots),
        "NumberRotorSlots": str(args.rotor_slots),
        "RatedSpeed": args.angular_velocity or "3000rpm",
        "RatedPower": args.rated_power or "1kW",
        "RatedVoltage": args.rated_voltage or "400V",
        "RotorMaterial": args.rotor_material,
        "StatorMaterial": args.stator_material,
    }
    for name, value in motor_params.items():
        if value is not None:
            app[name] = str(value)

    # User overrides
    for name, value in args.set_variable.items():
        app[name] = value

    # Solve
    if args.solve:
        print("Solving RMxprt ...")
        app.analyze()
        print("RMxprt solve complete.")

    # Export results
    if args.export_results:
        output_path = Path(args.export_results).expanduser().resolve()
        _ensure_parent_dir(output_path)
        app.export_variables_to_csv(output_file=str(output_path))
        print(f"Exported motor parameters: {output_path}")

    saved = app.save_project(file_name=str(project_path), overwrite=True)
    if not saved:
        raise RuntimeError(f"Failed to save RMxprt project.")

    print(f"Created RMxprt project: {project_path}")
    return 0


# ===========================================================================
# Argument parser
# ===========================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ANSYS Maxwell workflows built on PyAEDT for motor and electromagnetic automation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- doctor ----
    doctor = subparsers.add_parser("doctor", help="Inspect Python, PyAEDT, and AEDT environment.")
    doctor.add_argument("--json", action="store_true", help="JSON output.")
    doctor.set_defaults(func=cmd_doctor)

    # ---- new-project ----
    newp = subparsers.add_parser("new-project", help="Create minimal Maxwell project.")
    _add_project_args(newp)
    newp.set_defaults(func=cmd_new_project)

    # ---- analyze-project ----
    analyze = subparsers.add_parser("analyze-project", help="Re-solve existing Maxwell project.")
    _add_project_args(analyze)
    analyze.set_defaults(func=cmd_analyze_project)

    # ---- list-projects ----
    listp = subparsers.add_parser(
        "list-projects", help="List designs, setups, variables of an existing project (read-only)."
    )
    listp.add_argument("--project", required=True, help="Existing .aedt file.")
    listp.add_argument("--design", default=None)
    listp.add_argument("--maxwell-type", default="3D", choices=["3D", "2D"])
    listp.add_argument("--version", default=None)
    listp.add_argument("--non-graphical", action="store_true")
    listp.set_defaults(func=cmd_list_projects)

    # ---- new-motor-project ----
    motorp = subparsers.add_parser(
        "new-motor-project",
        help="Create a simple motor project (stator+rotor+winding+motion+setup).",
    )
    _add_motor_args(motorp)
    motorp.set_defaults(func=cmd_new_motor_project)

    # ---- analyze-motor ----
    analyzemo = subparsers.add_parser(
        "analyze-motor", help="Re-solve motor project with new parameters."
    )
    _add_motor_args(analyzemo)
    analyzemo.set_defaults(func=cmd_analyze_motor)

    # ---- new-rmxprt-project ----
    rmxprt_p = subparsers.add_parser(
        "new-rmxprt-project",
        help="Create quick analytical motor analysis using RMxprt.",
    )
    _add_rmxprt_args(rmxprt_p)
    rmxprt_p.set_defaults(func=cmd_new_rmxprt_project)

    return parser


# ---------------------------------------------------------------------------
# Argument group helpers
# ---------------------------------------------------------------------------

def _add_project_args(sub):
    """Common arguments for new-project and analyze-project."""
    sub.add_argument("--project", required=True, help="Output .aedt file path.")
    sub.add_argument("--design", default="Maxwell3DDesign1", help="Design name.")
    sub.add_argument("--maxwell-type", default="3D", choices=["3D", "2D"])
    sub.add_argument("--version", default=None, help="AEDT version, e.g. 2024.2.")
    sub.add_argument("--non-graphical", action="store_true")
    sub.add_argument("--set-variable", action="append", default=[], help="NAME=VALUE (repeatable).")
    # Geometry
    sub.add_argument("--geom", default="box",
                     choices=["box", "sphere", "cylinder", "rectangle", "circle", "arc"])
    sub.add_argument("--geom-name", default="Object1")
    sub.add_argument("--material", default="vacuum")
    sub.add_argument("--origin", type=_parse_triplet, default=["0mm", "0mm", "0mm"])
    sub.add_argument("--size", type=_parse_triplet, default=["10mm", "10mm", "1mm"])
    sub.add_argument("--radius", default="5mm")
    sub.add_argument("--length", default="10mm")
    sub.add_argument("--start-angle", default="0")
    sub.add_argument("--end-angle", default="90")
    # Boundaries
    sub.add_argument("--assign-flux-tangential", action="store_true",
                     help="Assign flux-tangential boundary (motor stator OD).")
    sub.add_argument("--flux-tangential-objects", default=None)
    sub.add_argument("--flux-tangential-name", default=None)
    sub.add_argument("--assign-symmetry", action="store_true")
    sub.add_argument("--symmetry-objects", default=None)
    sub.add_argument("--symmetry-name", default="Symmetry1")
    sub.add_argument("--symmetry-odd", default=True, type=bool)
    sub.add_argument("--assign-zero-h", action="store_true")
    sub.add_argument("--zero-h-objects", default=None)
    sub.add_argument("--assign-radiation", action="store_true")
    sub.add_argument("--radiation-name", default="Radiation1")
    sub.add_argument("--assign-insulating", action="store_true")
    sub.add_argument("--assign-resistive-sheet", action="store_true")
    sub.add_argument("--resistive-sheet-objects", default=None)
    sub.add_argument("--resistive-resistance", default="1ohm")
    # Setup
    sub.add_argument("--setup-name", default="Setup1", help="Setup name.")
    sub.add_argument("--setup-type", default=None,
                     help='Setup type string. Maxwell examples: "Magnetostatic", "Transient",'
                          '"Eddy Current", "Electrostatic", "Magnetodynamic".')
    sub.add_argument("--max-passes", type=int, default=20)
    sub.add_argument("--min-passes", type=int, default=2)
    sub.add_argument("--percent-error", default="2.0")
    sub.add_argument("--percent-refinement", default="30")
    # Sweep
    sub.add_argument("--sweep-name", default=None)
    sub.add_argument("--sweep-units", default="GHz")
    sub.add_argument("--sweep-start", type=float, default=1.0)
    sub.add_argument("--sweep-stop", type=float, default=2.0)
    sub.add_argument("--sweep-count", type=int, default=101)
    # Solve
    sub.add_argument("--solve", action="store_true")
    # Export
    sub.add_argument("--export-touchstone", default=None, help="Output .sNp file path.")
    sub.add_argument("--export-parametric-results", default=None, help="Output CSV for parametric data.")


def _add_motor_args(sub):
    """Arguments shared by new-motor-project and analyze-motor."""
    sub.add_argument("--project", required=True, help=".aedt file path.")
    sub.add_argument("--design", default="Maxwell3DDesign1")
    sub.add_argument("--maxwell-type", default="2D", choices=["3D", "2D"],
                     help="2D recommended for motor design.")
    sub.add_argument("--version", default=None)
    sub.add_argument("--non-graphical", action="store_true")
    sub.add_argument("--set-variable", action="append", default=[], help="NAME=VALUE")

    # Motor geometry
    sub.add_argument("--stator-od", default="100mm", help="Stator outer diameter.")
    sub.add_argument("--rotor-od", default="60mm", help="Rotor outer diameter.")
    sub.add_argument("--stack-length", default="80mm", help="Magnetic stack length.")
    sub.add_argument("--air-gap", default="0.5mm", help="Air gap length.")
    sub.add_argument("--stator-material", default="M19_24G", help="Stator lamination material.")
    sub.add_argument("--rotor-material", default="M19_24G", help="Rotor core material.")
    sub.add_argument("--stator-name", default="Stator")
    sub.add_argument("--rotor-name", default="Rotor")
    sub.add_argument("--airgap-name", default="AirGap")

    # Motor winding & electrical
    sub.add_argument("--pole-pairs", type=int, default=4)
    sub.add_argument("--stator-slots", type=int, default=36)
    sub.add_argument("--rotor-slots", type=int, default=40)
    sub.add_argument("--slot-depth", default="15mm")
    sub.add_argument("--rotor-thickness", default="20mm")
    sub.add_argument("--solution-type", default="Transient",
                     help="Maxwell solution type: Transient, Magnetostatic, Eddy Current, Magnetodynamic.")
    # Winding
    sub.add_argument("--winding-type", default="Current",
                     help="Winding type: Current, Voltage, Impedance.")
    sub.add_argument("--winding-current", type=float, default=1.0)
    sub.add_argument("--winding-voltage", type=float, default=0)
    sub.add_argument("--winding-resistance", type=float, default=0)
    sub.add_argument("--winding-phase", type=float, default=0)
    sub.add_argument("--winding-name", default="Winding1")
    sub.add_argument("--coil-conductors", type=int, default=10)
    sub.add_argument("--coil-polarity", default="Positive")
    sub.add_argument("--coil-name", default=None)

    # Boundaries
    sub.add_argument("--boundary-name", default="FluxTangent1")
    sub.add_argument("--assign-motion", action="store_true", help="Assign rotation to rotor.")
    sub.add_argument("--rotation-axis", default="Z", help="Rotation axis (Z or -Z).")
    sub.add_argument("--angular-velocity", default="1500rpm", help="Angular velocity.")
    sub.add_argument("--start-angle", default=0, type=float, help="Initial mechanical angle (deg).")
    sub.add_argument("--symmetry-mode", action="store_true", help="Apply symmetry boundary.")
    sub.add_argument("--symmetry-odd", default=True, type=bool)
    sub.add_argument("--symmetry-name", default="Symmetry1")

    # Setup
    sub.add_argument("--setup-name", default="Setup1")
    sub.add_argument("--setup-type", default="Transient",
                     help="Magnetostatic, Transient, Eddy Current, Magnetodynamic.")
    sub.add_argument("--max-passes", type=int, default=20)
    sub.add_argument("--min-passes", type=int, default=2)
    sub.add_argument("--percent-error", default="0.1")
    sub.add_argument("--stop-time", default="0.1s", help="Transient stop time.")
    sub.add_argument("--time-step", default="0.0001s", help="Transient time step.")

    # Solve & Export
    sub.add_argument("--solve", action="store_true")
    sub.add_argument("--export-torque-csv", default=None, help="Output CSV for torque/force data.")
    sub.add_argument("--export-results", default=None, help="Export field results folder.")


def _add_rmxprt_args(sub):
    """Arguments for the RMxprt analytical motor tool."""
    sub.add_argument("--project", required=True, help=".aedt file path.")
    sub.add_argument("--rmxprt-design", default="RMxprtDesign1")
    sub.add_argument("--version", default=None)
    sub.add_argument("--set-variable", action="append", default=[], help="NAME=VALUE")
    # Motor topology
    sub.add_argument("--rmxprt-topology", default="BLDC",
                     choices=["BLDC", "PMSM", "IM", "SRM", "LSSM", "ASSM", "PMDC", "DCM", "CPSM", "NSSM"],
                     help="Motor topology type.")
    # Geometry
    sub.add_argument("--stator-od", default="100mm")
    sub.add_argument("--rotor-od", default="60mm")
    sub.add_argument("--stack-length", default="80mm")
    sub.add_argument("--air-gap", default="0.5mm")
    sub.add_argument("--stator-material", default="M19_24G")
    sub.add_argument("--rotor-material", default="M19_24G")
    # Electrical
    sub.add_argument("--pole-pairs", type=int, default=4)
    sub.add_argument("--stator-slots", type=int, default=36)
    sub.add_argument("--rotor-slots", type=int, default=40)
    sub.add_argument("--angular-velocity", default="3000rpm")
    sub.add_argument("--rated-power", default="1kW")
    sub.add_argument("--rated-voltage", default="400V")
    # Solve & Export
    sub.add_argument("--solve", action="store_true")
    sub.add_argument("--export-results", default=None, help="Output CSV for motor parameters.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args) or 0)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
