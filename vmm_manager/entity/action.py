"""
Action entity.
"""
import json

from yamlable import YamlAble, yaml_info

from vmm_manager.infra.command import Command
from vmm_manager.util.config import (FIELD_GROUP, FIELD_ID, FIELD_IMAGE,
                                     FIELD_NETWORK_DEFAULT, FIELD_REGION)


@yaml_info(yaml_tag_ns='scvmm_manager')
class Action(YamlAble):
    ACAO_CRIAR_VM = 'create_vm'
    ACAO_EXCLUIR_VM = 'delete_vm'
    ACAO_EXCLUIR_DISCO_VM = 'delete_vm_disk'

    RESOURCE_IDENTIFIER_NAME = 'vm_name'
    RESOURCE_IDENTIFIER_ID = 'vm_id'

    def __init__(self, command, **kwargs):
        # Validate if the args contain the resource identifier
        if (
            'args' not in kwargs  # passed by Yamlable
            and Action.RESOURCE_IDENTIFIER_NAME not in kwargs
            and Action.RESOURCE_IDENTIFIER_ID not in kwargs
        ):
            raise ValueError(
                f'The args must contain the resource identifier: '
                f'{Action.RESOURCE_IDENTIFIER_NAME} or {Action.RESOURCE_IDENTIFIER_ID}.'
            )

        self.command = command
        self.args = kwargs

        self.__status_execucao = None
        self.__retorno_execucao = None
        self.__status_execucao_job = None

    def executar(self, group, cloud, servidor_acesso, guid):
        cmd = Command(self.command,
                      group=group,
                      field_group=FIELD_GROUP[0],
                      field_id=FIELD_ID[0],
                      field_region=FIELD_REGION[0],
                      cloud=cloud,
                      guid=guid,
                      vmm_server=servidor_acesso.vmm_server
                      )
        cmd.args.update(self.args)

        status, retorno = cmd.executar(servidor_acesso)

        self.__status_execucao = status
        self.__retorno_execucao = json.loads(
            retorno) if self.__status_execucao else retorno

        return self.__status_execucao, self.__retorno_execucao

    def informar_status_execucao_job(self, status):
        self.__status_execucao_job = status

    def is_criacao_vm(self):
        return self.command == Action.ACAO_CRIAR_VM

    def is_bloqueante(self):
        return (self.is_criacao_vm()
                or self.command == Action.ACAO_EXCLUIR_VM
                or self.command == Action.ACAO_EXCLUIR_DISCO_VM)

    def is_same_resource(self, other):
        if (self.RESOURCE_IDENTIFIER_NAME in self.args
                and self.RESOURCE_IDENTIFIER_NAME in other.args):
            return (self.args[self.RESOURCE_IDENTIFIER_NAME]
                    == other.args[self.RESOURCE_IDENTIFIER_NAME])

        if (self.RESOURCE_IDENTIFIER_ID in self.args
                and self.RESOURCE_IDENTIFIER_ID in other.args):
            return self.args[self.RESOURCE_IDENTIFIER_ID] == other.args[self.RESOURCE_IDENTIFIER_ID]

        return False

    def has_cmd_pos_execucao(self):
        return self.is_criacao_vm()

    def was_executada_com_sucesso(self):
        return (self.__status_execucao and
                self.__retorno_execucao.get('Status') == 'OK'
                and (self.__status_execucao_job is None or
                     self.__status_execucao_job))

    def get_resultado_execucao(self):
        if self.__status_execucao is None:
            raise AttributeError('Action not executed.')

        if self.__status_execucao:
            return self.__retorno_execucao

        return {'Msgs': self.__retorno_execucao}

    def get_cmd_pos_execucao(self, group, servidor_acesso):
        if self.is_criacao_vm():
            cmd = Command(
                'create_vm_pos',
                description=f"Add VMM tags for {self.args['vm_name']}",
                vmm_server=servidor_acesso.vmm_server,
                field_group=FIELD_GROUP[0],
                field_id=FIELD_ID[0],
                field_image=FIELD_IMAGE[0],
                field_region=FIELD_REGION[0],
                field_network_default=FIELD_NETWORK_DEFAULT[0],
                group=group
            )
            cmd.args.update(self.args)

            return cmd

        raise AttributeError(
            f'Action "{self.command}" does not have a post execution command.')

    def get_str_impressao_inline(self):
        cmd_args = ', '.join([f'{arg}={value}'
                              for arg, value in self.args.items()])

        return f'{self.command} - [{cmd_args}]'

    def __eq__(self, other):
        return isinstance(other, Action) and (self.command == other.command
                                              and self.args == other.args)

    def __str__(self):
        return f'''
            command: {self.command}
            args: {self.args}
            '''

    def __to_yaml_dict__(self):
        return {
            'command': self.command,
            'args': self.args
        }
