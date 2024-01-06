"""
Módulo que realiza o parser de um inventário remoto (no SCVMM)
"""
import json

from vmm_manager.entity.inventory import Inventory
from vmm_manager.entity.vm import VM
from vmm_manager.entity.vm_disk import VMDisk
from vmm_manager.entity.vm_network import VMNetwork
from vmm_manager.infra.command import Command
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType, VMStatusEnum
from vmm_manager.scvmm.scregion import SCRegion
from vmm_manager.util.config import (FIELD_GROUP, FIELD_ID, FIELD_IMAGE,
                                     FIELD_NETWORK_DEFAULT, FIELD_REGION)


# pylint: disable=too-few-public-methods
class ParserRemote:

    @staticmethod
    def __get_regioes_disponiveis(servidor_acesso):
        cmd = Command('get_available_regions',
                      vmm_server=servidor_acesso.vmm_server)
        status, regioes = cmd.executar(servidor_acesso)
        if not status:
            raise Exception(  # pylint: disable=broad-exception-raised
                f'Error getting available regions: {regioes}')

        regioes_remoto = json.loads(regioes)
        regioes_disponiveis = []
        for region in regioes_remoto:
            regiao_obj = SCRegion(
                region.get('HostID'),
                region.get('Hostname'),
                region.get('Group'),
                region.get('Cluster')
            )

            regioes_disponiveis.append(regiao_obj)

        return regioes_disponiveis

    def __init__(self, group, cloud):
        self.group = group
        self.cloud = cloud
        self.__inventario = None

    def __get_vms_servidor(self, servidor_acesso, filtro_nome_vm=None):
        cmd = Command(
            'get_vms_in_group',
            vmm_server=servidor_acesso.vmm_server,
            field_group=FIELD_GROUP[0],
            field_id=FIELD_ID[0],
            field_image=FIELD_IMAGE[0],
            field_region=FIELD_REGION[0],
            field_network_default=FIELD_NETWORK_DEFAULT[0],
            group=self.group,
            filtro_nome_vm=filtro_nome_vm,
            cloud=self.cloud
        )

        status, vms = cmd.executar(servidor_acesso)

        if not status:
            raise Exception(  # pylint: disable=broad-exception-raised
                f"Error getting VMs: {vms}")

        return vms

    def __get_discos_adicionais(self, servidor_acesso):
        cmd = Command('get_additional_disks',
                      vmm_server=servidor_acesso.vmm_server,
                      field_group=FIELD_GROUP[0],
                      field_id=FIELD_ID[0],
                      group=self.group,
                      cloud=self.cloud,
                      vm_nomes=','.join([f'"{vm_name}"' for vm_name in self.__inventario.vms]))
        status, additional_disks = cmd.executar(servidor_acesso)
        if not status:
            raise Exception(  # pylint: disable=broad-exception-raised
                f'Error getting additional disks: {additional_disks}')

        discos_vms_remoto = json.loads(additional_disks)
        discos_vms = {}
        for maquina_virtual in discos_vms_remoto:
            vm_name = maquina_virtual.get('Name')
            discos_vms[vm_name] = []

            for disco_remoto in maquina_virtual.get('Discos'):
                disco = VMDisk(
                    SCDiskBusType(disco_remoto.get('Type')),
                    disco_remoto.get('File'),
                    disco_remoto.get('SizeMB'),
                    SCDiskSizeType(disco_remoto.get('SizeType')),
                    disco_remoto.get('Path'))

                disco.set_parametros_extras_vmm(
                    disco_remoto.get('DriveID'),
                    disco_remoto.get('DiskID'),
                    disco_remoto.get('Bus'),
                    disco_remoto.get('Lun'),
                )

                discos_vms[vm_name].append(disco)

        return discos_vms

    def __montar_inventario(
        self,
        servidor_acesso,
        filtro_nome_vm=None,
        filtro_dados_completos=True
    ):
        self.__inventario = Inventory(self.group, self.cloud)

        vms_servidor = json.loads(
            self.__get_vms_servidor(servidor_acesso, filtro_nome_vm) or '{}')

        for maquina_virtual in vms_servidor:
            vms_rede = []

            for network in maquina_virtual.get('Networks'):
                vm_rede = VMNetwork(network.get('Name'), network.get('Principal'))
                vm_rede.ips = network.get('IPS', '').split(' ')
                vms_rede.append(vm_rede)

            self.__inventario.vms[maquina_virtual.get('Name')] = VM(
                maquina_virtual.get('Name'),
                bytearray(maquina_virtual.get('Description')).decode('utf-8'),  # convert utf-8 bytes to string
                maquina_virtual.get('Image'),
                maquina_virtual.get('Region'),
                maquina_virtual.get('Cpu'),
                maquina_virtual.get('Ram'),
                vms_rede,
                maquina_virtual.get('ID'),
                maquina_virtual.get('NestedVirtualization'),
                maquina_virtual.get('DynamicMemory'),
                VMStatusEnum(maquina_virtual.get('Status')),
                maquina_virtual.get('RegionHostname'),
            )

        # Obtendo dados adicionais
        if filtro_dados_completos:
            # discos
            self.__inventario.set_discos_vms(
                self.__get_discos_adicionais(servidor_acesso))

            # regioes
            self.__inventario.set_regioes_disponiveis(
                ParserRemote.__get_regioes_disponiveis(servidor_acesso))

    def get_inventario(self, servidor_acesso, filtro_nome_vm=None, filtro_dados_completos=True):
        if not self.__inventario:
            try:
                self.__montar_inventario(
                    servidor_acesso, filtro_nome_vm, filtro_dados_completos)
            # pylint: disable=broad-except
            except Exception as ex:
                return False, str(ex)

        return True, self.__inventario
