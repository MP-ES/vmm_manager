"""
Representação de um inventário
"""
import json
from vmm_manager.entidade.plano_execucao import PlanoExecucao
from vmm_manager.entidade.acao import Acao
from vmm_manager.util.config import CAMPO_AGRUPAMENTO
from vmm_manager.infra.comando import Comando


def json_handle_inventario(obj):
    if isinstance(obj, Inventario):
        return obj.to_dict()
    raise ValueError('Objeto precisa ser uma instância de inventário.')


class Inventario:
    REGIAO_PADRAO = 'default'

    @staticmethod
    def get_json(inventario_local, inventario_remoto):
        for nome_vm in inventario_remoto.vms:
            if nome_vm not in inventario_local.vms:
                # máquina órfã: não exibir
                continue

            inventario_remoto.vms[nome_vm].dados_ansible = \
                inventario_local.vms[nome_vm].dados_ansible

        return True, json.dumps(inventario_remoto,
                                default=json_handle_inventario,
                                sort_keys=True, indent=4)

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

    def lista_nome_vms_str(self):
        return ','.join(['"{}"'.format(nome_vm) for nome_vm in self.vms])

    def validar_no_servidor(self, servidor_acesso):
        imagens = set()
        redes = set()
        regioes = set()

        for maquina_virtual in self.vms.values():
            if maquina_virtual.imagem is None:
                raise ValueError(
                    'Imagem da VM {} não definida.'.format(maquina_virtual.nome))
            imagens.add(maquina_virtual.imagem)

            if maquina_virtual.regiao != Inventario.REGIAO_PADRAO:
                regioes.add(maquina_virtual.regiao)

            if maquina_virtual.qtde_cpu is None:
                raise ValueError(
                    'Quantidade de CPUs da VM {} não definida.'.format(maquina_virtual.nome))

            if maquina_virtual.qtde_ram_mb is None:
                raise ValueError(
                    'Quantidade de memória da VM {} não definida.'.format(maquina_virtual.nome))

            if maquina_virtual.get_qtde_rede_principal() != 1:
                raise ValueError(
                    'VM {} deve ter exatamente uma rede principal.'.format(maquina_virtual.nome))

            redes.update([rede.nome for rede in maquina_virtual.redes])

        cmd = Comando('validar_inventario', imagens=imagens,
                      nuvem=self.nuvem,
                      redes=redes,
                      servidor_vmm=servidor_acesso.servidor_vmm,
                      qtde_minima_regioes=len(regioes),
                      agrupamento=self.agrupamento,
                      lista_nome_vms_str=self.lista_nome_vms_str(),
                      campo_agrupamento=CAMPO_AGRUPAMENTO[0])
        _, msg = cmd.executar(servidor_acesso)
        if msg:
            raise ValueError(msg)

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
                     redes=[rede.nome for rede in self.vms[nome_vm].redes],
                     rede_principal=self.vms[nome_vm].get_rede_principal()
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

    def to_dict(self):
        return {
            'agrupamento': self.agrupamento,
            'nuvem': self.nuvem,
            'vms': [self.vms[vm_name].to_dict() for vm_name in self.vms]
        }
