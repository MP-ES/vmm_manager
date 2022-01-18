"""
Representação de um inventário
"""
import json
from vmm_manager.entidade.plano_execucao import PlanoExecucao
from vmm_manager.util.config import CAMPO_AGRUPAMENTO
from vmm_manager.infra.comando import Comando
from vmm_manager.scvmm.scregion import SCRegion


def json_handle_inventario(obj):
    if isinstance(obj, Inventario):
        return obj.to_dict()
    raise ValueError('Objeto precisa ser uma instância de inventário.')


class Inventario:

    @staticmethod
    def get_json(inventario_local, inventario_remoto, dados_completos=True):
        for nome_vm in inventario_remoto.vms:
            if nome_vm not in inventario_local.vms:
                # máquina órfã: não exibir
                continue

            inventario_remoto.vms[nome_vm].dados_ansible = \
                inventario_local.vms[nome_vm].dados_ansible

            # definindo tipo de impressão
            inventario_remoto.vms[nome_vm].to_json_dados_completos = dados_completos

        return True, json.dumps(inventario_remoto,
                                default=json_handle_inventario,
                                sort_keys=True, indent=4)

    def __init__(self, agrupamento, nuvem):
        self.agrupamento = agrupamento
        self.nuvem = nuvem
        self.vms = {}

        self.__regioes_por_letra_id = None

    def get_nome_no_regiao(self, regiao):
        if regiao in self.__regioes_por_letra_id:
            return self.__regioes_por_letra_id[regiao].nome_no

        raise ValueError(f"Região '{regiao}' não possui nó definido.")

    def get_id_no_regiao(self, regiao):
        if regiao in self.__regioes_por_letra_id:
            return self.__regioes_por_letra_id[regiao].id_no

        raise ValueError(f"Região '{regiao}' não possui nó definido.")

    def get_mapeamento_regioes(self):
        if self.__regioes_por_letra_id is None:
            ValueError('Mapeamento de regiões não definido.')

        return self.__regioes_por_letra_id

    def set_mapeamento_regioes(self, regioes_disponiveis):
        self.__regioes_por_letra_id = {}
        for regiao in regioes_disponiveis:
            self.__regioes_por_letra_id[regiao.letra_id] = regiao

    def calcular_plano_execucao(self, inventario_remoto):
        if (self.agrupamento != inventario_remoto.agrupamento
                or self.nuvem != inventario_remoto.nuvem):
            return False, 'Não é possível calcular o plano de execução \
                para inventários de agrupamento ou nuvem distintos.'

        plano_execucao = PlanoExecucao(self.agrupamento, self.nuvem)

        self.__add_acoes_criar_vms(inventario_remoto, plano_execucao)
        self.__add_acoes_execucao_excluir_vms(
            inventario_remoto, plano_execucao)

        self.__add_acoes_diferenca_vm(
            inventario_remoto, plano_execucao)
        self.__add_acoes_diferenca_discos_adicionais(
            inventario_remoto, plano_execucao)
        self.__add_acoes_diferenca_regiao(
            inventario_remoto, plano_execucao)

        return True, plano_execucao

    def gerar_plano_exclusao(self):
        plano_execucao = PlanoExecucao(self.agrupamento, self.nuvem)

        for maquina_virtual in self.vms.values():
            plano_execucao.acoes.append(maquina_virtual.get_acao_excluir_vm())

        return plano_execucao

    def is_vazio(self):
        return not self.vms

    def lista_nome_vms_str(self):
        return ','.join([f'"{nome_vm}"' for nome_vm in self.vms])

    def __validar_regras_locais(self):
        regioes = set()

        for maquina_virtual in self.vms.values():
            if maquina_virtual.regiao != SCRegion.REGIAO_PADRAO:
                regioes.add(maquina_virtual.regiao)

            if maquina_virtual.imagem is None:
                raise ValueError(
                    f'Imagem da VM {maquina_virtual.nome} não definida.')

            if maquina_virtual.qtde_cpu is None:
                raise ValueError(
                    f'Quantidade de CPUs da VM {maquina_virtual.nome} não definida.')

            if maquina_virtual.qtde_ram_mb is None:
                raise ValueError(
                    f'Quantidade de memória da VM {maquina_virtual.nome} não definida.')

            if maquina_virtual.get_qtde_rede_principal() != 1:
                raise ValueError(
                    f'VM {maquina_virtual.nome} deve ter exatamente uma rede principal.')

        regioes_validas = [chr(ord('A') + num)
                           for num in range(0, len(regioes))]
        for regiao in regioes:
            if regiao not in regioes_validas:
                raise ValueError(
                    f"Região '{regiao}' não é válida.")

    def validar(self, servidor_acesso):
        self.__validar_regras_locais()

        imagens = set()
        redes = set()
        regioes = set()

        for maquina_virtual in self.vms.values():
            imagens.add(maquina_virtual.imagem)

            if maquina_virtual.regiao != SCRegion.REGIAO_PADRAO:
                regioes.add(maquina_virtual.regiao)

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

    def set_discos_vms(self, discos_adicionais):
        for nome_vm in discos_adicionais:
            self.vms[nome_vm].add_discos_adicionais(discos_adicionais[nome_vm])

    def __add_acoes_criar_vms(self, inventario_remoto, plano_execucao):
        vms_inserir = [
            nome_vm_local for nome_vm_local in self.vms
            if nome_vm_local not in inventario_remoto.vms
        ]
        for nome_vm in vms_inserir:
            plano_execucao.acoes.append(self.vms[nome_vm].get_acao_criar_vm())

    def __add_acoes_execucao_excluir_vms(self, inventario_remoto, plano_execucao):
        vms_excluir = [
            nome_vm_remoto for nome_vm_remoto in inventario_remoto.vms
            if nome_vm_remoto not in self.vms
        ]
        for nome_vm in vms_excluir:
            plano_execucao.acoes.append(
                inventario_remoto.vms[nome_vm].get_acao_excluir_vm())

    def __add_acoes_diferenca_discos_adicionais(self, inventario_remoto, plano_execucao):
        for nome_vm, data_vm in self.vms.items():
            data_vm.add_acoes_diferenca_discos_adicionais(
                inventario_remoto.vms.get(nome_vm, None),
                plano_execucao)

    def __add_acoes_diferenca_regiao(self, inventario_remoto, plano_execucao):
        for nome_vm, data_vm in self.vms.items():
            data_vm.add_acoes_diferenca_regiao(
                inventario_remoto.vms.get(nome_vm, None),
                plano_execucao, inventario_remoto)

    def __add_acoes_diferenca_vm(self, inventario_remoto, plano_execucao):
        for nome_vm, data_vm in self.vms.items():
            if nome_vm in inventario_remoto.vms:
                data_vm.add_acoes_diferenca_vm(
                    inventario_remoto.vms[nome_vm], plano_execucao)

    def __eq__(self, other):
        return isinstance(other, Inventario) and (self.agrupamento == other.agrupamento
                                                  and self.nuvem == other.nuvem
                                                  and self.vms == other.vms)

    def __str__(self):
        return f'''
            agrupamento: {self.agrupamento}
            nuvem: {self.nuvem}
            vms: {self.vms}
            '''

    def to_dict(self):
        return {
            'agrupamento': self.agrupamento,
            'nuvem': self.nuvem,
            'vms': [vm_data.to_dict() for vm_data in self.vms.values()]
        }
