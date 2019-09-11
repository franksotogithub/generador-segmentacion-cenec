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

    def importar_capas(self, zonas,cod_oper='01'):
        print 'zonas>>>',zonas
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

        if cod_oper=='99':
            where_ubigeo = "({}) AND FASE=-1 ".format(where_ubigeo)
            where_zona = "({}) AND FASE=-1".format(where_zona)
        else:
            where_ubigeo = "({}) AND FASE=0 ".format(where_ubigeo)
            where_zona = "({}) AND FASE=0 ".format(where_zona)

        list_capas = [
            ["{}.DBO.TB_MANZANA".format(config.DB_NAME), "tb_manzana", 2],
            # ["{}.DBO.TB_SITIO_INTERES".format(config.DB_NAME), "tb_sitios_interes", 2],
            ["{}.DBO.TB_ZONA".format(config.DB_NAME), "tb_zona", 1],
            #["{}.DBO.TB_PUNTO_INICIO".format(config.DB_NAME), "tb_punto_inicio", 1],
            ["{}.DBO.TB_FRENTES".format(config.DB_NAME), "tb_frentes", 1],
            ["{}.DBO.TB_EJE_VIAL".format(config.DB_NAME), "tb_eje_vial", 2],
        ]

        ## 1 exportacion de datos a nivel de zona, 2 exportacion a nivel de distrito

        for i, capa in enumerate(list_capas):
            if (capa[2] == 1):
                where = where_zona
            else:
                where = where_ubigeo
            print('where>>>', where)
            x = arcpy.MakeQueryLayer_management(path_conexion, 'capa{}'.format(i),
                                                "select * from {} where  {}  ".format(capa[0], where))

            temp = arcpy.CopyFeatures_management(x, '{}/{}'.format(self.path_trabajo, capa[1]))


    def obtener_brigadas(self,cod_oper='01'):
        query_brigadas = """
                begin
                    select * from [dbo].[SEGM_U_BRIGADA] 
                    where isnull(COD_OPER,'01')='{cod_oper}'                  
                end
        """.format(cod_oper=cod_oper)

        print 'query_brigadas >>>',query_brigadas
        brigadas = to_dict(self.cursor.execute(query_brigadas))
        return brigadas

    def obtener_rutas(self, brigada):
        query_rutas = """
                begin
                    select * from [dbo].[SEGM_U_RUTA]
                    where CODDPTO = '{coddpto}' AND BRIGADA ='{brigada}' AND COD_OPER ='{cod_oper}' 
                    ORDER BY CODDPTO,RUTA 
                end
        """.format(coddpto=brigada["CODDPTO"], brigada=brigada["BRIGADA"],cod_oper=brigada["COD_OPER"])
        print 'query_rutas>>>',query_rutas
        rutas = to_dict(self.cursor.execute(query_rutas))
        return rutas

    def obtener_rutas_manzanas(self, ruta):

        query_rutas_manzanas = """
                            begin
                                   
                                SELECT B.*,B.MARCO_FIN CANT_EST ,A.FALSO_COD FROM TB_PSEUDO_CODIGO A
                                INNER JOIN SEGM_U_RUTA_MANZANA  B ON A.UBIGEO= B.UBIGEO AND A.ZONA=B.ZONA AND A.MANZANA=B.MZ AND A.FASE=B.FASE
                                where B.CODDPTO = '{coddpto}' AND B.RUTA ='{ruta}' AND B.COD_OPER = '{cod_oper}'
                                ORDER BY B.UBIGEO,B.ZONA,A.FALSO_COD
                            end
                    """.format(coddpto=ruta["CODDPTO"], ruta=ruta["RUTA"],cod_oper =ruta["COD_OPER"])
        print 'query_rutas_manzanas>>>',query_rutas_manzanas
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas))
        return rutas_manzanas

    def obtener_emp_por_ruta(self, ruta):
        query= """
                            begin
                                
                                SELECT *  FROM SEGM_U_EMPADRONADOR   
                                where CODSEDE = '{codsede}' AND RUTA ='{ruta}' AND COD_OPER='{cod_oper}'
                                order by CODSEDE,RUTA,EMP
                            end
                    """.format(codsede=ruta["CODSEDE"], ruta=ruta["RUTA"] , cod_oper=ruta["COD_OPER"])
        print 'obtener_emp_por_ruta>>>',query
        empadronadores = to_dict(self.cursor.execute(query))
        return empadronadores

    def obtener_rutas_manzanas_por_brigada(self, brigada):

        query_rutas_manzanas_por_brigada = """
                            begin
                                --SELECT B.*,A.FALSO_COD,B.MARCO_FIN CANT_EST FROM TB_MANZANA A
                                --INNER JOIN SEGM_U_RUTA_MANZANA  B ON A.UBIGEO= B.UBIGEO AND A.ZONA=B.ZONA AND A.MANZANA=B.MZ
                                --where CODDPTO = '{coddpto}' AND BRIGADA ='{brigada}'
                                --ORDER BY B.CODDPTO,B.ZONA,A.FALSO_COD
                                
                                SELECT B.*,B.MARCO_FIN CANT_EST ,A.FALSO_COD FROM TB_PSEUDO_CODIGO A
                                INNER JOIN SEGM_U_RUTA_MANZANA  B ON A.UBIGEO= B.UBIGEO AND A.ZONA=B.ZONA AND A.MANZANA=B.MZ AND A.FASE=B.FASE
                                where B.CODDPTO = '{coddpto}' AND B.BRIGADA ='{brigada}' AND B.COD_OPER = '{cod_oper}'
                                ORDER BY B.UBIGEO,B.ZONA,A.FALSO_COD
                            end
                    """.format(coddpto=brigada["CODDPTO"], brigada=brigada["BRIGADA"],cod_oper = brigada["COD_OPER"])
        print  'query_rutas_manzanas_por_brigada>>>', query_rutas_manzanas_por_brigada
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas_por_brigada))
        return rutas_manzanas



    def obtener_manzanas(self, zona):
        query_manzanas = """
        select UBIGEO,ZONA,MANZANA,CANT_EST,FALSO_COD from [DBO].[TB_MANZANA] 
        where UBIGEO = '{ubigeo}' and ZONA = '{zona}'    
        """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
        self.manzanas = to_dict(self.cursor.execute(query_manzanas))

    def procesar_croquis_listado(self,cod_oper='01'):
        if cod_oper =='01':
            self.path_croquis_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'croquis_listado')
            self.path_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'listado')
            self.path_croquis = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'croquis')
        elif cod_oper =='99':
            self.path_croquis_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'capacitacion','croquis_listado')
            self.path_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'capacitacion', 'listado')
            self.path_croquis = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'capacitacion', 'croquis')
        elif cod_oper == '98':
            self.path_croquis_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'curso', 'croquis_listado')
            self.path_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'curso', 'listado')
            self.croquis = path.join(config.BASE_DIR_CROQUIS_LISTADO, r'curso', 'croquis')

        brigadas = self.obtener_brigadas(cod_oper=cod_oper)
        zonas = []
        for brigada in brigadas:
            rutas = self.obtener_rutas(brigada)
            for ruta in rutas:
                rutas_manzanas = self.obtener_rutas_manzanas(ruta)
                zonas = zonas + [{'UBIGEO': e[0], 'ZONA': e[1]} for e in
                                 list(set((d['UBIGEO'], d['ZONA']) for d in rutas_manzanas))]
        ##############importando capas para los croquis###########
        self.importar_capas(zonas,cod_oper)

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
                                                      d['NOMCCCPP'],
                                                      d['BRIGADA'], d['PERIODO'], d['CODSEDE'], d['SEDE_OPERATIVA']) for
                                                  d in
                                                  rutas_manzanas_brigada))]

            output_brigada = path.join(self.path_listado,
                                       '{cod_oper}-{sede}-{brigada}.pdf'.format(cod_oper=brigada['COD_OPER'] ,sede=brigada['CODSEDE'],
                                                                             brigada=brigada['BRIGADA']))
            print "zonas_brigada>>>", zonas_brigada
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
            print "rutas>>>", rutas
            for ruta in rutas:
                rutas_manzanas = self.obtener_rutas_manzanas(ruta)
                info = [ruta, rutas_manzanas]
                output = path.join(self.path_listado,
                                   '{cod_oper}-{sede}-{brigada}-{ruta}.pdf'.format(cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'], ruta=ruta['RUTA']))
                zonas_rutas = [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                                'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                                'NOMCCCPP': e[9], 'BRIGADA': e[10], 'RUTA': ruta['RUTA'], 'PERIODO': e[11],
                                'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13]
                                } for e in list(set((d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
                                                     d['DISTRITO'], d['CODDPTO'], d['CODPROV'], d['CODDIST'],
                                                     d['CODCCPP'], d['NOMCCCPP'], d['BRIGADA'], d['PERIODO'],
                                                     d['CODSEDE'], d['SEDE_OPERATIVA']) for d in rutas_manzanas))]

                empadronadores = self.obtener_emp_por_ruta(ruta)

                print "empadronadores>>>", empadronadores
                for emp in empadronadores:
                    info[0]['EMP'] = emp['EMP']
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
                    list_out_croquis = self.croquis_ruta(info, zonas_rutas,emp)
                    list_out_croquis.append(output_listado)
                    final_out_ruta = path.join(self.path_croquis_listado,'{cod_oper}-{sede}-{brigada}-{ruta}-{emp}.pdf'.format(
                                                                           cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],
                                                                           brigada=ruta['BRIGADA'], ruta=ruta['RUTA'],emp=emp['EMP']))
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

            final_out_brigada= path.join(self.path_croquis_listado,'{cod_oper}-{sede}-{brigada}.pdf'.format(
                                                                   cod_oper=brigada['COD_OPER'],sede=brigada['CODSEDE'],
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

    def croquis_ruta(self, info, zonas,emp):
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



            codigo ='{cod_oper}{sede}{brigada}{ruta}{emp}'.format( cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],ruta=ruta['RUTA'],emp= emp['EMP'])

            list_text_el = [["COD_BARRA", "*{}*".format(codigo)], ["TEXT_COD_BARRA", "{}".format(codigo)],["CODDPTO", zona["CODDPTO"]], ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']],
                            ["ZONA", zona['ZONA']]]
            list_text_el = list_text_el + [["CODCCPP", zona['CODCCPP']], ["DEPARTAMENTO", zona['DEPARTAMENTO']]]
            list_text_el = list_text_el + [["PROVINCIA", zona['PROVINCIA']], ["DISTRITO", zona['DISTRITO']],
                                           ["NOMCCPP", zona['NOMCCCPP']]]
            list_text_el = list_text_el + [["BRIGADA", zona["BRIGADA"]], ["RUTA", zona["RUTA"]],
                                           ["CANT_EST", '{}'.format(zona["CANT_EST"])], ["FRASE", zona["FRASE"]],
                                           ["PERIODO", '{}'.format(zona["PERIODO"])]]

            list_text_el = list_text_el + [["DOC", "DOC.CENEC.03.07A"]]

            for text_el in list_text_el:
                el = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text = text_el[1]

            out_croquis = path.join(self.path_croquis,
                                    '{cod_oper}-{sede}-{brigada}-{ruta}-{ubigeo}-{zona}.pdf'.format(cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],
                                                                              ruta=ruta['RUTA'], ubigeo=zona['UBIGEO'],zona=zona['ZONA']))

            out_croquis_copia = path.join(self.path_croquis,
                                          '{cod_oper}-{sede}-{brigada}-{ruta}-{ubigeo}-{zona}-b.pdf'.format(cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],
                                                                                          ruta=ruta['RUTA'],
                                                                                          ubigeo=zona['UBIGEO'],
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
            print 'zona>>',zona

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

            codigo = '{cod_oper}{sede}{brigada}'.format(cod_oper=brigada['COD_OPER'], sede=brigada['CODSEDE'],
                                                                   brigada=brigada['BRIGADA'])

            list_text_el = [["COD_BARRA", "*{}*".format(codigo)], ["TEXT_COD_BARRA", "{}".format(codigo)],["CODDPTO", zona["CODDPTO"]], ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']],
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
                                    '{cod_oper}-{sede}-{brigada}-{ubigeo}-{zona}.pdf'.format(
                                                                                        cod_oper=brigada['COD_OPER'],
                                                                                        sede=brigada['CODSEDE'],
                                                                                        brigada=brigada['BRIGADA'],
                                                                                        ubigeo=zona['UBIGEO'],
                                                                                        zona=zona['ZONA']))

            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis)

        return list_out_croquis

s = CroquisListadoCENEC()
s.procesar_croquis_listado(cod_oper ='01')                                                                                                                                                                 *-+98q
