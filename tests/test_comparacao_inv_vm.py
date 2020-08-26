"""
Testes de comparação de inventários e geração de ações, focado em vms
"""
import random
import copy
from tests.base import Base
from tests.dados_teste import DadosTeste
from vmm_manager.entidade.plano_execucao import PlanoExecucao
from vmm_manager.entidade.inventario import Inventario


class TestComparacaoInvVm(Base):

    @staticmethod
    def alterar_desc_ram_cpu_vms_inventario(inventario):
        for vm_obj in inventario.vms.values():
            foi_alterada = False
            if random.getrandbits(1):
                vm_obj.descricao = DadosTeste.get_random_string_com_excecao(
                    vm_obj.descricao)
                foi_alterada = True
            if random.getrandbits(1):
                nova_qtde = random.randint(Base.CPU_MIN, Base.CPU_MAX)
                if nova_qtde != vm_obj.qtde_cpu:
                    foi_alterada = True
                vm_obj.qtde_cpu = nova_qtde
            if random.getrandbits(1):
                nova_qtde = random.randint(Base.RAM_MIN, Base.RAM_MAX)
                if nova_qtde != vm_obj.qtde_ram_mb:
                    foi_alterada = True
                vm_obj.qtde_ram_mb = nova_qtde

            if not foi_alterada:
                # forçando uma alteração
                vm_obj.descricao = DadosTeste.get_random_string_com_excecao(
                    vm_obj.descricao)

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

    @staticmethod
    def get_plano_execucao_atualizar_vm(inventario):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in inventario.vms:
            plano_execucao.acoes.append(
                inventario.vms[nome_vm].get_acao_atualizar_vm())

        return plano_execucao

    # pylint: disable=R0201
    def test_inventarios_iguais(self):
        inventario = Base.get_inventario_completo()

        status, plano_execucao = inventario.calcular_plano_execucao(inventario)

        assert status is True
        assert not plano_execucao.acoes

    def test_inventario_local_sem_remoto(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        inventario_remoto.vms = {}

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_criar_inventario(
            inventario_local)

    def test_inventario_remoto_sem_local(self):
        inventario_remoto = Base.get_inventario_completo()
        inventario_local = Inventario(
            inventario_remoto.agrupamento, inventario_remoto.nuvem)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_excluir_inventario(
            inventario_remoto)

    def test_inventario_local_vm_desc_ram_ou_cpu_alterados(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_desc_ram_cpu_vms_inventario(inventario_local)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_atualizar_vm(
            inventario_local)
