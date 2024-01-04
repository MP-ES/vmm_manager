"""
System Center Virtual Machine Manager (SCVMM) job.
"""

import json
from time import sleep

import tqdm

from vmm_manager.infra.command import Command
from vmm_manager.scvmm.enums import SCJobStatusEnum
from vmm_manager.util.msgs import formatar_msg_aviso


class SCJob():

    @staticmethod
    def monitore_jobs(jobs, servidor_acesso):
        if jobs:
            print('\nMonitoring jobs:')
            pbars = {}
            for job in jobs.values():
                pbar = tqdm.tqdm(total=100)
                pbar.set_description(job.vmm_id)
                pbars[job.vmm_id] = pbar

            # Monitorando jobs do VMM
            tem_jobs_em_andamento = len(pbars) > 0
            while tem_jobs_em_andamento:
                tem_jobs_em_andamento = False
                status, jobs_vmm = SCJob.__obter_status_jobs_vmm(
                    jobs.keys(), servidor_acesso)

                # No caso de erro na api, finalizar loop
                if not status:
                    tqdm.tqdm.write(
                        formatar_msg_aviso(
                            '\nError while monitoring jobs.\n'))
                    break

                # Atualizando status
                for job_vmm in json.loads(jobs_vmm):
                    vmm_id = job_vmm.get('ID')
                    jobs[vmm_id].atualizar(job_vmm)
                    pbars[vmm_id].update(jobs[vmm_id].ultimo_progresso)
                    pbars[vmm_id].refresh()

                    if not jobs[vmm_id].is_finalizado:
                        tem_jobs_em_andamento = True

                # Aguardando um tempo para próxima checagem
                if tem_jobs_em_andamento:
                    sleep(10)

            # finalizando barra
            for pbar in pbars.values():
                pbar.close()

    @staticmethod
    def __obter_status_jobs_vmm(jobs, servidor_acesso):
        cmd = Command('monitore_jobs',
                      vmm_server=servidor_acesso.vmm_server,
                      jobs=jobs)
        return cmd.executar(servidor_acesso)

    def __init__(self, vmm_id, acao):
        self.vmm_id = vmm_id
        self.acao = acao

        self.name = None
        self.status = None
        self.is_finalizado = None
        self.resumo_erro = None

        self.__is_sucesso = None
        self.__codigo_erro = None
        self.__msg_erro = None
        self.__acao_recomendada = None

        self.__progresso_anterior = 0
        self.progresso = 0
        self.ultimo_progresso = 0

        self.__processar_finalizacao_job()

    def is_finalizado_com_erro(self):
        return self.is_finalizado and not self.__is_sucesso

    def __processar_finalizacao_job(self):
        if self.is_finalizado:
            self.acao.informar_status_execucao_job(
                not self.is_finalizado_com_erro())

    def atualizar(self, job_vmm):
        self.name = job_vmm.get('Name')
        self.status = SCJobStatusEnum(job_vmm.get('Status'))
        self.is_finalizado = job_vmm.get('IsCompleted')

        self.__progresso_anterior = self.progresso
        self.progresso = job_vmm.get('ProgressValue')
        self.ultimo_progresso = self.progresso - self.__progresso_anterior

        if job_vmm.get('ErrorInfo'):
            self.__is_sucesso = job_vmm.get('ErrorInfo').get('IsSuccess')
            self.__codigo_erro = job_vmm.get('ErrorInfo').get('Code')
            self.__msg_erro = job_vmm.get('ErrorInfo').get('Problem')
            self.__acao_recomendada = job_vmm.get(
                'ErrorInfo').get('RecommendedAction')
            self.resumo_erro = job_vmm.get(
                'ErrorInfo').get('CSMMessageString')

        self.__processar_finalizacao_job()

    def __str__(self):
        return f'''
            vmm_id: {self.vmm_id}
            acao: {self.acao}
            name: {self.name}
            status: {self.status}
            is_finalizado: {self.is_finalizado}
            progresso: {self.progresso}
            is_sucesso: {self.__is_sucesso}
            codigo_erro: {self.__codigo_erro}
            msg_erro: {self.__msg_erro}
            acao_recomendada: {self.__acao_recomendada}
            resumo_erro: {self.resumo_erro}
            '''
