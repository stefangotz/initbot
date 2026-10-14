# Project Requirements

This file expresses requirements, invariants, and intended outcomes for this project.
Any abstraction level is fine, from workflows across to design choices down to implementation details.

The purpose is to document intent for two reasons:
- intent is sometimes difficult to infer from the implementation
- documented intent aides future maintenance

Yes, this is in progress and very incomplete and unstructured.

Requirement IDs are assigned randomly, e.g., via `seq 0 999999 | shuf | while read N && R="R${N}" && grep -E "\b${R}\b" ./requirements/requiremens.md > /dev/null; do true; done; echo "${R}"`

## Dependencies and Supply Chain

### R226113: Determinism and Reproducibility

With regard to the Python ecosystem, testing, and continuous integration, the project aims for all workflows to be fully defined by version-controlled project contents and independent of external factors.
That is: all workflows invoked on the same repository contents are intended to produce the same outputs or outcomes, regardless of when they are run or their execution environments.

The project strives to make use of best practices in the field and available technologies and tools to achieve those outcomes.
At the moment, those primarily revolve around pinning external artifacts by version and content hash wherever tooling allows to do so.

The execution environment beyond the Python ecosystem, testing, and continuous integration are out of scope.
For example, the project contents have no control over the shell binaries used to execute shell scripts (at least outside containers), the containerisation engine, or the operating system.
In those areas, the project relies on practical conventions, such as POSIX-ish shells and OSes and recent-ish Docker-like containerisation solutions, and assumes that developers and operators are responsible for the supply chain security of those components.

### R98665: Equivalence of Development and Production Environment

The project has several scenarios and environments for using project and external software artifacts.
The two main ones are development (including CI) and production (i.e., the container images the project generates and uses).

Those environments shall be equivalent in the versioning of their software supply chains.
They may differ in the amount of supply chain artifacts (such as production images not containing development tools), but where the same artifacts are in use, all environments shall use the same versions of those artifacts.

### R300734: uv

The project (currently) uses uv to manage the Python supply chain.
This includes the interpreter itself and dependencies.

The project uses a single uv version as defined in [tools/uv_version.sh](tools/uv_version.sh).
All workflows in the project shall make use of that version without explicitly restating it if possible.
The version information shall only be duplicated where necessary.

### R997031: Python Interpreter

The project uses a default Python version. as defined in [.python-version](.python-version).
All workflows in the project shall make use of that default version without explicitly restating it if possible.
The version information shall only be duplicated where necessary.

The project aims to remain compatible with all Python versions that have been released and haven't reached end of life.
The supported Python versions are referenced in several files throughout the code base.
Those files shall be kept in sync and shall be updated when a new version is released or a released version reaches end of life.
At any given time, the default Python version shall be the most recently released version.

Rationale:
The project aims to benefit from recent interpreter improvements.
However, it shall also be usable by users that are tied to a specific older maintained Python version.
