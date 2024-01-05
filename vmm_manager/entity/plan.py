"""
Execution plan entity.
"""
import os
import textwrap
import time
import uuid

import yaml
from yamlable import YamlAble, yaml_info

from vmm_manager.entity.action import Action
from vmm_manager.infra.command import Command
from vmm_manager.scvmm.scjob import SCJob
from vmm_manager.util.msgs import (formatar_msg_erro, imprimir_acao_corrente,
                                   imprimir_erro, imprimir_ok)


@yaml_info(yaml_tag_ns='scvmm_manager')
class Plan(YamlAble):
    ARQUIVO_PLANO_EXECUCAO = 'plan.yaml'
    ARQUIVO_LOG_ERROS = 'errors.log'

    @staticmethod
    def carregar_plano_execucao(execution_plan_file):
        try:
            with open(execution_plan_file, 'r', encoding='utf8') as file:
                plano_execucao = yaml.safe_load(file)
                return True, plano_execucao
        except (IOError, TypeError) as erro:
            return False, f"Error loading the plan '{execution_plan_file}'.\n{erro}"

    @staticmethod
    def excluir_arquivo():
        if os.path.exists(Plan.ARQUIVO_PLANO_EXECUCAO):
            os.remove(Plan.ARQUIVO_PLANO_EXECUCAO)

    @staticmethod
    def __excluir_arquivo_log_erros():
        if os.path.exists(Plan.ARQUIVO_LOG_ERROS):
            os.remove(Plan.ARQUIVO_LOG_ERROS)

    def __init__(self, group, cloud):
        self.group = group
        self.cloud = cloud
        self.actions = []
        self.interval_between_resources = 0

        self.__jobs_em_execucao = {}
        self.__guids_a_limpar = []
        self.__msgs_erros = ''

    def is_vazio(self):
        return not self.actions

    def gerar_arquivo(self):
        try:
            conteudo = yaml.safe_dump(self, default_flow_style=False)
            with open(Plan.ARQUIVO_PLANO_EXECUCAO, 'w', encoding='utf8') as arquivo_yaml:
                arquivo_yaml.write(conteudo)
        except IOError as erro:
            return False, f'Error generating file {Plan.ARQUIVO_PLANO_EXECUCAO}.\n{erro}'

        return True, conteudo

    def __executar_acoes(self, actions, servidor_acesso, ocultar_progresso):
        if not actions:
            return  # return early if there are no actions to execute

        # zerando jobs em execução
        self.__jobs_em_execucao = {}

        total_acoes = len(actions)
        for i in range(total_acoes):
            acao = actions[i]

            print(f'{textwrap.shorten(acao.get_str_impressao_inline(), 100)} => ',
                  end='', flush=True)

            # Caso específico de criação de vms
            guid = uuid.uuid4()
            if acao.is_criacao_vm():
                self.__guids_a_limpar.append(guid)

            acao.executar(self.group, self.cloud,
                          servidor_acesso, guid)

            # Tratando resultado
            if acao.was_executada_com_sucesso():
                guid = acao.get_resultado_execucao().get('Guid')
                if guid:
                    # Job em execução
                    self.__jobs_em_execucao[guid] = SCJob(
                        guid, acao)
                    print(f'[Started {guid}]')
                else:
                    # Comando já finalizado
                    imprimir_ok(ocultar_progresso)
            else:
                imprimir_erro(ocultar_progresso)
                self.__logar_erros_acao(
                    acao, acao.get_resultado_execucao().get('Msgs'))

            # If the action is not the last, check if we need to wait
            if i < total_acoes - 1:
                proxima_acao = actions[i + 1]

                if not acao.is_same_resource(proxima_acao) and self.interval_between_resources > 0:
                    print(
                        f'{textwrap.shorten(f"Waiting {self.interval_between_resources} seconds to start the next action", 100)} => ',  # noqa: E501
                        end='',
                        flush=True
                    )
                    time.sleep(self.interval_between_resources)
                    imprimir_ok(ocultar_progresso)

        # Monitorando jobs
        SCJob.monitore_jobs(self.__jobs_em_execucao, servidor_acesso)
        self.__coletar_resultado_jobs()

        # Ações pós execução
        print()
        self.__executar_cmds_finalizacao(
            actions, servidor_acesso, ocultar_progresso)

    def executar(self, servidor_acesso, ocultar_progresso, interval_between_resources=0):
        if self.is_vazio():
            return

        # update interval between resources
        if interval_between_resources >= 0:
            self.interval_between_resources = interval_between_resources

        print('\nApplied operations:')

        # actions bloqueantes primeiro
        acoes_bloqueantes = [
            acao for acao in self.actions if acao.is_bloqueante()]
        self.__executar_acoes(
            acoes_bloqueantes, servidor_acesso, ocultar_progresso)

        # demais ações, se não houve erro
        if not self.has_erro_execucao():
            acoes_nao_bloqueantes = [acao
                                     for acao in self.actions if not acao.is_bloqueante()]
            self.__executar_acoes(
                acoes_nao_bloqueantes, servidor_acesso, ocultar_progresso)

        # Ações de finalização
        self.__limpar_guids(servidor_acesso, ocultar_progresso)
        self.__processa_resultado_execucao()
        Plan.excluir_arquivo()

    def __executar_cmds_finalizacao(self, actions, servidor_acesso, ocultar_progresso):
        for acao in actions:
            if acao.was_executada_com_sucesso() and acao.has_cmd_pos_execucao():
                cmd = acao.get_cmd_pos_execucao(
                    self.group, servidor_acesso)

                imprimir_acao_corrente(cmd.description, ocultar_progresso)

                status, resultado = cmd.executar(servidor_acesso)

                if status:
                    imprimir_ok(ocultar_progresso)
                else:
                    imprimir_erro(ocultar_progresso)
                    self.__logar_erros_comando(cmd.description, resultado)

    def __limpar_guids(self, servidor_acesso, ocultar_progresso):
        if self.__guids_a_limpar:
            imprimir_acao_corrente(
                'Cleaning up temporary VMM objects', ocultar_progresso)

            cmd = Command(
                'clean_objects_after_vm_creation',
                vmm_server=servidor_acesso.vmm_server,
                guids=self.__guids_a_limpar
            )
            status, retorno = cmd.executar(servidor_acesso)

            if status:
                imprimir_ok(ocultar_progresso)
            else:
                imprimir_erro(ocultar_progresso)
                self.__logar_erros_comando(
                    'Clean up temporary VMM objects', retorno)

    def __processa_resultado_execucao(self):
        if self.has_erro_execucao():
            self.__gerar_arquivo_erros()
        else:
            Plan.__excluir_arquivo_log_erros()

    def imprimir_resultado_execucao(self):
        if self.has_erro_execucao():
            print(formatar_msg_erro(
                '\nSynchronization completed with errors. '
                f'More details in {Plan.ARQUIVO_LOG_ERROS}.'))
        else:
            print('\nSynchronization completed successfully.')

    def has_erro_execucao(self):
        return self.__msgs_erros

    def __coletar_resultado_jobs(self):
        if self.__jobs_em_execucao:
            for job in self.__jobs_em_execucao.values():
                if job.is_finalizado_com_erro():
                    print(formatar_msg_erro(
                        f'Process {job.vmm_id} finalized with error.'))
                    self.__logar_erros_acao(job.acao, job.resumo_erro)

    def __logar_erros_comando(self, command, erro):
        self.__msgs_erros += f'Error found in "{command}":\n{erro}\n\n'

    def __logar_erros_acao(self, acao, erro):
        self.__msgs_erros += f'Command:\n{acao.get_str_impressao_inline()}' \
            f'\n\nCaptured error:\n{erro}\n\n'

    def __gerar_arquivo_erros(self):
        try:
            with open(Plan.ARQUIVO_LOG_ERROS, 'w', encoding='utf8') as arquivo_erros:
                arquivo_erros.write(self.__msgs_erros)
        except IOError as erro:
            print(
                f'It was not possible to generate the error file ({Plan.ARQUIVO_LOG_ERROS}): '
                f'{erro}')

    def imprimir_acoes(self):
        for acao in self.actions:
            print(acao.get_str_impressao_inline())

    def __eq__(self, other):
        return isinstance(other, Plan) and (self.group == other.group
                                            and self.cloud == other.cloud
                                            and self.actions == other.actions)

    def __str__(self):
        return f'''
            group: {self.group}
            cloud: {self.cloud}
            actions: {','.join(str(acao) for acao in self.actions)}
            '''

    def __to_yaml_dict__(self):
        return {'group': self.group,
                'cloud': self.cloud,
                'actions': self.actions}

    @classmethod
    def __from_yaml_dict__(cls, dct, yaml_tag):
        plano_execucao = Plan(dct['group'], dct['cloud'])

        for acao_str in dct['actions']:
            acao = Action(acao_str.command, **acao_str.args['args'])
            plano_execucao.actions.append(acao)

        return plano_execucao
