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
from datetime import datetime
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

def cuerpo_hoja_listado_ruta(elementos,data,columnas,i,ancho=0.8):
    n=i
    for count, x in enumerate(data, i):
        registros = [
            [Paragraph(e, h3) for e in
             [u'{}'.format(count),
              u'{}'.format(x['UBIGEO']),
              u'{}'.format(x['DEPARTAMENTO']),
              u'{}'.format(x['PROVINCIA']),
              u'{}'.format(x['DISTRITO']),
              u'{}'.format(x['CODCCPP']),
              u'{}'.format(x['NOMCCCPP']),
              u'{}'.format(x['PERIODO']),
              u'{}'.format(x['ZONA']),
              u'{}'.format(x['MZ']),
              u'{}'.format(x['CANT_EST'])
              ]]
        ]

        Tabla2 = Table(registros, colWidths=columnas ,rowHeights=[ancho * cm])
        Tabla2.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        ]))

        elementos.append(Tabla2)
        n=n+1
    return n


def listado_ruta(info, output):
    #CANT_REG_PRIMERA_HOJA=36
    CANT_REG_PRIMERA_HOJA = 24
    CANT_REG_SIGUIENTES_HOJAS = 32
    CANT_REG_SIGUIENTES_ULTIMA_HOJA = CANT_REG_SIGUIENTES_HOJAS - 2

    cab=info[0]
    data= info[1]
    #coddpto = cab["CODDPTO"]
    #departamento = cab["DEPARTAMENTO"]
    coddpto = cab["CODSEDE"]
    departamento = cab["SEDE_OPERATIVA"]
    brigada = cab["BRIGADA"]
    ruta = cab["RUTA"]
    empadronador = ""
    cod_emp = cab["EMP"]

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
        ['', '', '', '', 'DOC.CENEC.03.08'],
        [ Paragraph(u'<b>A. ORGANIZACIÓN DE CAMPO</b>',h11), '', '', '', Paragraph(u'<b>B. NOMBRES Y APELLIDOS DEL EMPADRONADOR</b>',h11)],
        [Paragraph(u'<b>SEDE OPERATIVA: </b>', h1), u'{}'.format(coddpto), u'{}'.format(departamento), '',u'{}'.format(empadronador)],
        [Paragraph(u'<b>BRIGADA: </b>', h1), u'{}'.format(brigada), '', '', ''],
        [Paragraph(u'<b>RUTA: </b>', h1), u'{}'.format(ruta),'', '', ''],
        [Paragraph(u'<b>EMPADRONADOR: </b>', h1), u'{}'.format(cod_emp), '', '', ''],
        #cod_emp
        ]


    Tabla = Table(Filas, colWidths=[3.7 * cm, 1 * cm, 6.3 * cm, 1 * cm, 7.5 * cm],
                  rowHeights=[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm])


    Tabla.setStyle(TableStyle([
           ('TEXTCOLOR', (0, 0), (4, 0), colors.black),
           ('GRID', (0, 1), (2, 5), 1, colors.black),
           ('GRID', (4, 1), (4, 2), 1, colors.black),
           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
           ('ALIGN', (0, 1), (4, 1), 'CENTER'),
           ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
           ('ALIGN', (1, 1), (2, 5), 'CENTER'),
           ('FONTSIZE', (0, 0), (-1, -1), 8),
           ('BACKGROUND', (0, 1), (2, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('BACKGROUND', (0, 1), (0, 5), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('BACKGROUND', (4, 1), (4, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('SPAN', (0, 1), (2, 1)),
           ('SPAN', (1, 3), (2, 3)),
           ('SPAN', (1, 4), (2, 4)),
            ('SPAN', (1, 5), (2, 5)),
    ]))
    Elementos.append(Tabla)
    Elementos.append(Spacer(0, 10))

    CabeceraSecundaria = [
         [Paragraph(e, h3) for e in [u"<strong>Nº</strong>",u"<strong>UBIGEO</strong>", u"<strong>DEPARTAMENTO</strong>",
                                        u"<strong>PROVINCIA</strong>",u"<strong>DISTRITO</strong>",u"<strong>COD. CCPP</strong>",u"<strong>CENTRO  POBLADO</strong>",
                                        u"<strong>PER.</strong>",u"<strong>UBICACIÓN CENSAL</strong>","",u"<strong>TOT. EST.</strong>"
          ]],
          [Paragraph(e, h3) for e in["","","","","","","","","ZONA","MZ",""]],
        ]


    #columnas = [1.2 * cm, 1.5 * cm, 2.8 * cm, 3 * cm, 3.5 * cm, 1.2 * cm, 2.1 * cm, 1 * cm, 1.2 * cm, 1 * cm ,1*cm]
    columnas = [1.2 * cm, 1.5 * cm, 2.85 * cm, 2.85 * cm, 2.85 * cm, 1.2 * cm, 2.85 * cm, 1 * cm, 1.2 * cm, 1 * cm, 1 * cm]

    Tabla1 = Table(CabeceraSecundaria, colWidths=columnas)

    Tabla1.setStyle(TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTSIZE', (0, 1), (0, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (2, 0), (2, 1)),
            ('SPAN', (3, 0), (3, 1)),
            ('SPAN', (4, 0), (4, 1)),
            ('SPAN', (5, 0), (5, 1)),
            ('SPAN', (6, 0), (6, 1)),
            ('SPAN', (7, 0), (7, 1)),
            ('SPAN', (8, 0), (9, 0)),
            ('SPAN', (10, 0), (10, 1)),

        ]
    ))
    Elementos.append(Tabla1)

    nrows = len(data)

    p=1
    contador_lineas=0
    n_hoja=1

    ancho = 0.8
    data

    tam_max_distrito=max(list( len(e['DISTRITO']) for e in data))
    tam_max_nomccpp = max(list(len(e['NOMCCCPP']) for e in data))

    tam_max = max(tam_max_distrito,tam_max_nomccpp)
    #    [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
    #                            'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
    #                            'NOMCCCPP': e[9], 'BRIGADA': e[10], 'RUTA': ruta['RUTA'], 'PERIODO': e[11],
    #                            'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13], 'MANZANAS': e[14], 'CANT_EST': e[15],
    #                            'EMP': e[16]
    #                            } for e in list(set((d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
    #                                                 d['DISTRITO'], d['CODDPTO'], d['CODPROV'], d['CODDIST'],
    #                                                 d['CODCCPP'], d['NOMCCCPP'], d['BRIGADA'], d['PERIODO'],
    #                                                 d['CODSEDE'], d['SEDE_OPERATIVA'], d['MANZANAS'], d['CANT_EST'],
    #                                                 d['EMP']) for d in data))]

    if(tam_max>25 ):
        CANT_REG_PRIMERA_HOJA = 16
        CANT_REG_SIGUIENTES_HOJAS = 21
        CANT_REG_SIGUIENTES_ULTIMA_HOJA = CANT_REG_SIGUIENTES_HOJAS - 1
        ancho = 1.2

    if nrows > CANT_REG_PRIMERA_HOJA:
        HojaRegistros = contar_registros(nrows, CANT_REG_PRIMERA_HOJA, CANT_REG_SIGUIENTES_HOJAS)
        HojaRegistros.append((0,CANT_REG_PRIMERA_HOJA))
        HojaRegistros.sort(key=lambda n: n[0])
        i=1
        for rangos in HojaRegistros:
            datax= data[rangos[0]:rangos[1]]
            i=cuerpo_hoja_listado_ruta(Elementos,datax,columnas,i,ancho)
            Elementos.append(PageBreak())
            Elementos.append(Tabla1)

        cant_reg_ult_pag = HojaRegistros[-1][1] - HojaRegistros[-1][0]
        del Elementos[-1]
        if cant_reg_ult_pag < CANT_REG_SIGUIENTES_ULTIMA_HOJA:
            del Elementos[-1]

    else:
        cuerpo_hoja_listado_ruta(Elementos, data,columnas,1,ancho)

    Elementos.append(Spacer(0, 10))

    pdf = SimpleDocTemplate(output,
                            pagesize=A4,
                            rightMargin=65,
                            leftMargin=65,
                            topMargin=0.5 * cm,
                            bottomMargin=0.5 * cm,)


    PiePagina = [[Paragraph(u'{}'.format(u"EMPADRONADOR"), h3)],
                 [Paragraph(u'{}'.format(u"Todos los establecimientos que se encuentren ubicados en las manzanas que conforman su área de empadronamiento, deben ser empadronados. Si en su recorrido encuentra alguna modificación o una manzana no considerada en la cartografía deberá efectuar la actualización correspondiente."),h3)]]

    Tabla_Pie = Table(PiePagina, colWidths = [19.5 * cm],rowHeights=[0.8 * cm,1.4* cm])

    Tabla_Pie.setStyle( TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

    Elementos.append(Tabla_Pie)
    pdf.build(Elementos)
    return output


def listado_brigada(info, output):
    cab=info[0]
    data= info[1]
    coddpto = cab["CODSEDE"]
    departamento = cab["SEDE_OPERATIVA"]
    brigada = cab["BRIGADA"]

    empadronador = ""

    Plantilla = getSampleStyleSheet()

    Elementos = []


    Titulo = Paragraph(u'V CENSO NACIONAL ECONÓMICO <br/> 2019 - 2020',h_sub_tile)
    SubTitulo = Paragraph(u'<strong>LISTADO DE EMPADRONADORES POR MANZANAS Y ESTABLECIMIENTOS</strong>', h_sub_tile_2)


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
        ['', '', '', '', 'DOC.CENEC.03.10'],
        [ Paragraph(u'<b>A. ORGANIZACIÓN DE CAMPO</b>',h11), '', '', '', Paragraph(u'<b>B. NOMBRES Y APELLIDOS DEL JEFE DE BRIGADA</b>',h11)],
        [Paragraph(u'<b>SEDE OPERATIVA: </b>', h1), u'{}'.format(coddpto), u'{}'.format(departamento), '',u'{}'.format(empadronador)],
        [Paragraph(u'<b>BRIGADA: </b>', h1), u'{}'.format(brigada), '', '', ''],
        ]

    Tabla = Table(Filas, colWidths=[3.7 * cm, 1 * cm, 6.3 * cm, 7 * cm,  8.9 * cm],
                  rowHeights=[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm])


    Tabla.setStyle(TableStyle([
           ('TEXTCOLOR', (0, 0), (4, 0), colors.black),
           ('GRID', (0, 1), (2, 3), 1, colors.black),
           ('GRID', (4, 1), (4, 2), 1, colors.black),
           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
           ('ALIGN', (0, 1), (4, 1), 'CENTER'),
           ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
           ('ALIGN', (1, 1), (2, 3), 'CENTER'),
           ('FONTSIZE', (0, 0), (-1, -1), 8),
           ('BACKGROUND', (0, 1), (2, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('BACKGROUND', (0, 1), (0, 3), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('BACKGROUND', (4, 1), (4, 1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
           ('SPAN', (0, 1), (2, 1)),
           ('SPAN', (1, 3), (2, 3)),

    ]))
    Elementos.append(Tabla)
    Elementos.append(Spacer(0, 10))

    CabeceraSecundaria = [
         [Paragraph(e, h3) for e in [u"<strong>Nº</strong>",u"<strong>COD.RUTA.</strong>",u"<strong>COD.EMP.</strong>",u"<strong>UBIGEO</strong>", u"<strong>DEPARTAMENTO</strong>",
                                        u"<strong>PROVINCIA</strong>",u"<strong>DISTRITO</strong>",u"<strong>COD. CCPP</strong>",u"<strong>CENTRO POBLADO</strong>",
                                        u"<strong>PER.</strong>",u"<strong>UBICACIÓN CENSAL</strong>","",u"<strong>TOT. EST.</strong>"
          ]],
          [Paragraph(e, h3) for e in["","","","","","","","","","","ZONA","MZ",""]],
        ]

    columnas = [1.2* cm, 1.7*cm,1.7*cm,1.5 * cm, 3 * cm, 3 * cm, 3.5 * cm, 1.2 * cm, 2.3 * cm, 0.9 * cm,  1.2 * cm, 4.7 * cm ,1*cm]

    Tabla1 = Table(CabeceraSecundaria, colWidths=columnas)

    Tabla1.setStyle(TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTSIZE', (0, 1), (0, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (2, 0), (2, 1)),
            ('SPAN', (3, 0), (3, 1)),
            ('SPAN', (4, 0), (4, 1)),
            ('SPAN', (5, 0), (5, 1)),
            ('SPAN', (6, 0), (6, 1)),
            ('SPAN', (7, 0), (7, 1)),
            ('SPAN', (8, 0), (8, 1)),
            ('SPAN', (9, 0), (9, 1)),
            ('SPAN', (10, 0), (11, 0)),
            ('SPAN', (12, 0), (12, 1)),

        ]
    ))
    Elementos.append(Tabla1)

    nrows = len(data)

    p=1
    contador_lineas=0
    n_hoja=1

    for count,x in enumerate(data,1):
        registros = [
                    [Paragraph(e, h3) for e in
                    [u'{}'.format(count),
                     u'{}'.format(x['RUTA']),
                     u'{}'.format(x['EMP']),
                     u'{}'.format(x['UBIGEO']),
                     u'{}'.format(x['DEPARTAMENTO']),
                     u'{}'.format(x['PROVINCIA']),
                     u'{}'.format(x['DISTRITO']) ,
                     u'{}'.format(x['CODCCPP']),
                     u'{}'.format(x['NOMCCCPP']),
                     u'{}'.format(x['PERIODO']),
                     u'{}'.format(x['ZONA']),
                     u'{}'.format(x['MANZANAS']),
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



    pdf = SimpleDocTemplate(output,
                            pagesize=(29.7 * cm, 21 * cm),
                            #pagesize=A4,
                            rightMargin=65,
                            leftMargin=65,
                            topMargin=0.5 * cm,
                            bottomMargin=0.5 * cm,)


    PiePagina = [[Paragraph(u'{}'.format(u"JEFE DE BRIGADA"), h3)],
                 [Paragraph(u'{}'.format(u"Todos los establecimientos que se encuentren ubicados en las manzanas que conforman su área de empadronamiento, deben ser empadronados. Si en su recorrido encuentra alguna modificación o una manzana no considerada en la cartografía deberá efectuar la actualización correspondiente"),h3)]]

    Tabla_Pie = Table(PiePagina, colWidths = [26.8 * cm],rowHeights=[0.8 * cm,1.6* cm])

    Tabla_Pie.setStyle( TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

    Elementos.append(Tabla_Pie)


    pdf.build(Elementos)
    return output

def programacion_ruta(info,output):
    cab=info[0]
    data= info[1]
    coddpto = cab["CODSEDE"]
    departamento = cab["SEDE_OPERATIVA"]
    brigada = cab["BRIGADA"]
    ruta = cab["RUTA"]

    empadronador = ""

    Plantilla = getSampleStyleSheet()

    Elementos = []


    Titulo = Paragraph(u'V CENSO NACIONAL ECONÓMICO <br/> 2019 - 2020',h_sub_tile)
    SubTitulo = Paragraph(u'<strong>PROGRAMACIÓN DE RUTA DEL EMPADRONADOR</strong>', h_sub_tile_2)


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
        ['', '', '', '', 'DOC.CENEC.03.11'],
        [ Paragraph(u'<b>A. ORGANIZACIÓN DE CAMPO</b>',h11), '', '', '', Paragraph(u'<b>B. NOMBRES Y APELLIDOS DEL JEFE DE BRIGADA</b>',h11)],
        [Paragraph(u'<b>SEDE OPERATIVA: </b>', h1), u'{}'.format(coddpto), u'{}'.format(departamento), '',u'{}'.format(empadronador)],
        [Paragraph(u'<b>BRIGADA: </b>', h1), u'{}'.format(brigada), '', '', ''],
        [Paragraph(u'<b>RUTA: </b>', h1), u'{}'.format(ruta), '', '', ''],
        ]

    Tabla = Table(Filas, colWidths=[3.7 * cm, 1 * cm, 6.3 * cm, 7 * cm,  8.9 * cm],
                  rowHeights=[0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm, 0.4 * cm])


    Tabla.setStyle(TableStyle([
           ('TEXTCOLOR', (0, 0), (4, 0), colors.black),
           ('GRID', (0, 1), (2, 4), 1, colors.black),
           ('GRID', (4, 1), (4, 2), 1, colors.black),
           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
           ('ALIGN', (0, 1), (4, 1), 'CENTER'),
           ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
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
         [Paragraph(e, h3) for e in [u"Nº",u"UBIGEO", u"DEPARTAMENTO",
                                        u"PROVINCIA",u"DISTRITO",u"COD. CCPP",u"CENTRO POBLADO",
                                        u"UBICACIÓN CENSAL","",u"EST.",u"N° PERIODO","",u"PERIODO DE TRABAJO",
                                       u"DÍAS DE OPERACIÓN DE CAMPO","","","","","",u"ASIGNACIÓN DE FONDOS","","","",""


          ]],
          [Paragraph(e, h3) for e in["","","","","","","",u"ZONA",u"MANZANA","",
                                     "",u"FECHA INI",u"FECHA FIN",u"VIAJE",u"ACT-EMP.",u"RECUPERACION",
                                        u"DESCANSO",u"DIAS OPERATIVOS",u"TOT.DIAS",u"MOV.LOCAL",
                                       u"MOV.ESPECIAL", u"PASAJE",u"VIATICOS",u"TOTAL GENERAL s/."]],

        ]

    columnas = [1* cm, 1.2 * cm, 2 * cm, 2 * cm, 2 * cm, 1.2 * cm, 2.3 * cm, 1 * cm,  1.5 * cm, 1 * cm ,
                1*cm,1*cm,1*cm,1*cm,1*cm,1*cm,1*cm,1*cm,1*cm,0.8*cm,
                1*cm,1.2*cm,1*cm,1*cm]

    Tabla1 = Table(CabeceraSecundaria, colWidths=columnas)

    Tabla1.setStyle(TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 3),
            ('FONTSIZE', (0, 1), (0, -1), 3),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(220.0 / 255, 220.0 / 255, 220.0 / 255)),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (2, 0), (2, 1)),
            ('SPAN', (3, 0), (3, 1)),
            ('SPAN', (4, 0), (4, 1)),
            ('SPAN', (5, 0), (5, 1)),
            ('SPAN', (6, 0), (6, 1)),
            ('SPAN', (7, 0), (8, 0)),
            ('SPAN', (9, 0), (9, 1)),
            ('SPAN', (10, 0), (10, 1)),
            ('SPAN', (11, 0), (12, 0)),
            ('SPAN', (13, 0), (18, 0)),
            ('SPAN', (19, 0), (23, 0)),

        ]
    ))
    Elementos.append(Tabla1)

    nrows = len(data)

    p=1
    contador_lineas=0
    n_hoja=1

    for count,x in enumerate(data,1):
        registros = [
                    [Paragraph(e, h3) for e in
                    [
                     u'{}'.format(count),
                     u'{}'.format(x['UBIGEO']),
                     u'{}'.format(x['DEPARTAMENTO']),
                     u'{}'.format(x['PROVINCIA']),
                     u'{}'.format(x['DISTRITO']),
                     u'{}'.format(x['CODCCPP']),
                     u'{}'.format(x['NOMCCPP']),
                     u'{}'.format(x['ZONA']),
                     u'{}'.format(''),
                     u'{}'.format(x['CANT_EST']),
                     u'{}'.format(x['PERIODO']),


                     u'{}'.format( (datetime.strptime(x['FECHA_INI'][0:10], "%Y-%m-%d")).strftime("%d/%m/%Y")  ),
                     u'{}'.format( (datetime.strptime(x['FECHA_FIN'][0:10], "%Y-%m-%d")).strftime("%d/%m/%Y")  ),
                     u'{}'.format(x['DIAS_VIAJE']),
                     '',
                     u'{}'.format(x['DIAS_RECUPERACION']),
                     u'{}'.format(x['DIAS_DESCANSO']),
                     u'{}'.format(x['DIAS_OPERATIVOS']),
                     u'{}'.format(x['TOTAL_DIAS']),
                     u'{}'.format(x['MOV_LOCAL']),
                     u'{}'.format(x['MOV_ESPECIAL']),
                     u'{:6.2f}'.format( round(x['PASAJES'],3) ),
                     u'{}'.format(x['VIATICOS']),
                     ''
                     ]]
        ]
        Tabla2 = Table(registros, colWidths=columnas)
        Tabla2.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 5),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER')
                    ]))
        Elementos.append(Tabla2)


    Elementos.append(Spacer(0, 10))



    pdf = SimpleDocTemplate(output,
                            pagesize=(29.7 * cm, 21 * cm),
                            #pagesize=A4,
                            rightMargin=65,
                            leftMargin=65,
                            topMargin=0.5 * cm,
                            bottomMargin=0.5 * cm,)





    pdf.build(Elementos)
    return output

#def etiquetas(info,output):
