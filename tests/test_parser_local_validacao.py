"""
Testes do ParserLocal (casos que precisam dar erro)
"""
from unittest import mock
from random import randrange, randint
from vmm_manager.parser.parser_local import ParserLocal
from tests.base import Base
from tests.dados_teste import DadosTeste


# pylint: disable=R0201
class TestParserLocalValidacao(Base):

    def test_parser_inventario_vazio(self, tmpdir, servidor_acesso):
        arquivo_inventario = tmpdir.join('inventario_vazio.yaml')
        arquivo_inventario.write('')

        parser_local = ParserLocal(arquivo_inventario.strpath)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == 'Arquivo de inventário vazio.'

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vms_sem_imagem(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico()
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

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vm_sem_rede(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'imagem_padrao': dados_teste.get_random_word(),
             'qtde_cpu_padrao': randint(1, 64),
             'qtde_ram_mb_padrao': randint(512, 524288),
             'vms': [{
                 'nome': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.MAX_VMS_POR_TESTE))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == 'VM {} deve ter exatamente uma rede principal.'.format(
            inventario[0][0]['vms'][0]['nome'])

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_vm_sem_rede_principal(self, _, servidor_acesso, monkeypatch):
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
                 'nome': dados_teste.get_nome_unico()
             } for _ in range(randrange(1, Base.MAX_VMS_POR_TESTE))]
             },
            'inventario.yaml')]
        monkeypatch.setattr(ParserLocal, '_ParserLocal__carregar_yaml',
                            lambda mock: inventario)

        parser_local = ParserLocal(None)
        status, msg = parser_local.get_inventario(servidor_acesso)

        assert status is False
        assert msg == 'VM {} deve ter exatamente uma rede principal.'.format(
            inventario[0][0]['vms'][0]['nome'])

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_sem_grupo(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'grupo': '',
                         'vars': [
                             {
                                 'nome': dados_teste.get_random_word(),
                                 'valor': dados_teste.get_random_word()
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
        assert "vms.0.ansible.0.grupo: '' is not a caracteres alfabéticos." in msg

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_grupo_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_grupo = dados_teste.get_nome_unico()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'grupo': nome_grupo,
                         'vars': [
                             {
                                 'nome': dados_teste.get_random_word(),
                                 'valor': dados_teste.get_random_word()
                             }
                         ]
                     },
                     {
                         'grupo': nome_grupo
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
        assert msg == "Grupo ansible '{}' referenciado mais de uma vez para a VM '{}'.".format(
            nome_grupo, inventario[0][0]['vms'][0]['nome'])

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_grupo_var_duplicada(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_grupo = dados_teste.get_nome_unico()
        nome_var = dados_teste.get_nome_unico()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'grupo': nome_grupo,
                         'vars': [
                             {
                                 'nome': nome_var,
                                 'valor': dados_teste.get_random_word()
                             },
                             {
                                 'nome': nome_var,
                                 'valor': dados_teste.get_random_word()
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
        assert msg == ("Variável '{}' do grupo ansible '{}' "
                       .format(nome_var, nome_grupo) +
                       "referenciada mais de uma vez na VM '{}'."
                       .format(inventario[0][0]['vms'][0]['nome']))

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_ansible_var_invalida(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        inventario = [(
            {'agrupamento': dados_teste.get_random_word(),
             'nuvem': dados_teste.get_random_word(),
             'vms': [{
                 'nome': dados_teste.get_nome_unico(),
                 'ansible': [
                     {
                         'grupo': dados_teste.get_random_word(),
                         'vars': [
                             {
                                 'nome': ''
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
        assert "vms.0.ansible.0.vars.0.nome: '' is not a caracteres alfabéticos" in msg
        assert 'vms.0.ansible.0.vars.0.valor: Required field missing' in msg

    @mock.patch('vmm_manager.parser.parser_local.ParserLocal._ParserLocal__validar_arquivo_yaml',
                return_value=None)
    def test_parser_inventario_nome_vm_duplicado(self, _, servidor_acesso, monkeypatch):
        dados_teste = DadosTeste()
        nome_vm = dados_teste.get_nome_unico()
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