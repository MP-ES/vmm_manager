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
    principal: true
vms:
  - nome: VMM_TEST1
    descricao: "Test VM"
    redes:
      - nome: "vlan1"
        principal: true
      - nome: "vlan2"
    regiao: A
    discos_adicionais:
      - tipo: SCSI
        arquivo: "disk_var_dir"
        caminho: "C:\\Storage\\disk1"
        tamanho_mb: 1024
        tamanho_tipo: DynamicallyExpanding
  - nome: VMM_TEST2
    regiao: B
    ansible:
      - grupo: "web_server"
  - nome: VMM_TEST3
    ansible:
      - grupo: "database"
        vars:
          - nome: "data_dir"
            valor: "/mnt/data"
      - grupo: "load_balancer"
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
$HOME/.poetry/bin/poetry completions bash | sudo tee /etc/bash_completion.d/poetry.bash-completion
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
python -m pytest -vv
```

## Referências

- [Virtual Machine Manager](https://docs.microsoft.com/en-us/powershell/module/virtualmachinemanager/?view=systemcenter-ps-2019)
- [Poetry](https://python-poetry.org/)
