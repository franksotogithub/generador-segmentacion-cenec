# -*- coding: utf-8 -*-
#    IMPORTANDO LIBRERIAS NECESARIAS
from reportlab.platypus import Paragraph
from reportlab.platypus import Image
from reportlab.platypus import SimpleDocTemplate, Image
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet            #   ->  Importa clase de hoja de estilo
from reportlab.lib.pagesizes import A4,A3,letter,B2
from reportlab.lib import colors                                #   ->  Importa colores
from reportlab.platypus import Table                            #   -> Importa las funcionalidades para crear tablas
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle, PageBreak
from  reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.barcode import code39,code128
import arcpy
import math

from os import path
from conf import config

h1 = PS(
    name='Heading1',
    fontSize=7,
    leading=8
)

h11 = PS(
    name='Heading1',
    fontSize=7,
    leading=8,
    alignment=TA_CENTER
)

h111 = PS(
    name='Heading1',
    fontSize=7,
    leading=8,
    alignment=TA_RIGHT
)

h3 = PS(
    name='Normal',
    fontSize=6.5,
    leading=10,
    alignment=TA_CENTER
)

h4 = PS(
    name='Normal',
    fontSize=7,
    leading=10,
    alignment=TA_LEFT
)

h_sub_tile = PS(
    name='Heading1',
    fontSize=10,
    leading=14,
    alignment=TA_CENTER
)
h_sub_tile_2 = PS(
    name='Heading1',
    fontSize=11,
    leading=14,
    alignment=TA_CENTER
)


escudo_nacional = path.join(config.PATH_IMG,'Escudo_BN.png')
logo_nacional = path.join(config.PATH_IMG,'Inei_BN.png')

def contar_registros(rows,ini,rango):
    dato = ini
    while dato < rows:
        dato = dato + rango
    lista_ini = list(range(ini, dato - (rango - 1), rango))

    lista_fin = list(range(ini + rango, dato + 1, rango))

    lista_fin[-1] = rows
    final = zip(lista_ini, lista_fin)
    return final


def listado_ruta(info, output):
    cab=info[0]
    data= info[1]
    coddpto = cab["CODDPTO"]
    departamento = cab["DEPARTAMENTO"]
    brigada = cab["BRIGADA"]
    ruta = cab["RUTA"]
    empadronador = ""

    Plantilla = getSampleStyleSheet()

    Elementos = []


    Titulo = Paragraph(u'V CENSO NACIONAL ECONÓMICO <br/> 2019 - 2020',h_sub_tile)
    SubTitulo = Paragraph(u'<strong>LISTADO DE CENTROS POBLADOS Y MANZANAS DEL EMPADRONADOR</strong>', h_sub_tile_2)


    CabeceraPrincipal = [[Titulo,'',''],
                         [Image(escudo_nacional, width=50, height=50), SubTitulo, Image(logo_nacional, width=55, height=50)]]

    Tabla0 = Table(CabeceraPrincipal, colWidths=[2 * cm, 14 * cm, 2 * cm])

    Tabla0.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('SPAN', (0, 0), (2, 0)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

    ]))


    Elementos.append(Tabla0)
    Elementos.append(Spacer(0, 10))


    Filas = [
        ['', '', '', '', 'Doc.CENEC.XXX'],
        [ Paragraph(u'<b>A. ORGANIZACIÓN DE CAMPO</b>',h11), '', '', '', Paragraph(u'<b>B. NOMBRE Y APELLIDO DEL EMPADRONADOR</b>',h11)],
        [Paragraph(u'<b>DEPARTAMENTO: </b>', h1), u'{}'.format(coddpto), u'{}'.format(departamento), '',u'{}'.format(empadronador)],
        [Paragraph(u'<b>BRIGADA: </b>', h1), u'{}'.format(brigada), '', '', ''],
        [Paragraph(u'<b>RUTA: </b>', h1), u'{}'.format(ruta),'', '', ''],
        ]

    Tabla = Table(Filas, colWidths=[3.7 * cm, 1 * cm, 6.3 * cm, 7 * cm,  10 * cm],rowHeights=[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm])

    Tabla.setStyle(TableStyle([
           ('TEXTCOLOR', (0, 0), (4, 0), colors.black),
           ('GRID', (0, 1), (2, 4), 1, colors.black),
           ('GRID', (4, 1), (4, 2), 1, colors.black),
           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
           ('ALIGN', (0, 1), (4, 1), 'CENTER'),
           ('ALIGN', (0, 1), (0, 4), 'LEFT'),
           ('ALIGN', (1, 1), (2, 4), 'CENTER'),
           ('FONTSIZE', (0, 0), (-1, -1), 8),
           ('BACKGROUND', (0, 1), (2, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('BACKGROUND', (0, 1), (0, 4), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('BACKGROUND', (4, 1), (4, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('SPAN', (0, 1), (2, 1)),
           ('SPAN', (1, 3), (2, 3)),
           ('SPAN', (1, 4), (2, 4)),
    ]))
    Elementos.append(Tabla)
    Elementos.append(Spacer(0, 10))

    CabeceraSecundaria = [
         [Paragraph(e, h3) for e in [u"<strong>Nº ORD</strong>",u"<strong>UBIGEO</strong>", u"<strong>DEPARTAMENTO</strong>",
                                        u"<strong>PROVINCIA</strong>",u"<strong>DISTRITO</strong>",u"<strong>COD.CCPP</strong>",
                                        u"<strong>PERIODO</strong>",u"<strong>UBICACIÓN CENSAL</strong>","","",u"<strong>TOT. EST.</strong>"
          ]],
          [Paragraph(e, h3) for e in["","","","","","","","AREA","ZONA","MZ",""]],
        ]

    columnas= [2 * cm, 2 * cm,4*cm ,4* cm,4* cm,2*cm ,2*cm ,2*cm ,2* cm,2*cm ,2* cm]

    Tabla1 = Table(CabeceraSecundaria, colWidths=columnas)

    Tabla1.setStyle(TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (2, 0), (2, 1)),
            ('SPAN', (3, 0), (3, 1)),
            ('SPAN', (4, 0), (4, 1)),
            ('SPAN', (5, 0), (5, 1)),
            ('SPAN', (6, 0), (6, 1)),
            ('SPAN', (7, 0), (9, 0)),
            ('SPAN', (10, 0), (10, 1)),

        ]
    ))
    Elementos.append(Tabla1)

    nrows = len(data)

    p=1
    contador_lineas=0
    n_hoja=1
    #if nrows > p:
    #    contador_lineas = 1
    for count,x in enumerate(data,1):
        registros = [
                    [Paragraph(e, h3) for e in
                    [u'{}'.format(count),
                     u'{}'.format(x['UBIGEO']),
                     u'{}'.format(x['DEPARTAMENTO']),
                     u'{}'.format(x['PROVINCIA']),
                     u'{}'.format(x['DISTRITO']) ,
                     u'{}'.format(x['CODCCPP']),
                     u'{}'.format(x['NOMCCPP']),
                     u'{}'.format(x['Z_AE']),
                     u'{}'.format(x['ZONA']),
                     u'{}'.format(x['MZ']),
                     u'{}'.format(x['CANT_EST'])
                     ]]
        ]
        Tabla2 = Table(registros, colWidths=columnas)
        Tabla2.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER')
                    ]))
        Elementos.append(Tabla2)


    Elementos.append(Spacer(0, 10))



    pdf = SimpleDocTemplate(output,pagesize=(29.7 * cm, 21 * cm),
                            rightMargin=65,
                            leftMargin=65,
                            topMargin=0.5 * cm,
                            bottomMargin=0.5 * cm,)

    #   GENERACION DEL PDF FISICO

    pdf.build(Elementos)
    return output


