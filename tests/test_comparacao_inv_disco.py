"""
Testes de comparação de inventários e geração de ações, focado em discos
"""
import copy
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.entidade.vm_disco import VMDisco
from vmm_manager.entidade.vm_rede import VMRede
from vmm_manager.entidade.plano_execucao import PlanoExecucao
from tests.base import Base
from tests.dados_teste import DadosTeste


class TestComparacaoInvDisco(Base):

    @staticmethod
    def remover_discos_inventario(inventario):
        discos_removidos = {}
        for nome_vm in inventario.vms:
            discos_removidos[nome_vm] = inventario.vms[nome_vm].discos_adicionais
            inventario.vms[nome_vm].discos_adicionais = []
        return discos_removidos

    @ staticmethod
    def get_plano_execucao_criar_discos(inventario, discos_removidos):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in discos_removidos:
            for disco in discos_removidos[nome_vm].values():
                plano_execucao.acoes.append(
                    disco.get_acao_criar_disco(nome_vm))

        return plano_execucao

    @ staticmethod
    def get_plano_execucao_excluir_discos(inventario, discos_removidos):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in discos_removidos:
            for disco in discos_removidos[nome_vm].values():
                plano_execucao.acoes.append(
                    disco.get_acao_excluir_disco(inventario.vms[nome_vm].id_vmm))

        return plano_execucao

    # pylint: disable=R0201
    def test_discos_iguais(self):
        inventario = Base.get_inventario_completo(
            num_min_discos_por_vm=2)

        status, plano_execucao = inventario.calcular_plano_execucao(inventario)

        assert status is True
        assert not plano_execucao.acoes

    def test_disco_local_sem_remoto(self):
        inventario_local = Base.get_inventario_completo(
            num_min_discos_por_vm=2)
        inventario_remoto = copy.deepcopy(inventario_local)
        discos_removidos = self.remover_discos_inventario(inventario_remoto)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_criar_discos(inventario_local,
                                                                      discos_removidos)

    def test_disco_remoto_sem_local(self):
        inventario_local = Base.get_inventario_completo(
            num_min_discos_por_vm=2)
        inventario_remoto = copy.deepcopy(inventario_local)
        discos_removidos = self.remover_discos_inventario(inventario_local)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_excluir_discos(inventario_local,
                                                                        discos_removidos)
