"""
Inventory entity.
"""
import json
from vmm_manager.entidade.plan import Plan
from vmm_manager.util.config import CAMPO_AGRUPAMENTO
from vmm_manager.infra.comando import Comando
from vmm_manager.scvmm.scregion import SCRegion


def json_handle_inventario(obj):
    if isinstance(obj, Inventario):
        return obj.to_dict()
    raise ValueError('Objeto precisa ser uma instância de inventário.')


class Inventario:

    @staticmethod
    def get_json(inventario_local, inventario_remoto, all_data=True):
        for vm_name in inventario_remoto.vms:
            if vm_name not in inventario_local.vms:
                # máquina órfã: não exibir
                continue

            inventario_remoto.vms[vm_name].dados_ansible = \
                inventario_local.vms[vm_name].dados_ansible

            # definindo tipo de impressão
            inventario_remoto.vms[vm_name].to_json_dados_completos = all_data

        return True, json.dumps(inventario_remoto,
                                default=json_handle_inventario,
                                sort_keys=True, indent=4)

    def __init__(self, group, cloud):
        self.group = group
        self.cloud = cloud
        self.vms = {}

        self.__regioes_por_letra_id = None
        self.__regioes_disponiveis = None

    def get_nome_no_regiao(self, region):
        self.__retirar_regiao_pool(region)

        if region in self.__regioes_por_letra_id:
            return self.__regioes_por_letra_id[region].nome_no

        raise ValueError(f"Região '{region}' não possui nó definido.")

    def get_id_no_regiao(self, region):
        self.__retirar_regiao_pool(region)

        if region in self.__regioes_por_letra_id:
            return self.__regioes_por_letra_id[region].id_no

        raise ValueError(f"Região '{region}' não possui nó definido.")

    def get_mapeamento_regioes_to_test(self):
        # flush regions
        it_regioes = 0
        while self.__regioes_disponiveis:
            self.__retirar_regiao_pool(chr(ord('A') + it_regioes))
            it_regioes += 1

        if self.__regioes_por_letra_id is None:
            raise ValueError('Mapeamento de regiões não definido.')

        return self.__regioes_por_letra_id

    def set_regioes_disponiveis(self, regioes_disponiveis):
        self.__regioes_por_letra_id = {}
        self.__regioes_disponiveis = regioes_disponiveis

    def __retirar_regiao_pool(self, region):
        if region in self.__regioes_por_letra_id:
            return

        if not self.__regioes_disponiveis:
            return

        self.__regioes_por_letra_id[region] = self.__regioes_disponiveis.pop()

    def calcular_plano_execucao(self, inventario_remoto):
        if (self.group != inventario_remoto.group
                or self.cloud != inventario_remoto.cloud):
            return False, 'Não é possível calcular o plano de execução \
                para inventários de group ou cloud distintos.'

        plano_execucao = Plan(self.group, self.cloud)

        self.__add_acoes_criar_vms(inventario_remoto, plano_execucao)
        self.__add_acoes_execucao_excluir_vms(
            inventario_remoto, plano_execucao)

        self.__add_acoes_diferenca_vm(
            inventario_remoto, plano_execucao)
        self.__add_acoes_diferenca_discos_adicionais(
            inventario_remoto, plano_execucao)
        self.__add_acoes_diferenca_regiao(
            inventario_remoto, plano_execucao)
        self.__add_acoes_virtualizacao_aninhada(
            inventario_remoto, plano_execucao)
        self.__add_acoes_memoria_dinamica(
            inventario_remoto, plano_execucao)

        return True, plano_execucao

    def gerar_plano_exclusao(self):
        plano_execucao = Plan(self.group, self.cloud)

        for maquina_virtual in self.vms.values():
            plano_execucao.actions.append(
                maquina_virtual.get_acao_excluir_vm())

        return plano_execucao

    def is_vazio(self):
        return not self.vms

    def lista_nome_vms_str(self):
        return ','.join([f'"{vm_name}"' for vm_name in self.vms])

    def __validar_regras_locais(self):
        regioes = set()

        for maquina_virtual in self.vms.values():
            if maquina_virtual.region != SCRegion.REGIAO_PADRAO:
                regioes.add(maquina_virtual.region)

            if maquina_virtual.image is None:
                raise ValueError(
                    f'Imagem da VM {maquina_virtual.name} não definida.')

            if maquina_virtual.cpu is None:
                raise ValueError(
                    f'Quantidade de CPUs da VM {maquina_virtual.name} não definida.')

            if maquina_virtual.memory is None:
                raise ValueError(
                    f'Quantidade de memória da VM {maquina_virtual.name} não definida.')

            if maquina_virtual.get_qtde_rede_principal() != 1:
                raise ValueError(
                    f'VM {maquina_virtual.name} deve ter exatamente uma network default.')

    def validar(self, servidor_acesso):
        self.__validar_regras_locais()

        imagens = set()
        networks = set()
        regioes = set()

        for maquina_virtual in self.vms.values():
            imagens.add(maquina_virtual.image)

            if maquina_virtual.region != SCRegion.REGIAO_PADRAO:
                regioes.add(maquina_virtual.region)

            networks.update(
                [network.name for network in maquina_virtual.networks])

        cmd = Comando(
            'validar_inventario', imagens=imagens,
            cloud=self.cloud,
            networks=networks,
            servidor_vmm=servidor_acesso.servidor_vmm,
            qtde_minima_regioes=len(regioes),
            group=self.group,
            lista_nome_vms_str=self.lista_nome_vms_str(),
            campo_agrupamento=CAMPO_AGRUPAMENTO[0]
        )
        _, msg = cmd.executar(servidor_acesso)
        if msg:
            raise ValueError(msg)

    def set_discos_vms(self, additional_disks):
        for vm_name in additional_disks:
            self.vms[vm_name].add_discos_adicionais(additional_disks[vm_name])

    def __add_acoes_criar_vms(self, inventario_remoto, plano_execucao):
        vms_inserir = [
            nome_vm_local for nome_vm_local in self.vms
            if nome_vm_local not in inventario_remoto.vms
        ]
        for vm_name in vms_inserir:
            plano_execucao.actions.append(
                self.vms[vm_name].get_acao_criar_vm())

    def __add_acoes_execucao_excluir_vms(self, inventario_remoto, plano_execucao):
        vms_excluir = [
            nome_vm_remoto for nome_vm_remoto in inventario_remoto.vms
            if nome_vm_remoto not in self.vms
        ]
        for vm_name in vms_excluir:
            plano_execucao.actions.append(
                inventario_remoto.vms[vm_name].get_acao_excluir_vm())

    def __add_acoes_diferenca_discos_adicionais(self, inventario_remoto, plano_execucao):
        for vm_name, data_vm in self.vms.items():
            data_vm.add_acoes_diferenca_discos_adicionais(
                inventario_remoto.vms.get(vm_name, None),
                plano_execucao)

    def __add_acoes_diferenca_regiao(self, inventario_remoto, plano_execucao):
        for vm_name, data_vm in self.vms.items():
            data_vm.add_acoes_diferenca_regiao(
                inventario_remoto.vms.get(vm_name, None),
                plano_execucao, inventario_remoto)

    def __add_acoes_virtualizacao_aninhada(self, inventario_remoto, plano_execucao):
        for vm_name, data_vm in self.vms.items():
            data_vm.add_acoes_virtualizacao_aninhada(
                inventario_remoto.vms.get(vm_name, None),
                plano_execucao)

    def __add_acoes_memoria_dinamica(self, inventario_remoto, plano_execucao):
        for vm_name, data_vm in self.vms.items():
            data_vm.add_acoes_memoria_dinamica(
                inventario_remoto.vms.get(vm_name, None),
                plano_execucao)

    def __add_acoes_diferenca_vm(self, inventario_remoto, plano_execucao):
        for vm_name, data_vm in self.vms.items():
            if vm_name in inventario_remoto.vms:
                data_vm.add_acoes_diferenca_vm(
                    inventario_remoto.vms[vm_name], plano_execucao)

    def __eq__(self, other):
        return isinstance(other, Inventario) and (self.group == other.group
                                                  and self.cloud == other.cloud
                                                  and self.vms == other.vms)

    def __str__(self):
        return f'''
            group: {self.group}
            cloud: {self.cloud}
            vms: {self.vms}
            '''

    def to_dict(self):
        return {
            'group': self.group,
            'cloud': self.cloud,
            'vms': [vm_data.to_dict() for vm_data in self.vms.values()]
        }
