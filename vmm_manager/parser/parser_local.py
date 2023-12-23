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


# pylint: disable=too-few-public-methods
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
        additional_disks = []
        for item in dict_discos_adicionais or {}:
            file = item.get('file')

            if file in [additional_disk.file for additional_disk in additional_disks]:
                raise ValueError(
                    f"Disco '{file}' referenciado mais de uma vez "
                    f"para a VM '{nome_vm}'.")

            additional_disk = VMDisco(
                SCDiskBusType(item.get('bus_type')),
                item.get('file'),
                item.get('size_mb'),
                SCDiskSizeType(item.get('size_type')),
                item.get('path'))

            additional_disks.append(additional_disk)

        return additional_disks

    def __init__(self, inventory_file):
        self.__arquivo_inventario = inventory_file
        self.__inventario = None

    def __validar_arquivo_yaml(self):
        if not os.path.isfile(self.__arquivo_inventario):
            raise ValueError('Arquivo de inventário não encontrado.')
        if os.stat(self.__arquivo_inventario).st_size == 0:
            raise ValueError('Arquivo de inventário vazio.')

    def __montar_inventario(
        self,
        dados_inventario,
        filtro_nome_vm=None,
        filtro_dados_completos=True
    ):
        nomes_vm = []
        self.__inventario = Inventario(
            dados_inventario['group'], dados_inventario['cloud'])

        for maquina_virtual in dados_inventario['vms']:
            nome_vm = maquina_virtual.get('name').upper()
            if nome_vm in nomes_vm:
                raise ValueError(
                    f'VM {nome_vm} referenciada mais de uma vez no inventário.')
            nomes_vm.append(nome_vm)

            # filtrando vms: melhoria no desempenho
            if filtro_nome_vm and nome_vm != filtro_nome_vm:
                continue

            vm_redes = []
            nomes_redes = []
            for rede_vm in maquina_virtual.get(
                'networks',
                dados_inventario.get('networks_default', [])
            ):
                nome_rede = rede_vm.get('name')

                if nome_rede in nomes_redes:
                    raise ValueError(
                        f"Rede '{nome_rede}' referenciada mais de uma vez para a VM '{nome_vm}'.")

                nomes_redes.append(nome_rede)
                vm_redes.append(
                    VMRede(nome_rede, rede_vm.get('default', False)))

            self.__inventario.vms[nome_vm] = VM(
                nome_vm,
                maquina_virtual.get('description'),
                maquina_virtual.get(
                    'image', dados_inventario.get('image_default', None)),
                maquina_virtual.get('region', SCRegion.REGIAO_PADRAO),
                maquina_virtual.get(
                    'cpu', dados_inventario.get('cpu_default', None)),
                maquina_virtual.get(
                    'memory', dados_inventario.get('memory_default', None)),
                vm_redes,
                nested_virtualization=maquina_virtual.get(
                    'nested_virtualization',
                    dados_inventario.get('nested_virtualization_default', False)),
                dynamic_memory=maquina_virtual.get(
                    'dynamic_memory',
                    dados_inventario.get('dynamic_memory_default', True)),
            )
            self.__inventario.vms[nome_vm].extrair_dados_ansible_dict(
                maquina_virtual.get('ansible'))

            # Obtendo dados adicionais
            if filtro_dados_completos:
                # discos
                self.__inventario.vms[nome_vm].add_discos_adicionais(
                    ParserLocal.__get_discos_adicionais(nome_vm,
                                                        maquina_virtual.get('additional_disks')))

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
