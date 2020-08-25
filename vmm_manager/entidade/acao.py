"""
Representação de uma ação (um item do plano de execução)
"""
import json
from yamlable import yaml_info, YamlAble
from vmm_manager.infra.comando import Comando
from vmm_manager.util.config import (CAMPO_AGRUPAMENTO, CAMPO_ID,
                                     CAMPO_IMAGEM, CAMPO_REGIAO, CAMPO_REDE_PRINCIPAL)


@yaml_info(yaml_tag_ns='scvmm_manager')
class Acao(YamlAble):
    ACAO_CRIAR_VM = 'criar_vm'
    ACAO_EXCLUIR_VM = 'excluir_vm'
    ACAO_EXCLUIR_DISCO_VM = 'excluir_disco_vm'

    def __init__(self, nome_comando, **kwargs):
        self.nome_comando = nome_comando
        self.args = kwargs

        self.__status_execucao = None
        self.__retorno_execucao = None
        self.__status_execucao_job = None

    def executar(self, agrupamento, nuvem, servidor_acesso, guid):
        cmd = Comando(self.nome_comando,
                      agrupamento=agrupamento,
                      campo_agrupamento=CAMPO_AGRUPAMENTO[0],
                      campo_id=CAMPO_ID[0],
                      campo_regiao=CAMPO_REGIAO[0],
                      nuvem=nuvem,
                      guid=guid,
                      servidor_vmm=servidor_acesso.servidor_vmm)
        cmd.args.update(self.args)

        status, retorno = cmd.executar(servidor_acesso)

        self.__status_execucao = status
        self.__retorno_execucao = json.loads(
            retorno) if self.__status_execucao else retorno

        return self.__status_execucao, self.__retorno_execucao

    def informar_status_execucao_job(self, status):
        self.__status_execucao_job = status

    def is_criacao_vm(self):
        return self.nome_comando == Acao.ACAO_CRIAR_VM

    def is_bloqueante(self):
        return (self.is_criacao_vm()
                or self.nome_comando == Acao.ACAO_EXCLUIR_VM
                or self.nome_comando == Acao.ACAO_EXCLUIR_DISCO_VM)

    def has_cmd_pos_execucao(self):
        return self.is_criacao_vm()

    def was_executada_com_sucesso(self):
        return (self.__status_execucao and
                self.__retorno_execucao.get('Status') == 'OK'
                and (self.__status_execucao_job is None or
                     self.__status_execucao_job))

    def get_resultado_execucao(self):
        if self.__status_execucao is None:
            raise AttributeError('Ação não executada.')
        if self.__status_execucao:
            return self.__retorno_execucao
        return {'Msgs': self.__retorno_execucao}

    def get_cmd_pos_execucao(self, agrupamento, servidor_acesso):
        if self.is_criacao_vm():
            cmd = Comando('criar_vm_pos',
                          descricao=f"Taguear VM { self.args['nome']}",
                          servidor_vmm=servidor_acesso.servidor_vmm,
                          campo_agrupamento=CAMPO_AGRUPAMENTO[0],
                          campo_id=CAMPO_ID[0],
                          campo_imagem=CAMPO_IMAGEM[0],
                          campo_regiao=CAMPO_REGIAO[0],
                          campo_rede_principal=CAMPO_REDE_PRINCIPAL[0],
                          agrupamento=agrupamento)
            cmd.args.update(self.args)
            return cmd

        raise AttributeError(
            f'Ação "{self.nome_comando}" não possui comando de pós-execução.')

    def get_str_impressao_inline(self):
        return '{} - [{}]'.format(self.nome_comando,
                                  ', '.join(
                                      ['{}={}'.format(arg, self.args[arg])
                                       for arg in self.args]))

    def __eq__(self, other):
        return isinstance(other, Acao) and (self.nome_comando == other.nome_comando
                                            and self.args == other.args)

    def __str__(self):
        return f'''
            nome_comando: {self.nome_comando}
            args: {self.args}
            '''

    def __to_yaml_dict__(self):
        return {'nome_comando': self.nome_comando,
                'args': self.args}
