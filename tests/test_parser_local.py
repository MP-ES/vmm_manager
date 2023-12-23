"""
Testes do ParserLocal
"""
from unittest import mock
from random import randrange, randint, choice, getrandbits
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.parser.parser_local import ParserLocal
from tests.base import Base
from tests.dados_teste import DadosTeste


class TestParserLocal(Base):

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_min_padrao(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'image_default': dados_teste.get_random_word(),
             'cpu_default': randint(Base.CPU_MIN, Base.CPU_MAX),
             'memory_default': randint(Base.RAM_MIN, Base.RAM_MAX),
             'dynamic_memory_default': bool(getrandbits(1)),
             'nested_virtualization_default': bool(getrandbits(1)),
             'networks_default': [{
                 'name': dados_teste.get_random_word(),
                 'default': num_iter == 0,
             } for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'name': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, inventario_resposta = parser_local.get_inventario(
            servidor_acesso)

        assert status is True
        assert inventario_resposta == self.get_obj_inventario(inventario)

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_com_ansible(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'image_default': dados_teste.get_random_word(),
             'cpu_default': randint(Base.CPU_MIN, Base.CPU_MAX),
             'memory_default': randint(Base.RAM_MIN, Base.RAM_MAX),
             'dynamic_memory_default': bool(getrandbits(1)),
             'nested_virtualization_default': bool(getrandbits(1)),
             'networks_default': [{
                 'name': dados_teste.get_nome_unico(),
                 'default': num_iter == 0,
             } for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'ansible': [{
                     'group': dados_teste.get_nome_unico(),
                     'vars': [{
                         'name': dados_teste.get_nome_unico(),
                         'value': dados_teste.get_random_word()
                     } for _ in range(randrange(0, Base.ANSIBLE_ITERACAO_MAX))],
                 } for _ in range(randrange(1, Base.ANSIBLE_ITERACAO_MAX))],
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, inventario_resposta = parser_local.get_inventario(
            servidor_acesso)

        # Assert inventário
        assert status is True
        assert inventario_resposta == self.get_obj_inventario(inventario)

        # Assert dados ansible
        for nome_vm, data_vm in inventario_resposta.vms.items():
            dados_ansible_vm = data_vm.dados_ansible
            dados_ansible_ok = self.get_dados_ansible_vm(inventario, nome_vm)

            assert not dados_ansible_vm.keys() - dados_ansible_ok.keys()
            for nome_grupo in dados_ansible_vm:
                assert dados_ansible_vm[nome_grupo] == dados_ansible_ok[nome_grupo]

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_com_discos_adicionais(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'image_default': dados_teste.get_random_word(),
             'cpu_default': randint(Base.CPU_MIN, Base.CPU_MAX),
             'memory_default': randint(Base.RAM_MIN, Base.RAM_MAX),
             'dynamic_memory_default': bool(getrandbits(1)),
             'nested_virtualization_default': bool(getrandbits(1)),
             'networks_default': [{
                 'name': dados_teste.get_nome_unico(),
                 'default': num_iter == 0,
             } for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX))],
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'additional_disks': [{
                     'file': dados_teste.get_nome_unico(),
                     'bus_type': choice([enum.value for enum in SCDiskBusType]),
                     'size_mb': randint(1, 1073741824),
                     'size_type': choice([enum.value for enum in SCDiskSizeType]),
                 } for _ in range(randrange(1, Base.DISCOS_POR_VM_MAX))],
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, inventario_resposta = parser_local.get_inventario(
            servidor_acesso)

        # Assert inventário
        assert status is True
        assert inventario_resposta == self.get_obj_inventario(inventario)

        # Assert discos adicionais
        for nome_vm, data_vm in inventario_resposta.vms.items():
            discos_adicionais_vm = data_vm.additional_disks
            discos_adicionais_ok = self.get_discos_adicionais_vm(
                inventario, nome_vm)

            assert not discos_adicionais_vm.keys() - discos_adicionais_ok.keys()
            for file in discos_adicionais_vm:
                assert discos_adicionais_vm[file] == discos_adicionais_ok[file]

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_min_sem_padrao(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'description': dados_teste.get_random_word(),
                 'image': dados_teste.get_random_word(),
                 'cpu': randint(Base.CPU_MIN, Base.CPU_MAX),
                 'memory': randint(Base.RAM_MIN, Base.RAM_MAX),
                 'dynamic_memory': bool(getrandbits(1)),
                 'nested_virtualization': bool(getrandbits(1)),
                 'networks': [{
                     'name': dados_teste.get_nome_unico(),
                     'default': num_iter == 0
                 } for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX))],
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, inventario_resposta = parser_local.get_inventario(
            servidor_acesso)

        assert status is True
        assert inventario_resposta == self.get_obj_inventario(inventario)

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_min_com_mem_dinam_virtualizacao_aninhada_padrao(
        self,
        _,
        servidor_acesso,
        monkeypatch
    ):
        dados_teste = DadosTeste()
        inventario = [(
            {'group': dados_teste.get_random_word(),
             'cloud': dados_teste.get_random_word(),
             'vms': [{
                 'name': dados_teste.get_nome_unico(),
                 'description': dados_teste.get_random_word(),
                 'image': dados_teste.get_random_word(),
                 'cpu': randint(Base.CPU_MIN, Base.CPU_MAX),
                 'memory': randint(Base.RAM_MIN, Base.RAM_MAX),
                 'networks': [{
                     'name': dados_teste.get_nome_unico(),
                     'default': num_iter == 0
                 } for num_iter in range(randrange(1, Base.REDES_POR_VM_MAX))],
             } for _ in range(randrange(1, Base.VMS_POR_TESTE_MAX))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, inventario_resposta = parser_local.get_inventario(
            servidor_acesso)

        assert status is True
        assert inventario_resposta == self.get_obj_inventario(inventario)
