"""
Testes de comparação de inventários e geração de ações, focado em discos
"""
import copy
from random import randint

from tests.base import Base
from tests.utils import Utils
from vmm_manager.entity.plan import Plan
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType


class TestComparisonInvDisk(Base):
    TP_ALTERACAO_TP_BUS = 1
    TP_ALTERACAO_REDUCAO = 2
    TP_ALTERACAO_EXPANSAO = 3
    TP_ALTERACAO_TP_TAMANHO = 4
    TP_ALTERACAO_CAMINHO = 5

    @staticmethod
    def remover_discos_inventario(inventario):
        discos_removidos = {}
        for vm_name in inventario.vms:
            discos_removidos[vm_name] = inventario.vms[vm_name].additional_disks
            inventario.vms[vm_name].additional_disks = {}
        return discos_removidos

    @staticmethod
    def alterar_discos_inventario(inventario, tipo_alteracao):
        discos_alterados = {}
        for vm_name in inventario.vms:
            discos_alterados[vm_name] = inventario.vms[vm_name].additional_disks

            for disco in inventario.vms[vm_name].additional_disks.values():
                if tipo_alteracao == TestComparisonInvDisk.TP_ALTERACAO_TP_BUS:
                    disco.bus_type = Utils.get_random_lista_com_excecao(
                        list(SCDiskBusType), disco.bus_type)
                elif tipo_alteracao == TestComparisonInvDisk.TP_ALTERACAO_REDUCAO:
                    disco.size_mb = randint(
                        Base.TAMANHO_DISCO_MIN, disco.size_mb - 1)
                elif tipo_alteracao == TestComparisonInvDisk.TP_ALTERACAO_EXPANSAO:
                    disco.size_mb = randint(
                        disco.size_mb - 1, Base.TAMANHO_DISCO_MAX)
                elif tipo_alteracao == TestComparisonInvDisk.TP_ALTERACAO_CAMINHO:
                    disco.path = Utils.get_random_string_com_excecao(
                        disco.path)
                elif tipo_alteracao == TestComparisonInvDisk.TP_ALTERACAO_TP_TAMANHO:
                    disco.size_type = Utils.get_random_lista_com_excecao(
                        list(SCDiskSizeType), disco.size_type)

        return discos_alterados

    @staticmethod
    def get_plano_execucao_criar_discos(inventario, discos_removidos):
        plano_execucao = Plan(
            inventario.group, inventario.cloud)

        for vm_name in discos_removidos:
            for disco in discos_removidos[vm_name].values():
                plano_execucao.actions.append(
                    disco.get_acao_criar_disco(vm_name))

        return plano_execucao

    @staticmethod
    def get_plano_execucao_excluir_discos(inventario, discos_removidos):
        plano_execucao = Plan(
            inventario.group, inventario.cloud)

        for vm_name in discos_removidos:
            for disco in discos_removidos[vm_name].values():
                plano_execucao.actions.append(
                    disco.get_acao_excluir_disco(
                        inventario.vms[vm_name].vmm_id,
                        vm_name
                    )
                )

        return plano_execucao

    @staticmethod
    def get_plano_execucao_alterar_discos(inventario, discos_alterados, tipo_alteracao):
        plano_execucao = Plan(
            inventario.group, inventario.cloud)

        for vm_name in discos_alterados:
            for disco in discos_alterados[vm_name].values():
                if (tipo_alteracao in
                        [TestComparisonInvDisk.TP_ALTERACAO_TP_BUS,
                         TestComparisonInvDisk.TP_ALTERACAO_REDUCAO]):
                    plano_execucao.actions.append(
                        disco.get_acao_excluir_disco(
                            inventario.vms[vm_name].vmm_id,
                            vm_name
                        )
                    )
                    plano_execucao.actions.append(
                        disco.get_acao_criar_disco(vm_name))
                elif tipo_alteracao == TestComparisonInvDisk.TP_ALTERACAO_EXPANSAO:
                    plano_execucao.actions.append(
                        disco.get_acao_expandir_disco(
                            inventario.vms[vm_name].vmm_id,
                            disco.get_id_drive(),
                            vm_name
                        )
                    )
                elif tipo_alteracao == TestComparisonInvDisk.TP_ALTERACAO_CAMINHO:
                    plano_execucao.actions.append(
                        disco.get_acao_mover_disco(
                            inventario.vms[vm_name].vmm_id,
                            disco.get_id_disco(),
                            vm_name
                        )
                    )
                elif tipo_alteracao == TestComparisonInvDisk.TP_ALTERACAO_TP_TAMANHO:
                    plano_execucao.actions.append(
                        disco.get_acao_converter_disco(
                            inventario.vms[vm_name].vmm_id,
                            disco.get_id_drive(),
                            vm_name
                        )
                    )

        return plano_execucao

    def test_discos_iguais(self):
        inventario = Base.get_inventario_completo(
            num_min_discos_por_vm=2)

        status, plano_execucao = inventario.calcular_plano_execucao(inventario)

        assert status is True
        assert not plano_execucao.actions

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

    def test_disco_mudanca_tipo(self):
        inventario_local = Base.get_inventario_completo(
            num_min_discos_por_vm=2)
        inventario_remoto = copy.deepcopy(inventario_local)
        discos_alterados = self.alterar_discos_inventario(
            inventario_local, self.TP_ALTERACAO_TP_BUS)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_alterar_discos(inventario_local,
                                                                        discos_alterados,
                                                                        self.TP_ALTERACAO_TP_BUS)

    def test_disco_reduzido(self):
        inventario_local = Base.get_inventario_completo(
            num_min_discos_por_vm=2)
        inventario_remoto = copy.deepcopy(inventario_local)
        discos_alterados = self.alterar_discos_inventario(
            inventario_local, self.TP_ALTERACAO_REDUCAO)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_alterar_discos(inventario_local,
                                                                        discos_alterados,
                                                                        self.TP_ALTERACAO_REDUCAO)

    def test_disco_expandido(self):
        inventario_local = Base.get_inventario_completo(
            num_min_discos_por_vm=2)
        inventario_remoto = copy.deepcopy(inventario_local)
        discos_alterados = self.alterar_discos_inventario(
            inventario_local, self.TP_ALTERACAO_EXPANSAO)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_alterar_discos(inventario_local,
                                                                        discos_alterados,
                                                                        self.TP_ALTERACAO_EXPANSAO)

    def test_disco_movido(self):
        inventario_local = Base.get_inventario_completo(
            num_min_discos_por_vm=2)
        inventario_remoto = copy.deepcopy(inventario_local)
        discos_alterados = self.alterar_discos_inventario(
            inventario_local, self.TP_ALTERACAO_CAMINHO)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_alterar_discos(inventario_local,
                                                                        discos_alterados,
                                                                        self.TP_ALTERACAO_CAMINHO)

    def test_disco_convertido(self):
        inventario_local = Base.get_inventario_completo(
            num_min_discos_por_vm=2)
        inventario_remoto = copy.deepcopy(inventario_local)
        discos_alterados = self.alterar_discos_inventario(
            inventario_local, self.TP_ALTERACAO_TP_TAMANHO)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_alterar_discos(
            inventario_local,
            discos_alterados,
            self.TP_ALTERACAO_TP_TAMANHO)
