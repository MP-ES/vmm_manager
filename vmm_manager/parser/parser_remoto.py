"""
Módulo que realiza o parser de um inventário remoto (no SCVMM)
"""
import json
from vmm_manager.infra.comando import Comando
from vmm_manager.util.config import (CAMPO_AGRUPAMENTO, CAMPO_ID, CAMPO_IMAGEM,
                                     CAMPO_REGIAO, CAMPO_REDE_PRINCIPAL)
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.entidade.vm_rede import VMRede
from vmm_manager.scvmm.enums import VMStatusEnum


class ParserRemoto:
    def __init__(self, agrupamento, nuvem):
        self.agrupamento = agrupamento
        self.nuvem = nuvem
        self.__inventario = None

    def __get_vms_servidor(self, servidor_acesso, filtro_nome_vm=None):
        cmd = Comando('obter_vms_agrupamento',
                      servidor_vmm=servidor_acesso.servidor_vmm,
                      campo_agrupamento=CAMPO_AGRUPAMENTO[0],
                      campo_id=CAMPO_ID[0],
                      campo_imagem=CAMPO_IMAGEM[0],
                      campo_regiao=CAMPO_REGIAO[0],
                      campo_rede_principal=CAMPO_REDE_PRINCIPAL[0],
                      agrupamento=self.agrupamento,
                      filtro_nome_vm=filtro_nome_vm,
                      nuvem=self.nuvem)
        status, vms = cmd.executar(servidor_acesso)
        if not status:
            raise Exception(
                "Erro ao recuperar VM's do agrupamento: {}".format(vms))
        return vms

    def __montar_inventario(self, servidor_acesso, filtro_nome_vm=None):
        self.__inventario = Inventario(self.agrupamento, self.nuvem)
        vms_servidor = json.loads(
            self.__get_vms_servidor(servidor_acesso, filtro_nome_vm) or '{}')
        for maquina_virtual in vms_servidor:
            vms_rede = []
            for rede in maquina_virtual.get('Redes'):
                vm_rede = VMRede(rede.get('Nome'), rede.get('Principal'))
                vm_rede.ips = rede.get('IPS', '').split(' ')
                vms_rede.append(vm_rede)

            self.__inventario.vms[maquina_virtual.get('Nome')] = VM(
                maquina_virtual.get('Nome'),
                maquina_virtual.get('Descricao'),
                maquina_virtual.get('Imagem'),
                maquina_virtual.get('Regiao'),
                maquina_virtual.get('QtdeCpu'),
                maquina_virtual.get('QtdeRam'),
                vms_rede,
                maquina_virtual.get('ID'),
                VMStatusEnum(maquina_virtual.get('Status')),
                maquina_virtual.get('NoRegiao'),
            )

    def get_inventario(self, servidor_acesso, filtro_nome_vm=None):
        if not self.__inventario:
            try:
                self.__montar_inventario(servidor_acesso, filtro_nome_vm)
            # pylint: disable=broad-except
            except Exception as ex:
                return False, str(ex)

        return True, self.__inventario
