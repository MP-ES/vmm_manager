"""
Testes de comparação de inventários e geração de ações, focado em vms
"""
from tests.base import Base
from vmm_manager.entidade.plano_execucao import PlanoExecucao
from vmm_manager.entidade.inventario import Inventario


class TestComparacaoInvVm(Base):

    @staticmethod
    def get_plano_execucao_criar_inventario(inventario):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in inventario.vms:
            plano_execucao.acoes.append(
                inventario.vms[nome_vm].get_acao_criar_vm())

        for nome_vm in inventario.vms:
            for disco_adicional in inventario.vms[nome_vm].discos_adicionais:
                plano_execucao.acoes.append(
                    inventario.vms[nome_vm]
                    .discos_adicionais[disco_adicional]
                    .get_acao_criar_disco(nome_vm))

        for nome_vm in inventario.vms:
            plano_execucao.acoes.append(
                inventario.vms[nome_vm].get_acao_mover_vm_regiao(
                    inventario.get_id_no_regiao(inventario.vms[nome_vm].regiao)))

        return plano_execucao

    @staticmethod
    def get_plano_execucao_excluir_inventario(inventario):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in inventario.vms:
            plano_execucao.acoes.append(
                inventario.vms[nome_vm].get_acao_excluir_vm())

        return plano_execucao

    # pylint: disable=R0201
    def test_inventarios_iguais(self):
        inventario = Base.get_inventario_completo()

        status, plano_execucao = inventario.calcular_plano_execucao(inventario)

        assert status is True
        assert not plano_execucao.acoes

    def test_inventario_local_sem_remoto(self):
        inventario = Base.get_inventario_completo()

        status, plano_execucao = inventario.calcular_plano_execucao(
            Inventario(inventario.agrupamento, inventario.nuvem))

        assert status is True
        assert plano_execucao == self.get_plano_execucao_criar_inventario(
            inventario)

    def test_inventario_remoto_sem_local(self):
        inventario_remoto = Base.get_inventario_completo()
        inventario_local = Inventario(
            inventario_remoto.agrupamento, inventario_remoto.nuvem)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_excluir_inventario(
            inventario_remoto)
