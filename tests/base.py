"""
Classe com funções básicas de teste
"""
from vmm_manager.entidade.inventario import Inventario
from vmm_manager.entidade.vm import VM
from vmm_manager.entidade.vm_rede import VMRede
from vmm_manager.parser.parser_local import ParserLocal


class Base():
    MAX_VMS_POR_TESTE = 20
    MAX_REDES_POR_VM = 5
    MAX_ANSIBLE_ITERACAO = 10

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
                maquina_virtual.get('regiao', ParserLocal.REGIAO_PADRAO),
                maquina_virtual.get(
                    'qtde_cpu', array_yaml[0][0].get('qtde_cpu_padrao', None)),
                maquina_virtual.get(
                    'qtde_ram_mb', array_yaml[0][0].get('qtde_ram_mb_padrao', None)),
                vm_redes
            )
        return inventario
