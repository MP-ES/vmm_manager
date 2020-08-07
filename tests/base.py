"""
Classe com funções básicas de teste
"""
import uuid
from random import randrange, randint, choice
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.entidade.vm_rede import VMRede
from vmm_manager.entidade.vm_disco import VMDisco
from vmm_manager.entidade.vm_ansible import VMAnsible, VMAnsibleVars
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from tests.dados_teste import DadosTeste


class Base():
    MAX_VMS_POR_TESTE = 20
    MAX_REDES_POR_VM = 5
    MAX_DISCOS_POR_VM = 10
    MAX_ANSIBLE_ITERACAO = 10
    MAX_TAMANHO_DISCO = 1073741824
    MIN_CPU = 1
    MAX_CPU = 64
    MIN_RAM = 512
    MAX_RAM = 524288

    @staticmethod
    def get_inventario_completo(num_min_discos_por_vm=1):
        dados_teste = DadosTeste()
        inventario = Inventario(
            dados_teste.get_random_word(), dados_teste.get_random_word())

        for _ in range(randrange(1, Base.MAX_VMS_POR_TESTE)):
            nome_vm = dados_teste.get_nome_unico()

            redes_vm = []
            for num_iter in range(randrange(1, Base.MAX_REDES_POR_VM)):
                redes_vm.append(
                    VMRede(dados_teste.get_random_word(), num_iter == 0))

            discos_vm = []
            for num_iter in range(randrange(num_min_discos_por_vm, Base.MAX_DISCOS_POR_VM)):
                disco = VMDisco(
                    choice(list(SCDiskBusType)),
                    dados_teste.get_nome_unico(),
                    randint(1, Base.MAX_TAMANHO_DISCO),
                    choice(list(SCDiskSizeType)),
                    dados_teste.get_random_word()
                )
                disco.set_parametros_extras_vmm(
                    str(uuid.uuid4()),
                    str(uuid.uuid4()),
                    0,
                    num_iter + 1,
                )
                discos_vm.append(disco)

            vm_obj = VM(nome_vm,
                        dados_teste.get_random_word(),
                        dados_teste.get_random_word(),
                        dados_teste.get_random_word(),
                        randint(Base.MIN_CPU, Base.MAX_CPU),
                        randint(Base.MIN_RAM, Base.MAX_RAM),
                        redes_vm)
            vm_obj.add_discos_adicionais(discos_vm)
            inventario.vms[nome_vm] = vm_obj

        return inventario

    # pylint: disable=R0201
    def get_obj_inventario(self, array_yaml):
        inventario = Inventario(
            array_yaml[0][0]['agrupamento'], array_yaml[0][0]['nuvem'])

        for maquina_virtual in array_yaml[0][0]['vms']:
            vm_redes = []
            for rede_vm in maquina_virtual.get('redes', array_yaml[0][0].get('redes_padrao', [])):
                vm_redes.append(
                    VMRede(rede_vm.get('nome'), rede_vm.get('principal', False)))

            inventario.vms[maquina_virtual.get('nome')] = VM(
                maquina_virtual.get('nome'),
                maquina_virtual.get('descricao'),
                maquina_virtual.get(
                    'imagem', array_yaml[0][0].get('imagem_padrao', None)),
                maquina_virtual.get('regiao', Inventario.REGIAO_PADRAO),
                maquina_virtual.get(
                    'qtde_cpu', array_yaml[0][0].get('qtde_cpu_padrao', None)),
                maquina_virtual.get(
                    'qtde_ram_mb', array_yaml[0][0].get('qtde_ram_mb_padrao', None)),
                vm_redes
            )
        return inventario

    def get_dados_ansible_vm(self, array_yaml, nome_vm):
        lista_dados_ansible = {}

        for maquina_virtual in array_yaml[0][0]['vms']:
            if maquina_virtual.get('nome') != nome_vm:
                continue

            for item in maquina_virtual.get('ansible', {}):
                grupo = item.get('grupo')
                dados_ansible = VMAnsible(grupo)

                for variavel in item.get('vars', {}):
                    dados_ansible.variaveis.append(VMAnsibleVars(
                        variavel.get('nome'), variavel.get('valor')))

                lista_dados_ansible[grupo] = dados_ansible

        return lista_dados_ansible

    def get_discos_adicionais_vm(self, array_yaml, nome_vm):
        lista_discos_adicionais = {}

        for maquina_virtual in array_yaml[0][0]['vms']:
            if maquina_virtual.get('nome') != nome_vm:
                continue

            for item in maquina_virtual.get('discos_adicionais', {}):
                arquivo = item.get('arquivo')
                disco_adicional = VMDisco(SCDiskBusType(item.get('tipo')),
                                          arquivo,
                                          item.get('tamanho_mb'),
                                          SCDiskSizeType(
                                              item.get('tamanho_tipo')),
                                          item.get('caminho'))

                lista_discos_adicionais[arquivo] = disco_adicional

        return lista_discos_adicionais
