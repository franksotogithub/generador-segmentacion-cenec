# -*- coding: utf-8 -*-
from utils.query import to_dict
from utils.listado_urbano import listado_ruta, listado_brigada
from bd import cnx
import itertools
from os import path ,remove
from operator import itemgetter
import shutil
import arcpy
import expresiones_consulta_arcpy as expresion
from datetime import *
from conf import config

arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)


class CroquisListadoCENEC:
    zonas = []
    def __init__(self):
        self.conn, self.cursor = cnx.connect_bd()
        self.list_aeu_manzanas = []
        self.list_aeu = []
        self.list_aeu_manzanas_final = []
        self.list_aeu_final = []
        self.path_trabajo = config.PATH_TRABAJO
        self.path_aeu = path.join(self.path_trabajo, 'aeu')
        self.rutas = []
        self.rutas_manzanas = []
        self.path_croquis = config.PATH_CROQUIS
        self.path_listado = config.PATH_LISTADO
        self.path_programaciones = config.PATH_PROGRAMACIONES
        self.path_croquis_listado = config.PATH_CROQUIS_LISTADO
        self.path_plantilla_croquis_empadronador = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_empadronador.mxd')
        self.path_plantilla_croquis_brigada = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_brigada.mxd')



    def importar_capas(self, zonas):
        arcpy.env.overwriteOutput = True
        path_conexion = cnx.connect_arcpy()
        arcpy.env.workspace = path_conexion
        data = []
        for zona in zonas:
            data.append([zona['UBIGEO'], zona['ZONA']])

        where_zona = expresion.expresion(data, ['UBIGEO', 'ZONA'])
        where_ubigeo = expresion.expresion(data, ['UBIGEO'])

        for el in data:
            if (el[0][2:] == '1501'):
                where_ubigeo = """ (UBIGEO LIKE '1501%') OR ({})""".format(where_ubigeo)
                break

        # if (data[0][0][2:]=='1501'):
        #    where_ubigeo = """ UBIGEO LIKE '1501%' """

        list_capas = [
            ["{}.DBO.TB_MANZANA".format(config.DB_NAME), "tb_manzana", 2],
            # ["{}.DBO.TB_SITIO_INTERES".format(config.DB_NAME), "tb_sitios_interes", 2],
            ["{}.DBO.TB_ZONA".format(config.DB_NAME), "tb_zona", 1],
            ["{}.DBO.TB_PUNTO_INICIO".format(config.DB_NAME), "tb_punto_inicio", 1],
            ["{}.DBO.TB_FRENTES".format(config.DB_NAME), "tb_frentes", 1],
            ["{}.DBO.TB_EJE_VIAL".format(config.DB_NAME), "tb_eje_vial", 2],
        ]

        ## 1 exportacion de datos a nivel de zona, 2 exportacion a nivel de distrito

        for i, capa in enumerate(list_capas):
            if (capa[2] == 1):
                where = where_zona
            else:
                where = where_ubigeo

            x = arcpy.MakeQueryLayer_management(path_conexion, 'capa{}'.format(i),
                                                "select * from {} where  {}  ".format(capa[0], where))

            temp = arcpy.CopyFeatures_management(x, '{}/{}'.format(self.path_trabajo, capa[1]))

    def obtener_zonas(self):
        query_zonas = """
                begin
                    declare @table TABLE(
                    coddpto varchar(2),
                    codprov varchar(2),
                    coddist varchar(2),
                    ubigeo varchar(6),
                    zona varchar(6),
                    codccpp varchar(5),
                    departamento varchar(100),
                    provincia varchar(100),
                    distrito varchar(100),
                    nomccpp varchar(100)
                    );

                    select top {cant_zonas} a.CODDPTO,a.CODPROV,a.CODDIST,a.UBIGEO,a.ZONA,a.CODCCPP,a.DEPARTAMENTO,a.PROVINCIA,a.DISTRITO,a.NOMCCPP from DBO.TB_ZONA a
                    where a.flag_proc_segm=0 
                    order by 1,2

                    insert @table
                    select top {cant_zonas} a.CODDPTO,a.CODPROV,a.CODDIST,a.UBIGEO,a.ZONA,a.CODCCPP,a.DEPARTAMENTO,a.PROVINCIA,a.DISTRITO,a.NOMCCPP from DBO.TB_ZONA a
                    where a.flag_proc_segm = 0 
                    order by 1,2

                    update  a
                    set a.flag_proc_segm = 2
                    from DBO.TB_ZONA a
                    where ubigeo+zona in (select UBIGEO+ZONA from @table)
                end

        """.format(cant_zonas=self.cant_zonas)
        self.zonas = to_dict(self.cursor.execute(query_zonas))
        self.conn.commit()

    def obtener_brigadas(self):
        query_brigadas = """
                begin
                    select * from [dbo].[SEGM_U_BRIGADA]                    
                end
        """
        brigadas = to_dict(self.cursor.execute(query_brigadas))
        return brigadas

    def obtener_rutas(self, brigada):
        query_rutas = """
                begin
                    select * from [dbo].[SEGM_U_RUTA]
                    where CODDPTO = '{coddpto}' AND BRIGADA ='{brigada}'
                    ORDER BY CODDPTO,RUTA 
                end
        """.format(coddpto=brigada["CODDPTO"], brigada=brigada["BRIGADA"])
        rutas = to_dict(self.cursor.execute(query_rutas))
        return rutas

    def obtener_rutas_manzanas(self, ruta):

        query_rutas_manzanas = """
                            begin
                                SELECT B.*,A.FALSO_COD FROM TB_MANZANA A
                                INNER JOIN SEGM_U_RUTA_MANZANA  B ON A.UBIGEO= B.UBIGEO AND A.ZONA=B.ZONA AND A.MANZANA=B.MZ
                                where CODDPTO = '{coddpto}' AND RUTA ='{ruta}'
                                ORDER BY B.UBIGEO,B.ZONA,A.FALSO_COD
                            end
                    """.format(coddpto=ruta["CODDPTO"], ruta=ruta["RUTA"])
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas))
        return rutas_manzanas

    def obtener_rutas_manzanas_por_brigada(self, brigada):

        query_rutas_manzanas_por_brigada = """
                            begin
                                SELECT B.*,A.FALSO_COD FROM TB_MANZANA A
                                INNER JOIN SEGM_U_RUTA_MANZANA  B ON A.UBIGEO= B.UBIGEO AND A.ZONA=B.ZONA AND A.MANZANA=B.MZ
                                where CODDPTO = '{coddpto}' AND BRIGADA ='{brigada}'
                                ORDER BY B.CODDPTO,B.ZONA,A.FALSO_COD
                            end
                    """.format(coddpto=brigada["CODDPTO"], brigada=brigada["BRIGADA"])
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas_por_brigada))
        return rutas_manzanas

    def llave(self, x):
        return '{}{}{}'.format(x['UBIGEO'], x['ZONA'], x['AEU'])

    def crear_aeus(self):
        self.manzanas = sorted(self.manzanas, key=lambda k: k['FALSO_COD'])
        self.list_aeu = []
        self.list_aeu_manzanas = []
        numero_aeu = 1
        cant_est_agrupados = 0
        anterior_manzana = 0  # manzana inicial

        for manzana in self.manzanas:
            m = manzana.copy()
            cant_est = m['CANT_EST']
            if (cant_est > self.cant_est_max):
                if anterior_manzana == 1:  # la anterior manzana es una menor o igual a 16 viviendas
                    if cant_est_agrupados != 0:
                        numero_aeu = numero_aeu + 1

                cant_est_agrupados = 0
                anterior_manzana = 2  # La manzana nueva tiene mas de self.cant_est_max

                #####partiendo la manzana

                division = float(cant_est) / self.cant_est_max
                cant_aeus = int(math.ceil(division))
                residuo = cant_est % cant_aeus
                est_aeu = cant_est / cant_aeus
                i = 0
                est_aeu_aux = 0

                for i in range(cant_aeus):
                    n = m.copy()

                    if i > 0:
                        numero_aeu = numero_aeu + 1

                    if residuo > 0:
                        residuo = residuo - 1
                        est_aeu_aux = est_aeu + 1

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
                        cant_est_agrupados = cant_est
                        numero_aeu = numero_aeu + 1

                anterior_manzana = 1
                m['AEU'] = numero_aeu
                self.list_aeu_manzanas.append(m)

        for key, group in itertools.groupby(self.list_aeu_manzanas, key=lambda x: self.llave(x)):
            cant_est = 0
            aeu = ''
            ubigeo = ''
            zona = ''
            for el in list(group):
                cant_est = int(el['CANT_EST']) + cant_est
                aeu = el['AEU']
                ubigeo = el['UBIGEO']
                zona = el['ZONA']

            self.list_aeu.append({'UBIGEO': ubigeo, 'ZONA': zona, 'AEU': aeu, 'CANT_EST': cant_est})

    def obtener_manzanas(self, zona):
        query_manzanas = """
        select UBIGEO,ZONA,MANZANA,CANT_EST,FALSO_COD from [DBO].[TB_MANZANA] 
        where UBIGEO = '{ubigeo}' and ZONA = '{zona}'    
        """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
        self.manzanas = to_dict(self.cursor.execute(query_manzanas))

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
        self.importar_capas(zonas)

        for brigada in brigadas:
            rutas = self.obtener_rutas(brigada)
            list_out_croquis_brigada = []
            lista_emp_brigada_est = []
            rutas_manzanas_brigada = self.obtener_rutas_manzanas_por_brigada(brigada)

            zonas_brigada = [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                              'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                              'NOMCCPP': e[9], 'BRIGADA': e[10], 'RUTA': ruta['RUTA'], 'PERIODO': e[11],
                              'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13]
                              } for e in list(set((
                                                      d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
                                                      d['DISTRITO'],
                                                      d['CODDPTO'], d['CODPROV'], d['CODDIST'], d['CODCCPP'],
                                                      d['NOMCCPP'],
                                                      d['BRIGADA'], d['PERIODO'], d['CODSEDE'], d['SEDE_OPERATIVA']) for
                                                  d in
                                                  rutas_manzanas_brigada))]

            output_brigada = path.join(self.path_listado,
                                       '{departamento}-{brigada}.pdf'.format(departamento=brigada['CODDPTO'],
                                                                             brigada=brigada['BRIGADA']))

            for zona in zonas_brigada:
                filter_rutas_manzanas = [d for d in rutas_manzanas_brigada if
                                         (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])]
                cant_est = 0
                mensaje_manzanas = u'<BOL>OBSERVACIONES: </BOL>El área de empadronamiento comprende las manzanas '

                for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                    cant_est = cant_est + int(ruta_manzana['CANT_EST'])

                if len(filter_rutas_manzanas) > 10:
                    mensaje_manzanas = u"{} {} al {} ".format(mensaje_manzanas, filter_rutas_manzanas[0]['MZ'],
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
                info = [ruta, rutas_manzanas]
                output = path.join(self.path_listado,
                                   '{departamento}-{ruta}.pdf'.format(departamento=ruta['CODDPTO'], ruta=ruta['RUTA']))
                zonas_rutas = [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                                'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                                'NOMCCPP': e[9], 'BRIGADA': e[10], 'RUTA': ruta['RUTA'], 'PERIODO': e[11],
                                'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13]
                                } for e in list(set((d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
                                                     d['DISTRITO'], d['CODDPTO'], d['CODPROV'], d['CODDIST'],
                                                     d['CODCCPP'], d['NOMCCPP'], d['BRIGADA'], d['PERIODO'],
                                                     d['CODSEDE'], d['SEDE_OPERATIVA']) for d in rutas_manzanas))]

                for zona in zonas_rutas:
                    filter_rutas_manzanas = [d for d in rutas_manzanas if
                                             (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])]
                    cant_est = 0
                    mensaje_manzanas = u'<BOL>OBSERVACIONES: </BOL>El área de empadronamiento comprende las manzanas '

                    manzanas = u""

                    for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                        cant_est = cant_est + int(ruta_manzana['CANT_EST'])

                    if len(filter_rutas_manzanas) > 10:
                        mensaje_manzanas = u"{} {} al {}".format(mensaje_manzanas, filter_rutas_manzanas[0]['MZ'],
                                                                 filter_rutas_manzanas[-1]['MZ'])
                        manzanas = u"{} al {}".format(filter_rutas_manzanas[0]['MZ'], filter_rutas_manzanas[-1]['MZ'])

                    else:
                        for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                            if count == 1:
                                manzanas = u"{}".format(ruta_manzana['MZ'])
                            else:
                                manzanas = u"{}-{}".format(manzanas, ruta_manzana['MZ'])

                            if count == len(filter_rutas_manzanas):
                                mensaje_manzanas = u"{} {}".format(mensaje_manzanas, ruta_manzana['MZ'])

                            else:
                                mensaje_manzanas = u"{} {},".format(mensaje_manzanas, ruta_manzana['MZ'])

                    zona['MANZANAS'] = manzanas

                    zona['CANT_EST'] = cant_est
                    zona['FRASE'] = mensaje_manzanas
                    lista_emp_brigada_est.append(zona)

                output_listado = listado_ruta(info, output)
                list_out_croquis = self.croquis_ruta(info, zonas_rutas)
                list_out_croquis.append(output_listado)
                final_out_ruta = path.join(self.path_croquis_listado,
                                                                   '{departamento}-{brigada}-{ruta}.pdf'.format(
                                                                       departamento=ruta['CODDPTO'],
                                                                       brigada=ruta['BRIGADA'], ruta=ruta['RUTA']))
                if path.exists(final_out_ruta):
                    remove(final_out_ruta)


                pdfDoc_ruta = arcpy.mapping.PDFDocumentCreate(final_out_ruta)

                out_programacion_ruta = path.join(self.path_programaciones,
                                                  '{departamento}-{brigada}-{ruta}.pdf'.format(
                                                      departamento=ruta['CODDPTO'],
                                                      brigada=ruta['BRIGADA'], ruta=ruta['RUTA']))

                if path.exists(out_programacion_ruta):
                    list_out_croquis.append(out_programacion_ruta)
                else:
                    print out_programacion_ruta

                for el in list_out_croquis:
                    pdfDoc_ruta.appendPages(el)
                pdfDoc_ruta.saveAndClose()

            output_listado_brigada = listado_brigada([brigada, lista_emp_brigada_est], output_brigada)
            list_out_croquis_brigada = self.croquis_brigada([brigada, rutas_manzanas_brigada], zonas_brigada)
            list_out_croquis_brigada.append(output_listado_brigada)
            final_out_brigada= path.join(self.path_croquis_listado,'{departamento}-{brigada}.pdf'.format(
                                                                   departamento=brigada['CODDPTO'],
                                                                   brigada=brigada['BRIGADA']))



            if path.exists(final_out_brigada):
                remove(final_out_brigada)

            pdfDoc_brigada = arcpy.mapping.PDFDocumentCreate(final_out_brigada)

            out_programacion_brigada = path.join(self.path_programaciones,
                                                 '{departamento}-{brigada}.pdf'.format(
                                                     departamento=brigada['CODDPTO'],
                                                     brigada=brigada['BRIGADA']))

            if path.exists(out_programacion_brigada):
                list_out_croquis_brigada.append(out_programacion_brigada)
            else:
                print out_programacion_brigada

            for el in list_out_croquis_brigada:
                pdfDoc_brigada.appendPages(el)
            pdfDoc_brigada.saveAndClose()

    def croquis_ruta(self, info, zonas):
        list_out_croquis = []
        for zona in zonas:
            ruta = info[0]
            rutas_manzanas = info[1]
            manzanas = list(set((d['UBIGEO'], d['ZONA'], d['MZ']) for d in rutas_manzanas if
                                (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])))
            frentes_ini = [(d[0], d[1], d[2], 1) for d in manzanas]

            where_manzanas = expresion.expresion_2(manzanas,
                                                   [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            where_frentes_ini = expresion.expresion_2(frentes_ini,
                                                      [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"],
                                                       ["FRENTE_ORD", "SHORT"]])
            where_zonas = expresion.expresion_2([[zona['UBIGEO'], zona['ZONA']]],
                                                [["UBIGEO", "TEXT"], ["ZONA", "TEXT"]])
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

            # df.extent = zona_mfl.getSelectedExtent()

            list_text_el = [["CODDPTO", zona["CODDPTO"]], ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']],
                            ["ZONA", zona['ZONA']]]
            list_text_el = list_text_el + [["CODCCPP", zona['CODCCPP']], ["DEPARTAMENTO", zona['DEPARTAMENTO']]]
            list_text_el = list_text_el + [["PROVINCIA", zona['PROVINCIA']], ["DISTRITO", zona['DISTRITO']],
                                           ["NOMCCPP", zona['NOMCCPP']]]
            list_text_el = list_text_el + [["BRIGADA", zona["BRIGADA"]], ["RUTA", zona["RUTA"]],
                                           ["CANT_EST", '{}'.format(zona["CANT_EST"])], ["FRASE", zona["FRASE"]],
                                           ["PERIODO", '{}'.format(zona["PERIODO"])]]

            list_text_el = list_text_el + [["DOC", "DOC.CENEC.03.07A"]]

            for text_el in list_text_el:
                el = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text = text_el[1]

            out_croquis = path.join(self.path_croquis,
                                    '{departamento}-{ruta}-{zona}.pdf'.format(departamento=ruta['CODDPTO'],
                                                                              ruta=ruta['RUTA'], zona=zona['ZONA']))

            out_croquis_copia = path.join(self.path_croquis,
                                          '{departamento}-{ruta}-{zona}-copia.pdf'.format(departamento=ruta['CODDPTO'],
                                                                                          ruta=ruta['RUTA'],
                                                                                          zona=zona['ZONA']))

            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis)

            list_text_el = list_text_el + [["DOC", "DOC.CENEC.03.07B"]]
            for text_el in list_text_el:
                el = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text = text_el[1]
            arcpy.mapping.ExportToPDF(mxd, out_croquis_copia, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis_copia)
        return list_out_croquis

    def croquis_brigada(self, info, zonas):
        list_out_croquis = []
        for zona in zonas:
            brigada = info[0]
            rutas_manzanas = info[1]
            manzanas = list(set((d['UBIGEO'], d['ZONA'], d['MZ']) for d in rutas_manzanas if
                                (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])))
            frentes_ini = [(d[0], d[1], d[2], 1) for d in manzanas]

            where_manzanas = expresion.expresion_2(manzanas,
                                                   [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            where_frentes_ini = expresion.expresion_2(frentes_ini,
                                                      [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"],
                                                       ["FRENTE_ORD", "SHORT"]])
            where_zonas = expresion.expresion_2([[zona['UBIGEO'], zona['ZONA']]],
                                                [["UBIGEO", "TEXT"], ["ZONA", "TEXT"]])
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

            list_text_el = [["CODDPTO", zona["CODDPTO"]], ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']],
                            ["ZONA", zona['ZONA']]]
            list_text_el = list_text_el + [["CODCCPP", zona['CODCCPP']], ["DEPARTAMENTO", zona['DEPARTAMENTO']]]
            list_text_el = list_text_el + [["PROVINCIA", zona['PROVINCIA']], ["DISTRITO", zona['DISTRITO']],
                                           ["NOMCCPP", zona['NOMCCPP']]]
            list_text_el = list_text_el + [["BRIGADA", zona["BRIGADA"]], ["CANT_EST", '{}'.format(zona["CANT_EST"])],
                                           ["FRASE", zona["FRASE"]], ["PERIODO", '{}'.format(zona["PERIODO"])]]

            list_text_el = list_text_el + [["DOC", "DOC.CENEC.03.09"]]

            for text_el in list_text_el:
                el = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text = text_el[1]

            out_croquis = path.join(self.path_croquis,
                                    '{departamento}-{brigada}-{zona}.pdf'.format(departamento=brigada['CODDPTO'],
                                                                                 brigada=brigada['BRIGADA'],
                                                                                 zona=zona['ZONA']))

            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis)

        return list_out_croquis


s = CroquisListadoCENEC()
s.procesar_listado_croquis()
