"""
Classe com funções básicas de teste
"""
import uuid
from random import randrange, randint, choice, getrandbits
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.entidade.vm_rede import VMRede
from vmm_manager.entidade.vm_disco import VMDisco
from vmm_manager.entidade.vm_ansible import VMAnsible, VMAnsibleVars
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.scvmm.scregion import SCRegion
from tests.dados_teste import DadosTeste


class Base():
    VMS_POR_TESTE_MAX = 20
    REDES_POR_VM_MAX = 5
    DISCOS_POR_VM_MAX = 10
    ANSIBLE_ITERACAO_MAX = 10
    TAMANHO_DISCO_MIN = 1
    TAMANHO_DISCO_MAX = 1073741824
    CPU_MIN = 1
    CPU_MAX = 64
    RAM_MIN = 512
    RAM_MAX = 524288
    REGIOES_QTDE = 10

    @staticmethod
    def get_inventario_completo(num_min_discos_por_vm=1):
        dados_teste = DadosTeste()
        inventario = Inventario(
            dados_teste.get_random_word(), dados_teste.get_random_word())

        # regiões
        regioes = []
        for num_iter in range(0, Base.REGIOES_QTDE):
            regioes.append(SCRegion(
                str(uuid.uuid4()),
                dados_teste.get_nome_unico(),
                dados_teste.get_random_word(),
                dados_teste.get_random_word(),
                chr(ord('A') + num_iter)))
        inventario.set_regioes_disponiveis(regioes)

        for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX)):
            nome_vm = dados_teste.get_nome_unico()

            # redes
            redes_vm = []
            for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX)):
                redes_vm.append(
                    VMRede(dados_teste.get_random_word(), num_iter == 0))

            # discos adicionais
            discos_vm = []
            for num_iter in range(randrange(num_min_discos_por_vm, Base.DISCOS_POR_VM_MAX)):
                disco = VMDisco(
                    choice(list(SCDiskBusType)),
                    dados_teste.get_nome_unico(),
                    randint(Base.TAMANHO_DISCO_MIN, Base.TAMANHO_DISCO_MAX),
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

            regiao_vm = DadosTeste.get_random_regiao_vm(Base.REGIOES_QTDE)
            vm_obj = VM(nome_vm,
                        dados_teste.get_random_word(),
                        dados_teste.get_random_word(),
                        regiao_vm,
                        randint(Base.CPU_MIN, Base.CPU_MAX),
                        randint(Base.RAM_MIN, Base.RAM_MAX),
                        redes_vm,
                        virtualizacao_aninhada=bool(getrandbits(1)),
                        memoria_dinamica=bool(getrandbits(1)),
                        no_regiao=inventario.get_nome_no_regiao(regiao_vm))
            vm_obj.add_discos_adicionais(discos_vm)
            inventario.vms[nome_vm] = vm_obj

        return inventario

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
                maquina_virtual.get('regiao', SCRegion.REGIAO_PADRAO),
                maquina_virtual.get(
                    'qtde_cpu', array_yaml[0][0].get('qtde_cpu_padrao', None)),
                maquina_virtual.get(
                    'qtde_ram_mb', array_yaml[0][0].get('qtde_ram_mb_padrao', None)),
                vm_redes,
                virtualizacao_aninhada=maquina_virtual.
                get('virtualizacao_aninhada', array_yaml[0][0].get(
                    'virtualizacao_aninhada_padrao', False)),
                memoria_dinamica=maquina_virtual.get(
                    'memoria_dinamica', array_yaml[0][0].get('memoria_dinamica_padrao', True)),
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
