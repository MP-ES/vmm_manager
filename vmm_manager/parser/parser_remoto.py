"""
Módulo que realiza o parser de um inventário remoto (no SCVMM)
"""
import json
from vmm_manager.infra.comando import Comando
from vmm_manager.util.config import CAMPO_AGRUPAMENTO, CAMPO_ID, CAMPO_IMAGEM, CAMPO_REGIAO
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.scvmm.enums import VMStatusEnum


class ParserRemoto:
    def __init__(self, agrupamento, nuvem):
        self.agrupamento = agrupamento
        self.nuvem = nuvem
        self.__inventario = None

    def __get_vms_servidor(self, servidor_acesso):
        cmd = Comando('obter_vms_agrupamento',
                      servidor_vmm=servidor_acesso.servidor_vmm,
                      campo_agrupamento=CAMPO_AGRUPAMENTO[0],
                      campo_id=CAMPO_ID[0],
                      campo_imagem=CAMPO_IMAGEM[0],
                      campo_regiao=CAMPO_REGIAO[0],
                      agrupamento=self.agrupamento, nuvem=self.nuvem)
        status, vms = cmd.executar(servidor_acesso)
        if not status:
            raise Exception(
                "Erro ao recuperar VM's do agrupamento: {}".format(vms))
        return vms

    def __montar_inventario(self, servidor_acesso):
        self.__inventario = Inventario(self.agrupamento, self.nuvem)
        vms_servidor = json.loads(
            self.__get_vms_servidor(servidor_acesso) or '{}')
        for maquina_virtual in vms_servidor:
            self.__inventario.vms[maquina_virtual.get('Nome')] = VM(
                maquina_virtual.get('Nome'),
                maquina_virtual.get('Descricao'),
                maquina_virtual.get('Imagem'),
                maquina_virtual.get('Regiao'),
                maquina_virtual.get('QtdeCpu'),
                maquina_virtual.get('QtdeRam'),
                maquina_virtual.get('Redes'),
                maquina_virtual.get('ID'),
                VMStatusEnum(maquina_virtual.get('Status')),
                maquina_virtual.get('NoRegiao'),
            )

    def get_inventario(self, servidor_acesso):
        if not self.__inventario:
            try:
                self.__montar_inventario(servidor_acesso)
            # pylint: disable=broad-except
            except Exception as ex:
                return False, str(ex)

        return True, self.__inventario
