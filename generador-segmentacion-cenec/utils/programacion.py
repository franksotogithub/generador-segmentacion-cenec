# -*-coding: utf-8-*-

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.styles.borders import Border, Side
from openpyxl.styles import PatternFill
from openpyxl import drawing
import win32com.client
from os import path
import string
import xlsxwriter
from conf import config
from datetime import datetime


escudo_nacional = path.join(config.PATH_IMG,'Escudo_BN.png')
logo_nacional = path.join(config.PATH_IMG,'Inei_BN.png')



thin_border = Border(left=Side(style='thin'),
                     right=Side(style='thin'),
                     top=Side(style='thin'),
                     bottom=Side(style='thin'))

titleFill = PatternFill(start_color='D9D9D9',
                        end_color='D9D9D9',
                        fill_type='solid')

SHEEP='programacion'
SHEEP_ETIQUETAS ='etiquetas'

def abc(inicial, final):
    abc = list(string.ascii_uppercase)
    ini = abc.index(inicial)
    fin = abc.index(final)
    lista = abc[ini:fin + 1]
    return lista


def set_border(ws):

    list_col = abc('B', 'E') + abc('K', 'O')
    for i in list_col:
        ws["{}11".format(i)].border = thin_border
        ws["{}12".format(i)].border = thin_border
    list_fil = abc('E','G')
    for i in list_fil:
        ws["{}6".format(i)].border = thin_border
        ws["{}7".format(i)].border = thin_border
        ws["{}8".format(i)].border = thin_border
    list_fil2 = abc('F', 'M')
    for i in list_fil2:
        ws["{}10".format(i)].border = thin_border


def insertImage(ws):
    img = drawing.image.Image(escudo_nacional)
    img.drawing.width = 90
    img.drawing.height = 90
    ws.add_image(img, "C1")
    img2 = drawing.image.Image(logo_nacional)
    img2.drawing.width = 90
    img2.drawing.height = 90
    ws.add_image(img2, "X1")

def cuerpo_border(ws, alto):
    ws.column_dimensions['A'].width = 2
    ws.column_dimensions['B'].width = 6
    ws.column_dimensions['C'].width = 9
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 10
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 10
    ws.column_dimensions['J'].width = 15
    ws.column_dimensions['K'].width = 4
    ws.column_dimensions['L'].width = 10
    ws.column_dimensions['M'].width = 13
    ws.column_dimensions['N'].width = 13
    ws.column_dimensions['O'].width = 5
    ws.column_dimensions['P'].width = 10
    ws.column_dimensions['Q'].width = 10
    ws.column_dimensions['R'].width = 10
    ws.column_dimensions['S'].width = 11
    ws.column_dimensions['T'].width = 10
    ws.column_dimensions['U'].width = 10
    ws.column_dimensions['V'].width = 11
    ws.column_dimensions['W'].width = 10
    ws.column_dimensions['X'].width = 10
    ws.column_dimensions['Y'].width = 10
    ws.row_dimensions[12].height = 15
    ws.row_dimensions[13].height = 30

    columns = range(2,26)

    rows = range(12, 37)
    for col in columns:
        for row in rows:
            ws.cell(row=row, column=col).border = thin_border
            ws.cell(row=row, column=col).alignment = Alignment(horizontal="center", vertical="center",wrap_text=True)
            ws.cell(row=row, column=col).font = Font(bold=True, size=10)

def colorCelda(ws):
    ws['N6'].fill = titleFill
    for row in range(6,11):
        ws['B{}'.format(row)].fill = titleFill

    for x in abc('B', 'Y'):
        ws['{}12'.format(x)].fill = titleFill
        ws['{}13'.format(x)].fill = titleFill

    for x in range(34,36):
        ws['B{}'.format(x)].fill = titleFill

def diasCuerpo(ws):
    n = 0
    lista = abc('B', 'P')
    for x in lista:
        n = n + 1
        ws["{}10".format(x)] = u'{}'.format(n)
        ws["{}10".format(x)].alignment = Alignment(horizontal="center", vertical="center")

def formatocampos(ws):
    m = 0
    n = 0
    lista1 = abc('O', 'Y')
    lista2 = list(range(14, 33))
    for p in lista1:
        for q in lista2:

            ws["{}{}".format(p, q)].number_format = "@"

