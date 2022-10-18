# vmm-manager

Script python que gerencia recursos no System Center Virtual Machine Manager (SCVMM), de forma declarativa, com base em um arquivo de configuração YAML.

[![License](https://img.shields.io/github/license/MP-ES/vmm_manager.svg)](LICENSE)
[![Tests](https://github.com/MP-ES/vmm_manager/workflows/Tests/badge.svg)](https://github.com/MP-ES/vmm_manager/actions?query=workflow%3ATests)
[![Release](https://github.com/MP-ES/vmm_manager/workflows/Release/badge.svg)](https://github.com/MP-ES/vmm_manager/actions?query=workflow%3ARelease)
[![Python](https://img.shields.io/pypi/pyversions/vmm-manager.svg)](https://pypi.python.org/pypi/vmm-manager)
[![PyPI](http://img.shields.io/pypi/v/vmm-manager.svg)](https://pypi.python.org/pypi/vmm-manager)

## Pré-requisitos

É necessário ter uma máquina Windows, que servirá como ponto de acesso ao SCVMM, com as seguintes ferramentas:

- OpenSSH
- Módulo PowerShell do SCVMM (**virtualmachinemanager**), instalado junto com o Console do Virtual Machine Manager (VMM). Você também pode obtê-lo em <https://github.com/MP-ES/VirtualMachineManager-PowerShellModule>

## Instalação

```shell
pip install -U vmm-manager
```

## Uso

Para consultar as funções e os parâmetros disponíveis, utilize o comando:

```shell
vmm_manager -h
```

### Exemplo de arquivo de inventário

[inventario_exemplo.yaml](inventario_exemplo.yaml)

## Desenvolvimento

### Instalação e configuração do python-poetry

Execute os comandos a seguir:

```shell
# instalar o poetry
curl -sSL https://install.python-poetry.org | python3 -

# Configurar autocomplete
# Bash
poetry completions bash >> ~/.bash_completion
```

### Variáveis de ambiente

Defina as variáveis de ambiente de acordo com as instruções do arquivo **.env.default**. Você pode criar um arquivo **.env** e executar o comando `export $(cat .env | xargs)` para defini-las antes da execução do script.

### Como executar

```shell
# Carregando envs (opcional)
export $(cat .env | xargs)

# Instalando dependências
poetry install --no-root

# Executando script
poetry run python -m vmm_manager -h
```

### Comandos úteis para DEV

```shell
# Habilitar shell
poetry shell

# Incluir uma dependência
poetry add <pacote> [--dev]

# Executar lint
pylint --load-plugins pylint_quotes tests/* vmm_manager/*

# Executar testes
python -m pytest -vv

# listar virtualenvs
poetry env list

# Remover um virtualenv
poetry env remove <nome>
```

## Referências

- [Virtual Machine Manager](https://docs.microsoft.com/en-us/powershell/module/virtualmachinemanager/?view=systemcenter-ps-2019)
- [Poetry](https://python-poetry.org/)
