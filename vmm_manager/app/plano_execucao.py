"""
Módulo responsável por gerenciar o plano de execução das operações necessárias
à atualização do inventário
"""
import os
import uuid
import textwrap
from yamlable import yaml_info, YamlAble
import yaml
from vmm_manager.app.comando import Comando
from vmm_manager.app.util import CAMPO_AGRUPAMENTO, CAMPO_ID, CAMPO_IMAGEM, CAMPO_REGIAO
from vmm_manager.app.util import imprimir_acao_corrente, formatar_msg_erro
from vmm_manager.app.util import imprimir_erro, imprimir_ok
from vmm_manager.app.scvmm import SCJob


@yaml_info(yaml_tag_ns='scvmm_manager')
class Acao(YamlAble):
    def __init__(self, nome_comando, **kwargs):
        self.nome_comando = nome_comando
        self.args = kwargs

    def executar(self, agrupamento, nuvem, servidor_acesso, guid):
        cmd = Comando(self.nome_comando,
                      agrupamento=agrupamento,
                      nuvem=nuvem,
                      guid=guid,
                      servidor_vmm=servidor_acesso.servidor_vmm)
        cmd.args.update(self.args)

        return cmd.executar(servidor_acesso)

    def is_criacao_vm(self):
        return self.nome_comando == 'criar_vm'

    def get_cmd_pos_execucao(self, agrupamento, servidor_acesso):
        if self.is_criacao_vm():
            cmd = Comando('criar_vm_pos',
                          descricao='tagueamento da VM {}'.format(
                              self.args['nome']),
                          campo_agrupamento=CAMPO_AGRUPAMENTO[0],
                          campo_id=CAMPO_ID[0],
                          campo_imagem=CAMPO_IMAGEM[0],
                          campo_regiao=CAMPO_REGIAO[0],
                          agrupamento=agrupamento,
                          servidor_vmm=servidor_acesso.servidor_vmm)
            cmd.args.update(self.args)
            return cmd

        raise AttributeError(
            'Ação "{}" não possui comando de pós execução.'.format(self.nome_comando))

    def get_str_impressao_inline(self):
        return '{} - [{}]'.format(self.nome_comando,
                                  ', '.join(
                                      ['{}={}'.format(arg, self.args[arg])
                                       for arg in self.args]))

    def __eq__(self, other):
        return isinstance(other, Acao) and (self.nome_comando == other.nome_comando
                                            and self.args == other.args)

    def __str__(self):
        return '''
            nome_comando: {}
            args: {}
            '''.format(self.nome_comando,
                       self.args)

    def __to_yaml_dict__(self):
        return {'nome_comando': self.nome_comando,
                'args': self.args}


