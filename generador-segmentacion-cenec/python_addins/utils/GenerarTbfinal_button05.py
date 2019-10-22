import arcpy

arcpy.env.overwriteOutput = True

gdb = arcpy.GetParameter(0)



def crearFeatures(ubigeo, gdb):

    featureClass = [["SEGM_R_RUTA_{}".format(ubigeo), "POLYGON"], ["SEGM_R_CCPPRUTA_{}".format(ubigeo), "POINT"]]

    Campos_RUTA = [("UBIGEO", "TEXT", "6"), ("IDSCR", "TEXT", "14"), ("SCR", "TEXT", "3"), ("IDRUTA", "TEXT", "17"), ("RUTA", "TEXT", "3"),
                   ("N_VIV_RUTA", "SHORT", "5"), ("N_EMP_RUTA", "SHORT", "5")]

    Campos_CCPPRUTA = [("UBIGEO", "TEXT", "6"), ("IDSCR", "TEXT", "14"), ("SCR", "TEXT", "3"), ("IDAER", "TEXT", "12"),
                       ("AER_INI", "TEXT", "3"), ("AER_FIN", "TEXT", "3"),("IDRUTA", "TEXT", "17"), ("RUTA", "TEXT", "3"),
                       ("IDCCPP", "TEXT", "10"), ("CODCCPP", "TEXT", "4"),("NOMCCPP", "TEXT", "150"), ("CAT_CCPP", "TEXT", "50"),
                       ("OR_CCPP", "SHORT", "5"), ("VIV_CCPP", "SHORT", "5")]


    for i in featureClass:

        fc_tmp = arcpy.CreateFeatureclass_management("in_memory", i[0], i[1], "#", "#", "#", arcpy.SpatialReference(4326))

        if i[0] == "SEGM_R_RUTA_{}".format(ubigeo):
            for n in Campos_RUTA:
                if n[1] == "TEXT":
                    arcpy.AddField_management(fc_tmp, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
                else:
                    arcpy.AddField_management(fc_tmp, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')
        elif i[0] == "SEGM_R_CCPPRUTA_{}".format(ubigeo):
            for n in Campos_CCPPRUTA:
                if n[1] == "TEXT":
                    arcpy.AddField_management(fc_tmp, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
                else:
                    arcpy.AddField_management(fc_tmp, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')

        wspace = r'{}\Resultados'.format(gdb)

        arcpy.CreateFeatureclass_management(wspace, i[0], i[1], fc_tmp, "#", "#", arcpy.SpatialReference(4326))


def reordenarRutas(rutas, seccion, maxRutas):

    rutas_copy = arcpy.CopyFeatures_management(rutas, 'in_memory\\rutas_copy')

    arcpy.AddField_management(rutas_copy, "RUTA", "TEXT", '#', '#', 3)
    arcpy.AddField_management(rutas_copy, "SCR", "TEXT", '#', '#', 3)

    ruta_mfl = arcpy.MakeFeatureLayer_management(rutas_copy, "ruta_mfl")

    orderby = (None, "ORDER BY SCR ASC")

    contador = 0
    for x in[[x[0], x[1]] for x in arcpy.da.SearchCursor(seccion, ["SHAPE@", "SCR"], "#", None, False, orderby)]:
        seleccion = arcpy.SelectLayerByLocation_management(ruta_mfl, "WITHIN", x[0], "#", "NEW_SELECTION", "NOT_INVERT")
        listaRutas = [m for m in arcpy.da.SearchCursor(seleccion, ["SHAPE@Y", "OID@"])]
        listaRutas.sort(key=lambda orden:orden[0], reverse=True)
        for n in listaRutas:
            with arcpy.da.UpdateCursor(rutas_copy, ["RUTA", "SCR"], "OBJECTID = {}".format(n[1])) as cursorUC:
                for m in cursorUC:
                    m[0] = str(maxRutas + contador + 1)
                    m[1] = str(x[1])
                    contador = contador + 1
                    cursorUC.updateRow(m)
            del cursorUC

    return rutas_copy


def reordenarCcppRuta(rutas_copy, ccppruta, maxRutas):

    ccpprutas_copy = arcpy.CopyFeatures_management(ccppruta, 'in_memory\\ccpprutas_copy')

    arcpy.AddField_management(ccpprutas_copy , "RUTA", "TEXT", '#', '#', 3)
    arcpy.AddField_management(ccpprutas_copy , "SCR", "TEXT", '#', '#', 3)

    ccpps_mfl = arcpy.MakeFeatureLayer_management(ccpprutas_copy, 'ccpps_mfl')

    for x in arcpy.da.SearchCursor(rutas_copy, ["SHAPE@", "RUTA", "SCR"]):
        seleccion = arcpy.SelectLayerByLocation_management(ccpps_mfl, "INTERSECT", x[0], "#", "NEW_SELECTION", "NOT_INVERT")

        ruta = str(x[1])
        scr = str(x[2])
        arcpy.CalculateField_management(seleccion, "RUTA", ruta)
        arcpy.AddMessage(ruta)
        arcpy.CalculateField_management(seleccion, "SCR", scr)

    return ccpprutas_copy


def tb_Rutas(rutas_copy, SEGM_R_CCPPRUTA, SEGM_R_RUTA):
    arcpy.Append_management(rutas_copy, SEGM_R_RUTA, "NO_TEST")
    with arcpy.da.UpdateCursor(SEGM_R_RUTA, ["IDSCR", "IDRUTA", "UBIGEO", "SCR", "RUTA", "N_VIV_RUTA"]) as cursorUC:
        for x in cursorUC:
            x[3] = (x[3]).zfill(3)
            x[4] = (x[4]).zfill(3)
            x[0] = '{}00000{}'.format(x[2], x[3])
            x[1] = '{}{}'.format(x[0], x[4])
            viviendas = sum(m[0] for m in arcpy.da.SearchCursor(SEGM_R_CCPPRUTA, ["VIV_CCPP"], "IDRUTA = '{}'".format(x[1])))
            x[5] = viviendas

            cursorUC.updateRow(x)
    del cursorUC


def tb_ccppRutas(ccpprutas_copy, SEGM_R_CCPPRUTA):

    arcpy.Append_management(ccpprutas_copy, SEGM_R_CCPPRUTA, "NO_TEST")
    with arcpy.da.UpdateCursor(SEGM_R_CCPPRUTA, ["IDSCR", "IDRUTA", "UBIGEO", "SCR", "RUTA"]) as cursorUC:
        for x in cursorUC:
            x[3] = (x[3]).zfill(3)
            x[4] = (x[4]).zfill(3)
            x[0] = '{}00000{}'.format(x[2], x[3])
            x[1] = '{}{}'.format(x[0], x[4])
            cursorUC.updateRow(x)
    del cursorUC


def generarTablas(gdb):

    desc = arcpy.Describe(gdb)
    validacion = desc.basename
    ubigeo = validacion[10:16]

    informacion = []

    seccion = r'{}\Procesamiento\SCR_{}'.format(gdb, ubigeo)
    ruta = r'{}\Procesamiento\RUTAS_{}'.format(gdb, ubigeo)
    ccppruta = r'{}\Procesamiento\CCPPRUTAS_{}'.format(gdb, ubigeo)
    SEGM_R_CCPPRUTA = r'{}\Resultados\SEGM_R_CCPPRUTA_{}'.format(gdb, ubigeo)
    SEGM_R_RUTA = r'{}\Resultados\SEGM_R_RUTA_{}'.format(gdb, ubigeo)
    RUTA_OLD = r'{}\Resultados\RUTA_OLD_{}'.format(gdb, ubigeo)

    maxRutas = len([h for h in arcpy.da.SearchCursor(RUTA_OLD, ["IDRUTA"])])
    arcpy.AddMessage(maxRutas)


    crearFeatures(ubigeo, gdb)
    rutas_copy = reordenarRutas(ruta, seccion, maxRutas)
    ccpprutas_copy = reordenarCcppRuta(rutas_copy, ccppruta, maxRutas)
    tb_ccppRutas(ccpprutas_copy, SEGM_R_CCPPRUTA)
    tb_Rutas(rutas_copy, SEGM_R_CCPPRUTA, SEGM_R_RUTA)
    arcpy.SetParameterAsText(1, SEGM_R_CCPPRUTA)
    arcpy.SetParameterAsText(2, SEGM_R_RUTA)



generarTablas(gdb)