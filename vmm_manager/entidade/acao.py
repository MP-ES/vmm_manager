"""
Representação de uma ação (um item do plano de execução)
"""
from yamlable import yaml_info, YamlAble
from vmm_manager.infra.comando import Comando
from vmm_manager.util.config import CAMPO_AGRUPAMENTO, CAMPO_ID, CAMPO_IMAGEM, CAMPO_REGIAO


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
