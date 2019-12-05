# -*- coding: latin-1 -*-
import subprocess
from bd import cnx
from query import actualizar_flag_proc_segm ,actualizar_flag_proc_segm_distrito,obtener_zonas ,obtener_distritos
import sys
from datetime import *
import os
import socket
from conf import config
#
#
equipo=socket.gethostname()
cnxn, cursor=cnx.connect_bd()
COD_OPER = '90'
CANT_EST_MAX = 480
CANT_ZONAS = 100


for i in range(20):
    proceso = subprocess.Popen("c:\Python27\ArcGIS10.3\python.exe segmentacion.py {cod_oper} {cant_est_max} {cant_zonas}".format(cod_oper=COD_OPER, cant_est_max = CANT_EST_MAX, cant_zonas =CANT_ZONAS),
                               shell=True,stderr=subprocess.PIPE)
    errores = proceso.stderr.read()
    print errores





