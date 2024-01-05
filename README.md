# vmm-manager

Python script that manages resources in the System Center Virtual Machine Manager (SCVMM), in a declarative way, based on a YAML configuration file.

[![License](https://img.shields.io/github/license/MP-ES/vmm_manager.svg)](LICENSE)
[![Integration](https://github.com/MP-ES/vmm_manager/workflows/Integration/badge.svg)](https://github.com/MP-ES/vmm_manager/actions?query=workflow%3AIntegration)
[![Release](https://github.com/MP-ES/vmm_manager/workflows/Release/badge.svg)](https://github.com/MP-ES/vmm_manager/actions?query=workflow%3ARelease)
[![Python](https://img.shields.io/pypi/pyversions/vmm-manager.svg)](https://pypi.python.org/pypi/vmm-manager)
[![PyPI](http://img.shields.io/pypi/v/vmm-manager.svg)](https://pypi.python.org/pypi/vmm-manager)

## Breaking changes

### 1.0.0

- The inventory file schema has completely changed. See the [**inventory_example.yaml**](inventory_example.yaml) file for more details.
- The command parameters were renamed to be more consistent.
- The API and inventory schema are now stable.

## Prerequisites

You need a Windows machine, which will serve as the access point to SCVMM, with the following tools:

- OpenSSH
- SCVMM's PowerShell Module (**virtualmachinemanager**), installed with the Virtual Machine Manager (VMM) Console. You can also get it at <https://github.com/MP-ES/VirtualMachineManager-PowerShellModule>

## Installation

```shell
pip install -U vmm-manager
```

## How to use

Use the command below to see the available options:

```shell
vmm_manager -h
```

### Environment variables

You can set environment variables to avoid passing the same parameters every time you run the script. See an example in the [**.env.default**](.env.default) file.

### Example of a inventory file

[inventory_example.yaml](inventory_example.yaml)

## Development

### Install Poetry

Run the following commands to install Poetry:

```shell
# install
curl -sSL https://install.python-poetry.org | python3 -

# auto-completion
# Bash
poetry completions bash >> ~/.bash_completion
```

### Environment variables (optional)

Use the **.env.default** file as a template to create a **.env** file with the environment variables needed to run the script. You can load them by running the command `export $(cat .env | xargs)` before executing the script.

### How to run

```shell
# Loading environment variables (optional)
export $(cat .env | xargs)

# Install dependencies
poetry install --no-root

# Run
poetry run python -m vmm_manager -h
```

### Helpful commands

```shell
# Poetry shell
poetry shell

# Add a dependency
poetry add <pacote> [--dev]

# Update dependencies
poetry update

# Run linting
flake8 . && isort --check-only --diff .

# Fix dependencies sorting
isort .

# Run tests
python -m pytest -vv

# List virtualenvs
poetry env list

# Remove a virtualenv
poetry env remove <name>
```

## References

- [Virtual Machine Manager](https://docs.microsoft.com/en-us/powershell/module/virtualmachinemanager/?view=systemcenter-ps-2019)
- [Poetry](https://python-poetry.org/)
