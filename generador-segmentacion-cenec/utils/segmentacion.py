from utils.query import to_dict
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

UBIGEO='{}'.format(sys.argv[1])
ZONA='{}'.format(sys.argv[2])


class SegmentacionCENEC:
    zonas =[]
    def __init__(self, zonas, cant_est_max):
        self.conn, self.cursor = cnx.connect_bd()
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
        self.path_croquis = config.PATH_CROQUIS
        self.path_listado = config.PATH_LISTADO
        self.path_programaciones = config.PATH_PROGRAMACIONES
        self.path_croquis_listado = config.PATH_CROQUIS_LISTADO
        self.path_plantilla_croquis_empadronador = path.join( config.PATH_PLANTILLA_CROQUIS ,'croquis_empadronador.mxd')
        self.path_plantilla_croquis_brigada = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_brigada.mxd')
        self.zonas = zonas

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
            ["{}.DBO.TB_MANZANA".format(config.DB_NAME), "tb_manzana_procesar", 2],

        ]

        ## 1 exportacion de datos a nivel de zona, 2 exportacion a nivel de distrito

        for i, capa in enumerate(list_capas):
            if (capa[2]==1):
                where= where_zona
            else:
                where = where_ubigeo

            x = arcpy.MakeQueryLayer_management(path_conexion, 'capa{}'.format(i),
                                                "select * from {} where  {}  ".format(capa[0], where))

            temp = arcpy.CopyFeatures_management(x, '{}/{}'.format(self.path_trabajo,capa[1]))



    def llave(self,x):
        return '{}{}{}'.format(x['UBIGEO'] , x['ZONA'] , x['AEU'])

    def crear_aeus(self):
        self.manzanas = sorted (self.manzanas,key = lambda k:k['FALSO_COD'])
        self.list_aeu = []
        self.list_aeu_manzanas = []
        numero_aeu=1
        cant_est_agrupados=0
        anterior_manzana = 0 #manzana inicial

        for manzana in self.manzanas:
            m=manzana.copy()
            cant_est=m['CANT_EST']
            if (cant_est > self.cant_est_max):
                if anterior_manzana == 1:  # la anterior manzana es una menor o igual a 16 viviendas
                    if cant_est_agrupados != 0:
                        numero_aeu = numero_aeu + 1

                cant_est_agrupados = 0
                anterior_manzana = 2  #La manzana nueva tiene mas de self.cant_est_max

                #####partiendo la manzana

                division = float(cant_est) / self.cant_est_max
                cant_aeus = int(math.ceil(division))
                residuo = cant_est % cant_aeus
                est_aeu = cant_est / cant_aeus
                i = 0
                est_aeu_aux = 0

                for i in range(cant_aeus):
                    n=m.copy()

                    if i>0:
                        numero_aeu = numero_aeu + 1

                    if residuo > 0:
                        residuo = residuo - 1
                        est_aeu_aux = est_aeu +1

                    else:
                        est_aeu_aux = est_aeu
                    n['CANT_EST'] = est_aeu_aux
                    n['AEU'] = numero_aeu
                    self.list_aeu_manzanas.append(n)
            else:
                cant_est_agrupados = cant_est_agrupados + cant_est


                if (anterior_manzana == 2 or anterior_manzana == 0):  #
                    cant_est_agrupados = cant_est
                    if anterior_manzana == 2:
                        numero_aeu = numero_aeu + 1

                else:

                    if (cant_est_agrupados <= self.cant_est_max):
                        numero_aeu = numero_aeu

                    else:
                        cant_est_agrupados= cant_est
                        numero_aeu = numero_aeu + 1

                anterior_manzana = 1
                m['AEU']=numero_aeu
                self.list_aeu_manzanas.append(m)



        for key, group in itertools.groupby(self.list_aeu_manzanas, key=lambda x:self.llave(x)):
            cant_est=0
            aeu=''
            ubigeo=''
            zona=''
            for el in list(group):
                cant_est = int(el['CANT_EST']) + cant_est
                aeu=el['AEU']
                ubigeo = el['UBIGEO']
                zona = el['ZONA']

            self.list_aeu.append({'UBIGEO':ubigeo,'ZONA':zona,'AEU':aeu,'CANT_EST':cant_est})

    def obtener_manzanas(self,zona):
        query_manzanas = """
        select UBIGEO,ZONA,MANZANA,CANT_EST,FALSO_COD from [DBO].[TB_MANZANA] 
        where UBIGEO = '{ubigeo}' and ZONA = '{zona}'    
        """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
        self.manzanas = to_dict(self.cursor.execute(query_manzanas))

    def procesar_aeus(self):

        if arcpy.Exists(self.path_aeu):
            arcpy.Delete_management(self.path_aeu)

        for zona in self.zonas:
            self.obtener_manzanas(zona)
            self.crear_aeus()
            self.crear_limite_aeus()
            self.list_aeu_manzanas_final  =self.list_aeu_manzanas_final + self.list_aeu_manzanas
            self.list_aeu_final  = self.list_aeu_final +self.list_aeu

    def exportando_resultados_aeu(self):
        insert_sql = ""
        arcpy.env.overwriteOutput = True
        path_conexion = cnx.connect_arcpy()
        arcpy.env.workspace = path_conexion

        list_capas=[
            [  self.path_aeu,path.join(path_conexion,'{}.DBO.SEGM_U_AEU'.format(config.DB_NAME))]
        ]

        for zona in self.zonas:
            sql_query = """
                    DELETE DBO.SEGM_U_AEU where ubigeo='{ubigeo}' and zona='{zona}'
                    """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
            self.cursor.execute(sql_query)
            self.conn.commit()

        for i , el in enumerate(list_capas):#
            a = arcpy.MakeFeatureLayer_management(el[0], "MakeFeatureLayer{}".format(i))
            arcpy.Append_management(a, el[1], "NO_TEST")

    def exportando_resultados_aeu_manzana(self):
        insert_sql = ""

        for zona in self.zonas:
            sql_query = """
                    DELETE DBO.[SEGM_U_AEU_MANZANA] where ubigeo='{ubigeo}' and zona='{zona}'
                    """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
            self.cursor.execute(sql_query)
            self.conn.commit()

        for count, aeu in enumerate(self.list_aeu_manzanas_final, 1):


            if count == 1:
                insert_sql = """ insert into [SEGM_U_AEU_MANZANA](ubigeo,zona,aeu,manzana,cant_est)  values """
            insert_sql = """{insert_sql} ('{ubigeo}','{zona}','{aeu}','{manzana}',{cant_est}) """.format(insert_sql=insert_sql,
                                                                                             ubigeo=aeu['UBIGEO'],
                                                                                             zona=aeu['ZONA'],
                                                                                             aeu=aeu['AEU'],
                                                                                             manzana=aeu['MANZANA'],
                                                                                             cant_est=int(aeu['CANT_EST']))
            if count < len(self.list_aeu_manzanas_final):
                insert_sql = """{insert_sql},""".format(insert_sql=insert_sql)

        self.cursor.execute(insert_sql)
        self.conn.commit()

    def exportar_resultados(self):
        self.exportando_resultados_aeu()
        self.exportando_resultados_aeu_manzana()

    def crear_limite_aeus(self):
        arcpy.env.overwriteOutput = True
        path_manzana=path.join(self.path_trabajo, 'tb_manzana')
        arcpy.MakeFeatureLayer_management(path_manzana, "tb_manzana")
        for aeu in self.list_aeu:
            print 'self.list_aeu>>>',self.list_aeu
            list_aeu_man=[[d['UBIGEO'],d['ZONA'],d['MANZANA']] for d in self.list_aeu_manzanas if(d['AEU']==aeu['AEU'] and d['UBIGEO']==aeu['UBIGEO'] and d['ZONA']== aeu['ZONA'] )]
            where_manzanas = expresion.expresion_2(list_aeu_man,[["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            tb_manzana_selec=arcpy.SelectLayerByAttribute_management("tb_manzana_procesar", "NEW_SELECTION", where_manzanas)
            if (int(arcpy.GetCount_management(tb_manzana_selec).getOutput(0)) > 0):
                out_feature_1 = "in_memory/Buffer{}{}{}".format(aeu["UBIGEO"],aeu["ZONA"],aeu["AEU"])
                out_feature = "in_memory/out_feature{}{}{}".format(aeu["UBIGEO"],aeu["ZONA"],aeu["AEU"])
                arcpy.Buffer_analysis(tb_manzana_selec, out_feature_1, '5 METERS', 'FULL', 'FLAT', 'LIST')
                arcpy.Dissolve_management(out_feature_1, out_feature)
                add_fields = [ ["UBIGEO","TEXT","'{}'".format(aeu["UBIGEO"])],["ZONA","TEXT","'{}'".format(aeu["ZONA"])],["AEU","TEXT","'{}'".format(str(aeu["AEU"]).zfill(3)) ],["CANT_EST","SHORT",int(aeu["CANT_EST"])]]

                for add_field in add_fields:
                    arcpy.AddField_management(out_feature, add_field[0], add_field[1])
                    arcpy.CalculateField_management(out_feature,add_field[0], add_field[2], "PYTHON_9.3")

                if arcpy.Exists(self.path_aeu):
                    arcpy.Append_management(out_feature, self.path_aeu, "NO_TEST")
                else:
                    arcpy.CopyFeatures_management(out_feature, self.path_aeu)

    def procesar_listado_croquis(self):
        brigadas = self.obtener_brigadas()

        zonas = []
        for brigada in brigadas:
            rutas = self.obtener_rutas(brigada)
            for ruta in rutas:
                rutas_manzanas = self.obtener_rutas_manzanas(ruta)
                zonas = zonas + [{'UBIGEO': e[0], 'ZONA': e[1]} for e in
                                 list(set((d['UBIGEO'], d['ZONA']) for d in rutas_manzanas))]
        ##############importando capas para los croquis###########
        #self.importar_capas(zonas)

        for brigada in brigadas:
            rutas = self.obtener_rutas(brigada)
            list_out_croquis_brigada=[]
            lista_emp_brigada_est = []
            rutas_manzanas_brigada=self.obtener_rutas_manzanas_por_brigada(brigada)

            zonas_brigada = [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                           'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                           'NOMCCPP': e[9], 'BRIGADA': e[10], 'RUTA': ruta['RUTA'], 'PERIODO': e[11],
                           'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13]
                           } for e in list(set((
                                               d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'], d['DISTRITO'],
                                               d['CODDPTO'], d['CODPROV'], d['CODDIST'], d['CODCCPP'], d['NOMCCPP'],
                                               d['BRIGADA'], d['PERIODO'], d['CODSEDE'], d['SEDE_OPERATIVA']) for d in
                                               rutas_manzanas_brigada))]

            output_brigada = path.join(self.path_listado,
                               '{departamento}-{brigada}.pdf'.format(departamento=brigada['CODDPTO'], brigada=brigada['BRIGADA']))

            for zona in zonas_brigada:
                filter_rutas_manzanas = [d for d in rutas_manzanas_brigada if
                                         (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])]
                cant_est = 0
                mensaje_manzanas = u'<BOL>OBSERVACIONES: </BOL>El area de empadronamiento comprende las manzanas '

                for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                    cant_est = cant_est + int(ruta_manzana['CANT_EST'])

                if len(filter_rutas_manzanas) > 10:
                    mensaje_manzanas = u"del {} {} al {} ".format(mensaje_manzanas, filter_rutas_manzanas[0]['MZ'],
                                                                  filter_rutas_manzanas[-1]['MZ'])

                else:
                    for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                        if count == len(filter_rutas_manzanas):
                            mensaje_manzanas = u"{} {}".format(mensaje_manzanas, ruta_manzana['MZ'])
                        else:
                            mensaje_manzanas = u"{} {},".format(mensaje_manzanas, ruta_manzana['MZ'])

                zona['CANT_EST'] = cant_est
                zona['FRASE'] = mensaje_manzanas




            for ruta in rutas:
                rutas_manzanas = self.obtener_rutas_manzanas(ruta)
                info = [ruta,rutas_manzanas]
                output = path.join(self.path_listado,'{departamento}-{ruta}.pdf'.format(departamento=ruta['CODDPTO'],ruta=ruta['RUTA']))
                zonas_rutas = [  {'UBIGEO':e[0],'ZONA': e[1],'DEPARTAMENTO':e[2],'PROVINCIA':e[3],
                                 'DISTRITO':e[4],'CODDPTO':e[5],'CODPROV':e[6],'CODDIST':e[7],'CODCCPP':e[8],'NOMCCPP':e[9],'BRIGADA':e[10],'RUTA':ruta['RUTA'],'PERIODO':e[11] ,
                                 'CODSEDE':e[12],'SEDE_OPERATIVA':e[13]
                                 }   for e in   list(set((d['UBIGEO'], d['ZONA'] ,d['DEPARTAMENTO'],d['PROVINCIA'],d['DISTRITO'],d['CODDPTO'],d['CODPROV'],d['CODDIST'],d['CODCCPP'],d['NOMCCPP'],d['BRIGADA'],d['PERIODO'],d['CODSEDE'],d['SEDE_OPERATIVA']) for d in rutas_manzanas))]


                for zona in zonas_rutas:
                    filter_rutas_manzanas = [ d for d in rutas_manzanas if (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])]
                    cant_est=0
                    mensaje_manzanas =u'<BOL>OBSERVACIONES: </BOL>El area de empadronamiento comprende las manzanas '

                    manzanas = u""


                    for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                        cant_est = cant_est + int(ruta_manzana['CANT_EST'])
                        #if count == 1:
                        #    manzanas = u"{}".format(ruta_manzana['MZ'])
                        #else:
                        #    manzanas = u"{}-{}".format(manzanas,ruta_manzana['MZ'])



                    if len(filter_rutas_manzanas)>10:
                        mensaje_manzanas = u"{} {} al {}".format(mensaje_manzanas,filter_rutas_manzanas[0]['MZ'],filter_rutas_manzanas[-1]['MZ'])
                        manzanas =u"{} al {}".format(filter_rutas_manzanas[0]['MZ'],filter_rutas_manzanas[-1]['MZ'])

                    else:
                        for count,ruta_manzana in enumerate(filter_rutas_manzanas,1):
                            if count == 1:
                               manzanas = u"{}".format(ruta_manzana['MZ'])
                            else:
                               manzanas = u"{}-{}".format(manzanas,ruta_manzana['MZ'])

                            if count==len(filter_rutas_manzanas):
                                mensaje_manzanas = u"{} {}".format(mensaje_manzanas,ruta_manzana['MZ'])

                            else:
                                mensaje_manzanas = u"{} {},".format(mensaje_manzanas, ruta_manzana['MZ'])

                    zona['MANZANAS'] = manzanas

                    zona['CANT_EST']=cant_est
                    zona['FRASE'] = mensaje_manzanas
                    lista_emp_brigada_est.append(zona)


                output_listado=listado_ruta(info, output)
                list_out_croquis=self.croquis_ruta(info,zonas_rutas)
                list_out_croquis.append(output_listado)
                pdfDoc = arcpy.mapping.PDFDocumentCreate(path.join(self.path_croquis_listado, '{departamento}-{brigada}-{ruta}.pdf'.format(departamento=ruta['CODDPTO'],brigada=ruta['BRIGADA'],ruta=ruta['RUTA'])))

                out_programacion_ruta = path.join(self.path_programaciones,
                          '{departamento}-{brigada}-{ruta}.pdf'.format(departamento=ruta['CODDPTO'],
                                                                       brigada=ruta['BRIGADA'], ruta=ruta['RUTA']))

                if path.exists(out_programacion_ruta):
                    list_out_croquis.append(out_programacion_ruta)
                else:
                    print out_programacion_ruta


                for el in list_out_croquis:
                    pdfDoc.appendPages(el)
                pdfDoc.saveAndClose()


            output_listado_brigada = listado_brigada([brigada,lista_emp_brigada_est], output_brigada)
            list_out_croquis_brigada = self.croquis_brigada([brigada,rutas_manzanas_brigada], zonas_brigada)
            list_out_croquis_brigada.append(output_listado_brigada)
            pdfDoc = arcpy.mapping.PDFDocumentCreate(path.join(self.path_croquis_listado,
                                                               '{departamento}-{brigada}.pdf'.format(
                                                                   departamento=brigada['CODDPTO'],
                                                                   brigada=brigada['BRIGADA'])))
            out_programacion_brigada=path.join(self.path_programaciones,
                                              '{departamento}-{brigada}.pdf'.format(
                                                                   departamento=brigada['CODDPTO'],
                                                                   brigada=brigada['BRIGADA']))

            if path.exists(out_programacion_brigada):
                list_out_croquis_brigada.append(out_programacion_brigada)
            else:
                print out_programacion_brigada

            for el in list_out_croquis_brigada:
                pdfDoc.appendPages(el)
            pdfDoc.saveAndClose()

    def croquis_ruta(self,info,zonas):
        list_out_croquis=[]
        for zona in zonas:
            ruta = info[0]
            rutas_manzanas = info[1]
            manzanas= list(set((d['UBIGEO'], d['ZONA'],d['MZ']) for d in rutas_manzanas if (d['UBIGEO']==zona['UBIGEO'] and d['ZONA']==zona['ZONA']) ))
            frentes_ini = [(d[0], d[1],d[2],1) for d in manzanas]

            where_manzanas = expresion.expresion_2(manzanas,[["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            where_frentes_ini = expresion.expresion_2(frentes_ini,
                                                   [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"],["FRENTE_ORD", "SHORT"]])
            where_zonas = expresion.expresion_2([ [zona['UBIGEO'], zona['ZONA']] ], [["UBIGEO", "TEXT"], ["ZONA", "TEXT"]])
            mxd = arcpy.mapping.MapDocument(self.path_plantilla_croquis_empadronador)
            df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
            zona_mfl = arcpy.mapping.ListLayers(mxd, "TB_ZONAS")[0]
            mzs_mfl = arcpy.mapping.ListLayers(mxd, "TB_MZS_ORD")[0]
            frentes_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES")[0]
            frentes_inicio_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES_INICIO")[0]

            frentes_mfl.definitionQuery = where_manzanas
            frentes_inicio_mfl.definitionQuery = where_frentes_ini

            mzs_mfl.definitionQuery = where_manzanas
            zona_mfl.definitionQuery = where_zonas

            df.extent = mzs_mfl.getSelectedExtent()
            dflinea = arcpy.Polyline(
                arcpy.Array([arcpy.Point(df.extent.XMin, df.extent.YMin), arcpy.Point(df.extent.XMax, df.extent.YMax)]),
                df.spatialReference)
            distancia = dflinea.getLength("GEODESIC", "METERS")
            if (float(distancia) <= 100):
                df.scale = df.scale * 4
            elif (float(distancia) > 100 and float(distancia) <= 490):
                df.scale = df.scale * 3
            elif (float(distancia) > 490 and float(distancia) <= 900):
                df.scale = df.scale * 1.5
            elif (float(distancia) > 900 and float(distancia) <= 1200):
                df.scale = df.scale * 1.25
            elif (float(distancia) > 1200 and float(distancia) <= 1800):
                df.scale = df.scale * 1.10
            elif (float(distancia) > 1800):
                df.scale = df.scale * 1.02

            #df.extent = zona_mfl.getSelectedExtent()

            list_text_el = [["CODDPTO", zona["CODDPTO"]] , ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']], ["ZONA", zona['ZONA']]]
            list_text_el = list_text_el +   [["CODCCPP", zona['CODCCPP']], ["DEPARTAMENTO", zona['DEPARTAMENTO']]]
            list_text_el = list_text_el +   [["PROVINCIA", zona['PROVINCIA']], ["DISTRITO", zona['DISTRITO']], ["NOMCCPP",zona['NOMCCPP']]]
            list_text_el = list_text_el + [["BRIGADA",zona["BRIGADA"]],["RUTA",zona["RUTA"]],["CANT_EST", '{}'.format(zona["CANT_EST"])], ["FRASE", zona["FRASE"]],["PERIODO",'{}'.format(zona["PERIODO"])]]

            list_text_el = list_text_el + [["DOC","DOC.CENEC.03.07A"]]

            for text_el in list_text_el:
                el=arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text=text_el[1]

            out_croquis = path.join(self.path_croquis,
                               '{departamento}-{ruta}-{zona}.pdf'.format(departamento=ruta['CODDPTO'], ruta=ruta['RUTA'],zona=zona['ZONA']))

            out_croquis_copia = path.join(self.path_croquis,
                                    '{departamento}-{ruta}-{zona}-copia.pdf'.format(departamento=ruta['CODDPTO'],
                                                                              ruta=ruta['RUTA'], zona=zona['ZONA']))

            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis)

            list_text_el = list_text_el + [["DOC", "DOC.CENEC.03.07B"]]
            for text_el in list_text_el:
                el = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text = text_el[1]
            arcpy.mapping.ExportToPDF(mxd, out_croquis_copia, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis_copia)
        return list_out_croquis

    def croquis_brigada(self,info,zonas):
        list_out_croquis=[]
        for zona in zonas:
            brigada = info[0]
            rutas_manzanas = info[1]
            manzanas= list(set((d['UBIGEO'], d['ZONA'],d['MZ']) for d in rutas_manzanas if (d['UBIGEO']==zona['UBIGEO'] and d['ZONA']==zona['ZONA']) ))
            frentes_ini = [(d[0], d[1],d[2],1) for d in manzanas]

            where_manzanas = expresion.expresion_2(manzanas,[["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            where_frentes_ini = expresion.expresion_2(frentes_ini,
                                                   [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"],["FRENTE_ORD", "SHORT"]])
            where_zonas = expresion.expresion_2([ [zona['UBIGEO'], zona['ZONA']] ], [["UBIGEO", "TEXT"], ["ZONA", "TEXT"]])
            mxd = arcpy.mapping.MapDocument(self.path_plantilla_croquis_brigada)
            df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
            zona_mfl = arcpy.mapping.ListLayers(mxd, "TB_ZONAS")[0]
            mzs_mfl = arcpy.mapping.ListLayers(mxd, "TB_MZS_ORD")[0]
            frentes_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES")[0]
            frentes_inicio_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES_INICIO")[0]
            frentes_mfl.definitionQuery = where_manzanas
            frentes_inicio_mfl.definitionQuery = where_frentes_ini
            mzs_mfl.definitionQuery = where_manzanas
            zona_mfl.definitionQuery = where_zonas

            df.extent = mzs_mfl.getSelectedExtent()
            dflinea = arcpy.Polyline(
                arcpy.Array([arcpy.Point(df.extent.XMin, df.extent.YMin), arcpy.Point(df.extent.XMax, df.extent.YMax)]),
                df.spatialReference)
            distancia = dflinea.getLength("GEODESIC", "METERS")
            if (float(distancia) <= 100):
                df.scale = df.scale * 4
            elif (float(distancia) > 100 and float(distancia) <= 490):
                df.scale = df.scale * 3
            elif (float(distancia) > 490 and float(distancia) <= 900):
                df.scale = df.scale * 1.5
            elif (float(distancia) > 900 and float(distancia) <= 1200):
                df.scale = df.scale * 1.25
            elif (float(distancia) > 1200 and float(distancia) <= 1800):
                df.scale = df.scale * 1.10
            elif (float(distancia) > 1800):
                df.scale = df.scale * 1.02

            list_text_el = [["CODDPTO", zona["CODDPTO"]] , ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']], ["ZONA", zona['ZONA']]]
            list_text_el = list_text_el +   [["CODCCPP", zona['CODCCPP']], ["DEPARTAMENTO", zona['DEPARTAMENTO']]]
            list_text_el = list_text_el +   [["PROVINCIA", zona['PROVINCIA']], ["DISTRITO", zona['DISTRITO']], ["NOMCCPP",zona['NOMCCPP']]]
            list_text_el = list_text_el + [["BRIGADA",zona["BRIGADA"]],["CANT_EST", '{}'.format(zona["CANT_EST"])], ["FRASE", zona["FRASE"]],["PERIODO",'{}'.format(zona["PERIODO"])]]

            list_text_el = list_text_el + [["DOC","DOC.CENEC.03.09"]]

            for text_el in list_text_el:
                el=arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text=text_el[1]

            out_croquis = path.join(self.path_croquis,
                               '{departamento}-{brigada}-{zona}.pdf'.format(departamento=brigada['CODDPTO'], brigada=brigada['BRIGADA'],zona=zona['ZONA']))

            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis)


        return list_out_croquis


    def procesar_zonas(self):
        print datetime.today()
        self.importar_capas_segmentacion()
        print datetime.today()
        self.procesar_aeus()
        print datetime.today()
        self.exportar_resultados()
        print datetime.today()


s= SegmentacionCENEC(zonas=[{'UBIGEO':UBIGEO,'ZONA':ZONA}],cant_est_max=150)
s.procesar_zonas()