def llenarTotal(ws):
    for x in abc('F', 'O'):
        ws['{}13'.format(x)] = "=SUM({}14: {}100)".format(x, x)

def cabecera(data_cabecera,wb):


    ws = wb.get_sheet_by_name(SHEEP)

    ws["D1"] = u'V CENSO NACIONAL ECONÓMICO 2019 - 2020'
    ws["D2"] = u'2019 - 2020'
    ws["D4"] = u'PROGRAMACIÓN DE RUTA DEL EMPADRONADOR'


    ws["B6"] = u'A. ORGANIZACION DE CAMPO '
    ws["B7"] = u'SEDE OPERATIVA'
    ws["E7"] = data_cabecera['CODSEDE']
    ws["F7"] = data_cabecera['SEDE_OPERATIVA']

    ws["B8"] = u'BRIGADA'
    ws["E8"] = data_cabecera['BRIGADA']

    if 'RUTA' in data_cabecera.keys() :
        ws["B9"] = u'RUTA'
        ws["E9"] = data_cabecera['RUTA']

        ws["B10"] = u'EMPADRONADOR'
        ws["E10"] = data_cabecera['EMPADRONADOR']
        ws["N10"] = u'DOC.CENEC.03.11'
        ws["N6"] = u'B. NOMBRE Y APELLIDO DEL EMPADRONADOR'

    else:
        ws["N10"] = u'DOC.CENEC.03.12'
        ws["N6"] = u'B. NOMBRE Y APELLIDO DEL JEFE DE BRIGADA'

    ws["N7"] = u''


    ws["N10"].alignment = Alignment(horizontal="right", vertical="bottom")
    ws["N10"].font = Font(bold=True)
    ws["B12"] = u'N° ORD'
    ws["C12"] = u'UBIGEO'
    ws["D12"] = u'DEPARTAMENTO'
    ws["E12"] = u'PROVINCIA'
    ws["F12"] = u'DISTRITO'
    ws["G12"] = u'COD CCPP'
    ws["H12"] = u'CENTRO POBLADO'
    ws["I12"] = u'UBICACIÓN CENSAL'   #MERGE
    ws["K12"] = u'EST.'
    ws["L12"] = u'N° PERIODO'
    ws["M12"] = u'PERIODO TRABAJO'    #MERGE
    ws["O12"] = u'DÍAS DE OPERACIÓN DE CAMPO' #MERGE
    ws["U12"] = u'ASOCIACIÓN DE FONDOS' #MERGE


    ws["I13"] = u'ZONA'
    ws["J13"] = u'MANZANA'
    ws["M13"] = u'FECHA INI'
    ws["N13"] = u'FECHA FIN'
    ws["O13"] = u'VIAJE'
    ws["P13"] = u'DIAS TRABAJO'
    ws["Q13"] = u'RECUPERACIÓN'
    ws["R13"] = u'DESCANSO'
    ws["S13"] = u'DÍAS OPERATIVOS'
    ws["T13"] = u'TOT.DÍAS'
    ws["U13"] = u'MOV.LOCAL'
    ws["V13"] = u'MOV.ESPECIAL'
    ws["W13"] = u'PASAJE'
    ws["X13"] = u'VIÁTICOS'
    ws["Y13"] = u'TOTAL GENERAL s/.'
    ws["B34"] = u'TOTAL DEL PERIODO'
    ws["B35"] = u'TOTAL DE LA RUTA'
    ws["B36"] = u'OBSERVACIONES'

    celdasCabecera = [
        'D1:W1','D2:W2','D4:W4',
        'B12:B13',
        'C12:C13',
        'D12:D13',
        'E12:E13',
        'F12:F13',
        'G12:G13',
        'H12:H13',
        'I12:J12',
        'K12:K13',
        'L12:L13',
        'M12:N12',
        'O12:T12',
        'U12:Y12',
        'N10:Y10',
        'N6:Y6',
        'N7:Y7',
        'B6:F6',
        'B7:D7',
        'B8:D8',
        'B9:D9',
        'B10:D10',
        'E8:F8',
        'E9:F9',
        'E10:F10',
        'B34:J34',
        'B35:J35',
        'B36:J36',
        'K36:Y36',
    ]

    for cells in celdasCabecera:
        ws.merge_cells(cells)


    for x in abc('O', 'Y'):
        ws['{}34'.format(x)] = "=SUM({}14: {}33)".format(x, x)
        ws['{}35'.format(x)] = "=SUM({}14: {}33)".format(x, x)

    cells_cabecera=[]

    for row in range(12,14):
        for column in abc('B', 'Y'):
            cell= '{}{}'.format(column,row)
            ws[cell].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws[cell].font = Font(bold=True, size=8)
            ws[cell].border = thin_border

    for row in range(6,11):
        ws['B{}'.format(row)].alignment = Alignment( vertical="center", wrap_text=True)
        ws['B{}'.format(row)].font = Font(bold=True, size=12)
        for column in abc('B', 'F'):
            ws['{}{}'.format(column,row)].border = thin_border


    for row in range(6, 8):
        for column in abc('N', 'Y'):
            ws['{}{}'.format(column, row)].border = thin_border


    list_cell = ['D1','D2','D4','B6','N6','B34','B35','B36']
    for cell in list_cell:
        ws[cell].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        if cell not in ['B6','N6','B34','B35','B36']:
            ws[cell].font = Font(bold=True, size=16)
        else:
            ws[cell].font = Font(bold=True, size=12)





