"""
Representação de um plano de execução
"""
import os
import uuid
import textwrap
from yamlable import yaml_info, YamlAble
import yaml
from vmm_manager.infra.comando import Comando
from vmm_manager.util.msgs import imprimir_acao_corrente, formatar_msg_erro
from vmm_manager.util.msgs import imprimir_erro, imprimir_ok
from vmm_manager.scvmm.scjob import SCJob
from vmm_manager.entidade.acao import Acao


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

    def executar(self, servidor_acesso, ocultar_progresso):
        if not self.is_vazio():
            print('\nOperações executadas:')
            for acao in self.acoes:
                print('{:<100} => '.format(textwrap.shorten(acao.get_str_impressao_inline(), 100)),
                      end='', flush=True)
                guid = uuid.uuid4()

                # Caso específico de criação de vms
                if acao.is_criacao_vm():
                    self.__guids_a_limpar.append(guid)

                acao.executar(self.agrupamento, self.nuvem,
                              servidor_acesso, guid)

                # Tratando resultado
                if acao.was_executada_com_sucesso():
                    guid = acao.get_resultado_execucao().get('Guid')
                    if guid:
                        # Job em execução
                        self.__jobs_em_execucao[guid] = SCJob(
                            guid, acao)
                        print('[Iniciado {}]'.format(guid))
                    else:
                        # Comando já finalizado
                        imprimir_ok(ocultar_progresso)
                else:
                    imprimir_erro(ocultar_progresso)
                    self.__logar_erros_acao(
                        acao, acao.get_resultado_execucao().get('Msgs'))

            # Monitorando jobs
            SCJob.monitorar_jobs(self.__jobs_em_execucao, servidor_acesso)
            self.__coletar_resultado_jobs()

            # Ações pós execução dos comandos do plano
            print()
            self.__executar_cmds_finalizacao(
                servidor_acesso, ocultar_progresso)
            self.__limpar_guids(servidor_acesso, ocultar_progresso)
            self.__processa_resultado_execucao()
            PlanoExecucao.excluir_arquivo()

    def __executar_cmds_finalizacao(self, servidor_acesso, ocultar_progresso):
        for acao in self.acoes:
            if acao.was_executada_com_sucesso() and acao.has_cmd_pos_execucao():
                cmd = acao.get_cmd_pos_execucao(
                    self.agrupamento, servidor_acesso)

                imprimir_acao_corrente('Executando {}'.format(
                    cmd.descricao), ocultar_progresso)

                status, resultado = cmd.executar(servidor_acesso)

                if status:
                    imprimir_ok(ocultar_progresso)
                else:
                    imprimir_erro(ocultar_progresso)
                    self.__logar_erros_comando(cmd.descricao, resultado)

    def __limpar_guids(self, servidor_acesso, ocultar_progresso):
        if self.__guids_a_limpar:
            imprimir_acao_corrente(
                'Limpando objetos temporários', ocultar_progresso)

            cmd = Comando('limpar_objs_criacao_vm',
                          servidor_vmm=servidor_acesso.servidor_vmm,
                          guids=self.__guids_a_limpar)
            status, retorno = cmd.executar(servidor_acesso)

            if status:
                imprimir_ok(ocultar_progresso)
            else:
                imprimir_erro(ocultar_progresso)
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
        else:
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
