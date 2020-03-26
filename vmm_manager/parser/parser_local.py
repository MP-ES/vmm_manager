"""
Módulo que realiza o parser de um inventário local
"""
import os
import yamale
from vmm_manager.infra.comando import Comando
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM


class ParserLocal:
    REGIAO_PADRAO = 'default'
    __ARQUIVO_SCHEMA = '../includes/schema.yaml'
    __YAML_PARSER = 'ruamel'

    @staticmethod
    def __get_schema_yaml():
        return yamale.make_schema(
            os.path.join(
                os.path.dirname(__file__), ParserLocal.__ARQUIVO_SCHEMA),
            parser=ParserLocal.__YAML_PARSER)

    def __init__(self, arquivo_inventario):
        self.__arquivo_inventario = arquivo_inventario
        self.__inventario = None

    def __validar_arquivo_yaml(self):
        if not os.path.isfile(self.__arquivo_inventario):
            raise ValueError('Arquivo de inventário não encontrado.')
        if os.stat(self.__arquivo_inventario).st_size == 0:
            raise ValueError('Arquivo de inventário vazio.')

    def __validar_inventario_servidor(self, servidor_acesso):
        imagens = set()
        redes = set()
        regioes = set()
        for maquina_virtual in self.__inventario.vms.values():
            if maquina_virtual.imagem is None:
                raise ValueError(
                    'Imagem da VM {} não definida.'.format(maquina_virtual.nome))
            imagens.add(maquina_virtual.imagem)

            if maquina_virtual.regiao != ParserLocal.REGIAO_PADRAO:
                regioes.add(maquina_virtual.regiao)

            if maquina_virtual.qtde_cpu is None:
                raise ValueError(
                    'Quantidade de CPUs da VM {} não definida.'.format(maquina_virtual.nome))

            if maquina_virtual.qtde_ram_mb is None:
                raise ValueError(
                    'Quantidade de memória da VM {} não definida.'.format(maquina_virtual.nome))

            if maquina_virtual.redes is None:
                raise ValueError(
                    'Redes da VM {} não definida.'.format(maquina_virtual.nome))
            redes.update([rede['nome'] for rede in maquina_virtual.redes])

        cmd = Comando('validar_inventario', imagens=imagens,
                      nuvem=self.__inventario.nuvem,
                      redes=redes,
                      servidor_vmm=servidor_acesso.servidor_vmm,
                      qtde_minima_regioes=len(regioes))
        _, msg = cmd.executar(servidor_acesso)
        if msg:
            raise ValueError(msg)

    def __montar_inventario(self, dados_inventario):
        nomes_vm = []
        self.__inventario = Inventario(
            dados_inventario['agrupamento'], dados_inventario['nuvem'])

        for maquina_virtual in dados_inventario['vms']:
            nome_vm = maquina_virtual.get('nome')
            if nome_vm in nomes_vm:
                raise ValueError(
                    'VM {} referenciada mais de uma vez no inventário.'.format(nome_vm))
            nomes_vm.append(nome_vm)

            self.__inventario.vms[nome_vm] = VM(
                nome_vm,
                maquina_virtual.get('descricao'),
                maquina_virtual.get(
                    'imagem', dados_inventario.get('imagem_padrao', None)),
                maquina_virtual.get('regiao', ParserLocal.REGIAO_PADRAO),
                maquina_virtual.get(
                    'qtde_cpu', dados_inventario.get('qtde_cpu_padrao', None)),
                maquina_virtual.get(
                    'qtde_ram_mb', dados_inventario.get('qtde_ram_mb_padrao', None)),
                maquina_virtual.get(
                    'redes', dados_inventario.get('redes_padrao', None))
            )

    def __carregar_yaml(self):
        return yamale.make_data(self.__arquivo_inventario,
                                parser=ParserLocal.__YAML_PARSER)

    def get_inventario(self, servidor_acesso):
        if not self.__inventario:
            try:
                self.__validar_arquivo_yaml()
                dados_yaml = self.__carregar_yaml()
                dados_inventario = yamale.validate(ParserLocal.__get_schema_yaml(),
                                                   dados_yaml, strict=True)
                self.__montar_inventario(dados_inventario[0][0])
                self.__validar_inventario_servidor(servidor_acesso)
            except (SyntaxError, ValueError) as ex:
                return False, str(ex)

        return True, self.__inventario