def crear_excel(cabecera, output,alto):
    wb = xlsxwriter.Workbook(path.join(config.PATH_PROGRAMACIONES,output))
    ws = wb.add_worksheet(SHEEP)
    ws.print_area(1, 2, 36, 26)
    ws.fit_to_pages(1, 1)
    wb.close()


def crear_excel_etiquetas( output):
    wb = xlsxwriter.Workbook(output)
    ws = wb.add_worksheet(SHEEP_ETIQUETAS)
    ws.print_area(1, 2, 36, 26)
    ws.fit_to_pages(1, 1)
    wb.close()

def excel2PDF(output,sheep=SHEEP,orientacion=1):
    o = win32com.client.Dispatch("Excel.Application")
    o.Visible = 0
    o.DisplayAlerts = 0
    name,formato=output.split('.')
    path_pdf = '{}{}'.format(name,'.pdf')
    wb = o.Workbooks.Open(output)
    ws=wb.Sheets(sheep)
    ws.PageSetup.Orientation=orientacion
    ws.PageSetup.LeftMargin = 1
    ws.PageSetup.RightMargin = 1
    ws.ExportAsFixedFormat(0, path_pdf)
    wb.Close()

def llenar_excel(info, output, alto):
    data_cabecera = info[0]
    wb = load_workbook(output)
    cabecera(data_cabecera, wb)
    ws = wb.get_sheet_by_name(SHEEP)
    data_cuerpo = info[1]
    for row in range(0,alto):
        i=row + 14
        x=data_cuerpo[row]
        ws["B{}".format(i)]=u'{}'.format(row+1)
        ws["C{}".format(i)]=u'{}'.format(x['UBIGEO'])
        ws["D{}".format(i)]=u'{}'.format(x['DEPARTAMENTO'])
        ws["E{}".format(i)]=u'{}'.format(x['PROVINCIA'])
        ws["F{}".format(i)]=u'{}'.format(x['DISTRITO'])
        ws["G{}".format(i)]=u'{}'.format(x['CODCCPP'])
        ws["H{}".format(i)]=u'{}'.format(x['NOMCCPP'])
        ws["I{}".format(i)]=u'{}'.format(x['ZONA'])
        ws["J{}".format(i)]=u'{}'.format(x['MANZANAS'])
        ws["K{}".format(i)]=u'{}'.format(x['CANT_EST'])
        ws["L{}".format(i)]=u'{}'.format(x['PERIODO'])
        ws["M{}".format(i)]=u'{}'.format((datetime.strptime(x['FECHA_INI'][0:10], "%Y-%m-%d")).strftime("%d/%m/%Y"))
        ws["N{}".format(i)]=u'{}'.format((datetime.strptime(x['FECHA_FIN'][0:10], "%Y-%m-%d")).strftime("%d/%m/%Y"))
        ws["O{}".format(i)]=int(x['DIAS_VIAJE'])
        ws["P{}".format(i)]=int(x['DIAS_TRABAJO'])
        ws["Q{}".format(i)]=int(x['DIAS_RECUPERACION'])
        ws["R{}".format(i)]=int(x['DIAS_DESCANSO'])
        ws["S{}".format(i)]=int(x['DIAS_OPERATIVOS'])
        ws["T{}".format(i)]=int(x['TOTAL_DIAS'])
        ws["U{}".format(i)]=int(x['MOV_LOCAL'])
        ws["V{}".format(i)]=int(x['MOV_ESPECIAL'])
        ws["W{}".format(i)]=float(u'{:6.2f}'.format(round(x['PASAJES'], 3)))
        ws["X{}".format(i)]=int(x['VIATICOS'])
        ws["Y{}".format(i)] = u''



    insertImage(ws)
    cuerpo_border(ws, alto)
    formatocampos(ws)

    colorCelda(ws)
    wb.save(output)
    wb.close()

