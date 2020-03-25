"""
Representação de um inventário
"""

from vmm_manager.entidade.plano_execucao import PlanoExecucao
from vmm_manager.entidade.acao import Acao


class Inventario:
    def __init__(self, agrupamento, nuvem):
        self.agrupamento = agrupamento
        self.nuvem = nuvem
        self.vms = {}

    def calcular_plano_execucao(self, inventario_remoto):
        if (self.agrupamento != inventario_remoto.agrupamento
                or self.nuvem != inventario_remoto.nuvem):
            return False, 'Não é possível calcular o plano de execução \
                para inventários de agrupamento ou nuvem distintos.'

        plano_execucao = PlanoExecucao(self.agrupamento, self.nuvem)

        self.__add_acoes_criar_vms(inventario_remoto, plano_execucao)
        self.__add_acoes_execucao_excluir_vms(
            inventario_remoto, plano_execucao)

        return True, plano_execucao

    def gerar_plano_exclusao(self):
        plano_execucao = PlanoExecucao(self.agrupamento, self.nuvem)

        for maquina_virtual in self.vms.values():
            plano_execucao.acoes.append(
                Acao('excluir_vm',
                     id_vmm=maquina_virtual.id_vmm
                     )
            )

        return plano_execucao

    def is_vazio(self):
        return not self.vms

    def __add_acoes_criar_vms(self, inventario_remoto, plano_execucao):
        vms_inserir = [
            nome_vm_local for nome_vm_local in self.vms
            if nome_vm_local not in inventario_remoto.vms
        ]
        for nome_vm in vms_inserir:
            plano_execucao.acoes.append(
                Acao('criar_vm',
                     nome=self.vms[nome_vm].nome,
                     descricao=self.vms[nome_vm].descricao,
                     imagem=self.vms[nome_vm].imagem,
                     regiao=self.vms[nome_vm].regiao,
                     qtde_cpu=self.vms[nome_vm].qtde_cpu,
                     qtde_ram_mb=self.vms[nome_vm].qtde_ram_mb,
                     redes=[rede['nome'] for rede in self.vms[nome_vm].redes]
                     )
            )

    def __add_acoes_execucao_excluir_vms(self, inventario_remoto, plano_execucao):
        vms_excluir = [
            nome_vm_remoto for nome_vm_remoto in inventario_remoto.vms
            if nome_vm_remoto not in self.vms
        ]
        for nome_vm in vms_excluir:
            plano_execucao.acoes.append(
                Acao('excluir_vm',
                     id_vmm=inventario_remoto.vms[nome_vm].id_vmm
                     )
            )

    def __eq__(self, other):
        return isinstance(other, Inventario) and (self.agrupamento == other.agrupamento
                                                  and self.nuvem == other.nuvem
                                                  and self.vms == other.vms)

    def __str__(self):
        return '''
            agrupamento: {}
            nuvem: {}
            vms: {}
            '''.format(self.agrupamento,
                       self.nuvem,
                       self.vms)
