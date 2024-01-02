"""
Testes do ParserLocal (casos que precisam dar erro)
"""
import re
from random import choice, randint, randrange
from unittest import mock

from tests.base import Base
from tests.dados_teste import DadosTeste
from vmm_manager.parser.parser_local import ParserLocal
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType


class TestParserLocalValidacao(Base):

    def test_parser_inventario_vazio(self, tmpdir, servidor_acesso):
        inventory_file = tmpdir.join('inventario_vazio.yaml')
        inventory_file.write('')

        parser_local = ParserLocal(inventory_file.strpath)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == 'Arquivo de inventário vazio.'

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vms_sem_imagem(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Imagem da VM {inventario[0][0]['vms'][0]['name']} não definida."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vms_nome_invalido(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        qtde_vms = randrange(1, Base.VMS_POR_TESTE_MAX)
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_random_nome_vm_incorreto()
             } for _ in range(qtde_vms)]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert qtde_vms == sum(1 for _ in re.finditer(
            re.escape('is not a alphanumeric characters (max 15)'), msg))

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vm_sem_rede(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'image_default': dados_teste.get_random_word(),
             'cpu_default': randint(Base.CPU_MIN, Base.CPU_MAX),
             'memory_default': randint(Base.RAM_MIN, Base.RAM_MAX),
             'vms': [{
                 'name': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"VM {inventario[0][0]['vms'][0]['name']}" \
            ' deve ter exatamente uma network default.'

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vm_sem_rede_principal(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'image_default': dados_teste.get_random_word(),
             'cpu_default': randint(Base.CPU_MIN, Base.CPU_MAX),
             'memory_default': randint(Base.RAM_MIN, Base.RAM_MAX),
             'networks_default': [{
                 'name': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'name': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"VM {inventario[0][0]['vms'][0]['name']}" \
            ' deve ter exatamente uma network default.'

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vm_rede_duplicada(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_rede = dados_teste.get_nome_unico()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'image_default': dados_teste.get_random_word(),
             'cpu_default': randint(Base.CPU_MIN, Base.CPU_MAX),
             'memory_default': randint(Base.RAM_MIN, Base.RAM_MAX),
             'networks_default': [{
                 'name': nome_rede,
                 'default': num_iter == 0,
             } for num_iter in range(randrange(2, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'name': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Rede '{nome_rede}' referenciada mais de uma vez " \
            f"para a VM '{inventario[0][0]['vms'][0]['name']}'."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vms_com_regiao(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'image_default': dados_teste.get_random_word(),
             'cpu_default': randint(Base.CPU_MIN, Base.CPU_MAX),
             'memory_default': randint(Base.RAM_MIN, Base.RAM_MAX),
             'networks_default': [{
                 'name': dados_teste.get_nome_unico(),
                 'default': num_iter == 0,
             } for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'region': DadosTeste.get_regiao_vm_por_iteracao(num_iter)
             } for num_iter in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, _ = parser_local.get_inventario(servidor_acesso)

        assert status is True

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_sem_grupo(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'group': '',
                         'vars': [
                             {
                                 'name': dados_teste.get_random_word(),
                                 'value': dados_teste.get_random_word()
                             }
                         ]
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert "vms.0.ansible.0.group: '' is not a alphanumeric characters." in msg

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_grupo_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_grupo = dados_teste.get_nome_unico()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'group': nome_grupo,
                         'vars': [
                             {
                                 'name': dados_teste.get_random_word(),
                                 'value': dados_teste.get_random_word()
                             }
                         ]
                     },
                     {
                         'group': nome_grupo
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Grupo ansible '{nome_grupo}' referenciado mais de uma vez " \
            f"para a VM '{inventario[0][0]['vms'][0]['name']}'."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_grupo_var_duplicada(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_grupo = dados_teste.get_nome_unico()
        nome_var = dados_teste.get_nome_unico()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'group': nome_grupo,
                         'vars': [
                             {
                                 'name': nome_var,
                                 'value': dados_teste.get_random_word()
                             },
                             {
                                 'name': nome_var,
                                 'value': dados_teste.get_random_word()
                             }
                         ]
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Variável '{nome_var}' do group ansible '{nome_grupo}' " \
            f"referenciada mais de uma vez na VM '{inventario[0][0]['vms'][0]['name']}'."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_var_invalida(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'group': dados_teste.get_random_word(),
                         'vars': [
                             {
                                 'name': ''
                             }
                         ]
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert "vms.0.ansible.0.vars.0.name: '' is not a alphanumeric characters" in msg
        assert 'vms.0.ansible.0.vars.0.value: Required field missing' in msg

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_disco_adicional_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        file = dados_teste.get_nome_unico()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'additional_disks': [
                     {
                         'file': file,
                         'bus_type': choice([enum.value for enum in SCDiskBusType]),
                         'size_mb': randint(Base.TAMANHO_DISCO_MIN, Base.TAMANHO_DISCO_MAX),
                         'size_type': choice([enum.value for enum in SCDiskSizeType]),
                     },
                     {
                         'file': file,
                         'bus_type': choice([enum.value for enum in SCDiskBusType]),
                         'size_mb': randint(Base.TAMANHO_DISCO_MIN, Base.TAMANHO_DISCO_MAX),
                         'size_type': choice([enum.value for enum in SCDiskSizeType]),
                     }
                 ]
             }]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"Disco '{file}' referenciado mais de uma vez " \
            f"para a VM '{inventario[0][0]['vms'][0]['name']}'."

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_nome_vm_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        vm_name = dados_teste.get_nome_unico()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'image_default': dados_teste.get_random_word(),
             'cpu_default': randint(Base.CPU_MIN, Base.CPU_MAX),
             'memory_default': randint(Base.RAM_MIN, Base.RAM_MAX),
             'networks_default': [{
                 'name': dados_teste.get_random_word()
             } for _ in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'name': vm_name
             } for _ in range(randrange(2, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == f"VM {inventario[0][0]['vms'][0]['name']}" \
            ' referenciada mais de uma vez no inventário.'
