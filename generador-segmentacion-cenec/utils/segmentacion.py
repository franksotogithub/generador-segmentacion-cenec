
from utils.query import to_dict , obtener_zonas
from utils.listado_urbano import listado_ruta , listado_brigada
from bd import cnx
import itertools
from os import path
from operator import itemgetter
import shutil
import arcpy
import expresiones_consulta_arcpy as expresion
from datetime import *
from  conf import config
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)
import math
UBIGEO='{}'.format(sys.argv[1])

class SegmentacionCENEC:
    zonas =[]

    def __init__(self,distrito, cant_est_max=150):
        self.conn, self.cursor = cnx.connect_bd()
        self.distrito=distrito
        self.cant_zonas= 0
        self.cant_est_max = cant_est_max
        self.list_aeu_manzanas =[]
        self.list_aeu = []
        self.list_aeu_manzanas_final = []
        self.list_aeu_final = []
        self.path_trabajo = config.PATH_TRABAJO_PROCESAR
        self.path_aeu = path.join(self.path_trabajo, 'aeu')
        self.rutas =[]
        self.rutas_manzanas = []
        self.zonas = obtener_zonas(self.cursor, self.conn, cant_zonas=100)

    def importar_capas_segmentacion(self):
        arcpy.env.overwriteOutput = True
        path_conexion = cnx.connect_arcpy()
        arcpy.env.workspace = path_conexion
        data = []
        for zona in self.zonas:
            data.append([zona['UBIGEO'],zona['ZONA']])

        where_zona = expresion.expresion(data, ['UBIGEO','ZONA'])
        where_ubigeo = expresion.expresion(data, ['UBIGEO'])

        list_capas = [
            ["{}.sde.TB_MANZANA".format(config.DB_NAME), "tb_manzana_procesar", 2],

        ]

        for i, capa in enumerate(list_capas):
            if (capa[2]==1):
                where=  where_zona
            else:
                where = where_ubigeo

            where = "({}) ".format(where)

            x = arcpy.MakeQueryLayer_management(path_conexion, 'capa{}'.format(i),
                                                "select * from {} where  {}  ".format(capa[0], where))

            temp = arcpy.CopyFeatures_management(x, '{}/{}'.format(self.path_trabajo,capa[1]))

    def llave(self,x):
        return '{}{}{}'.format(x['UBIGEO'] , x['ZONA'] , x['AEU'])

    def crear_list_aeu(self):
        self.list_aeu = []
        for key, group in itertools.groupby(self.list_aeu_manzanas, key=lambda x:self.llave(x)):
            cant_est = 0
            mercado = 0
            puesto = 0
            total_est = 0
            aeu=''
            ubigeo=''
            zona=''
            n_manzanas =0
            for el in list(group):
                n_manzanas = n_manzanas+1
                total_est = int(el['TOTAL_EST']) + total_est
                cant_est = int(el['CANT_EST']) + cant_est
                mercado = int(el['MERCADO']) + mercado
                puesto = int(el['PUESTO']) + puesto
                aeu=el['AEU']
                ubigeo = el['UBIGEO']
                zona = el['ZONA']

            self.list_aeu.append({'UBIGEO':ubigeo,'ZONA':zona,'AEU':aeu,'AEU_TEMP':aeu , 'TOTAL_EST':total_est , 'CANT_EST':cant_est , 'MERCADO': mercado , 'PUESTO' :puesto, 'N_MANZANAS':n_manzanas })

    def crear_aeus(self):
        self.manzanas = sorted (self.manzanas,key = lambda k:k['FALSO_COD'])

        self.list_aeu_manzanas = []
        numero_aeu=1
        cant_est_agrupados=0
        anterior_manzana = 0 #manzana inicial
        total_est_zona = 0

        flag_segunda_pasada = 1

        n = 0


        for m in self.manzanas:
            total_est_zona = int(m['CANT_EST']) + int(m['PUESTO']) + total_est_zona
            if int(m['TOTAL_EST']) > self.cant_est_max:
                flag_segunda_pasada = 0

        if (total_est_zona < self.cant_est_max):
            flag_segunda_pasada = 0


        if (flag_segunda_pasada ==1):
            n = int(math.ceil((total_est_zona/float(self.cant_est_max))))
            restriccion = int(math.ceil( total_est_zona/float(n)))


        else:
            restriccion = self.cant_est_max

        for manzana in self.manzanas:
            m=manzana.copy()
            cant_est= int(m['CANT_EST'])
            mercado = int(m['MERCADO'])
            puesto = int(m['PUESTO'])
            total_est = int(m['CANT_EST']) + int(m['PUESTO'])

            if (flag_segunda_pasada == 1 and numero_aeu == n):

                restriccion = self.cant_est_max


            if (total_est > self.cant_est_max):

                if anterior_manzana == 1:  # la anterior manzana es una menor o igual a 16 viviendas
                    if cant_est_agrupados != 0:
                        numero_aeu = numero_aeu + 1

                cant_est_agrupados = 0
                anterior_manzana = 2  #La manzana nueva tiene mas de self.cant_est_max

                #####partiendo la manzana


                #division = float(cant_est) / self.cant_est_max
                #cant_aeus = int(math.ceil(division))
                #residuo = total_est % cant_aeus
                #est_aeu = total_est / cant_aeus
                #i = 0
                #est_aeu_aux = 0
