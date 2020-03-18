# O que é este código

Script python que gerencia um inventário de máquinas no SCVMM, com base em um arquivo de configuração YAML.

## Pré-requisitos

É necessário instalar o OpenSSH na máquina Windows que será utilizada para gerenciar o inventário (**VMM_SERVIDOR_ACESSO**). Também é necessário executar o comando `set-executionpolicy unrestricted` no PowerShell, com poderes administrativos.

## Como usar

```shell
pipenv run python vmm_manager.py -h
```

## Comandos para DEV

```shell
# Instalando dependências do pipenv
pipenv install --dev

# Habilitando shell
pipenv shell

# Instalando uma dependência específica
pipenv install <pacote> [--dev]

# Gerar requirements
pipenv lock -r > requirements.txt

# Executar lint
pylint app/* tests/* vmm_manager.py

# Executar testes
python -m pytest -v
```

## Referências

- [Virtual Machine Manager](https://docs.microsoft.com/en-us/powershell/module/virtualmachinemanager/?view=systemcenter-ps-2019)
