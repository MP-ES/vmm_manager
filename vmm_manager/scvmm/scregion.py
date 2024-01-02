"""
System Center Virtual Machine Manager (SCVMM) region.
"""

# pylint: disable=too-few-public-methods


class SCRegion():
    REGION_DEFAULT = 'default'

    def __init__(self, id_no, nome_no, group, cluster, letra_id=None):
        self.id_no = id_no
        self.nome_no = nome_no
        self.group = group
        self.cluster = cluster
        self.letra_id = letra_id

    def __str__(self):
        return f'''
            id_no: {self.id_no}
            nome_no: {self.nome_no}
            group: {self.group}
            cluster: {self.cluster}
            letra_id: {self.letra_id}
            '''
