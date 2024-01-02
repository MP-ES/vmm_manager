"""
Testes de comparação de inventários e geração de ações, focado em vms
"""
import copy
import random

import pytest

from tests.base import Base
from tests.dados_teste import DadosTeste
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.plan import Plan


class TestComparacaoInvVm(Base):

    @staticmethod
    def alterar_desc_ram_cpu_vms_inventario(inventario):
        for vm_obj in inventario.vms.values():
            foi_alterada = False
            if random.getrandbits(1):
                vm_obj.description = DadosTeste.get_random_string_com_excecao(
                    vm_obj.description)
                foi_alterada = True
            if random.getrandbits(1):
                nova_qtde = random.randint(Base.CPU_MIN, Base.CPU_MAX)
                if nova_qtde != vm_obj.cpu:
                    foi_alterada = True
                vm_obj.cpu = nova_qtde
            if random.getrandbits(1):
                nova_qtde = random.randint(Base.RAM_MIN, Base.RAM_MAX)
                if nova_qtde != vm_obj.memory:
                    foi_alterada = True
                vm_obj.memory = nova_qtde

            if not foi_alterada:
                # forçando uma alteração
                vm_obj.description = DadosTeste.get_random_string_com_excecao(
                    vm_obj.description)

    @staticmethod
    def alterar_imagem_vms_inventario(inventario):
        for vm_obj in inventario.vms.values():
            vm_obj.image = DadosTeste.get_random_string_com_excecao(
                vm_obj.image)

    @staticmethod
    def alterar_redes_vms_inventario(inventario):
        for vm_obj in inventario.vms.values():
            if random.getrandbits(1):
                vm_obj.networks = []
            else:
                for network in vm_obj.networks:
                    network.name = DadosTeste.get_random_string_com_excecao(
                        network.name)

    @staticmethod
    def alterar_virtualizacao_aninhada_vms_inventario(inventario, novo_valor):
        for vm_obj in inventario.vms.values():
            vm_obj.nested_virtualization = novo_valor

    @staticmethod
    def alterar_memoria_dinamica_vms_inventario(inventario, novo_valor):
        for vm_obj in inventario.vms.values():
            vm_obj.dynamic_memory = novo_valor

    @staticmethod
    def get_plano_execucao_criar_inventario(inventario):
        plano_execucao = Plan(
            inventario.group, inventario.cloud)

        for vm_name in inventario.vms:
            plano_execucao.actions.append(
                inventario.vms[vm_name].get_acao_criar_vm())

        for vm_name in inventario.vms:
            for additional_disk in inventario.vms[vm_name].additional_disks:
                plano_execucao.actions.append(
                    inventario.vms[vm_name]
                    .additional_disks[additional_disk]
                    .get_acao_criar_disco(vm_name))

        for vm_name in inventario.vms:
            plano_execucao.actions.append(
                inventario.vms[vm_name].get_acao_mover_vm_regiao(
                    inventario.get_id_no_regiao(inventario.vms[vm_name].region)))

        for vm_name in inventario.vms:
            if inventario.vms[vm_name].nested_virtualization:
                plano_execucao.actions.append(
                    inventario.vms[vm_name].get_acao_atualizar_virtualizacao_aninhada())

        return plano_execucao

    @staticmethod
    def get_plano_execucao_excluir_inventario(inventario):
        plano_execucao = Plan(
            inventario.group, inventario.cloud)

        for vm_name in inventario.vms:
            plano_execucao.actions.append(
                inventario.vms[vm_name].get_acao_excluir_vm())

        return plano_execucao

    @staticmethod
    def get_plano_execucao_atualizar_vm(inventario):
        plano_execucao = Plan(
            inventario.group, inventario.cloud)

        for vm_name in inventario.vms:
            plano_execucao.actions.append(
                inventario.vms[vm_name].get_acao_atualizar_vm(inventario.vms[vm_name].vmm_id))

        return plano_execucao

    @staticmethod
    def get_plano_execucao_resetar_vm(inventario):
        plano_execucao = Plan(
            inventario.group, inventario.cloud)

        for vm_name in inventario.vms:
            plano_execucao.actions.append(
                inventario.vms[vm_name].get_acao_excluir_vm())
            plano_execucao.actions.append(
                inventario.vms[vm_name].get_acao_criar_vm())

        return plano_execucao

    @staticmethod
    def get_plano_execucao_alterar_virtualizacao_aninhada(
        inventario_local,
        inventario_remoto,
        novo_valor
    ):
        plano_execucao = Plan(
            inventario_local.group, inventario_local.cloud)

        for vm_name in inventario_local.vms:
            if inventario_remoto.vms[vm_name].nested_virtualization != novo_valor:
                plano_execucao.actions.append(
                    inventario_local.vms[vm_name].get_acao_atualizar_virtualizacao_aninhada())

        return plano_execucao

    @staticmethod
    def get_plano_execucao_alterar_memoria_dinamica(
        inventario_local,
        inventario_remoto,
        novo_valor
    ):
        plano_execucao = Plan(
            inventario_local.group, inventario_local.cloud)

        for vm_name in inventario_local.vms:
            if inventario_remoto.vms[vm_name].dynamic_memory != novo_valor:
                plano_execucao.actions.append(
                    inventario_local.vms[vm_name].get_acao_atualizar_memoria_dinamica())

        return plano_execucao

    def test_inventarios_iguais(self):
        inventario = Base.get_inventario_completo()

        status, plano_execucao = inventario.calcular_plano_execucao(inventario)

        assert status is True
        assert not plano_execucao.actions

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
            inventario_remoto.group, inventario_remoto.cloud)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_excluir_inventario(
            inventario_remoto)

    def test_inventario_local_vms_desc_ram_ou_cpu_alterados(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_desc_ram_cpu_vms_inventario(inventario_local)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_atualizar_vm(
            inventario_local)

    def test_inventario_local_vms_imagem_alterada(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_imagem_vms_inventario(inventario_local)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_resetar_vm(
            inventario_local)

    def test_inventario_local_vms_redes_alteradas(self):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_redes_vms_inventario(inventario_local)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_resetar_vm(
            inventario_local)

    @pytest.mark.parametrize('nested_virtualization', [True, False])
    def test_inventario_local_vms_virtualizacao_aninhada_alterada(self, nested_virtualization):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_virtualizacao_aninhada_vms_inventario(
            inventario_local, nested_virtualization)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_alterar_virtualizacao_aninhada(
            inventario_local, inventario_remoto, nested_virtualization)

    @pytest.mark.parametrize('dynamic_memory', [True, False])
    def test_inventario_local_vms_memoria_dinamica_alterada(self, dynamic_memory):
        inventario_local = Base.get_inventario_completo()
        inventario_remoto = copy.deepcopy(inventario_local)
        self.alterar_memoria_dinamica_vms_inventario(
            inventario_local, dynamic_memory)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_alterar_memoria_dinamica(
            inventario_local, inventario_remoto, dynamic_memory)
