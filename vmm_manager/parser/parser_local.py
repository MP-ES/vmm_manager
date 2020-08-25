"""
Módulo que realiza o parser de um inventário local
"""
import os
import yamale
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.entidade.vm_rede import VMRede
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.entidade.vm_disco import VMDisco
from vmm_manager.scvmm.scregion import SCRegion


class ParserLocal:
    __ARQUIVO_SCHEMA = '../includes/schema.yaml'
    __YAML_PARSER = 'ruamel'

    @staticmethod
    def __get_schema_yaml():
        return yamale.make_schema(
            os.path.join(
                os.path.dirname(__file__), ParserLocal.__ARQUIVO_SCHEMA),
            parser=ParserLocal.__YAML_PARSER)

    @staticmethod
    def __get_discos_adicionais(nome_vm, dict_discos_adicionais):
        discos_adicionais = []
        for item in dict_discos_adicionais or {}:
            arquivo = item.get('arquivo')

            if arquivo in [disco_adicional.arquivo for disco_adicional in discos_adicionais]:
                raise ValueError(
                    f"Disco '{arquivo}' referenciado mais de uma vez "
                    f"para a VM '{nome_vm}'.")

            disco_adicional = VMDisco(
                SCDiskBusType(item.get('tipo')),
                item.get('arquivo'),
                item.get('tamanho_mb'),
                SCDiskSizeType(item.get('tamanho_tipo')),
                item.get('caminho'))

            discos_adicionais.append(disco_adicional)

        return discos_adicionais

    def __init__(self, arquivo_inventario):
        self.__arquivo_inventario = arquivo_inventario
        self.__inventario = None

    def __validar_arquivo_yaml(self):
        if not os.path.isfile(self.__arquivo_inventario):
            raise ValueError('Arquivo de inventário não encontrado.')
        if os.stat(self.__arquivo_inventario).st_size == 0:
            raise ValueError('Arquivo de inventário vazio.')

    def __montar_inventario(self, dados_inventario,
                            filtro_nome_vm=None, filtro_dados_completos=True):
        nomes_vm = []
        self.__inventario = Inventario(
            dados_inventario['agrupamento'], dados_inventario['nuvem'])

        for maquina_virtual in dados_inventario['vms']:
            nome_vm = maquina_virtual.get('nome').upper()
            if nome_vm in nomes_vm:
                raise ValueError(
                    f'VM {nome_vm} referenciada mais de uma vez no inventário.')
            nomes_vm.append(nome_vm)

            # filtrando vms: melhoria no desempenho
            if filtro_nome_vm and nome_vm != filtro_nome_vm:
                continue

            vm_redes = []
            nomes_redes = []
            for rede_vm in maquina_virtual.get('redes', dados_inventario.get('redes_padrao', [])):
                nome_rede = rede_vm.get('nome')

                if nome_rede in nomes_redes:
                    raise ValueError(
                        f"Rede '{nome_rede}' referenciada mais de uma vez para a VM '{nome_vm}'.")

                nomes_redes.append(nome_rede)
                vm_redes.append(
                    VMRede(nome_rede, rede_vm.get('principal', False)))

            self.__inventario.vms[nome_vm] = VM(
                nome_vm,
                maquina_virtual.get('descricao'),
                maquina_virtual.get(
                    'imagem', dados_inventario.get('imagem_padrao', None)),
                maquina_virtual.get('regiao', SCRegion.REGIAO_PADRAO),
                maquina_virtual.get(
                    'qtde_cpu', dados_inventario.get('qtde_cpu_padrao', None)),
                maquina_virtual.get(
                    'qtde_ram_mb', dados_inventario.get('qtde_ram_mb_padrao', None)),
                vm_redes
            )
            self.__inventario.vms[nome_vm].extrair_dados_ansible_dict(
                maquina_virtual.get('ansible'))

            # Obtendo dados adicionais
            if filtro_dados_completos:
                # discos
                self.__inventario.vms[nome_vm].add_discos_adicionais(
                    ParserLocal.__get_discos_adicionais(nome_vm,
                                                        maquina_virtual.get('discos_adicionais')))

    def __carregar_yaml(self):
        return yamale.make_data(self.__arquivo_inventario,
                                parser=ParserLocal.__YAML_PARSER)

    def get_inventario(self, servidor_acesso, filtro_nome_vm=None, filtro_dados_completos=True):
        if not self.__inventario:
            try:
                self.__validar_arquivo_yaml()
                dados_yaml = self.__carregar_yaml()
                parser = ParserLocal.__get_schema_yaml()

                yamale.validate(parser, dados_yaml, strict=True)

                self.__montar_inventario(
                    dados_yaml[0][0], filtro_nome_vm, filtro_dados_completos)
                self.__inventario.validar(servidor_acesso)
            except (SyntaxError, ValueError) as ex:
                return False, str(ex)

        return True, self.__inventario
