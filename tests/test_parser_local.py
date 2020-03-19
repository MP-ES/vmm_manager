"""
Testes do ParserLocal
"""
from unittest import mock
from random import randrange, randint
from vmm_manager.app.inventario import ParserLocal
from tests.base import Base
from tests.dados_teste import DadosTeste


# pylint: disable=R0201
class TestParserLocal(Base):

    def test_parser_inventario_vazio(self, tmpdir, servidor_acesso):
        arquivo_inventario = tmpdir.join('inventario_vazio.yaml')
        arquivo_inventario.write('')

        parser_local = ParserLocal(arquivo_inventario.strpath)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == 'Arquivo de inventário vazio.'

    @mock.patch('app.inventario.ParserLocal._ParserLocal__validar_arquivo_yaml', return_value=None)
    def test_parser_inventario_vms_sem_imagem(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_vm()
             } for _ in range(randrange(1, Base.MAX_VMS_POR_TESTE))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == 'Imagem da VM {} não definida.'.format(
            inventario[0][0]['vms'][0]['nome'])

    @mock.patch('app.inventario.ParserLocal._ParserLocal__validar_arquivo_yaml', return_value=None)
    def test_parser_inventario_nome_vm_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_vm = dados_teste.get_nome_vm()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(1, 64),
             'qtde_ram_mb_padrao': randint(512, 524288),
             'redes_padrao': [{
                 'nome': dados_teste.get_random_word()
             } for _ in range(randrange(1, Base.MAX_REDES_POR_VM))],
             'vms': [{
                 'nome': nome_vm
             } for _ in range(randrange(2, Base.MAX_VMS_POR_TESTE))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == 'VM {} referenciada mais de uma vez no inventário.'.format(
            inventario[0][0]['vms'][0]['nome'])

    @mock.patch('app.inventario.ParserLocal._ParserLocal__validar_arquivo_yaml', return_value=None)
    def test_parser_inventario_min_padrao(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(1, 64),
             'qtde_ram_mb_padrao': randint(512, 524288),
             'redes_padrao': [{
                 'nome': dados_teste.get_random_word()
             } for _ in range(randrange(1, Base.MAX_REDES_POR_VM))],
             'vms': [{
                 'nome': dados_teste.get_nome_vm()
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

    @mock.patch('app.inventario.ParserLocal._ParserLocal__validar_arquivo_yaml', return_value=None)
    def test_parser_inventario_min_sem_padrao(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_vm(),
                 'descricao': dados_teste.get_random_word(),
                 'imagem': dados_teste.get_random_word(),
                 'qtde_cpu': randint(1, 64),
                 'qtde_ram_mb': randint(512, 524288),
                 'redes': [{
                     'nome': dados_teste.get_random_word()
                 } for _ in range(randrange(1, Base.MAX_REDES_POR_VM))],
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
