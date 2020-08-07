"""
Testes de comparação de inventários e geração de ações, focado em discos
"""
from random import randint
import copy
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.entidade.plano_execucao import PlanoExecucao
from tests.base import Base
from tests.dados_teste import DadosTeste


class TestComparacaoInvDisco(Base):
    TP_ALTERACAO_TP_BUS = 1
    TP_ALTERACAO_REDUCAO = 2
    TP_ALTERACAO_EXPANSAO = 3
    TP_ALTERACAO_TP_TAMANHO = 4
    TP_ALTERACAO_CAMINHO = 5

    @staticmethod
    def remover_discos_inventario(inventario):
        discos_removidos = {}
        for nome_vm in inventario.vms:
            discos_removidos[nome_vm] = inventario.vms[nome_vm].discos_adicionais
            inventario.vms[nome_vm].discos_adicionais = []
        return discos_removidos

    @staticmethod
    def alterar_discos_inventario(inventario, tipo_alteracao):
        discos_alterados = {}
        for nome_vm in inventario.vms:
            discos_alterados[nome_vm] = inventario.vms[nome_vm].discos_adicionais

            for disco in inventario.vms[nome_vm].discos_adicionais.values():
                if tipo_alteracao == TestComparacaoInvDisco.TP_ALTERACAO_TP_BUS:
                    disco.tipo = DadosTeste.get_random_lista_com_excecao(
                        list(SCDiskBusType), disco.tipo)
                elif tipo_alteracao == TestComparacaoInvDisco.TP_ALTERACAO_REDUCAO:
                    disco.tamanho_mb = randint(
                        Base.TAMANHO_DISCO_MIN, disco.tamanho_mb - 1)
                elif tipo_alteracao == TestComparacaoInvDisco.TP_ALTERACAO_EXPANSAO:
                    disco.tamanho_mb = randint(
                        disco.tamanho_mb - 1, Base.TAMANHO_DISCO_MAX)
                elif tipo_alteracao == TestComparacaoInvDisco.TP_ALTERACAO_CAMINHO:
                    disco.caminho = DadosTeste.get_random_string_com_excecao(
                        disco.caminho)
                elif tipo_alteracao == TestComparacaoInvDisco.TP_ALTERACAO_TP_TAMANHO:
                    disco.tamanho_tipo = DadosTeste.get_random_lista_com_excecao(
                        list(SCDiskSizeType), disco.tamanho_tipo)

        return discos_alterados

    @staticmethod
    def get_plano_execucao_criar_discos(inventario, discos_removidos):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in discos_removidos:
            for disco in discos_removidos[nome_vm].values():
                plano_execucao.acoes.append(
                    disco.get_acao_criar_disco(nome_vm))

        return plano_execucao

    @staticmethod
    def get_plano_execucao_excluir_discos(inventario, discos_removidos):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in discos_removidos:
            for disco in discos_removidos[nome_vm].values():
                plano_execucao.acoes.append(
                    disco.get_acao_excluir_disco(inventario.vms[nome_vm].id_vmm))

        return plano_execucao

    @staticmethod
    def get_plano_execucao_alterar_discos(inventario, discos_alterados, tipo_alteracao):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in discos_alterados:
            for disco in discos_alterados[nome_vm].values():
                if (tipo_alteracao in
                        [TestComparacaoInvDisco.TP_ALTERACAO_TP_BUS,
                         TestComparacaoInvDisco.TP_ALTERACAO_REDUCAO]):
                    plano_execucao.acoes.append(
                        disco.get_acao_excluir_disco(inventario.vms[nome_vm].id_vmm))
                    plano_execucao.acoes.append(
                        disco.get_acao_criar_disco(nome_vm))
                elif tipo_alteracao == TestComparacaoInvDisco.TP_ALTERACAO_EXPANSAO:
                    plano_execucao.acoes.append(
                        disco.get_acao_expandir_disco(inventario.vms[nome_vm].id_vmm,
                                                      disco.get_id_drive()))
                elif tipo_alteracao == TestComparacaoInvDisco.TP_ALTERACAO_CAMINHO:
                    plano_execucao.acoes.append(
                        disco.get_acao_mover_disco(inventario.vms[nome_vm].id_vmm,
                                                   disco.get_id_disco()))
                elif tipo_alteracao == TestComparacaoInvDisco.TP_ALTERACAO_TP_TAMANHO:
                    plano_execucao.acoes.append(
                        disco.get_acao_converter_disco(inventario.vms[nome_vm].id_vmm,
                                                       disco.get_id_drive()))

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

    def test_recriar_disco_mudanca_tipo(self):
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

    def test_recriar_disco_reduzido(self):
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