def ListadoDistrito(informacion,output):
    cab=informacion[0]
    data=informacion[1]
    resumen = informacion[2]

    ubigeo=cab[0]
    coddep=cab[1]
    departamento=cab[2]
    codprov=cab[3]
    provincia=cab[4]
    coddist = cab[5]
    distrito = cab[6]
    dist_ope=cab[7]


    cant_zonas=resumen[1]
    cant_secc = resumen[2]
    cant_aeus = resumen[3]
    cant_mzs=resumen[4]
    cant_viv = resumen[5]



    Plantilla = getSampleStyleSheet()

    h_codigo = PS(
        name='Codigo',
        fontSize=8,
        alignment=TA_RIGHT
    )

    h1 = PS(
        name='Heading1',
        fontSize=7,
        leading=8
    )

    h11 = PS(
        name='Heading1',
        fontSize=7,
        leading=8,
        alignment=TA_CENTER
    )

    h111 = PS(
        name='Heading1',
        fontSize=7,
        leading=8,
        alignment=TA_RIGHT
    )

    h3 = PS(
        name='Normal',
        fontSize=6.5,
        leading=10,
        alignment=TA_CENTER
    )

    h4 = PS(
        name='Normal',
        fontSize=7,
        leading=10,
        alignment=TA_LEFT
    )

    h_sub_tile = PS(
        name='Heading1',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER
    )
    h_sub_tile_2 = PS(
        name='Heading1',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER
    )

    #   LISTA QUE CONTIENE LOS ELEMENTOS A GRAFICAR EN EL PDF

    Elementos = []

    #   AGREGANDO IMAGENES, TITULOS Y SUBTITULOS
    print ubigeo

    barcode = code128.Code128(u'{}'.format(ubigeo))


    Titulo = Paragraph(u'CENSOS NACIONALES 2017: XII DE POBLACIÓN, VII DE VIVIENDA Y III DE COMUNIDADES INDÍGENAS <br/> III Censo de Comunidades Nativas y I Censo de Comunidades Campesinas',
                       h_sub_tile)
    SubTitulo = Paragraph(u'<strong>MARCO DE ZONAS, SECCIONES  CENSALES, ÁREAS DE EMPADRONAMIENTO URBANO, MANZANAS Y VIVIENDAS DEL DISTRITO/DISTRITO OPERATIVO </strong>',h_sub_tile_2)

    CabeceraPrincipal = [
                        [barcode,'',''],
                        [Image(EscudoNacional, width=50, height=50), Titulo, Image(LogoInei, width=55, height=50)],
                         ['', SubTitulo, '']

    ]


    Tabla0 = Table(CabeceraPrincipal, colWidths=[2 * cm, 14 * cm, 2 * cm]    )

    Tabla0.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ALIGN', (0, 0), (2, 0), 'RIGHT'),
        ('SPAN', (0, 0), (2, 0)),
        ('SPAN', (0, 1), (0, 2)),
        ('SPAN', (2, 1), (2, 2)),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE')

    ]))




    Elementos.append(Tabla0)
    Elementos.append(Spacer(0, 10))

    #   CREACION DE LAS TABLAS PARA LA ORGANIZACION DEL TEXTO
    #   Se debe cargar la informacion en aquellos espacios donde se encuentra el texto 'R'

    Filas = [
        [Paragraph(u'<b>Doc.CPV.03.159</b>', h111),'','' ,'',''],
        [Paragraph(u'<b>A. UBICACIÓN GEOGRÁFICA</b>', h11), '', '','',''],
        [Paragraph(u'<b>DEPARTAMENTO</b>', h1), u'{}'.format(coddep), u'{}'.format(departamento),'',''],

        [Paragraph(u'<b>PROVINCIA</b>', h1), u'{}'.format(codprov), u'{}'.format(provincia),'',''],
        [Paragraph(u'<b>DISTRITO</b>', h1), u'{}'.format(coddist), u'{}'.format(distrito),Paragraph(u'<b>DISTRITO OPERATIVO CENSAL</b>', h1), u'{}'.format(dist_ope)],
    ]


    #   Permite el ajuste del ancho de la tabla

    Tabla = Table(Filas, colWidths=[3.6 * cm, 1 * cm, 4.5 * cm,5.2 * cm,4.5 * cm],
                  rowHeights=[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm])

    Tabla.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (2, 0), colors.black),
        ('ALIGN', (0, 0), (4, 0), 'RIGHT'),
        ('ALIGN', (1, 2), (1, 4), 'CENTER'),
        ('VALIGN', (0, 0), (4, 4), 'MIDDLE'),
        ('GRID', (0, 1), (4, 4), 1, colors.black),

        ('SPAN', (0, 0), (4, 0)),

        ('SPAN', (0, 1), (4, 1)),


        ('SPAN', (2, 2), (4, 2)),
        ('SPAN', (2, 3), (4, 3)),

        ('FONTSIZE', (1, 1), (4, 4), 8),
        ('BACKGROUND', (0, 1), (0, 4), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (0, 1), (4, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (3, 4), (3,4), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),

    ]))



    Elementos.append(Tabla)
    Elementos.append(Spacer(0, 10))

    CabeceraSecundaria = [
        [Paragraph(e, h3) for e in [u"<strong> B. INFORMACIÓN DE LA ZONA CENSAL</strong>", "", "","","","",""]],
        [Paragraph(e, h3) for e in [u"<strong>NOMBRE DEL CENTRO POBLADO</strong>",u"<strong>ZONA Nº</strong>",u"<strong>SUBZONA Nº</strong>",u"<strong>SECCIÓN Nº</strong>",u"<strong>A.E.U. Nº</strong>", u"<strong>MANZANA Nº</strong>",u"<strong>Nº DE VIVIENDAS </strong>"]],
        [Paragraph(e, h3) for e in [u"<strong>(1)</strong>", u"<strong>(2)</strong>", u"<strong>(3)</strong>",u"<strong>(4)</strong>",u"<strong>(5)</strong>",u"<strong>(6)</strong>",u"<strong>(7)</strong>"]],
    ]

    Tabla1 = Table(CabeceraSecundaria, colWidths=[5*cm,1.8*cm,1.8*cm, 1.8*cm, 1.8*cm,4.8*cm,1.8*cm], rowHeights=[0.5 * cm,1 * cm,0.5 * cm])

    Tabla1.setStyle(TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
            ('SPAN', (0, 0), (6, 0))

        ]
    ))

    Elementos.append(Tabla1)
    nrows = len(data)
    #   CUERPO QUE CONTIENE LOS LA INFORMACION A MOSTRAR


    if nrows > 38:

        ##### funcion contar_registros(cantidad_total_registros, cantidad_registros_pagina inicial,cantidad_registros_paginas_siguientes)
        HojaRegistros = contar_registros(nrows, 38, 52)
        HojaRegistros.append((0, 38))
        HojaRegistros.sort(key=lambda n: n[0])


        for rangos in HojaRegistros:
            for aeu in ([ (x[0],x[1],x[2],x[3],x[4],x[5],x[6])  for x in data])[rangos[0]:rangos[1]]:
                nomccpp=aeu[0]
                zona=aeu[1]
                subzona=aeu[2]
                seccion=aeu[3]
                aeus = aeu[4]
                manzanas = aeu[5]
                viviendas_aeu = aeu[6]

                Registros = [
                    [u'{}'.format(nomccpp),u'{}'.format(zona),u'{}'.format(subzona),u'{}'.format(seccion),u'{}'.format(aeus), u'{}'.format(manzanas), u'{}'.format(viviendas_aeu)]
                ]

                Tabla2 = Table(Registros, colWidths=[5*cm,1.8*cm,1.8*cm, 1.8*cm, 1.8*cm,4.8*cm,1.8*cm], rowHeights=[0.5 * cm])

                Tabla2.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER')
                ]))
                Elementos.append(Tabla2)

            Elementos.append(PageBreak())

            Elementos.append(Tabla1)
        cant_reg_ult_pag=HojaRegistros[-1][1]-HojaRegistros[-1][0]
        del Elementos[-1]
        if cant_reg_ult_pag<49:
            del Elementos[-1]
    else:
        for aeu in ([(x[0],x[1],x[2],x[3],x[4],x[5],x[6]) for x in data]):
            nomccpp=aeu[0]
            zona = aeu[1]
            subzona = aeu[2]
            seccion = aeu[3]
            aeus = aeu[4]
            manzanas = aeu[5]
            viviendas_aeu = aeu[6]
            Registros = [[u'{}'.format(nomccpp),u'{}'.format(zona), u'{}'.format(subzona), u'{}'.format(seccion), u'{}'.format(aeus),u'{}'.format(manzanas), u'{}'.format(viviendas_aeu)]]

            Tabla2 = Table(Registros, colWidths=[5*cm,1.8*cm,1.8*cm, 1.8*cm, 1.8*cm,4.8*cm,1.8*cm], rowHeights=[0.5 * cm])

            Tabla2.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER')
            ]))


            Elementos.append(Tabla2)
        if (nrows > 34):
            Elementos.append(PageBreak())

    Elementos.append(Spacer(0, 10))

    FilasPiePagina = [
                     [Paragraph(u'{}'.format(u"<strong>C. RESUMEN DEL DISTRITO</strong>"),h3),''],
                     [Paragraph(u'{}'.format(u"<strong>TOTAL DE ZONAS / SUBZONAS</strong>"), h1), u'{}'.format(cant_zonas)],
                     [Paragraph(u'{}'.format(u"<strong>TOTAL DE SECCIONES</strong>"),h1),u'{}'.format(cant_secc)],
                     [Paragraph(u'{}'.format(u"<strong>TOTAL DE AEUS</strong>"),h1), u'{}'.format(cant_aeus)],
                     [Paragraph(u'{}'.format(u"<strong>TOTAL DE MANZANAS</strong>"), h1), u'{}'.format(cant_mzs)],
                     [Paragraph(u'{}'.format(u"<strong>TOTAL DE VIVIENDAS</strong>"), h1), u'{}'.format(cant_viv)]
                    ]

    Tabla_Pie = Table(FilasPiePagina, colWidths=[6*cm,3.4 * cm], rowHeights=6*[0.5 * cm])

    Tabla_Pie.setStyle(TableStyle([
            ('GRID', (0, 0), (1, 5), 1, colors.black),
            ('ALIGN', (0, 1), (0, 5), 'LEFT'),
            ('ALIGN', (1, 1), (1, 5), 'RIGHT'),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('SPAN', (0, 0), (1,0)),
            ('BACKGROUND', (0, 0), (0, 5), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
            ('BACKGROUND', (0, 0), (1, 0), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),

           #('BACKGROUND', (0, 0), (0, 4), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           #('BACKGROUND', (0, 0), (1, 0), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),

        ]))

    Elementos.append(Tabla_Pie)


    # SE DETERMINAN LAS CARACTERISTICAS DEL PDF (RUTA DE ALMACENAJE, TAMAÑO DE LA HOJA, ETC)

    pdf = SimpleDocTemplate(output, pagesize=A4,
                            rightMargin=65,
                            leftMargin=65,
                            topMargin=0.5 * cm,
                            bottomMargin=0.5 * cm,)

    #   GENERACION DEL PDF FISICO

    pdf.build(Elementos)


def ListadoViviendasDesocupadas(SECCION_fc,VIV_fc,output):
    coddep = SECCION_fc[0]
    departamento = SECCION_fc[1]
    codprov = SECCION_fc[2]
    provincia = SECCION_fc[3]
    coddist = SECCION_fc[4]
    distrito = SECCION_fc[5]
    #codccpp = SECCION_fc[6]
    #nomccpp = SECCION_fc[7]
    #catccpp = SECCION_fc[8]
    zona = SECCION_fc[9]
    seccion = SECCION_fc[10]
    #aeuini = SECCION_fc[11]
    #aeufin = SECCION_fc[12]
    #viviendas = SECCION_fc[13]

    #   CREACION DE PLANTILLA

    Plantilla = getSampleStyleSheet()


    #   CREADO ESTILOS DE TEXTO

    h1 = PS(
        name = 'Heading1',
        fontSize = 7,
        leading = 8
        )

    h11 = PS(
        name = 'Heading1',
        fontSize = 7,
        leading = 8,
        alignment = TA_CENTER
        )
    h3 = PS(
        name = 'Normal',
        fontSize = 6.5,
        leading = 10,
        alignment = TA_CENTER
        )

    h4 = PS(
        name = 'Normal',
        fontSize = 7,
        leading = 10,
        alignment = TA_LEFT
        )
    h5 = PS(
        name='Normal',
        fontSize=12,
        leading=10,
        alignment=TA_CENTER
    )

    h_sub_tile = PS(
        name = 'Heading1',
        fontSize = 10,
        leading = 14,
        alignment = TA_CENTER
        )
    h_sub_tile_2 = PS(
        name = 'Heading1',
        fontSize = 11,
        leading = 14,
        alignment = TA_CENTER
        )


    #   LISTA QUE CONTIENE LOS ELEMENTOS A GRAFICAR EN EL PDF

    Elementos = []


    #   AGREGANDO IMAGENES, TITULOS Y SUBTITULOS



    Titulo = Paragraph(u'CENSOS NACIONALES 2017: XII DE POBLACIÓN, VII DE VIVIENDA<br/>Y III DE COMUNIDADES INDÍGENAS',h_sub_tile)
    SubTitulo = Paragraph(u'<strong>LISTADO DE VIVIENDAS DESOCUPADAS</strong>', h_sub_tile_2)

    CabeceraPrincipal = [[Image(EscudoNacional, width=50, height=50), Titulo, Image(LogoInei, width=55, height=50)],
                         ['', SubTitulo, '']]

    Tabla0 = Table(CabeceraPrincipal, colWidths = [2 * cm, 14 * cm, 2 * cm])

    Tabla0.setStyle( TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

        ]))

    Elementos.append(Tabla0)
    Elementos.append(Spacer(0,10))


    #   CREACION DE LAS TABLAS PARA LA ORGANIZACION DEL TEXTO
    #   Se debe cargar la informacion en aquellos espacios donde se encuentra el texto 'R'

    Filas = [
        ['', '', '', '', '', Paragraph('<b>Doc. CPV</b>', h1)],
        [Paragraph(u'<b>A. UBICACIÓN GEOGRÁFICA</b>', h1), '', '', '', Paragraph(u'<b>B. UBICACIÓN CENSAL</b>', h1), ''],
        [Paragraph(u'<b>DEPARTAMENTO</b>', h1), u'{}'.format(coddep), u'{}'.format(departamento), '', Paragraph(u'<b>ZONA Nº</b>', h1),u'{}'.format(zona)],
        [Paragraph(u'<b>PROVINCIA</b>', h1), u'{}'.format(codprov), u'{}'.format(provincia), '', Paragraph(u'<b>SECCIÓN Nº</b>', h1), u'{}'.format(seccion )],
        [Paragraph(u'<b>DISTRITO</b>', h1), u'{}'.format(coddist), u'{}'.format(distrito), '', '', ''],
        #[Paragraph(u'<b>CENTRO POBLADO</b>', h1), u'{}'.format(codccpp), u'{}'.format(nomccpp), '', '', ''],
        #[Paragraph(u'<b>CATEGORÍA DEL CENTRO POBLADO</b>', h1), u'{}'.format(catccpp), '', '', Paragraph(u'<b>TOTAL DE VIVIENDAS<br/>DEL A.E.U.</b>', h1),'{}'.format(viviendas)]
        ]
    #   Permite el ajuste del ancho de la tabla

    Tabla = Table(Filas, colWidths=[3.7 * cm, 1 * cm, 8.1 * cm, 0.3 * cm, 4.7 * cm, 2 * cm],
                           rowHeights=[0.4 * cm, 0.4  * cm, 0.4  * cm, 0.4  * cm, 0.4  * cm ])

    #   Se cargan los estilos, como bordes, alineaciones, fondos, etc

    Tabla.setStyle(TableStyle([
                ('TEXTCOLOR', (0, 0), (5, 0), colors.black),
                ('ALIGN', (4, 0), (5, 0), 'RIGHT'),
                ('ALIGN', (1, 2), (1, 4), 'CENTER'),
                ('ALIGN', (5, 2), (5, 4), 'CENTER'),
                ('VALIGN', (0, 0), (5,4 ), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (5, 4), 8),
                ('GRID', (0, 1), (2, 4), 1, colors.black),
                ('GRID', (4, 1), (5, 4), 1, colors.black),
                ('SPAN', (0, 1), (2, 1)),
                ('SPAN', (4, 1), (5, 1)),

                ('BACKGROUND', (0, 1), (0, 4), colors.Color(220.0/255,220.0/255,220.0/255)),
                ('BACKGROUND', (0, 1), (2, 1), colors.Color(220.0/255,220.0/255,220.0/255)),
                ('BACKGROUND', (4, 1), (5, 1), colors.Color(220.0/255,220.0/255,220.0/255)),
                ('BACKGROUND', (4, 1), (4, 4), colors.Color(220.0/255,220.0/255,220.0/255)),

                #('BACKGROUND', (0, 1), (0, 4), colors.Color(220.0/255,220.0/255,220.0/255)),
                #('BACKGROUND', (0, 1), (2, 1), colors.Color(220.0/255,220.0/255,220.0/255)),
                #('BACKGROUND', (4, 1), (5, 1), colors.Color(220.0/255,220.0/255,220.0/255)),
                #('BACKGROUND', (4, 1), (4, 4), colors.Color(220.0/255,220.0/255,220.0/255)),

            ]))


    #   AGREGANDO LAS TABLAS A LA LISTA DE ELEMENTOS DEL PDF

    Elementos.append(Tabla)
    Elementos.append(Spacer(0,10))

    #   AGREGANDO CABECERA N 2

    Filas2 = [
        [Paragraph(e, h3) for e in [u"<strong>Mz Nº</strong>", u"<strong>Frent N°</strong>", u"<strong>AEU</strong>", u"<strong>Ord Reg</strong>", u"<strong>DIRECCIÓN DE LA VIVIENDA</strong>", "", "", "", "", "", "", "", "", u"<strong>CONDICIÓN</strong>"]],
        [Paragraph(e, h3) for e in ["", "", "", "", u"<strong>Tipo de Vía</strong>", u"<strong>Nombre de Vía</strong>", u"<strong>Nº de Puerta</strong>", u"<strong>Block</strong>", u"<strong>Mz Nº</strong>", u"<strong>Lote Nº</strong>", u"<strong>Piso Nº</strong>", u"<strong>Int. Nº</strong>", u"<strong>Km. Nº</strong>", ""]],
        [Paragraph(e, h3) for e in [u"<strong>(1)</strong>", u"<strong>(2)</strong>", u"<strong>(3)</strong>", u"<strong>(4)</strong>", u"<strong>(5)</strong>", "<strong>(6)</strong>", u"<strong>(7)</strong>", u"<strong>(8)</strong>", u"<strong>(9)</strong>", u"<strong>(10)</strong>", u"<strong>(11)</strong>", u"<strong>(12)</strong>", u"<strong>(13)</strong>", u"<strong>(14)</strong>"]]
         ]

    Tabla2 = Table(Filas2, colWidths = [0.8 * cm, 0.8 * cm, 0.90 * cm, 1 * cm, 1.2 * cm, 4.6 * cm, 1.2 * cm, 1.1 * cm, 0.8 * cm, 1 * cm, 1 * cm, 0.9 * cm, 0.9 * cm, 3.6 * cm])

    Tabla2.setStyle(TableStyle([
                    ('GRID', (1, 1), (-2, -2), 1, colors.black),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                    ('BACKGROUND', (0, 0), (-1, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                    #('BACKGROUND', (0, 0), (-1, 0), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                    #('BACKGROUND', (0, 0), (-1, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                    ('SPAN', (4, 0), (12, 0)),
                    ('SPAN', (0, 0), (0, 1)),
                    ('SPAN', (1, 0), (1, 1)),
                    ('SPAN', (2, 0), (2, 1)),
                    ('SPAN', (3, 0), (3, 1)),
                    ('SPAN', (13, 0), (13, 1)),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                    ('BACKGROUND', (0, 0), (13, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                    #('BACKGROUND', (0, 0), (13, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                    ]))



    Elementos.append(Tabla2)

    #ListFields = [field.name for field in arcpy.ListFields(VIV_fc)]
    ListFields = [ "MANZANA", "FRENTE_ORD","AEU" , "ID_REG_OR","P20", "P21", "P22_A", "P22_B", "P23", "P24","P25", "P26", "P27_A", "P28", "P30"]



    nrows = len([x[0] for x in arcpy.da.SearchCursor(VIV_fc, ["AEU"])])

    print nrows

    if nrows > 20:
        HojaRegistros = contar_registros(nrows,20,26)
        HojaRegistros.append((0, 20))
        HojaRegistros.sort(key = lambda n:n[0])

        for rangos in HojaRegistros:

            for viv in ([x for x in arcpy.da.SearchCursor(VIV_fc, ListFields)])[rangos[0]:rangos[1]]:

                vivn = "" if str(viv[0])=="0" else str(viv[0])
                mzinei = viv[1]
                idregord = viv[2]
                frente = viv[3]
                tvia = viv[4]
                nomvia = "{}{}".format(viv[5][0:24], "..") if len(viv[5]) > 26 else viv[5]
                npuerta = viv[6]
                block = viv[8]
                mzmuni = viv[9]
                lote = viv[10]
                piso = viv[11]
                interior = viv[12]
                kmn = viv[13]
                if int(viv[14]) == 3:
                    condicion = u"En alquiler o venta"
                if int(viv[14]) == 4:
                    condicion = u"En construcción o reparación"
                if int(viv[14]) == 5:
                    condicion = u"Abandonada o cerrada"
                if int(viv[14]) == 6:
                    condicion = u"Otra causa"

                registros = [[vivn, mzinei, idregord, frente, tvia, Paragraph(u'{}'.format(nomvia), h4), npuerta, block, mzmuni, lote, piso, interior, kmn, Paragraph(u'{}'.format(condicion), h4)]]

                RegistrosIngresados = Table(registros,
                          colWidths = [0.8 * cm, 0.8 * cm, 0.90 * cm, 1 * cm, 1.2 * cm, 4.6 * cm, 1.2 * cm, 1.1 * cm, 0.8 * cm, 1 * cm, 1 * cm, 0.9 * cm, 0.9 * cm, 3.6 * cm],
                          rowHeights=[1 * cm])

                RegistrosIngresados.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 7),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (4, 0), 'CENTER'),
                        ('ALIGN', (6, 0), (12, 0), 'CENTER')
                        ]))

                Elementos.append(RegistrosIngresados)
            Elementos.append(PageBreak())
            Elementos.append(Tabla2)

        del Elementos[-1]
        del Elementos[-1]
    else:
        for viv in (
        [x for x in arcpy.da.SearchCursor(VIV_fc, ListFields)]):
        #for viv in ([x for x in arcpy.da.SearchCursor(VIV_fc, ListFields, "LLAVE_AEU = '{}'".format(identificador))]):
            vivn = "" if str(viv[0])=="0" else str(viv[0])
            mzinei = viv[1]
            idregord = viv[2]
            frente = viv[3]
            tvia = viv[4]
            nomvia = "{}{}".format(viv[5][0:24], "..") if len(viv[5]) > 26 else viv[5]
            npuerta = viv[6]
            block = viv[8]
            mzmuni = viv[9]
            lote = viv[10]
            piso = viv[11]
            interior = viv[12]
            kmn = viv[13]

            if int(viv[14])==3:
                condicion = u"En alquiler o venta"
            if int(viv[14])==4:
                condicion = u"En construcción o reparación"
            if int(viv[14])==5:
                condicion = u"Abandonada o cerrada"
            if int(viv[14])==6:
                condicion = u"Otra causa"


            registros = [[vivn, mzinei, idregord, frente, tvia, Paragraph(u'{}'.format(nomvia), h4), npuerta, block, mzmuni, lote, piso, interior, kmn, Paragraph(u'{}'.format(condicion), h4)]]
            RegistrosIngresados = Table(registros,
                      colWidths = [0.8 * cm, 0.8 * cm, 0.90 * cm, 1 * cm, 1.2 * cm, 4.6 * cm, 1.2 * cm, 1.1 * cm, 0.8 * cm, 1 * cm, 1 * cm, 0.9 * cm, 0.9 * cm, 3.6 * cm],
                      rowHeights=[1 * cm])
            RegistrosIngresados.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (4, 0), 'CENTER'),
                    ('ALIGN', (6, 0), (12, 0), 'CENTER')
                    ]))
            Elementos.append(RegistrosIngresados)
        if (nrows > 17):
            Elementos.append(PageBreak())


    #   SE DETERMINAN LAS CARACTERISTICAS DEL PDF (RUTA DE ALMACENAJE, TAMANIO DE LA HOJA, ETC)

    #destino = "\\\srv-fileserver\\CPV2017\\list_segm_tab_2\\urbano\\{}\\{}\\{}{}{}{}.pdf".format(aeu[0],zona_cod,aeu[0],zona_cod,seccion,aeus)
    destino=output
    pdf = SimpleDocTemplate(destino, pagesize=A4,
        rightMargin=65,
        leftMargin=65,
        topMargin=0.5 * cm,
        bottomMargin=0.5 * cm, )

    pdf.build(Elementos)

    print "Finalizado"


