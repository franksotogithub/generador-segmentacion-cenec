#import insumos_segmentacion
import subprocess
from bd import cnx
from query import actualizar_flag_proc_segm ,obtener_zonas
import sys
from datetime import *
import os
import socket
from conf import config


proceso = subprocess.Popen("python insumos_segmentacion.py {ubigeo} ".format(ubigeo='100902'), shell=True,stderr=subprocess.PIPE)
errores = proceso.stderr.read()
print errores