"""
Testes de comparação de inventários e geração de ações, focado em regiões
"""
import copy

from tests.base import Base
from tests.utils import Utils
from vmm_manager.entity.plan import Plan
from vmm_manager.scvmm.scregion import SCRegion


class TestComparisonInvRegion(Base):
    @staticmethod
    def alterar_regiao_vms_para_default(inventario):
        for vm_name in inventario.vms:
            inventario.vms[vm_name].region = SCRegion.REGION_DEFAULT

    @staticmethod
    def alterar_nome_nos_regiao(inventario):
        for region in inventario.get_mapeamento_regioes_to_test().values():
            region.nome_no = Utils.get_random_string_com_excecao(
                region.nome_no)

    @staticmethod
    def alterar_regiao_vms(inventario):
        lista_regioes = inventario.get_mapeamento_regioes_to_test().keys()
        for vm_obj in inventario.vms.values():
            vm_obj.region = Utils.get_random_lista_com_excecao(
                lista_regioes, vm_obj.region)

    @staticmethod
    def get_plano_execucao_mover_vms_regiao(inventario):
        plano_execucao = Plan(
            inventario.group, inventario.cloud)

        for vm_obj in inventario.vms.values():
            plano_execucao.actions.append(
                vm_obj.get_acao_mover_vm_regiao(inventario.get_id_no_regiao(vm_obj.region)))

        return plano_execucao

    def test_regioes_iguais(self):
        inventario = Base.get_inventario_completo()

        status, plano_execucao = inventario.calcular_plano_execucao(inventario)

        assert status is True
        assert not plano_execucao.actions

    def test_regiao_local_default(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_regiao_vms_para_default(inventario_local)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert not plano_execucao.actions

    def test_regiao_remota_default(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_regiao_vms_para_default(inventario_remoto)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_mover_vms_regiao(
            inventario_local)

    def test_no_regiao_alterado(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_nome_nos_regiao(inventario_remoto)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_mover_vms_regiao(
            inventario_local)

    def test_regiao_vm_alterada(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_regiao_vms(inventario_remoto)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_mover_vms_regiao(
            inventario_local)
