# O que é este código

Script python que gerencia um inventário de máquinas no SCVMM, com base em um arquivo de configuração YAML.

![Tests](https://github.com/MP-ES/vmm_manager/workflows/Tests/badge.svg)

## Pré-requisitos

É necessário instalar o OpenSSH na máquina Windows que será utilizada para gerenciar o inventário (**VMM_SERVIDOR_ACESSO**). Também é necessário executar o comando `set-executionpolicy unrestricted` no PowerShell, com poderes administrativos.

### Instalação e configuração do python-poetry

Execute os comandos a seguir:

```shell
# instalar o poetry
curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
echo 'source $HOME/.poetry/env' >>~/.bashrc

# Configurar autocomplete
# Bash
poetry completions bash | sudo tee /etc/bash_completion.d/poetry.bash-completion
```

## Como usar

```shell
poetry run python -m vmm_manager -h
```

## Comandos para DEV

```shell
# Instalando dependências
poetry install

# Habilitando shell
poetry shell

# Instalando uma dependência específica
poetry add <pacote> [--dev]

# Executar lint
pylint tests/* vmm_manager/*

# Executar testes
python -m pytest -v
```

## Referências

- [Virtual Machine Manager](https://docs.microsoft.com/en-us/powershell/module/virtualmachinemanager/?view=systemcenter-ps-2019)