def llenar_excel_etiqueta(c, ws,x):

    i=x

    #print 'c>>>',c
    ws["B{}".format(i)] = u'Sede'
    ws["C{}".format(i)] = u'{}'.format(c['SEDE_OPERATIVA'])
    ws["D{}".format(i)] = u'Brigada'
    ws["E{}".format(i)] = u'{}'.format(c['BRIGADA'])
    i = i+1
    if 'RUTA' in c.keys():
        ws["B{}".format(i)] = u'Ruta'

        ws["C{}".format(i)] = u'{}'.format(c['RUTA'])
        ws["D{}".format(i)] = u'Empadronador'
        ws["E{}".format(i)] = u'{}'.format(c['EMPADRONADOR'])
        i = i + 1

    ws["B{}".format(i)] =u'Periodo'
    ws["D{}".format(i)] = u'{}'.format(c['PERIODO'])
    i = i + 1
    ws["B{}".format(i)].font =Font(name='3 of 9 Barcode' ,size=48)
    ws["B{}".format(i)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    if 'RUTA' in c.keys():
        ws["B{}".format(i)] = '{cod_oper}{periodo}{codsede}{brigada}{ruta}{emp}'.format(cod_oper=c['COD_OPER'],
                                                                               periodo = c['PERIODO'],
                                                                               codsede=c['CODSEDE'],
                                                                               brigada=c['BRIGADA'], ruta=c['BRIGADA'],
                                                                               emp=c['EMPADRONADOR'])

    else:
        ws["B{}".format(i)] = '{cod_oper}{periodo}{codsede}{brigada}'.format(cod_oper=c['COD_OPER'],
                                                                    periodo=c['PERIODO'],
                                                                    codsede=c['CODSEDE'],
                                                                    brigada=c['BRIGADA'])

    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 20

    merge_celdas = [
        'B{i}:C{i}'.format(i=i-1),
        'D{i}:E{i}'.format(i=i-1),
        'B{i}:E{i}'.format(i=i),
    ]

    for cells in merge_celdas:
        ws.merge_cells(cells)


    lista1 = abc('B', 'E')
    lista2 = list(range(x, i+1))
    for p in lista1:
        for q in lista2:
            ws["{}{}".format(p, q)].border = thin_border
            if p in ['B','D'] and q<i:
                ws["{}{}".format(p, q)].fill = titleFill
                ws["{}{}".format(p, q)].font = Font(bold=True)
            elif p in ['B','D'] and (q==i):
                ws["{}{}".format(p, q)].alignment = Alignment(horizontal="center", vertical="center")



    i = i + 2

    return i

def crear_programacion_rutas(info,output):
    cabecera=info[0]
    cuerpo = info[1]
    alto = len(cuerpo)
    crear_excel(cabecera,output,alto)
    llenar_excel(info,output,alto)
    excel2PDF(output)

def crear_programacion_brigadas(info,output):
    cabecera = info[0]
    cuerpo = info[1]
    alto = len(cuerpo)
    crear_excel(cabecera, output, alto)
    llenar_excel(info, output, alto)
    excel2PDF(output,orientacion=2)


def crear_etiquetas(data,output):

    crear_excel_etiquetas( output)

    j=2
    wb = load_workbook(output)
    ws = wb.get_sheet_by_name(SHEEP_ETIQUETAS)
    for e in data:
        j=llenar_excel_etiqueta(e, ws,j)
    wb.save(output)
    wb.close()
    excel2PDF(output,sheep=SHEEP_ETIQUETAS)
    #for ruta in rutas ()




