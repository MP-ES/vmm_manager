"""
Módulo relacionado ao servidor que executará os comandos PowerShell
"""
import os
import re
import socket
import tempfile

import paramiko


def escapar_echo_cmd(conteudo):
    conteudo_escapado = re.sub(
        r'(&|\\|<|>|\^|\|)', r'^\1', conteudo, flags=re.RegexFlag.MULTILINE)
    conteudo_escapado = re.sub(r'\n', ';', conteudo_escapado)
    return conteudo_escapado


class AccessServer:
    __PASTA_TEMPORARIA = 'vmm_temp'
    __ENCODE_CMD = 'cp850'
    __ENCODE_WINDOWS = 'iso-8859-1'
    __TIMEOUT_CONEXAO = 60
    __DEFAULT_SSH_PORT = 22

    @staticmethod
    def __get_caminho_arquivo(name):
        return f'{AccessServer.__PASTA_TEMPORARIA}/{os.path.basename(name)}'

    def __init__(self, servidor, usuario, senha, vmm_server):
        self.servidor = servidor
        self.vmm_server = vmm_server
        self.usuario = usuario
        self.senha = senha

        self.conexao = None
        self.conexao_sftp = None
        self.__msg_erro_conexao = None
        self.__msg_erro_conexao_sftp = None

    def __del__(self):
        if self.conexao:
            self.conexao.close()
        if self.conexao_sftp:
            self.conexao_sftp.close()

    def get_msg_erro_conexao(self):
        if self.__msg_erro_conexao:
            return f'It was not possible to connect to the access server. {self.__msg_erro_conexao}'
        return None

    def get_msg_erro_conexao_sftp(self):
        if self.__msg_erro_conexao_sftp:
            return ('It was not possible to open a SFPT connection '
                    f'with the access server. {self.__msg_erro_conexao_sftp}')
        return None

    def __is_conexao_ok(self):
        if self.conexao:
            self.conexao.close()
        self.__conectar()
        return not self.__msg_erro_conexao

    def __conectar(self):
        try:
            self.conexao = paramiko.SSHClient()
            self.conexao.load_system_host_keys()
            self.conexao.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.conexao.connect(hostname=self.servidor,
                                 port=self.__DEFAULT_SSH_PORT,
                                 username=self.usuario,
                                 password=self.senha,
                                 banner_timeout=AccessServer.__TIMEOUT_CONEXAO)
        except paramiko.AuthenticationException:
            self.__msg_erro_conexao = 'User or password invalid.'
        except paramiko.SSHException as ex:
            self.__msg_erro_conexao = f'Error to establish SSH connection: {ex}'
        except (socket.error, socket.timeout) as ex:
            self.__msg_erro_conexao = f'Socket error: {ex}'

    def __is_conexao_sftp_ok(self):
        if self.conexao_sftp:
            self.conexao_sftp.close()
        self.__conectar_sftp()
        return not self.__msg_erro_conexao_sftp

    def __conectar_sftp(self):
        try:
            paramiko_transport = paramiko.Transport(
                (self.servidor, self.__DEFAULT_SSH_PORT))
            paramiko_transport.connect(
                username=self.usuario, password=self.senha)
            self.conexao_sftp = paramiko.SFTPClient.from_transport(
                paramiko_transport)

        except paramiko.AuthenticationException:
            self.__msg_erro_conexao_sftp = 'User or password invalid.'
        except paramiko.SSHException as ex:
            self.__msg_erro_conexao_sftp = f'Error to establish SSH connection: {ex}'
        except (socket.error, socket.timeout) as ex:
            self.__msg_erro_conexao_sftp = f'Socket error: {ex}'

    def __executar_comando(self, cmd):
        if self.__is_conexao_ok():
            try:
                _, stdout, stderr = self.conexao.exec_command(cmd)
                stderr_msg = stderr.read().decode(AccessServer.__ENCODE_CMD)
                if stdout.channel.recv_exit_status() != 0 or stderr_msg:
                    return False, stderr_msg

                return True, stdout.read().decode(AccessServer.__ENCODE_CMD)
            except paramiko.SSHException as ex:
                return False, f"Error to execute '{cmd}': {ex}"
            except socket.error as ex:
                return False, f"Socket error to execute '{cmd}': {ex}"
        else:
            return False, self.get_msg_erro_conexao()

    def __enviar_arquivo(self, nome_arquivo):
        resultado = self.__executar_comando(
            f'if not exist "{AccessServer.__PASTA_TEMPORARIA}" '
            f'mkdir "{AccessServer.__PASTA_TEMPORARIA}"')

        if not resultado[0]:
            return resultado

        if self.__is_conexao_sftp_ok():
            file_attrs = self.conexao_sftp.put(
                nome_arquivo,
                AccessServer.__get_caminho_arquivo(
                    nome_arquivo
                ),
                confirm=True
            )
            return True, file_attrs

        return False, self.get_msg_erro_conexao_sftp()

    def __excluir_arquivo(self, name):
        self.__executar_comando('del {}'.format(
            AccessServer.__get_caminho_arquivo(name).replace('/', '\\')))

    def get_caminho_lockfile(self, group, cloud):
        return self.__get_caminho_arquivo(f'{group}-{cloud}.lock')

    def executar_script(self, name, conteudo):
        try:
            arquivo_script = None

            if self.__is_conexao_ok():
                with tempfile.NamedTemporaryFile(
                        prefix=name, suffix='.ps1', delete=True) as arquivo_script:
                    arquivo_script.file.write(conteudo.encode(
                        AccessServer.__ENCODE_WINDOWS))
                    arquivo_script.flush()

                    res_envio_arquivo = self.__enviar_arquivo(
                        arquivo_script.name)
                    if not res_envio_arquivo[0]:
                        return res_envio_arquivo

                    caminho_arquivo = AccessServer.__get_caminho_arquivo(
                        arquivo_script.name)
                    resultado = self.__executar_comando(
                        f'powershell.exe -file {caminho_arquivo}')

                    self.__excluir_arquivo(arquivo_script.name)

                    return resultado

            return False, self.get_msg_erro_conexao()
        # pylint: disable=broad-except
        except Exception as ex:
            return False, f'Error "{type(ex).__name__}" to execute script: {ex}'
        finally:
            if arquivo_script:
                arquivo_script.close()