def ListadoDeEstudiantes(informacion, output):
    cab=informacion[0]
    data=informacion[1]
    coddep=cab[0]
    departamento=cab[1]
    codprov=cab[2]
    provincia=cab[3]
    coddist = cab[4]
    distrito = cab[5]
    codccpp = cab[6]
    nomccpp = cab[7]
    zona = cab[8]
    subzona=cab[9]

    if subzona=='0' or subzona==0 :
        subzona=''
    else:
        subzona = '-{}'.format(subzona)


    Plantilla = getSampleStyleSheet()

    h1 = PS(
        name='Heading1',
        fontSize=7,
        leading=8
    )

    h11 = PS(
        name='Heading1',
        fontSize=7,
        leading=8,
        alignment=TA_CENTER
    )
    h111 = PS(
        name='Heading1',
        fontSize=7,
        leading=8,
        alignment=TA_RIGHT
    )

    h3 = PS(
        name='Normal',
        fontSize=6.5,
        leading=10,
        alignment=TA_CENTER
    )

    h4 = PS(
        name='Normal',
        fontSize=7,
        leading=10,
        alignment=TA_LEFT
    )
    h5 = PS(
        name='Normal',
        fontSize=10,
        leading=10,
        alignment=TA_CENTER
    )

    h_sub_tile = PS(
        name='Heading1',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER
    )
    h_sub_tile_2 = PS(
        name='Heading1',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER
    )


    Elementos = []





    Titulo = Paragraph(u'CENSOS NACIONALES 2017: XII DE POBLACIÓN, VII DE VIVIENDA Y III DE COMUNIDADES INDÍGENAS<br/>III CENSO DE COMUNIDADES NATIVAS  Y I CENSO DE COMUNIDADES CAMPESINAS',h_sub_tile)
    SubTitulo = Paragraph(u'<strong>DIRECTORIO DE VIVIENDAS CON ESTUDIANTES Y EMPLEADOS PÚBLICOS</strong>', h_sub_tile_2)

    CabeceraPrincipal = [[Image(EscudoNacional, width=50, height=50), Titulo, Image(LogoInei, width=55, height=50)],
                         ['', SubTitulo, '']]

    Tabla0 = Table(CabeceraPrincipal, colWidths=[2 * cm, 24 * cm, 2 * cm])

    Tabla0.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

    ]))

    Elementos.append(Tabla0)
    Elementos.append(Spacer(0, 10))

    Filas = [
        ['', '', '', '', Paragraph('<b>Doc.CPV.03.300</b>', h111), ''],
        [Paragraph(u'<b>A. UBICACIÓN GEOGRÁFICA</b>', h11), '', '', '', Paragraph(u'<b>B. UBICACIÓN CENSAL</b>', h11),''],
        [Paragraph(u'<b>DEPARTAMENTO</b>', h1), u'{}'.format(coddep), u'{}'.format(departamento), '',Paragraph(u'<b>ZONA CENSAL Nº</b>', h1), u'{}{}'.format(zona,subzona)],
        [Paragraph(u'<b>PROVINCIA</b>', h1), u'{}'.format(codprov), u'{}'.format(provincia), '','', ''],
        #Paragraph(u'<b>PROVINCIA</b>', h1), u'{}'.format(codprov), u'{}'.format(provincia), '', Paragraph(u'<b>SUBZONA</b>', h1), u'{}'.format(subzona)],
        [Paragraph(u'<b>DISTRITO</b>', h1), u'{}'.format(coddist), u'{}'.format(distrito), '','', ''],
        [Paragraph(u'<b>CENTRO POBLADO</b>', h1), u'{}'.format(codccpp), u'{}'.format(nomccpp), '', '', ''],

    ]






    Tabla = Table(Filas, colWidths=[5 * cm, 2 * cm, 12 * cm, 1 * cm, 5 * cm, 3 * cm],
                  rowHeights=[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm])

    Tabla.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (5, 0), colors.black),
        ('ALIGN', (4, 0), (5, 0), 'RIGHT'),
        ('ALIGN', (1, 2), (1, 5), 'CENTER'),
        ('ALIGN', (5, 2), (5, 5), 'CENTER'),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 1), (2, 5), 1, colors.black),
        ('GRID', (4, 1), (5, 2), 1, colors.black),

        ('SPAN', (4, 0), (5, 0)),
        ('SPAN', (0, 1), (2, 1)),
        ('SPAN', (4, 1), (5, 1)),


        ('BACKGROUND', (0, 1), (0, 5), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (0, 1), (2, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (4, 1), (5, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (4, 2), (4, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),

    ]))

    #   AGREGANDO LAS TABLAS A LA LISTA DE ELEMENTOS DEL PDF

    Elementos.append(Tabla)
    Elementos.append(Spacer(0, 10))

    #   AGREGANDO CABECERA N 2

    Filas2 = [
        [Paragraph(e, h3) for e in [u"<strong>Nº ORDEN</strong>",u"<strong>SECC. CENSAL Nº</strong>" ,u"<strong>MZ CENSAL Nº</strong>", u"<strong>FRENTE Nº</strong>",
                                    u"<strong>DIRECCIÓN DE LA VIVIENDA</strong>", "", "", "", "", "", "","",
                                    u"<strong>APELLIDOS Y NOMBRES DEL/DE LA<br/>JEFE/A DEL HOGAR</strong>",u"<strong>TOTAL DE PERSONAS QUE:</strong>","",""]],

        [Paragraph(e, h3) for e in ["", "", "", "",u"<strong>Tipo de Vía</strong>", u"<strong>Nombre de Vía</strong>",
                                    u"<strong>Nº de Puerta</strong>", u"<strong>Block</strong>",
                                    u"<strong>Mz Nº</strong>", u"<strong>Lote Nº</strong>", u"<strong>Piso Nº</strong>",
                                    u"<strong>Int. Nº</strong>", "",

                                    #u"<strong>TRABAJAN EN EL SECTOR PÚBLICO</strong>", u"<strong>ESTUDIAN EN LA  UNIVERSIDAD  O INSTITUTO SUPERIOR</strong>",u"<strong>TRABAJAN Y ESTUDIAN EN LA   UNIVERSIDAD  O INSTITUTO SUPERIOR</strong>", u"<strong>ESTUDIANTES DEL 5TO DE SECUNDARIA</strong>"
                                    u"<strong>TRABAJAN EN EL SECTOR PÚBLICO</strong>",
                                    u"<strong>ESTUDIAN EN LA  UNIVERSIDAD  O INSTITUTO SUPERIOR</strong>",
                                    #u"<strong>TRABAJAN Y ESTUDIAN EN LA   UNIVERSIDAD  O INSTITUTO SUPERIOR</strong>",
                                    u"<strong>Egresados de Sec./Estudiantes de 4TO Y 5TO. año  de Sec.</strong>"

                                    ]],
        [Paragraph(e, h3) for e in
         [u"<strong>(1)</strong>", u"<strong>(2)</strong>", u"<strong>(3)</strong>", u"<strong>(4)</strong>",
          u"<strong>(5)</strong>", u"<strong>(6)</strong>", u"<strong>(7)</strong>", u"<strong>(8)</strong>",
          u"<strong>(9)</strong>", u"<strong>(10)</strong>", u"<strong>(11)</strong>", u"<strong>(12)</strong>",
          u"<strong>(13)</strong>",u"<strong>(14)</strong>",u"<strong>(15)</strong>",u"<strong>(16)</strong>"
          #   ,u"<strong>(17)</strong>"

          ]]
    ]

    #Tabla2 = Table(Filas2,colWidths=[1.5*cm,1.25*cm,1.25*cm,1.25*cm,1.25*cm,3.5*cm,1.5 * cm, 1 * cm, 1 * cm, 1 * cm,1*cm, 1*cm, 5* cm,1.75*cm,1.75*cm,1.75*cm,1.75*cm])
    Tabla2 = Table(Filas2,
                   colWidths=[1.5 * cm, 1.30 * cm, 1.30 * cm, 1.30 * cm, 1.25 * cm, 3.5 * cm, 1.5 * cm, 1 * cm, 1 * cm,
                              1 * cm, 1 * cm, 1 * cm, 5 * cm, 2.28 * cm, 2.28 * cm, 2.29 * cm])

    Tabla2.setStyle(TableStyle([

        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (0, 0), (-1, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('SPAN', (3, 0), (3, 1)),
        ('SPAN', (4, 0), (11, 0)),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (12, 0), (12, 1)),
        ('SPAN', (13, 0), (15, 0)),
        #('SPAN', (13, 0), (16, 0)),
    ]))

    Elementos.append(Tabla2)

    nrows = len(data)


    if nrows > 15:
       HojaRegistros = contar_registros(nrows, 15, 20)
       HojaRegistros.append((0, 15))
       HojaRegistros.sort(key=lambda n: n[0])
       for rangos in HojaRegistros:
           for viv in (data)[rangos[0]:rangos[1]]:
               vivn=viv[0]
               seccion=viv[1]
               mzinei = viv[2]
               frente = viv[3]
               tvia = viv[4]
               nomvia = u"{}{}".format(viv[5][0:24], "..") if len(viv[5]) > 26 else viv[5]
               npuerta = viv[6]
               block = viv[7]
               mzmuni = viv[8]
               lote = viv[9]
               piso = viv[10]
               interior = viv[11]
               jefehogar = viv[12]
               trab_sec_pub =viv[13]
               est_uni=viv[14]

               est_5_secund = viv[15]
               registros = [
                   [vivn, seccion,mzinei, frente, tvia, Paragraph(u'{}'.format(nomvia), h4), npuerta, block, mzmuni, lote,
                    piso, interior, Paragraph(u'{}'.format(jefehogar), h4),trab_sec_pub,est_uni,est_5_secund ]]

               RegistrosIngresados = Table(registros,colWidths=[1.5 * cm, 1.30 * cm, 1.30 * cm, 1.30 * cm, 1.25 * cm, 3.5 * cm, 1.5 * cm, 1 * cm, 1 * cm,
                              1 * cm, 1 * cm, 1 * cm, 5 * cm, 2.28 * cm, 2.28 * cm, 2.29 * cm]



                                           )

               RegistrosIngresados.setStyle(TableStyle([
                   ('GRID', (0, 0), (-1, -1), 1, colors.black),
                   ('FONTSIZE', (0, 0), (-1, -1), 7),
                   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                   ('ALIGN', (0, 0), (4, 0), 'CENTER'),
                   ('ALIGN', (6, 0), (15, 0), 'CENTER')
               ]))

               Elementos.append(RegistrosIngresados)
           Elementos.append(PageBreak())
           Elementos.append(Tabla2)

       del Elementos[-1]
       del Elementos[-1]
    else:
       for viv in (data):
           vivn = viv[0]
           seccion = viv[1]
           mzinei = viv[2]
           frente = viv[3]
           tvia = viv[4]
           nomvia = u"{}{}".format(viv[5][0:24], "..") if len(viv[5]) > 26 else viv[5]
           npuerta = viv[6]
           block = viv[7]
           mzmuni = viv[8]
           lote = viv[9]
           piso = viv[10]
           interior = viv[11]
           jefehogar = viv[12]
           trab_sec_pub = viv[13]
           est_uni = viv[14]

           trabajan_o_estudian = ''
           est_5_secund = viv[15]

           registros = [
               [vivn, seccion, mzinei, frente, tvia, Paragraph(u'{}'.format(nomvia), h4), npuerta, block, mzmuni, lote,
                piso, interior, Paragraph(u'{}'.format(jefehogar), h4), trab_sec_pub, est_uni, est_5_secund]]

           RegistrosIngresados = Table(registros,
                                       colWidths=[1.5 * cm, 1.30 * cm, 1.30 * cm, 1.30 * cm, 1.25 * cm, 3.5 * cm,
                                                  1.5 * cm, 1 * cm, 1 * cm,
                                                  1 * cm, 1 * cm, 1 * cm, 5 * cm, 2.28 * cm, 2.28 * cm, 2.29 * cm]

                                       )

           RegistrosIngresados.setStyle(TableStyle([
               ('GRID', (0, 0), (-1, -1), 1, colors.black),
               ('FONTSIZE', (0, 0), (-1, -1), 7),
               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
               ('ALIGN', (0, 0), (4, 0), 'CENTER'),
               ('ALIGN', (6, 0), (15, 0), 'CENTER')
           ]))
           Elementos.append(RegistrosIngresados)

    Elementos.append(Spacer(0, 10))





    pdf = SimpleDocTemplate(output, pagesize=(29.7*cm, 21*cm),
                            rightMargin=20,
                            leftMargin=20,
                            topMargin=0.25 * cm,
                            bottomMargin=0.25 * cm, )


    pdf.build(Elementos)

    print "Finalizado"



