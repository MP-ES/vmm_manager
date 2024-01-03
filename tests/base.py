"""
Classe com funções básicas de teste
"""
import uuid
from random import choice, getrandbits, randint, randrange

from tests.utils import Utils
from vmm_manager.entity.inventory import Inventory
from vmm_manager.entity.vm import VM
from vmm_manager.entity.vm_ansible import VMAnsible, VMAnsibleVars
from vmm_manager.entity.vm_disk import VMDisk
from vmm_manager.entity.vm_network import VMNetwork
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.scvmm.scregion import SCRegion


class Base():
    VMS_POR_TESTE_MAX = 20
    REDES_POR_VM_MAX = 5
    DISCOS_POR_VM_MAX = 10
    ANSIBLE_ITERACAO_MAX = 10
    TAMANHO_DISCO_MIN = 1
    TAMANHO_DISCO_MAX = 1073741824
    CPU_MIN = 1
    CPU_MAX = 64
    RAM_MIN = 512
    RAM_MAX = 524288
    REGIOES_QTDE = 10

    @staticmethod
    def get_inventario_completo(num_min_discos_por_vm=1):
        dados_teste = Utils()
        inventario = Inventory(
            dados_teste.get_random_word(), dados_teste.get_random_word())

        # regiões
        regioes = []
        for num_iter in range(0, Base.REGIOES_QTDE):
            regioes.append(SCRegion(
                str(uuid.uuid4()),
                dados_teste.get_nome_unico(),
                dados_teste.get_random_word(),
                dados_teste.get_random_word(),
                chr(ord('A') + num_iter)))
        inventario.set_regioes_disponiveis(regioes)

        for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX)):
            vm_name = dados_teste.get_nome_unico()

            # networks
            redes_vm = []
            for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX)):
                redes_vm.append(
                    VMNetwork(dados_teste.get_random_word(), num_iter == 0))

            # discos adicionais
            discos_vm = []
            for num_iter in range(randrange(num_min_discos_por_vm, Base.DISCOS_POR_VM_MAX)):
                disco = VMDisk(
                    choice(list(SCDiskBusType)),
                    dados_teste.get_nome_unico(),
                    randint(Base.TAMANHO_DISCO_MIN, Base.TAMANHO_DISCO_MAX),
                    choice(list(SCDiskSizeType)),
                    dados_teste.get_random_word()
                )
                disco.set_parametros_extras_vmm(
                    str(uuid.uuid4()),
                    str(uuid.uuid4()),
                    0,
                    num_iter + 1,
                )
                discos_vm.append(disco)

            regiao_vm = Utils.get_random_regiao_vm(Base.REGIOES_QTDE)
            vm_obj = VM(vm_name,
                        dados_teste.get_random_word(),
                        dados_teste.get_random_word(),
                        regiao_vm,
                        randint(Base.CPU_MIN, Base.CPU_MAX),
                        randint(Base.RAM_MIN, Base.RAM_MAX),
                        redes_vm,
                        nested_virtualization=bool(getrandbits(1)),
                        dynamic_memory=bool(getrandbits(1)),
                        no_regiao=inventario.get_nome_no_regiao(regiao_vm))
            vm_obj.add_discos_adicionais(discos_vm)
            inventario.vms[vm_name] = vm_obj

        return inventario

    def get_obj_inventario(self, array_yaml):
        inventario = Inventory(
            array_yaml[0][0]['group'], array_yaml[0][0]['cloud'])

        for maquina_virtual in array_yaml[0][0]['vms']:
            vm_redes = []

            for rede_vm in maquina_virtual.get(
                'networks',
                array_yaml[0][0].get('networks_default', [])
            ):
                vm_redes.append(
                    VMNetwork(rede_vm.get('name'), rede_vm.get('default', False)))

            inventario.vms[maquina_virtual.get('name')] = VM(
                maquina_virtual.get('name'),
                maquina_virtual.get('description'),
                maquina_virtual.get(
                    'image', array_yaml[0][0].get('image_default', None)),
                maquina_virtual.get('region', SCRegion.REGION_DEFAULT),
                maquina_virtual.get(
                    'cpu', array_yaml[0][0].get('cpu_default', None)),
                maquina_virtual.get(
                    'memory', array_yaml[0][0].get('memory_default', None)),
                vm_redes,
                nested_virtualization=maquina_virtual.
                get('nested_virtualization', array_yaml[0][0].get(
                    'nested_virtualization_default', False)),
                dynamic_memory=maquina_virtual.get(
                    'dynamic_memory', array_yaml[0][0].get('dynamic_memory_default', True)),
            )
        return inventario

    def get_dados_ansible_vm(self, array_yaml, vm_name):
        lista_dados_ansible = {}

        for maquina_virtual in array_yaml[0][0]['vms']:
            if maquina_virtual.get('name') != vm_name:
                continue

            for item in maquina_virtual.get('ansible', {}):
                group = item.get('group')
                dados_ansible = VMAnsible(group)

                for variavel in item.get('vars', {}):
                    dados_ansible.variaveis.append(VMAnsibleVars(
                        variavel.get('name'), variavel.get('value')))

                lista_dados_ansible[group] = dados_ansible

        return lista_dados_ansible

    def get_discos_adicionais_vm(self, array_yaml, vm_name):
        lista_discos_adicionais = {}

        for maquina_virtual in array_yaml[0][0]['vms']:
            if maquina_virtual.get('name') != vm_name:
                continue

            for item in maquina_virtual.get('additional_disks', {}):
                file = item.get('file')
                additional_disk = VMDisk(
                    SCDiskBusType(item.get('bus_type')),
                    file,
                    item.get('size_mb'),
                    SCDiskSizeType(item.get('size_type')),
                    item.get('path')
                )

                lista_discos_adicionais[file] = additional_disk

        return lista_discos_adicionais
