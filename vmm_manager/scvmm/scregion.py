"""
Representação de um nó de um cluster no system center virtual machine manager.
Para seguir a nomemclatura de nuvem, designado aqui como 'Region'
"""


# pylint: disable=too-few-public-methods
class SCRegion():
    REGIAO_PADRAO = 'default'

    def __init__(self, id_no, nome_no, grupo, cluster, letra_id=None):
        self.id_no = id_no
        self.nome_no = nome_no
        self.grupo = grupo
        self.cluster = cluster
        self.letra_id = letra_id

    def __str__(self):
        return f'''
            id_no: {self.id_no}
            nome_no: {self.nome_no}
            grupo: {self.grupo}
            cluster: {self.cluster}
            letra_id: {self.letra_id}
            '''
