"""
Configuração dos testes
"""
import pytest


@pytest.fixture(scope='function')
def servidor_acesso(mocker):
    srv = mocker.Mock()
    srv.executar_script.return_value = True, ''
    return srv
