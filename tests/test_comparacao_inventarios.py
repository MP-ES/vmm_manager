"""
Testes de comparação de inventários e geração de ações
"""
from random import randrange, randint
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.entidade.vm_rede import VMRede
from vmm_manager.entidade.plano_execucao import PlanoExecucao
from vmm_manager.entidade.acao import Acao
from tests.base import Base
from tests.dados_teste import DadosTeste


class TestComparacaoInventarios(Base):

    @staticmethod
    def get_plano_execucao_criar_inventario(inventario):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in inventario.vms:
            plano_execucao.acoes.append(
                Acao('criar_vm',
                     nome=inventario.vms[nome_vm].nome,
                     descricao=inventario.vms[nome_vm].descricao,
                     regiao=inventario.vms[nome_vm].regiao,
                     imagem=inventario.vms[nome_vm].imagem,
                     qtde_cpu=inventario.vms[nome_vm].qtde_cpu,
                     qtde_ram_mb=inventario.vms[nome_vm].qtde_ram_mb,
                     redes=[rede.nome
                            for rede in inventario.vms[nome_vm].redes],
                     rede_principal=inventario.vms[nome_vm].get_rede_principal(
                     )
                     ))

        return plano_execucao

    @staticmethod
    def get_plano_execucao_excluir_inventario(inventario):
        plano_execucao = PlanoExecucao(
            inventario.agrupamento, inventario.nuvem)

        for nome_vm in inventario.vms:
            plano_execucao.acoes.append(
                Acao('excluir_vm',
                     id_vmm=inventario.vms[nome_vm].id_vmm
                     ))

        return plano_execucao

    @staticmethod
    def get_inventario_completo():
        dados_teste = DadosTeste()
        inventario = Inventario(
            dados_teste.get_random_word(), dados_teste.get_random_word())

        for _ in range(randrange(1, TestComparacaoInventarios.MAX_VMS_POR_TESTE)):
            nome_vm = dados_teste.get_nome_unico()

            redes_vm = []
            for num_iter in range(randrange(1, Base.MAX_REDES_POR_VM)):
                redes_vm.append(
                    VMRede(dados_teste.get_random_word(), num_iter == 0))

            inventario.vms[nome_vm] = VM(nome_vm,
                                         dados_teste.get_random_word(),
                                         dados_teste.get_random_word(),
                                         dados_teste.get_random_word(),
                                         randint(1, 64),
                                         randint(512, 524288),
                                         redes_vm)

        return inventario

    def test_inventarios_iguais(self):
        inventario = self.get_inventario_completo()

        status, plano_execucao = inventario.calcular_plano_execucao(inventario)

        assert status is True
        assert not plano_execucao.acoes

    def test_inventario_local_sem_remoto(self):
        inventario = self.get_inventario_completo()

        status, plano_execucao = inventario.calcular_plano_execucao(
            Inventario(inventario.agrupamento, inventario.nuvem))

        assert status is True
        assert plano_execucao == self.get_plano_execucao_criar_inventario(
            inventario)

    def test_inventario_remoto_sem_local(self):
        inventario_remoto = self.get_inventario_completo()
        inventario_local = Inventario(
            inventario_remoto.agrupamento, inventario_remoto.nuvem)

        status, plano_execucao = inventario_local.calcular_plano_execucao(
            inventario_remoto)

        assert status is True
        assert plano_execucao == self.get_plano_execucao_excluir_inventario(
            inventario_remoto)
