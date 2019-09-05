# -*- coding: utf-8 -*-
import subprocess
from bd import cnx
from query import actualizar_flag_proc_segm ,obtener_zonas
import sys
from datetime import *
import os
import socket
from conf import config
#
#
equipo=socket.gethostname()
cnxn, cursor=cnx.connect_bd()



for el in range(10):
    lista_zonas = obtener_zonas(cursor,cnxn,cant_zonas=1)
    #f=open(config.PATH_TXT_ZONAS,"w+")
    if len(lista_zonas)>0:
        for el in lista_zonas:
            ubigeo = el['UBIGEO']
            zona = el['ZONA']
            proceso = subprocess.Popen("python segmentacion.py {} {}".format(ubigeo, zona), shell=True,stderr=subprocess.PIPE)
            errores = proceso.stderr.read()
            errores_print = u'{}'.format(errores)

            if len(errores_print) > 0:
                print 'algo salido mal'
                actualizar_flag_proc_segm(cursor,cnxn,ubigeo, zona, flag=2, equipo=equipo, error=errores_print)
            else:
                print 'nada salio mal'
                actualizar_flag_proc_segm(cursor,cnxn,ubigeo, zona, flag=1, equipo=equipo)
    else:
        break

