# vmm-manager

Script python que gerencia recursos no System Center Virtual Machine Manager (SCVMM), de forma declarativa, com base em um arquivo de configuração YAML.

![License](https://img.shields.io/github/license/MP-ES/vmm_manager.svg)
![Tests](https://github.com/MP-ES/vmm_manager/workflows/Tests/badge.svg)
![Release](https://github.com/MP-ES/vmm_manager/workflows/Release/badge.svg)
![Python](https://img.shields.io/pypi/pyversions/vmm-manager.svg)
![PyPI](http://img.shields.io/pypi/v/vmm-manager.svg)

## Pré-requisitos

É necessário ter uma máquina Windows, que servirá como ponto de acesso ao SCVMM, com as seguintes ferramentas:

- OpenSSH
- Módulo PowerShell do SCVMM (**virtualmachinemanager**), geralmente instalado junto com o Console do Virtual Machine Manager (VMM)
  
Nessa máquina, também é necessário executar o comando PowerShell `set-executionpolicy unrestricted`, com poderes administrativos.

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

```yaml
agrupamento: vmm_manager_test
nuvem: "developer"
imagem_padrao: "vm_linux"
qtde_cpu_padrao: 1
qtde_ram_mb_padrao: 512
redes_padrao:
  - nome: "vlan1"
vms:
  - nome: VMM_TEST1
    descricao: "Test VM"
    redes:
      - nome: "vlan1"
      - nome: "vlan2"
    regiao: A
  - nome: VMM_TEST2
    regiao: B
  - nome: VMM_TEST3
```

## Desenvolvimento

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
pylint tests/* vmm_manager/*

# Executar testes
python -m pytest -v
```

## Referências

- [Virtual Machine Manager](https://docs.microsoft.com/en-us/powershell/module/virtualmachinemanager/?view=systemcenter-ps-2019)
- [Python-Poetry](https://python-poetry.org/)
