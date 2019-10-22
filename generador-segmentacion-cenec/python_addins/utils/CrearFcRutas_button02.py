# -*- coding: latin-1 -*-

import arcpy
import os

arcpy.env.overwriteOutput = True

gdb = arcpy.GetParameter(0)

#lyrRuta = r'\\192.168.201.115\cpv2017\SegmentacionRural_Procesamiento\Insumos\RUTA_FINAL.lyr'


def crearFeature(codsede,gdb):
    dataset =  r'{}\Procesamiento'.format(gdb)
    rutaFD = r'{}\Generales'.format(gdb)
    mxd = arcpy.mapping.MapDocument("CURRENT")
    arcpy.env.overwriteOutput= True
    arcpy.env.workspace = rutaFD
    features=arcpy.ListFeatureClasses()
    temp_aes=[feature for feature in features if feature[0:3] == 'AES'][0]
    path_aes = r'{}\{}'.format(rutaFD,temp_aes)
    #arcpy.AddWarning(path_aes)

    mf_aeus = arcpy.MakeFeatureLayer_management(path_aes,'aeus')
    select = arcpy.SelectLayerByAttribute_management(mf_aeus, 'NEW_SELECTION', 'RUTA IS NOT NULL')
    points = arcpy.FeatureToPoint_management(select, 'in_memory/points')
    mf_points = arcpy.MakeFeatureLayer_management(points, 'points')
    rutas = list(set((x[0], x[1]) for x in arcpy.da.SearchCursor(points, ["CODSEDE","RUTA"])))

    campos_RUTAS = [
                ("CODSEDE","TEXT","2",""),
                ("RUTA","TEXT","4","") ,
                ("BRIGADA","TEXT","3",""),
                ("CANT_PEA","SHORT","4",0)
                ]
    campos_BRIGADA = [
        ("CODSEDE", "TEXT", "2", ""),
        ("BRIGADA", "TEXT", "3", "")
    ]

    campos_PROGRAMACION_BRIGADAS = [
                ("PK_AEU","TEXT","15"),
                ("CODSEDE","TEXT","2"),
                ("RUTA", "SHORT", "3"),
                ("BRIGADA", "SHORT", "3"),
                ("UBIGEO", "TEXT", "6"),
                ("ZONA", "TEXT", "6"),
                ("AEU", "TEXT", "3"),

                ("TOTAL_EST", "SHORT", "3"),
                ("CANT_EST", "SHORT", "3"),
                ("MERCADO", "SHORT", "3"),
                ("PUESTO", "SHORT", "3"),
                ("ORDEN", "SHORT", "3"),
                ("PERIODO", "SHORT", "3"), ("FECHA_INI","DATE","40"),
                ("FECHA_FIN","DATE","40"), ("DIAS_VIAJE", "SHORT", "3"),
                ("DIAS_TRABAJO", "SHORT", "3"),("GABINETE","SHORT","3"),("DIAS_RECUPERACION", "SHORT", "3"),("DIAS_DESCANSO", "SHORT", "3"),
                ("DIAS_OPERATIVOS", "SHORT", "3"),("PASAJES", "DOUBLE", "3"), ("VIATICOS", "SHORT", "3"),
                ("MOV_LOCAL", "SHORT", "3"),("MOV_ESPECIAL", "SHORT", "3")

                ]

    ############ CREANDO RUTAS##############
    for ruta in rutas:
        new_points = arcpy.SelectLayerByAttribute_management(mf_points, "NEW_SELECTION"," CODSEDE='{}' and RUTA={} ".format(ruta[0], ruta[1]))

        ruta_x = arcpy.PointsToLine_management(new_points, 'in_memory/rutas_temp', '','ORDEN')

        geometria = [(el[0]) for el in arcpy.da.SearchCursor(ruta_x, ['SHAPE@'])][0]

        aeus_ruta = arcpy.SelectLayerByAttribute_management(mf_aeus, 'NEW_SELECTION', " CODSEDE='{}' and RUTA={} ".format(ruta[0],ruta[1]))

        personal_ad = 0
        brigada = 0
        for el in arcpy.da.SearchCursor(aeus_ruta, ['PERSONAL_AD','BRIGADA']):
            personal_ad= int(el[0]) +personal_ad
            if el[1] is not None:
                if brigada < int(el[1]):
                    brigada = int(el[1])


        if arcpy.Exists('{}/rutas_temp'.format(dataset))== False:

            rutas_fm = arcpy.CreateFeatureclass_management(dataset, "rutas_temp", "POLYLINE", "#", "#", "#",
                                                         arcpy.SpatialReference(4326))
            for n in campos_RUTAS:
                if n[1] == "TEXT":
                    arcpy.AddField_management(rutas_fm, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
                else:
                    arcpy.AddField_management(rutas_fm, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')


        with arcpy.da.InsertCursor('{}/rutas_temp'.format(dataset),
                                   ['SHAPE@', 'CODSEDE', 'RUTA', 'BRIGADA', 'CANT_PEA']) as cursor:
            row = (geometria, ruta[0],str(ruta[1]).zfill(3) , str(brigada).zfill(3), personal_ad + 1)
            cursor.insertRow(row)
        del cursor



    #mxd = arcpy.mapping.MapDocument("CURRENT")
    #df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
    #for lyr in arcpy.mapping.ListLayers(mxd, "", df):
    #    if lyr.name.lower() == "aeus":
    #        arcpy.mapping.RemoveLayer(df, lyr)

    rutas_fm_final = arcpy.CopyFeatures_management('{}/rutas_temp'.format(dataset),'{}/rutas_{}'.format(dataset,codsede))

    arcpy.Delete_management('{}/rutas_temp'.format(dataset))


    ##############CREANDO BRIGADAS############################
    brigadas=arcpy.MinimumBoundingGeometry_management(rutas_fm_final, '{}/brigadas_{}'.format(dataset, codsede), "CONVEX_HULL",
                                             "LIST", ["CODSEDE", "BRIGADA"])


    #list_brigadas = list(set((x[0], x[1]) for x in arcpy.da.SearchCursor(rutas_fm_final, ["CODSEDE", "BRIGADA"])))
#
    #mf_rutas = arcpy.MakeFeatureLayer_management('{}/rutas_{}'.format(dataset,codsede), 'mf_rutas')
#

    #for brigada in list_brigadas:
    #    temp_rutas = arcpy.SelectLayerByAttribute_management(mf_rutas,'NEW_SELECTION',"CODSEDE = '{}' and BRIGADA = '{}'".format(brigada[0],brigada[1]))
    #    brigada_x = arcpy.MinimumBoundingGeometry_management(temp_rutas,'in_memory/brigadas_temp' )
#
    #    geometria = [(el[0]) for el in arcpy.da.SearchCursor(brigada_x, ['SHAPE@'])][0]
#
    #    if arcpy.Exists('{}/brigadas_temp'.format(dataset))==False:
    #        brigadas_fm = arcpy.CreateFeatureclass_management(dataset, "brigadas_temp", "POLYGON", "#", "#", "#",
    #                                                       arcpy.SpatialReference(4326))
#
    #        for n in campos_BRIGADA:
    #            if n[1] == "TEXT":
    #                arcpy.AddField_management(brigadas_fm, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
    #            else:
    #                arcpy.AddField_management(brigadas_fm, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')
#
    #    with arcpy.da.InsertCursor('{}/brigadas_temp'.format(dataset),
    #                               ['SHAPE@', 'CODSEDE',  'BRIGADA']) as cursor:
    #        row = (geometria, brigada[0], brigada[1])
    #        cursor.insertRow(row)
#
    #del cursor
#
    #brigadas_fm_final = arcpy.CopyFeatures_management('{}/brigadas_temp'.format(dataset),
    #                                                   '{}/brigadas_{}'.format(dataset, codsede))
    #
    #arcpy.Delete_management('{}/brigadas_temp'.format(dataset))
#
    ######PROGRAMACION DE BRIGADAS ############

    #programacion_brigadas = arcpy.CreateTable_management(gdb, "programacion_brigadas")
    programacion_brigadas = arcpy.CreateFeatureclass_management(dataset, "programacion_brigadas_{codsede}".format(codsede=codsede), "POLYGON", "#", "#", "#", arcpy.SpatialReference(4326))

    for n in campos_PROGRAMACION_BRIGADAS:
        if n[1] == "TEXT":
            arcpy.AddField_management(programacion_brigadas, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
        else:
            arcpy.AddField_management(programacion_brigadas, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')

    mf_aeus_select=arcpy.SelectLayerByAttribute_management(mf_aeus, 'NEW_SELECTION' )

    list_aeus =  [ x for x in arcpy.da.SearchCursor(mf_aeus, ['CODSEDE', 'BRIGADA','CANT_EST','PERIODO',
                                                              'FECHA_INI','FECHA_FIN','DIAS_VIAJE',
                                                              'DIAS_TRABAJO','DIAS_RECUPERACION','DIAS_DESCANSO',
                                                              'DIAS_OPERATIVOS','PASAJES','VIATICOS',
                                                              'MOV_LOCAL','MOV_ESPECIAL','ORDEN','UBIGEO','ZONA','AEU','SHAPE@',
                                                              'RUTA','PK_AEU','TOTAL_EST','MERCADO','PUESTO'])]


    for x in list_aeus:

        with arcpy.da.InsertCursor('{dataset}/programacion_brigadas_{codsede}'.format(dataset=dataset,codsede=codsede),
                                                             ['CODSEDE', 'BRIGADA','CANT_EST','PERIODO',
                                                              'FECHA_INI','FECHA_FIN','DIAS_VIAJE',
                                                              'DIAS_TRABAJO','DIAS_RECUPERACION','DIAS_DESCANSO',
                                                              'DIAS_OPERATIVOS','PASAJES','VIATICOS',
                                                              'MOV_LOCAL','MOV_ESPECIAL','ORDEN','UBIGEO','ZONA','AEU','SHAPE@',
                                                              'RUTA','PK_AEU','TOTAL_EST','MERCADO','PUESTO']) as cursor:

            row = (x[0], x[1], x[2], x[3],None,None,0,0,0,0,0,0,x[12],0,0,x[15],x[16],x[17],x[18],x[19],x[20],x[21],x[22],x[23],x[24])

            cursor.insertRow(row)

    del cursor

    #######################PROGRAMACION ADICIONAL###################
    mf_aeus_select = arcpy.SelectLayerByAttribute_management(mf_aeus, 'NEW_SELECTION', 'PERSONAL_AD > 0')
    cant_adicional=int(arcpy.GetCount_management(mf_aeus_select)[0])

    if(cant_adicional>0):
        programacion_adicional = arcpy.CreateFeatureclass_management(dataset, "programacion_adicional_{codsede}".format(
            codsede=codsede), "POLYGON", "#", "#", "#", arcpy.SpatialReference(4326))
        for n in campos_PROGRAMACION_BRIGADAS:
            if n[1] == "TEXT":
                arcpy.AddField_management(programacion_adicional, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
            else:
                arcpy.AddField_management(programacion_adicional, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')



        list_aeus =  [ x for x in arcpy.da.SearchCursor(mf_aeus_select, ['CODSEDE', 'BRIGADA','CANT_EST','PERIODO',
                                                                  'FECHA_INI','FECHA_FIN','DIAS_VIAJE',
                                                                  'DIAS_TRABAJO','DIAS_RECUPERACION','DIAS_DESCANSO',
                                                                  'DIAS_OPERATIVOS','PASAJES','VIATICOS',
                                                                  'MOV_LOCAL','MOV_ESPECIAL','ORDEN','UBIGEO','ZONA','AEU','SHAPE@',
                                                                  'RUTA','PK_AEU','TOTAL_EST','MERCADO','PUESTO','PERSONAL_AD'])]



        for x in list_aeus:
            personal_ad = int(x[25])

            for i in range(personal_ad):

                with arcpy.da.InsertCursor('{dataset}/programacion_adicional_{codsede}'.format(dataset=dataset,codsede=codsede),
                                                                        ['CODSEDE', 'BRIGADA','CANT_EST','PERIODO',
                                                                      'FECHA_INI','FECHA_FIN','DIAS_VIAJE',
                                                                      'DIAS_TRABAJO','DIAS_RECUPERACION','DIAS_DESCANSO',
                                                                      'DIAS_OPERATIVOS','PASAJES','VIATICOS',
                                                                      'MOV_LOCAL','MOV_ESPECIAL','ORDEN','UBIGEO','ZONA','AEU','SHAPE@',
                                                                      'RUTA','PK_AEU','TOTAL_EST','MERCADO','PUESTO']) as cursor:


                    row = (x[0], x[1], x[2], x[3],x[4],x[5],x[6],x[7],x[8],x[9],x[10],x[11],x[12],x[13],x[14],x[15],x[16],x[17],x[18],x[19],x[20],x[21],x[22],x[23],x[24] )

                    cursor.insertRow(row)

            del cursor



    return rutas_fm_final,brigadas,programacion_brigadas



def validarGDB(gdb):
    desc = arcpy.Describe(gdb)
    validacion = desc.basename
    if validacion[0:8] == 'BD_SEGM_':
        if arcpy.Exists(r'{}\Procesamiento'.format(gdb)):
            codsede = validacion[8:10]
            rutas,brigadas,programacion_brigadas = crearFeature(codsede,gdb)
            arcpy.SetParameterAsText(1, rutas)
            arcpy.SetParameterAsText(2, brigadas)
            arcpy.SetParameterAsText(3, programacion_brigadas)
            params = arcpy.GetParameterInfo()
        else:
            arcpy.AddError("OBSERVACION:")
            arcpy.AddError("No se encuentra el dataset 'Procesamiento' dentro de la GDB ingresada")
    else:
        arcpy.AddError("OBSERVACION:")
        arcpy.AddError("Ingrese la GDB correcta")


validarGDB(gdb)