@yaml_info(yaml_tag_ns='scvmm_manager')
class PlanoExecucao(YamlAble):
    ARQUIVO_PLANO_EXECUCAO = 'plan.yaml'
    ARQUIVO_LOG_ERROS = 'erros.log'

    @staticmethod
    def carregar_plano_execucao(arquivo_plano_execucao):
        try:
            with open(arquivo_plano_execucao, 'r') as arquivo:
                plano_execucao = yaml.safe_load(arquivo)
                return True, plano_execucao
        except (IOError, TypeError) as erro:
            return False, "Erro ao carregar plano de execução '{}'.\n{}".format(
                arquivo_plano_execucao,
                erro)

    @staticmethod
    def excluir_arquivo():
        if os.path.exists(PlanoExecucao.ARQUIVO_PLANO_EXECUCAO):
            os.remove(PlanoExecucao.ARQUIVO_PLANO_EXECUCAO)

    @staticmethod
    def __excluir_arquivo_log_erros():
        if os.path.exists(PlanoExecucao.ARQUIVO_LOG_ERROS):
            os.remove(PlanoExecucao.ARQUIVO_LOG_ERROS)

    def __init__(self, agrupamento, nuvem):
        self.agrupamento = agrupamento
        self.nuvem = nuvem
        self.acoes = []
        self.__jobs_em_execucao = {}
        self.__guids_a_limpar = []
        self.__cmds_finalizacao = []
        self.__msgs_erros = ''

    def is_vazio(self):
        return not self.acoes

    def gerar_arquivo(self):
        try:
            conteudo = yaml.safe_dump(self, default_flow_style=False)
            with open(PlanoExecucao.ARQUIVO_PLANO_EXECUCAO, 'w') as arquivo_yaml:
                arquivo_yaml.write(conteudo)
        except IOError as erro:
            return False, 'Erro ao gerar arquivo {}.\n{}'.format(
                PlanoExecucao.ARQUIVO_PLANO_EXECUCAO,
                erro)

        return True, conteudo

    def executar(self, servidor_acesso):
        if not self.is_vazio():
            print('\nOperações executadas:')
            for acao in self.acoes:
                print('{:<100} => '.format(textwrap.shorten(acao.get_str_impressao_inline(), 100)),
                      end='', flush=True)
                guid = uuid.uuid4()

                # Caso específico de criação de vms
                if acao.is_criacao_vm():
                    self.__guids_a_limpar.append(guid)
                    self.__cmds_finalizacao.append(
                        acao.get_cmd_pos_execucao(self.agrupamento, servidor_acesso))

                status, retorno = acao.executar(
                    self.agrupamento, self.nuvem, servidor_acesso, guid)

                # Tratando resultado
                if status:
                    if retorno:
                        # Job em execução
                        self.__jobs_em_execucao[retorno] = SCJob(retorno, acao)
                        print('[Iniciado {}]'.format(retorno))
                    else:
                        # Comando já finalizado
                        imprimir_ok()
                else:
                    imprimir_erro()
                    self.__logar_erros_acao(acao, retorno)

            # Monitorando jobs
            SCJob.monitorar_jobs(self.__jobs_em_execucao, servidor_acesso)
            self.__coletar_resultado_jobs()

            # Ações pós execução dos comandos do plano
            self.__executar_cmds_finalizacao(servidor_acesso)
            self.__limpar_guids(servidor_acesso)
            self.__processa_resultado_execucao()
            PlanoExecucao.excluir_arquivo()

    def __executar_cmds_finalizacao(self, servidor_acesso):
        if self.__cmds_finalizacao:
            print()
            for cmd in self.__cmds_finalizacao:
                imprimir_acao_corrente('Executando {}'.format(cmd.descricao))

                status, resultado = cmd.executar(servidor_acesso)

                if status:
                    imprimir_ok()
                else:
                    imprimir_erro()
                    self.__logar_erros_comando(cmd.descricao, resultado)

    def __limpar_guids(self, servidor_acesso):
        if self.__guids_a_limpar:
            if not self.__cmds_finalizacao:
                print()
            imprimir_acao_corrente('Limpando objetos temporários')

            cmd = Comando('limpar_objs_criacao_vm',
                          servidor_vmm=servidor_acesso.servidor_vmm,
                          guids=self.__guids_a_limpar)
            status, retorno = cmd.executar(servidor_acesso)

            if status:
                imprimir_ok()
            else:
                imprimir_erro()
                self.__logar_erros_comando(
                    'limpar objetos temporários', retorno)

    def __processa_resultado_execucao(self):
        if self.__msgs_erros:
            self.__gerar_arquivo_erros()
        else:
            PlanoExecucao.__excluir_arquivo_log_erros()

    def imprimir_resultado_execucao(self):
        if self.__msgs_erros:
            print(formatar_msg_erro('\nErro ao executar algumas operações. Mais detalhes em {}.'
                                    .format(PlanoExecucao.ARQUIVO_LOG_ERROS)))

        print('\nSincronização executada com sucesso.')

    def __coletar_resultado_jobs(self):
        if self.__jobs_em_execucao:
            for job in self.__jobs_em_execucao.values():
                if job.is_finalizado_com_erro():
                    print(formatar_msg_erro(
                        'Processo {} finalizado com erro.'.format(job.id_vmm)))
                    self.__logar_erros_acao(job.acao, job.resumo_erro)

    def __logar_erros_comando(self, comando, erro):
        self.__msgs_erros += 'Erro no comando "{}":\n{}\n\n'.format(
            comando, erro)

    def __logar_erros_acao(self, acao, erro):
        self.__msgs_erros += 'Comando:\n{}\n\nErro capturado:\n{}\n\n'.format(
            acao.get_str_impressao_inline(), erro)

    def __gerar_arquivo_erros(self):
        try:
            with open(PlanoExecucao.ARQUIVO_LOG_ERROS, 'w') as arquivo_erros:
                arquivo_erros.write(self.__msgs_erros)
        except IOError as erro:
            print('Não foi possível gerar arquivo de erros ({}): {}'.format(
                PlanoExecucao.ARQUIVO_LOG_ERROS, erro))

    def imprimir_acoes(self):
        for acao in self.acoes:
            print(acao.get_str_impressao_inline())

    def __eq__(self, other):
        return isinstance(other, PlanoExecucao) and (self.agrupamento == other.agrupamento
                                                     and self.nuvem == other.nuvem
                                                     and self.acoes == other.acoes)

    def __str__(self):
        return '''
            agrupamento: {}
            nuvem: {}
            acoes: {}
            '''.format(self.agrupamento,
                       self.nuvem,
                       ','.join(str(acao) for acao in self.acoes))

    def __to_yaml_dict__(self):
        return {'agrupamento': self.agrupamento,
                'nuvem': self.nuvem,
                'acoes': self.acoes}

    @classmethod
    def __from_yaml_dict__(cls, dct, yaml_tag):
        plano_execucao = PlanoExecucao(dct['agrupamento'], dct['nuvem'])
        for acao_str in dct['acoes']:
            acao = Acao(acao_str.nome_comando)
            acao.args = acao_str.args['args']
            plano_execucao.acoes.append(acao)
        return plano_execucao
