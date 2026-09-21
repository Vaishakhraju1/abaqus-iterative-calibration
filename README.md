# Abaqus iterative calibration

A generalised example of a closed-loop CAE workflow: update Young's modulus, run an analysis, read nodal displacement from the ODB and repeat until a target response is reached.

Adapted and refactored from research automation scripts. The public version replaces project geometry, node identifiers, measured targets and local paths with a synthetic two-node axial bar. It adds an explicit parameter marker, instance-qualified node lookup, bracketed bisection, an evaluation limit and separate files for each evaluation. No third-party optimisation code or original research models/data are included.

## Quick demonstration without Abaqus

Requires Python 3.8 or newer and only the standard library. Run from this repository:

```sh
python run_calibration.py --mode demo
python -m unittest discover -s tests -v
```

Demo mode uses the analytical axial-bar relationship `u = F L / (A E)`. It **does not run Abaqus** or validate the solver adapter. The synthetic example uses F=1 N, L=10 mm and A=1 mm². The target relative displacement is 0.005 mm, so the expected modulus is 2000 MPa. With the default bracket [1000, 3000] MPa, the analytical demo converges in three evaluations.

## Run with Abaqus

Use an installed, licensed Abaqus/CAE release with Python 3 support, from the repository directory:

```sh
abaqus cae noGUI=run_calibration.py -- --mode abaqus
```

This command submits actual solver jobs. Each job must report COMPLETED before its ODB is read. The ODB is opened read-only, the requested step must reach its end time and the file is closed after extraction. Each run gets a fresh directory under `runs/`, containing the template snapshot, `run.json`, `history.csv` and a separate folder per evaluation. Existing output directories are rejected; no previous job files are deleted. Maximum evaluations bounds the number of jobs, not their runtime; licensing waits and long analyses may still require manual interruption.

## Response definition

The calibrated response is **norm(U_A − U_B)**, the magnitude of the difference between two nodal displacement vectors. It is neither the deformed separation of the nodes nor the change in their initial separation. Each node is identified by instance name and label. This distinction matters when adapting the example to a different engineering target.

## Adapting a model

Supply a self-contained input template with exactly one `{{YOUNGS_MODULUS}}` marker at the intended elastic modulus. Use `--template`, `--instance-a`, `--node-a`, `--instance-b`, `--node-b`, `--step`, `--lower`, `--upper`, `--target` and `--tolerance` as appropriate. Input coordinates and output displacements must use a consistent coordinate system. Auxiliary include files and user subroutines are not staged by this example. Demo mode always uses the bundled analytical bar and rejects custom templates.

Bisection requires responses at the parameter bounds to bracket the target and assumes continuity. A monotonic response is recommended. This is a single-parameter demonstration, not a general inverse solver; validate identifiability, mesh sensitivity, constitutive assumptions and units for the actual model.

## Validation status

The pure-Python controller, node selection and template rendering are covered by standalone tests. The analytical demonstration is runnable without Abaqus. The supplied Abaqus input deck and solver adapter have **not been executed in Abaqus during publication** and need validation in the target installation.

API references: [Abaqus job submission and completion](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKERRefMap/simaker-c-jobpyc.htm), [ODB field access example](https://docs.software.vt.edu/abaqusv2025/English/SIMACAECMDRefMap/simacmd-c-odbintroexafieldoppyc.htm).
