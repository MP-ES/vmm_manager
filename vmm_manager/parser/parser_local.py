"""
Módulo que realiza o parser de um inventário local
"""
import os
import yamale
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.entidade.vm_rede import VMRede


class ParserLocal:
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

    def __montar_inventario(self, dados_inventario, filtro_nome_vm=None):
        nomes_vm = []
        self.__inventario = Inventario(
            dados_inventario['agrupamento'], dados_inventario['nuvem'])

        for maquina_virtual in dados_inventario['vms']:
            nome_vm = maquina_virtual.get('nome').upper()
            if nome_vm in nomes_vm:
                raise ValueError(
                    'VM {} referenciada mais de uma vez no inventário.'.format(nome_vm))
            nomes_vm.append(nome_vm)

            # filtrando vms: melhoria no desempenho
            if filtro_nome_vm and nome_vm != filtro_nome_vm:
                continue

            vm_redes = []
            for rede_vm in maquina_virtual.get('redes', dados_inventario.get('redes_padrao', [])):
                vm_redes.append(
                    VMRede(rede_vm.get('nome'), rede_vm.get('principal', False)))

            self.__inventario.vms[nome_vm] = VM(
                nome_vm,
                maquina_virtual.get('descricao'),
                maquina_virtual.get(
                    'imagem', dados_inventario.get('imagem_padrao', None)),
                maquina_virtual.get('regiao', Inventario.REGIAO_PADRAO),
                maquina_virtual.get(
                    'qtde_cpu', dados_inventario.get('qtde_cpu_padrao', None)),
                maquina_virtual.get(
                    'qtde_ram_mb', dados_inventario.get('qtde_ram_mb_padrao', None)),
                vm_redes
            )
            self.__inventario.vms[nome_vm].extrair_dados_ansible_dict(
                maquina_virtual.get('ansible'))

    def __carregar_yaml(self):
        return yamale.make_data(self.__arquivo_inventario,
                                parser=ParserLocal.__YAML_PARSER)

    def get_inventario(self, servidor_acesso, filtro_nome_vm=None):
        if not self.__inventario:
            try:
                self.__validar_arquivo_yaml()
                dados_yaml = self.__carregar_yaml()
                dados_inventario = yamale.validate(ParserLocal.__get_schema_yaml(),
                                                   dados_yaml, strict=True)
                self.__montar_inventario(
                    dados_inventario[0][0], filtro_nome_vm)
                self.__inventario.validar_no_servidor(servidor_acesso)
            except (SyntaxError, ValueError) as ex:
                return False, str(ex)

        return True, self.__inventario