def listado_emp_especial(informacion,nivel,tipo,output):
    cab = informacion[0]
    data = informacion[1]
    coddep = cab[0]
    departamento = cab[1]
    codprov = cab[2]
    provincia = cab[3]
    coddist = cab[4]
    distrito = cab[5]


    if nivel==2:
        codccpp = cab[6]
        nomccpp = cab[7]
        zona = cab[8]
        subzona=cab[9]
        viviendas=cab[11]

    Plantilla = getSampleStyleSheet()

    h1 = PS(
        name='Heading1',
        fontSize=7,
        leading=8
    )

    h11 = PS(
        name='Heading1',
        fontSize=7,
        leading=8,
        alignment=TA_CENTER
    )
    h111 = PS(
        name='Heading1',
        fontSize=7,
        leading=8,
        alignment=TA_RIGHT
    )

    h3 = PS(
        name='Normal',
        fontSize=6.5,
        leading=10,
        alignment=TA_CENTER
    )



    h4 = PS(
        name='Normal',
        fontSize=7,
        leading=10,
        alignment=TA_LEFT
    )
    h5 = PS(
        name='Normal',
        fontSize=5,
        leading=5,
        alignment=TA_CENTER
    )

    h_sub_tile = PS(
        name='Heading1',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER
    )
    h_sub_tile_2 = PS(
        name='Heading1',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER
    )

    Elementos = []

    Titulo = Paragraph(
        u'CENSOS NACIONALES 2017: XII DE POBLACIÓN, VII DE VIVIENDA Y III DE COMUNIDADES INDÍGENAS<br/>III CENSO DE COMUNIDADES NATIVAS  Y I CENSO DE COMUNIDADES CAMPESINAS',
        h_sub_tile)

    if tipo==1 and nivel==2:
        SubTitulo = Paragraph(u'<strong>LISTADO DE VIVIENDAS COLECTIVAS INSTITUCIONALES DE LA ZONA CENSAL</strong>',
                          h_sub_tile_2)
    elif tipo==2 and nivel==2:
        SubTitulo = Paragraph(u'<strong>LISTADO DE VIVIENDAS COLECTIVAS NO INSTITUCIONALES DE LA ZONA CENSAL</strong>',
                              h_sub_tile_2)
    elif tipo==1 and nivel==1:
        SubTitulo = Paragraph(u'<strong>LISTADO DISTRITAL DE VIVIENDAS COLECTIVAS INSTITUCIONALES</strong>',
                              h_sub_tile_2)

    elif tipo==2 and nivel==1:
        SubTitulo = Paragraph(u'<strong>LISTADO DISTRITAL DE VIVIENDAS COLECTIVAS NO INSTITUCIONALES</strong>',
                              h_sub_tile_2)


    CabeceraPrincipal = [[Image(EscudoNacional, width=50, height=50), Titulo, Image(LogoInei, width=55, height=50)],
                         ['', SubTitulo, '']]

    Tabla0 = Table(CabeceraPrincipal, colWidths=[2 * cm, 24 * cm, 2 * cm])

    Tabla0.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

    ]))

    Elementos.append(Tabla0)
    Elementos.append(Spacer(0, 10))




    if nivel==2:


        if tipo==1:
            etiq_documento = ['', '', '', '', Paragraph(u'<b>Doc.CPV.34.</b>', h111), '']
        else:
            etiq_documento = ['', '', '', '', Paragraph(u'<b>Doc.CPV.34A</b>', h111), '']

        el1=[Paragraph(u'<b>A. UBICACIÓN GEOGRÁFICA</b>', h11), '', '', '', Paragraph(u'<b>B. UBICACIÓN CENSAL</b>', h11),'','','']
        el2=[Paragraph(u'<b>DEPARTAMENTO</b>', h1), u'{}'.format(coddep), u'{}'.format(departamento), '',Paragraph(u'<b>ZONA CENSAL Nº</b>', h1), u'{}'.format(zona),Paragraph(u'<b>SUBZONA</b>', h1), u'{}'.format(subzona)]

    else:
        if tipo==1:
            etiq_documento = ['', '', '', '','','', Paragraph('<b>Doc.CPV.03.33</b>', h111), '']
        else:
            etiq_documento = ['', '', '', '','','', Paragraph('<b>Doc.CPV.03.33A</b>', h111), '']
        el1=[Paragraph(u'<b>A. UBICACIÓN GEOGRÁFICA</b>', h11), '', '', '', '','','','']
        el2 = [Paragraph(u'<b>DEPARTAMENTO</b>', h1), u'{}'.format(coddep), u'{}'.format(departamento), '','', '','','']






    Filas = [
        etiq_documento,el1,el2,
        [Paragraph(u'<b>PROVINCIA</b>', h1), u'{}'.format(codprov), u'{}'.format(provincia), '', '', '','',''],
        [Paragraph(u'<b>DISTRITO</b>', h1), u'{}'.format(coddist), u'{}'.format(distrito), '', '', '','',''],

    ]


    tam_filas=[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm]

    if nivel==2:
        tam_filas =[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm,0.4 * cm, 0.4 * cm]

    #if nivel==2:


        Filas.extend([

        [Paragraph(u'<b>CENTRO POBLADO</b>', h1), u'{}'.format(codccpp), u'{}'.format(nomccpp), '', '', '', '', ''],
        [Paragraph(u'<b>CATEGORÍA DEL CENTRO POBLADO</b>', h1), u'CIUDAD', '', '', Paragraph(u'<b>TOTAL DE VIVIENDAS COLECTIVAS DE LA ZONA</b>', h1), '', u'{}'.format(viviendas), '']

        ]

        )


    tam_columns=[5 * cm, 2 * cm, 10 * cm, 1 * cm, 5 * cm, 2 * cm,2*cm,1*cm]

    Tabla = Table(Filas, colWidths=tam_columns,
                  rowHeights=tam_filas
                  #rowHeights=[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm]

                  )

    list_estilos=[
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('SPAN', (-2, 0), (-1, 0)),

        ('ALIGN', (1, 2), (1, 4), 'CENTER'),
        ('ALIGN', (5, 2), (5, 4), 'CENTER'),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 1), (2, -1), 1, colors.black),


        ('SPAN', (0, 1), (2, 1)),


        ('BACKGROUND', (0, 1), (0, -1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (0, 1), (2, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),


    ]


    if nivel==2:
        list_estilos.extend(
         [
        ('GRID', (4, 1), (-1, 2), 1, colors.black),
        ('GRID', (4, -1), (-1, -1), 1, colors.black),


        ('BACKGROUND', (4, 1), (-1, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (4, 2), (4, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
         ('BACKGROUND', (6, 2), (6, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (4, -1), (4, -1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('SPAN', (4, 1), (-1, 1)),
        ('SPAN', (4,-1), (5, -1)),
        ('SPAN', (6, -1), (7, -1)),
        ('ALIGN', (4, 0), (5, 0), 'RIGHT'),
         ]
        )

    Tabla.setStyle(
    TableStyle(list_estilos)

    )





    Elementos.append(Tabla)
    Elementos.append(Spacer(0, 10))

    #################   AGREGANDO CABECERA A LA TABLA




    fila2= [Paragraph(e, h3) for e in
         [u"<strong>Nº ORDEN</strong>", u"<strong>MZ Nº</strong>",
          u"<strong>FRENTE Nº</strong>",
          u"<strong>DIRECCIÓN DE LA VIVIENDA COLECTIVA</strong>", "", "", "", "", "", "", "","",

          u"<strong>NOMBRE<br/> COMERCIAL/RAZÓN SOCIAL </strong>", u"<strong>Nº DE PERSONAS </strong>"]]

    fila3=[Paragraph(e, h5) for e in ["", "", "", u"<strong>CATEGORIA DE VIA</strong>", u"<strong>NOMBRE DE LA VIA</strong>",
                                    u"<strong>Nº PUERTA</strong>",u"<strong>Nº MZ</strong>", u"<strong>Nº LOTE</strong>",
                                    u"<strong>INTERIOR</strong>",
                                    u"<strong>BLOCK</strong>",
                                    u"<strong>Nº PISO</strong>",
                                    u"<strong>KM</strong>","",""
                                    ]]



    if nivel==1 :  ###distrital

        fila2.insert(1, Paragraph(u"<strong>ZONA Nº</strong>", h3))
        fila3.insert(1, "")
        fila1=[[Paragraph(e, h3) for e in [u"<strong>B.INFORMACIÓN DE LA VIVIENDA COLECTIVA INSTITUCIONAL</strong>"]]]

        for el in range(14):
            fila1.append("")



    else:   #####zonal


        fila1 = [[Paragraph(e, h3) for e in [u"<strong>C.INFORMACIÓN DE LA VIVIENDA COLECTIVA INSTITUCIONAL</strong>"]]]
        for el in range(13):
            fila1.append("")


    Filas2 = [ fila1,fila2,fila3,]


    if nivel==1:

        tam_columns = [0.975 * cm, 0.975 * cm, 0.975 * cm, 0.975 * cm, 1.25 * cm, 5 * cm, 1 * cm, 1 * cm, 1 * cm,
                       1 * cm,1 * cm, 1 * cm, 1 * cm, 8.85 * cm, 2 * cm]

    else:
        tam_columns = [1.30 * cm, 1.30 * cm, 1.30 * cm, 1.25 * cm, 5 * cm, 1 * cm, 1 * cm, 1 * cm, 1 * cm,
                       1 * cm, 1 * cm, 1 * cm, 8.85 * cm, 2 * cm]


    Tabla2 = Table(Filas2,
                   colWidths= tam_columns )

    list_span=[]

    if nivel==1:
        for i in range(4):
            list_span.append(('SPAN', (i, 1), (i, 2)))
        for i in range(13,15):
            list_span.append(('SPAN', (i, 1), (i, 2)))

        list_span.append(('SPAN', (4, 1), (12, 1)))
    else:
        for i in range(3):
            list_span.append(('SPAN', (i, 1), (i, 2)))
        for i in range(12, 14):
            list_span.append(('SPAN', (i, 1), (i, 2)))


        list_span.append(('SPAN', (3, 1), (11, 1)))

    estilo_cab_cuerpo_tabla=[
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (0, 0), (-1, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('BACKGROUND', (0, 0), (-1, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('SPAN', (0, 0), (-1, 0)),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]
    estilo_cab_cuerpo_tabla.extend(list_span)


    Tabla2.setStyle(TableStyle(estilo_cab_cuerpo_tabla))
    Elementos.append(Tabla2)
    nrows = len(data)

    #####################cuerpo tabla##############################



    estilo_cuerpo_tabla=[
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, -1), (0, -1), 'CENTER'),

        ]

    #if nivel==1:
    #    p=22
    #else:
    p = 20
    contador_lineas=0
    n_hoja=1
    if nrows > p:
       contador_lineas = 1
       for viv in data:
           vivn = viv[0]
           zona = viv[1]
           mzinei = viv[2]
           frente = viv[3]
           tvia = viv[4]
           nomvia = viv[5]
           #nomvia = u"{}{}".format(viv[5][0:24], "..") if len(viv[5]) > 26 else viv[5]
           npuerta = viv[6]
           block = viv[7]
           mzmuni = viv[8]
           lote = viv[9]
           piso = viv[10]
           interior = viv[11]
           km = viv[12]
           nom_estab = viv[13]
           nom_comercial = viv[14]
           n_personas = viv[15]

           registros = [
               [vivn, mzinei, frente, tvia, Paragraph(u'{}'.format(nomvia), h4), npuerta, mzmuni, lote,
                interior, block, piso, km,
                Paragraph(u'{}'.format(nom_comercial), h4), n_personas]]
           if nivel == 1:
               registros[0].insert(1, zona)

           RegistrosIngresados = Table(registros, colWidths=tam_columns)

           RegistrosIngresados.setStyle(estilo_cuerpo_tabla)

           tam_mzs=len(nom_comercial)
           lineas=tam_mzs/50.0
           cant_lineas=math.ceil(lineas)
           contador_lineas=cant_lineas+contador_lineas
           Elementos.append(RegistrosIngresados)

           if n_hoja==1:
               if contador_lineas>p:
                   n_hoja=n_hoja+1
                   Elementos.append(PageBreak())
                   Elementos.append(Tabla2)
                   contador_lineas=1
           else:
               if contador_lineas >28:
                   n_hoja = n_hoja + 1
                   Elementos.append(PageBreak())
                   Elementos.append(Tabla2)
                   contador_lineas = 1




    else:
       for viv in data:
           vivn = viv[0]
           zona = viv[1]
           mzinei = viv[2]
           frente = viv[3]
           tvia = viv[4]
           nomvia=viv[5]
           npuerta = viv[6]
           block = viv[7]
           mzmuni = viv[8]
           lote = viv[9]
           piso = viv[10]
           interior = viv[11]
           km = viv[12]
           nom_estab = viv[13]
           nom_comercial = viv[14]
           n_personas = viv[15]

           registros = [
               [vivn, mzinei, frente, tvia, Paragraph(u'{}'.format(nomvia), h4), npuerta, mzmuni, lote,
                interior, block, piso, km,
                Paragraph(u'{}'.format(nom_comercial), h4), n_personas]]
           if nivel == 1:
               registros[0].insert(1, zona)

           RegistrosIngresados = Table(registros, colWidths=tam_columns)

           RegistrosIngresados.setStyle(estilo_cuerpo_tabla)


           Elementos.append(RegistrosIngresados)
       if (nrows > p):
           Elementos.append(PageBreak())



    Elementos.append(Spacer(0, 10))

    pdf = SimpleDocTemplate(output, pagesize=(29.7 * cm, 21 * cm),
                            rightMargin=20,
                            leftMargin=20,
                            topMargin=0.25 * cm,
                            bottomMargin=0.25 * cm, )

    pdf.build(Elementos)

    print "Finalizado"




def listado_depart_prov(informacion,nivel,output):
    cab = informacion[0]
    data = informacion[1]

    if nivel == 1:
        dep = cab[0]
        subdep = cab[1]



    if nivel==2:
        dep = cab[0]
        prov = cab[1]
        subprov = cab[2]

    Plantilla = getSampleStyleSheet()

    h1 = PS(
        name='Heading1',
        fontSize=7,
        leading=8
    )

    h11 = PS(
        name='Heading1',
        fontSize=7,
        leading=8,
        alignment=TA_CENTER
    )
    h111 = PS(
        name='Heading1',
        fontSize=7,
        leading=8,
        alignment=TA_RIGHT
    )

    h3 = PS(
        name='Normal',
        fontSize=6,
        leading=10,
        alignment=TA_CENTER
    )

    h4 = PS(
        name='Normal',
        fontSize=6,
        leading=5,
        alignment=TA_LEFT
    )


    h5 = PS(
        name='Normal',
        fontSize=5,
        leading=10,
        alignment=TA_CENTER
    )

    h_sub_tile = PS(
        name='Heading1',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER
    )
    h_sub_tile_2 = PS(
        name='Heading1',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER
    )

    Elementos = []

    Titulo = Paragraph(
        u'CENSOS NACIONALES 2017: XII DE POBLACIÓN, VII DE VIVIENDA Y III DE COMUNIDADES INDÍGENAS<br/>III CENSO DE COMUNIDADES NATIVAS  Y I CENSO DE COMUNIDADES CAMPESINAS',
        h_sub_tile)

    if nivel==1:
        SubTitulo = Paragraph(u'<strong>NÚMERO DE ZONAS, SUBZONAS, SECCIONES CENSALES, ÁREAS DE EMPADRONAMIENTO URBANO, MANZANAS Y VIVIENDAS DEL DEPARTAMENTO </strong>',
                          h_sub_tile_2)

    else:
        SubTitulo = Paragraph(u'<strong> NÚMERO DE ZONAS, SUBZONAS, SECCIONES CENSALES, ÁREAS DE EMPADRONAMIENTO URBANO, MANZANAS Y VIVIENDAS DE LA PROVINCIA</strong>',
            h_sub_tile_2)

    CabeceraPrincipal = [[Image(EscudoNacional, width=50, height=50), Titulo, Image(LogoInei, width=55, height=50)],
                         ['', SubTitulo, '']]

    Tabla0 = Table(CabeceraPrincipal, colWidths=[2 * cm, 14 * cm, 2 * cm])

    Tabla0.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

    ]))

    Elementos.append(Tabla0)
    Elementos.append(Spacer(0, 10))


    if nivel==1:
        etiq_documento=['','', '',  Paragraph('<b>DOC.CPV.03.161</b>', h111)]
        el1=[Paragraph(u'<b> UBICACIÓN GEOGRÁFICA</b>', h11), '', '', '']
        #el2=[Paragraph(u'<b>DEPARTAMENTO</b>', h1), u'{}'.format(dep), Paragraph(u'<b>SUB DEPARTAMENTO</b>', h1), u'{}'.format(subdep)]
        el2 = [Paragraph(u'<b>DEPARTAMENTO</b>', h1), u'{}'.format(dep), '','']
        el3 = ['','','','']

    else:
        etiq_documento = ['','', '',  Paragraph('<b>DOC.CPV.03.160</b>', h111)]
        el1=[Paragraph(u'<b> UBICACIÓN GEOGRÁFICA</b>', h11), '', '', '']
        el2 = [Paragraph(u'<b>DEPARTAMENTO</b>', h1), u'{}'.format(dep),'','']
        #el3 = [Paragraph(u'<b>PROVINCIA</b>', h1), u'{}'.format(prov), Paragraph(u'<b>SUB PROVINCIA</b>', h1), u'{}'.format(subprov)]
        el3 = [Paragraph(u'<b>PROVINCIA</b>', h1), u'{}'.format(prov), '','']

    Filas = [etiq_documento, el1, el2,el3]



    Tabla = Table(Filas, colWidths=[4*cm,5*cm,4*cm,5*cm],
                  rowHeights=[0.4 * cm, 0.4 * cm, 0.4 * cm,0.4 * cm])


    list_estilos=[
        ('TEXTCOLOR', (0, 0), (3, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('SPAN', (0, 1), (-1, 1)),
        ('BACKGROUND', (0, 1), (-1, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),


    ]

    if nivel==1:
        list_estilos.extend(
            [
                ('GRID', (0, 1), (-1, 2), 1, colors.black),
                ('BACKGROUND', (0, 2), (0, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                #('BACKGROUND', (2, 2), (2, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                ('ALIGN', (0, 1), (0, 2), 'RIGHT'),
                ('SPAN', (1, 2), (-1, 2)),

            ]
        )



    else:
        list_estilos.extend(
            [
                ('GRID', (0, 1), (-1, 3), 1, colors.black),
                ('BACKGROUND', (0, 2), (0, 2), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                ('BACKGROUND', (0, 3), (0, 3), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                #('BACKGROUND', (2, 3), (2, 3), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
                ('ALIGN', (0, 1), (0, 2), 'RIGHT'),
                ('ALIGN', (2, 1), (2, 2), 'RIGHT'),
                ('SPAN', (1, 2), (-1, 2)),
                ('SPAN', (1, 3), (-1, 3)),
            ]
        )

    Tabla.setStyle(
    TableStyle(list_estilos)

    )





    Elementos.append(Tabla)
    Elementos.append(Spacer(0, 10))






    fila2= [Paragraph(e, h3) for e in
         [u"<strong>UBIGEO</strong>",u"<strong>Distrito</strong>", u"<strong>Subdistrito</strong>",]]


    fila2.extend([Paragraph(e,h5) for e in [u"<strong>Nº de zonas</strong>",
          u"<strong>Nº de subzonas</strong>",
          u"<strong>Nº de secciones censales </strong>",
          u"<strong>Nº de AEUs</strong>",
          u"<strong>Nº de Mz. Censales </strong>",
          u"<strong>Nº de viviendas </strong>"]])




    if nivel==1 :  ###departamental

        fila2.insert(1, Paragraph(u"<strong>Provincia</strong>", h3))
        #fila2.insert(2, Paragraph(u"<strong>Subprovincia</strong>", h3))




    Filas2 = [ fila2]


    if nivel==1:
        #tam_columns = [2*cm,2 * cm, 2 * cm, 2 * cm, 2 * cm, 1 * cm, 1 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm,1.5 * cm]
        tam_columns = [2 * cm, 2 * cm, 3 * cm, 3 * cm, 1 * cm, 1.5 * cm, 1.5 * cm, 1 * cm, 1.5 * cm, 1.5 * cm]

    else:
        tam_columns = [2*cm,4 * cm, 4 * cm, 1 * cm, 1.5 * cm, 1.5 * cm, 1 * cm, 1.5 * cm,1.5 * cm]
        #tam_columns = [3 * cm, 3 * cm, 3 * cm, 3 * cm, 1 * cm, 1 * cm, 1 * cm, 1 * cm, 1 * cm,
        #               1 * cm]


    Tabla2 = Table(Filas2,
                   colWidths= tam_columns )


    estilo_cab_cuerpo_tabla=[
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),

        ('GRID', (0, 0), (-1, 0), 1, colors.black),
    ]


    Tabla2.setStyle(TableStyle(estilo_cab_cuerpo_tabla))
    Elementos.append(Tabla2)
    nrows = len(data)

    #####################cuerpo tabla##############################

    estilo_cuerpo_tabla=[
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (-1, 0), (-1, 0), 'CENTER'),
        ]

    estilo_primera_fila = [

        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    if nivel==1:
        estilo_primera_fila.append(('ALIGN', (0, 0), (3, 0), 'CENTER'))
        estilo_primera_fila.append(('SPAN', (0, 0), (3,0)))

    else:
        estilo_primera_fila.append(('ALIGN', (0, 0), (1, 0), 'CENTER'))
        estilo_primera_fila.append(('SPAN', (0, 0), (1, 0)))


    i=0


    p = 32
    contador_lineas = 0
    n_hoja = 1

    if nivel==1:
        parametro_linea = 15.0
    else:
        parametro_linea=26.0

    if nrows > p:
        contador_lineas = 1
        for viv in data:
            prov = viv[2]
            subprov = viv[3]
            distrito = viv[4]
            subdistrito = viv[5]
            zonas = viv[6]
            subzonas = viv[7]
            secciones = viv[8]
            aeus = viv[9]
            manzanas = viv[10]
            viviendas = viv[11]
            ubigeo=viv[12]


            registros = [[Paragraph(u"{}".format(el), h5) for el in
                         [ubigeo,distrito, subdistrito, zonas, subzonas, secciones, aeus, manzanas, viviendas]]]
            if nivel == 1:
                registros[0].insert(1, Paragraph(prov, h5))
                #registros[0].insert(2, Paragraph(subprov, h5))

            if i == 0:
                registros[0][0] = Paragraph(u"<strong>TOTAL</strong>", h5)  # '<strong>TOTAL</strong>'
                RegistrosIngresados = Table(registros, colWidths=tam_columns)
                RegistrosIngresados.setStyle(TableStyle(estilo_primera_fila))
            else:
                RegistrosIngresados = Table(registros, colWidths=tam_columns)
                RegistrosIngresados.setStyle(TableStyle(estilo_cuerpo_tabla))
            Elementos.append(RegistrosIngresados)


            if nivel==1:
                max_tam_registros=max([ len(u"{}".format(el)) for el in  [prov,distrito, subdistrito]  ])

            else:
                max_tam_registros = max([len(u"{}".format(el)) for el in [distrito, subdistrito]])


            print max_tam_registros


            lineas = max_tam_registros / parametro_linea
            cant_lineas = math.ceil(lineas)
            print 'cant_lineas',cant_lineas
            contador_lineas = cant_lineas + contador_lineas


            if n_hoja == 1:
                if contador_lineas > p:
                    n_hoja = n_hoja + 1
                    Elementos.append(PageBreak())
                    Elementos.append(Tabla2)
                    contador_lineas = 1
            else:
                if contador_lineas > 40:
                    n_hoja = n_hoja + 1


                    if i<nrows-1:
                        Elementos.append(PageBreak())
                        Elementos.append(Tabla2)
                    contador_lineas = 1


            i = i + 1


    else:
        for viv in data:
            prov = viv[2]
            subprov = viv[3]
            distrito = viv[4]
            subdistrito = viv[5]
            zonas = viv[6]
            subzonas = viv[7]
            secciones = viv[8]
            aeus = viv[9]
            manzanas = viv[10]
            viviendas = viv[11]
            ubigeo = viv[12]

            registros = [[Paragraph(u"{}".format(el), h5) for el in
                         [ubigeo,distrito, subdistrito, zonas, subzonas, secciones, aeus, manzanas, viviendas]]]

            if nivel == 1:
                registros[0].insert(1, Paragraph(prov, h5))
                #registros[0].insert(2, Paragraph(subprov, h5))

            if i == 0:
                registros[0][0] = Paragraph(u"<strong>TOTAL</strong>", h5)
                RegistrosIngresados = Table(registros, colWidths=tam_columns)
                RegistrosIngresados.setStyle(TableStyle(estilo_primera_fila))
            else:
                RegistrosIngresados = Table(registros, colWidths=tam_columns)
                RegistrosIngresados.setStyle(TableStyle(estilo_cuerpo_tabla))
            Elementos.append(RegistrosIngresados)
            i = i + 1


    Elementos.append(Spacer(0, 10))


    pdf = SimpleDocTemplate(output, pagesize=A4,
                            rightMargin=65,
                            leftMargin=65,
                            topMargin=0.5 * cm,
                            bottomMargin=0.5 * cm, )

    #pdf = SimpleDocTemplate(output, pagesize=(29.7 * cm, 21 * cm),
    #                        rightMargin=20,
    #                        leftMargin=20,
    #                        topMargin=0.25 * cm,
    #                        bottomMargin=0.25 * cm, )

    pdf.build(Elementos)

    print "Finalizado"



