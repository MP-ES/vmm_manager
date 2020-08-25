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
from vmm_manager.entidade.vm_disco import VMDisco
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.scvmm.scregion import SCRegion


class ParserRemoto:

    @staticmethod
    def __get_regioes_disponiveis(servidor_acesso):
        cmd = Comando('obter_regioes_disponiveis',
                      servidor_vmm=servidor_acesso.servidor_vmm)
        status, regioes = cmd.executar(servidor_acesso)
        if not status:
            raise Exception(
                f'Erro ao recuperar regiões disponíveis: {regioes}')

        regioes_remoto = json.loads(regioes)
        regioes_disponiveis = []
        for indice, regiao in enumerate(regioes_remoto):
            regiao_obj = SCRegion(
                regiao.get('IDNo'),
                regiao.get('NomeNo'),
                regiao.get('Grupo'),
                regiao.get('Cluster'),
                chr(ord('A') + indice)
            )

            regioes_disponiveis.append(regiao_obj)

        return regioes_disponiveis

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
                f"Erro ao recuperar VM's do agrupamento: {vms}")
        return vms

    def __get_discos_adicionais(self, servidor_acesso):
        cmd = Comando('obter_discos_adicionais',
                      servidor_vmm=servidor_acesso.servidor_vmm,
                      campo_agrupamento=CAMPO_AGRUPAMENTO[0],
                      campo_id=CAMPO_ID[0],
                      agrupamento=self.agrupamento,
                      nuvem=self.nuvem,
                      vm_nomes=','.join([f'"{nome_vm}"' for nome_vm in self.__inventario.vms]))
        status, discos_adicionais = cmd.executar(servidor_acesso)
        if not status:
            raise Exception(
                f'Erro ao recuperar discos adicionais: {discos_adicionais}')

        discos_vms_remoto = json.loads(discos_adicionais)
        discos_vms = {}
        for maquina_virtual in discos_vms_remoto:
            nome_vm = maquina_virtual.get('Nome')
            discos_vms[nome_vm] = []

            for disco_remoto in maquina_virtual.get('Discos'):
                disco = VMDisco(
                    SCDiskBusType(disco_remoto.get('Tipo')),
                    disco_remoto.get('Arquivo'),
                    disco_remoto.get('TamanhoMB'),
                    SCDiskSizeType(disco_remoto.get('TamanhoTipo')),
                    disco_remoto.get('Caminho'))

                disco.set_parametros_extras_vmm(
                    disco_remoto.get('IDDrive'),
                    disco_remoto.get('IDDisco'),
                    disco_remoto.get('Bus'),
                    disco_remoto.get('Lun'),
                )

                discos_vms[nome_vm].append(disco)

        return discos_vms

    def __montar_inventario(self, servidor_acesso,
                            filtro_nome_vm=None, filtro_dados_completos=True):
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

        # Obtendo dados adicionais
        if filtro_dados_completos:
            # discos
            self.__inventario.set_discos_vms(
                self.__get_discos_adicionais(servidor_acesso))

            # regioes
            self.__inventario.set_mapeamento_regioes(
                ParserRemoto.__get_regioes_disponiveis(servidor_acesso))

    def get_inventario(self, servidor_acesso, filtro_nome_vm=None, filtro_dados_completos=True):
        if not self.__inventario:
            try:
                self.__montar_inventario(
                    servidor_acesso, filtro_nome_vm, filtro_dados_completos)
            # pylint: disable=broad-except
            except Exception as ex:
                return False, str(ex)

        return True, self.__inventario
