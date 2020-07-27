"""
Testes do ParserLocal
"""
from unittest import mock
from random import randrange, randint, choice
from vmm_manager.scvmm.enums import SCDiskBusType, SCDiskSizeType
from vmm_manager.parser.parser_local import ParserLocal
from tests.base import Base
from tests.dados_teste import DadosTeste


# pylint: disable=R0201
class TestParserLocal(Base):

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_min_padrao(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(1, 64),
             'qtde_ram_mb_padrao': randint(512, 524288),
             'redes_padrao': [{
                 'nome': dados_teste.get_random_word(),
                 'principal': num_iter == 0,
             } for num_iter in range(randrange(1, Base.MAX_REDES_POR_VM))],
             'vms': [{
                 'nome': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.MAX_VMS_POR_TESTE))]
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
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(1, 64),
             'qtde_ram_mb_padrao': randint(512, 524288),
             'redes_padrao': [{
                 'nome': dados_teste.get_random_word(),
                 'principal': num_iter == 0,
             } for num_iter in range(randrange(1, Base.MAX_REDES_POR_VM))],
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [{
                     'grupo': dados_teste.get_nome_unico(),
                     'vars': [{
                         'nome': dados_teste.get_nome_unico(),
                         'valor': dados_teste.get_random_word()
                     } for _ in range(randrange(0, Base.MAX_ANSIBLE_ITERACAO))],
                 } for _ in range(randrange(1, Base.MAX_ANSIBLE_ITERACAO))],
             } for _ in range(randrange(1, Base.MAX_VMS_POR_TESTE))]
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
        for nome_vm in inventario_resposta.vms:
            dados_ansible_vm = inventario_resposta.vms[nome_vm].dados_ansible
            dados_ansible_ok = self.get_dados_ansible_vm(inventario, nome_vm)

            assert not dados_ansible_vm.keys() - dados_ansible_ok.keys()
            for nome_grupo in dados_ansible_vm:
                assert dados_ansible_vm[nome_grupo] == dados_ansible_ok[nome_grupo]

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_com_discos_adicionais(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(1, 64),
             'qtde_ram_mb_padrao': randint(512, 524288),
             'redes_padrao': [{
                 'nome': dados_teste.get_random_word(),
                 'principal': num_iter == 0,
             } for num_iter in range(randrange(1, Base.MAX_REDES_POR_VM))],
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'discos_adicionais': [{
                     'arquivo': dados_teste.get_nome_unico(),
                     'tipo': choice([enum.value for enum in SCDiskBusType]),
                     'tamanho_mb': randint(1, 1073741824),
                     'tamanho_tipo': choice([enum.value for enum in SCDiskSizeType]),
                 } for _ in range(randrange(1, Base.MAX_DISCOS_POR_VM))],
             } for _ in range(randrange(1, Base.MAX_VMS_POR_TESTE))]
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
        for nome_vm in inventario_resposta.vms:
            discos_adicionais_vm = inventario_resposta.vms[nome_vm].discos_adicionais
            discos_adicionais_ok = self.get_discos_adicionais_vm(
                inventario, nome_vm)

            assert not discos_adicionais_vm.keys() - discos_adicionais_ok.keys()
            for arquivo in discos_adicionais_vm:
                assert discos_adicionais_vm[arquivo] == discos_adicionais_ok[arquivo]

    @ mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                 return_value=None)
    def test_parser_inventario_min_sem_padrao(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'descricao': dados_teste.get_random_word(),
                 'imagem': dados_teste.get_random_word(),
                 'qtde_cpu': randint(1, 64),
                 'qtde_ram_mb': randint(512, 524288),
                 'redes': [{
                     'nome': dados_teste.get_nome_unico(),
                     'principal': num_iter == 0
                 } for num_iter in range(randrange(1, Base.MAX_REDES_POR_VM))],
             } for _ in range(randrange(1, Base.MAX_VMS_POR_TESTE))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, inventario_resposta = parser_local.get_inventario(
            servidor_acesso)

        assert status is True
        assert inventario_resposta == self.get_obj_inventario(inventario)