#
                #for i in range(cant_aeus):
                #    n=m.copy()
#
                #    if i>0:
                #        numero_aeu = numero_aeu + 1
#
                #    if residuo > 0:
                #        residuo = residuo - 1
                #        est_aeu_aux = est_aeu +1
#
                #    else:
                #        est_aeu_aux = est_aeu
                #    n['CANT_EST'] = est_aeu_aux
                #    n['AEU'] = numero_aeu
                #    self.list_aeu_manzanas.append(n)

                ###############################
                m['AEU'] = numero_aeu
                m['MANZANA'] =(m['MANZANA'])
                self.list_aeu_manzanas.append(m)
                #################################

            else:


                cant_est_agrupados = cant_est_agrupados + total_est
                if (anterior_manzana == 2 or anterior_manzana == 0):  #
                    cant_est_agrupados = total_est
                    if anterior_manzana == 2:
                        numero_aeu = numero_aeu + 1

                else:

                    if (cant_est_agrupados <= restriccion):
                        numero_aeu = numero_aeu

                    else:
                        cant_est_agrupados= total_est
                        numero_aeu = numero_aeu + 1

                anterior_manzana = 1
                m['AEU'] = numero_aeu
                m['MANZANA'] = str(m['MANZANA'])
                self.list_aeu_manzanas.append(m)
        self.crear_list_aeu()
        ##############segunda _pasada#################
        cant_est=0
        nuevo_aeu=1
        if(flag_segunda_pasada == 1):
            for count,aeu in enumerate(self.list_aeu,1):
                cant_est= cant_est + int(aeu['TOTAL_EST'])

                if cant_est>self.cant_est_max:
                    nuevo_aeu = nuevo_aeu+1
                    cant_est = aeu['TOTAL_EST']
                aeu['AEU'] = nuevo_aeu

                for m in self.list_aeu_manzanas:
                    if (m['AEU'] == aeu['AEU_TEMP'] and m['ZONA'] == aeu['ZONA'] and m['UBIGEO'] == aeu['UBIGEO']):
                        m['AEU'] = nuevo_aeu


            self.crear_list_aeu()

    def obtener_zonas(self):
        query_manzanas = """
                            SELECT * FROM sde.TB_ZONA
                            WHERE UBIGEO = '{ubigeo}' 
                             
        """.format(ubigeo=self.distrito['UBIGEO'])

        self.zonas = to_dict(self.cursor.execute(query_manzanas))

    def obtener_manzanas(self,zona):
        query_manzanas = """
                            SELECT B.*,A.MARCO_FIN CANT_EST ,A.MARCO_FIN  + A.PUESTO TOTAL_EST, A.MERCADO MERCADO, A.PUESTO PUESTO  ,A.FALSO_COD FALSO_COD FROM TRABAJO_PSEUDO_CODIGO A
                            INNER JOIN sde.TB_MANZANA  B ON A.UBIGEO= B.UBIGEO AND A.ZONA=B.ZONA AND A.MANZANA=B.MANZANA 
                            where b.UBIGEO = '{ubigeo}' and b.ZONA = '{zona}' 
                            ORDER BY B.UBIGEO,B.ZONA,A.FALSO_COD 
        """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
        self.manzanas = to_dict(self.cursor.execute(query_manzanas))

    def procesar_aeus(self):

        if arcpy.Exists(self.path_aeu):
            arcpy.Delete_management(self.path_aeu)

        for zona in self.zonas:
            self.obtener_manzanas(zona)
            self.crear_aeus()
            self.crear_limite_aeus()
            self.list_aeu_manzanas_final = self.list_aeu_manzanas_final + self.list_aeu_manzanas
            self.list_aeu_final  = self.list_aeu_final +self.list_aeu

    def exportando_resultados_aeu(self):
        arcpy.env.overwriteOutput = True
        path_conexion = cnx.connect_arcpy()
        arcpy.env.workspace = path_conexion

        list_capas=[
            [  self.path_aeu,path.join(path_conexion,'{}.SDE.SEGM_U_AEU'.format(config.DB_NAME))]
        ]

        for zona in self.zonas:
            sql_query = """
                    DELETE SDE.SEGM_U_AEU where ubigeo='{ubigeo}' and zona='{zona}'
                    """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
            self.cursor.execute(sql_query)
            self.conn.commit()


        for i , el in enumerate(list_capas):
            a = arcpy.MakeFeatureLayer_management(el[0], "MakeFeatureLayer{}".format(i))
            arcpy.Append_management(a, el[1], "NO_TEST")

        sql_query = """
                    UPDATE A
                    SET 
                    a.DIAS_VIAJE=0,	
                    a.DIAS_TRABAJO=0,	
                    a.DIAS_RECUPERACION=0,
                    a.DIAS_DESCANSO=0,
                    a.DIAS_OPERATIVOS=0,
                    a.TOTAL_DIAS=0,
                    a.PASAJES=0,
                    a.VIATICOS=0,
                    a.MOV_LOCAL=0,
                    a.MOV_ESP=0,	
                    a.PERSONAL_AD=0,
                    a.GABINETE =0,
                    a.PK_AEU = a.ubigeo+a.zona+a.aeu,
                    a.CODSEDE = B.CODSEDE,
                    a.CODSUBSEDE =0 
                    FROM sde.SEGM_U_AEU A
                    inner join  tb_ZONA b on A.UBIGEO= B.UBIGEO AND A.ZONA=B.ZONA
                    
                    
                     update  sde.SEGM_U_AEU
                     set  PERSONAL_AD = CEILING ( cast (total_est as float) /150 ) 
                     where TOTAL_EST >150  AND N_MANZANAS=1
                            
                  
        """
        self.cursor.execute(sql_query)
        self.conn.commit()

    def exportando_resultados_aeu_tabular(self):
        insert_sql = ""

        for zona in self.zonas:
            sql_query = """
                    DELETE sde.[SEGM_U_AEU_TABULAR] where ubigeo='{ubigeo}' and zona='{zona}' and techo ={techo}
                    """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'] ,techo = self.cant_est_max)
            self.cursor.execute(sql_query)
            self.conn.commit()

        sql_query = "select max([OBJECTID]) as maximo from sde.[SEGM_U_AEU_TABULAR]"

        row=self.cursor.execute(sql_query).fetchone()

        cant_reg = row.maximo if row.maximo is not None else 0


        for count, aeu in enumerate(self.list_aeu_final, 1):

            if count == 1:
                insert_sql = """ insert into sde.[SEGM_U_AEU_TABULAR]([OBJECTID],ubigeo,zona,aeu,n_manzanas,total_est,cant_est,mercado,puesto,techo)  """
            insert_sql = """{insert_sql} select {i},'{ubigeo}','{zona}','{aeu}','{n_manzanas}',{total_est},{cant_est},{mercado},{puesto},{techo} """.format( i = cant_reg + count,insert_sql=insert_sql,
                                                                                             ubigeo=aeu['UBIGEO'],
                                                                                             zona=aeu['ZONA'],
                                                                                             aeu=str(aeu['AEU']).zfill(3),
                                                                                             n_manzanas=aeu['N_MANZANAS'],
                                                                                             cant_est=int(aeu['CANT_EST']),
                                                                                             total_est = int(aeu['TOTAL_EST']),
                                                                                             mercado = int(aeu['MERCADO']),
                                                                                             puesto = int(aeu['PUESTO']),
                                                                                             techo = int(self.cant_est_max)
                                                                                                )
            if count < len(self.list_aeu_final):
                insert_sql = """{insert_sql} union all """.format(insert_sql=insert_sql)




        self.cursor.execute(insert_sql)
        self.conn.commit()


    def exportando_resultados_aeu_manzana(self):
        insert_sql = ""

        for zona in self.zonas:
            sql_query = """
                    DELETE sde.[SEGM_U_AEU_MANZANA] where ubigeo='{ubigeo}' and zona='{zona}'
                    """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
            self.cursor.execute(sql_query)
            self.conn.commit()

        sql_query = "select max([OBJECTID]) as maximo from sde.[SEGM_U_AEU_MANZANA]"

        row=self.cursor.execute(sql_query).fetchone()

        cant_reg = row.maximo if row.maximo is not None else 0


        for count, aeu in enumerate(self.list_aeu_manzanas_final, 1):

            if count == 1:
                insert_sql = """ insert into sde.[SEGM_U_AEU_MANZANA]([OBJECTID],ubigeo,zona,aeu,manzana,total_est)  """
            insert_sql = """{insert_sql} select {i},'{ubigeo}','{zona}','{aeu}','{manzana}',{cant_est} """.format( i = cant_reg + count,insert_sql=insert_sql,
                                                                                             ubigeo=aeu['UBIGEO'],
                                                                                             zona=aeu['ZONA'],
                                                                                             aeu=str(aeu['AEU']).zfill(3),
                                                                                             manzana=aeu['MANZANA'],
                                                                                             cant_est=int(aeu['CANT_EST']) + int(aeu['PUESTO'])
                                                                                                                           )
            if count < len(self.list_aeu_manzanas_final):
                insert_sql = """{insert_sql} union all """.format(insert_sql=insert_sql)

        self.cursor.execute(insert_sql)
        self.conn.commit()


    def exportando_resultados_aeu_manzana_tabular(self):
        insert_sql = ""

        for zona in self.zonas:
            sql_query = """
                    DELETE sde.[SEGM_U_AEU_MANZANA_TABULAR] where ubigeo='{ubigeo}' and zona='{zona}' and techo = {techo}
                    """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'] , techo = self.cant_est_max)
            self.cursor.execute(sql_query)
            self.conn.commit()

        sql_query = "select max([OBJECTID]) as maximo from sde.[SEGM_U_AEU_MANZANA_TABULAR]"

        row=self.cursor.execute(sql_query).fetchone()

        cant_reg = row.maximo if row.maximo is not None else 0

        for count, aeu in enumerate(self.list_aeu_manzanas_final, 1):

            if count == 1:
                insert_sql = """ insert into sde.[SEGM_U_AEU_MANZANA_TABULAR]([OBJECTID],ubigeo,zona,aeu,manzana,total_est,techo)  """
            insert_sql = """{insert_sql} select {i},'{ubigeo}','{zona}','{aeu}','{manzana}',{cant_est},{techo} """.format( i = cant_reg + count,insert_sql=insert_sql,
                                                                                             ubigeo=aeu['UBIGEO'],
                                                                                             zona=aeu['ZONA'],
                                                                                             aeu=str(aeu['AEU']).zfill(3),
                                                                                             manzana=aeu['MANZANA'],
                                                                                             cant_est=int(aeu['CANT_EST']) + int(aeu['PUESTO']) ,techo= int(self.cant_est_max)
                                                                                                                           )
            if count < len(self.list_aeu_manzanas_final):
                insert_sql = """{insert_sql} union all """.format(insert_sql=insert_sql)

        self.cursor.execute(insert_sql)
        self.conn.commit()


    def exportar_resultados(self):

        #self.exportando_resultados_aeu_tabular()
        #self.exportando_resultados_aeu_manzana_tabular()
        self.exportando_resultados_aeu()
        self.exportando_resultados_aeu_manzana()

    def crear_limite_aeus(self):
        arcpy.env.overwriteOutput = True
        path_manzana=path.join(self.path_trabajo, 'tb_manzana_procesar')
        arcpy.MakeFeatureLayer_management(path_manzana, "tb_manzana_procesar")
        for aeu in self.list_aeu:
            list_aeu_man=[[d['UBIGEO'],d['ZONA'],d['MANZANA']] for d in self.list_aeu_manzanas if(d['AEU']==aeu['AEU'] and d['UBIGEO']==aeu['UBIGEO'] and d['ZONA']== aeu['ZONA'] )]

            where_manzanas = expresion.expresion_2(list_aeu_man,[["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])


            tb_manzana_select = arcpy.SelectLayerByAttribute_management("tb_manzana_procesar", "NEW_SELECTION", where_manzanas)
            if (int(arcpy.GetCount_management(tb_manzana_select).getOutput(0)) > 0):
                out_feature = arcpy.AggregatePolygons_cartography(tb_manzana_select,'in_memory/manzanas_{}{}{}'.format(aeu["UBIGEO"],aeu["ZONA"],aeu["AEU"]),"30 METERS")
                out_feature_1 = arcpy.Dissolve_management(out_feature, 'in_memory/dissolve_manzanas_{}{}{}'.format(aeu["UBIGEO"],aeu["ZONA"],aeu["AEU"]))

                add_fields = [
                                  ["UBIGEO", "TEXT", "'{}'".format(aeu["UBIGEO"])],
                                  ["ZONA", "TEXT", "'{}'".format(aeu["ZONA"])],
                                  ["AEU", "TEXT", "'{}'".format(str(aeu["AEU"]).zfill(3))],
                                  ["TOTAL_EST", "SHORT", int(aeu["TOTAL_EST"])],
                                  ["CANT_EST", "SHORT", int(aeu["CANT_EST"])],
                                  ["MERCADO", "SHORT", int(aeu["MERCADO"])],
                                  ["PUESTO", "SHORT", int(aeu["PUESTO"])],
                                  ["N_MANZANAS", "SHORT", int(len(list_aeu_man))],
                              ]


                for add_field in add_fields:
                    arcpy.AddField_management(out_feature_1, add_field[0], add_field[1])
                    arcpy.CalculateField_management(out_feature_1,add_field[0], add_field[2], "PYTHON_9.3")

                if arcpy.Exists(self.path_aeu):
                    arcpy.Append_management(out_feature_1, self.path_aeu, "NO_TEST")
                else:
                    arcpy.CopyFeatures_management(out_feature_1, self.path_aeu)

    def procesar_zonas(self):
        print datetime.today()
        self.importar_capas_segmentacion()
        print datetime.today()
        self.procesar_aeus()
        print datetime.today()
        self.exportar_resultados()
        print datetime.today()
        self.list_aeu_manzanas_final = []
        self.list_aeu_final = []


s= SegmentacionCENEC(distrito ={'UBIGEO':UBIGEO},cant_est_max =150)
s.procesar_zonas()
s.conn.close()
