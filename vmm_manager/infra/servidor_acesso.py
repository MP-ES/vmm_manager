"""
Módulo relacionado ao servidor que executará os comandos PowerShell
"""
import os
import re
import socket
import tempfile
import paramiko
from vmm_manager.util.msgs import formatar_msg_erro


def escapar_echo_cmd(conteudo):
    conteudo_escapado = re.sub(
        r'(&|\\|<|>|\^|\|)', r'^\1', conteudo, flags=re.RegexFlag.MULTILINE)
    conteudo_escapado = re.sub(r'\n', ';', conteudo_escapado)
    return conteudo_escapado


class ServidorAcesso:
    __PASTA_TEMPORARIA = 'vmm_temp'
    __ENCODE_CMD = 'cp850'
    __ENCODE_WINDOWS = 'iso-8859-1'

    @staticmethod
    def __get_caminho_arquivo(nome):
        return '{}/{}'.format(ServidorAcesso.__PASTA_TEMPORARIA, os.path.basename(nome))

    def __init__(self, servidor, usuario, senha, servidor_vmm):
        self.servidor = servidor
        self.servidor_vmm = servidor_vmm
        self.usuario = usuario
        self.senha = senha
        self.conexao = None

    def __del__(self):
        if self.conexao:
            self.conexao.close()

    def __conectar(self):
        try:
            self.conexao = paramiko.SSHClient()
            self.conexao.load_system_host_keys()
            self.conexao.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.conexao.connect(hostname=self.servidor,
                                 username=self.usuario,
                                 password=self.senha)
            return True
        except paramiko.AuthenticationException:
            print(formatar_msg_erro('\nUsuário ou senha inválidos.'))
            return False
        except paramiko.SSHException as ex:
            print(formatar_msg_erro(
                '\nErro ao estabelecer conexão SSH: {}'.format(ex)))
            return False
        except (socket.error, socket.timeout) as ex:
            print(formatar_msg_erro('\nErro de socket: {}'.format(ex)))
            return False

    def __executar_comando(self, cmd):
        if self.__conectar():
            try:
                _, stdout, stderr = self.conexao.exec_command(cmd)
                stderr_msg = stderr.read().decode(ServidorAcesso.__ENCODE_CMD)
                if stdout.channel.recv_exit_status() != 0 or stderr_msg:
                    return False, stderr_msg

                return True, stdout.read().decode(ServidorAcesso.__ENCODE_CMD)
            except paramiko.SSHException as ex:
                return False, "Erro ao executar comando '{}': {}".format(cmd, ex)
            except socket.error as ex:
                return False, "Erro de socket ao executar '{}': {}".format(cmd, ex)
        else:
            return False, 'Conexão não estabelecida.'

    def __enviar_arquivo(self, nome_arquivo):
        self.__executar_comando('if not exist "{}" mkdir "{}"'.format(
            ServidorAcesso.__PASTA_TEMPORARIA, ServidorAcesso.__PASTA_TEMPORARIA))

        return self.conexao.open_sftp().put(nome_arquivo,
                                            ServidorAcesso.__get_caminho_arquivo(
                                                nome_arquivo),
                                            confirm=True)

    def __excluir_arquivo(self, nome):
        self.__executar_comando('del {}'.format(
            ServidorAcesso.__get_caminho_arquivo(nome).replace('/', '\\')))

    def get_caminho_lockfile(self, agrupamento, nuvem):
        return self.__get_caminho_arquivo('{}-{}.lock'.format(agrupamento, nuvem))

    def executar_script(self, nome, conteudo):
        try:
            arquivo_script = tempfile.NamedTemporaryFile(
                prefix=nome, suffix='.ps1', delete=True)
            arquivo_script.file.write(conteudo.encode(
                ServidorAcesso.__ENCODE_WINDOWS))
            arquivo_script.flush()

            self.__enviar_arquivo(arquivo_script.name)

            resultado = self.__executar_comando('powershell.exe -file {}'.format(
                ServidorAcesso.__get_caminho_arquivo(arquivo_script.name)))

            self.__excluir_arquivo(arquivo_script.name)
            return resultado
        # pylint: disable=broad-except
        except Exception as ex:
            return False, 'Erro ao executar script: {}'.format(ex)
        finally:
            arquivo_script.close()
