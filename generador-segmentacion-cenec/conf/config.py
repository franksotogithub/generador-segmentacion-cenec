import os
HOST = '172.18.1.41'
DB_NAME = 'CENEC_SEGMENTACION'
USER = 'fsoto'
PASSWORD = 'MBs0p0rt301'

PATH_CONEXION = r'Database Connections\Connection to 172.18.1.41.sde'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_TRABAJO  = os.path.join(BASE_DIR,r'archivos_trabajo\segmentacion_cenec.gdb')
PATH_TRABAJO_PROCESAR  = os.path.join(BASE_DIR,r'archivos_trabajo\segmentacion_cenec_procesar.gdb')
PATH_IMG = os.path.join(BASE_DIR,r'imagenes')
PATH_CROQUIS = os.path.join(BASE_DIR,r'croquis')
PATH_LISTADO = os.path.join(BASE_DIR,r'listado')
PATH_PROGRAMACIONES = os.path.join(BASE_DIR,r'programaciones')
PATH_CROQUIS_LISTADO = os.path.join(BASE_DIR,r'croquis_listado')

PATH_PLANTILLA_CROQUIS = os.path.join(BASE_DIR,r'plantilla-croquis')
PATH_PLANTILLA_LAYERS = os.path.join(BASE_DIR,r'plantilla-layers')

PATH_TXT_ZONAS = os.path.join(BASE_DIR,r'archivos_trabajo','txt_zonas.txt')