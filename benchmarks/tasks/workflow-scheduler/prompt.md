Implement the deterministic workflow scheduling engine described in `context/context.md`. Build a modular Python package under `submission/flowbench/` and provide the CLI entry point `python -m flowbench INPUT.json --output OUTPUT.json`. Run it on `inputs/workflows.json` and save the result to `submission/schedules.json`. The hidden evaluator will also run additional workflows and invalid inputs. Match every validation, retry, dependency, ordering, and output rule in the context contract.

## Fixed task package

Read every file listed in `context_files` in `task.json`. Work from this task workspace, use relative paths, and write deliverables under `submission/`.
