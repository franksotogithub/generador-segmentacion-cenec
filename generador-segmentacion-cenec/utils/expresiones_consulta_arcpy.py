# -*- coding: utf-8 -*-
def expresion_ubigeos(where_list):
    m=0
    where_expression=""
    for x in where_list:
        if (m + 1) == len(where_list):
            where_expression = where_expression + ' "UBIGEO"=\'%s\' ' % where_list[m]
        else:
            where_expression = where_expression + ' "UBIGEO"=\'%s\' OR' % (where_list[m])

        m = m + 1

    return  where_expression



def expresion(data,campos):
    m = 0
    where_expression = ""
    cant_campos=len(campos)

    for fila in data:
        if (m + 1) == len(data):
            fila_expresion=""
            n = 0
            for campo in campos:


                if (n+1)==len(campos):
                    fila_expresion =  u"""{} \"{nombre_campo}\"=\'{data}\'  """.format(fila_expresion,nombre_campo=campos[n],data=fila[n])
                else:
                    fila_expresion = u"""{} \"{nombre_campo}\"=\'{data}\' AND """.format(fila_expresion,nombre_campo=campos[n],data=fila[n])
                n=n+1
            #where_expression = where_expression + "("+fila_expresion+")"
            where_expression =   u"{} ({})".format(where_expression,fila_expresion)

        else:
            fila_expresion = ""
            n = 0
            for campo in campos:

                if (n+1) == len(campos):
                    fila_expresion =   u"""{} \"{nombre_campo}\"=\'{data}\'  """.format(fila_expresion,nombre_campo=campos[n],data=fila[n])
                else:
                    fila_expresion =  u"""{} \"{nombre_campo}\"=\'{data}\' AND """.format(fila_expresion,nombre_campo=campos[n],data=fila[n])
                n = n + 1
            where_expression =  u"{} ({}) OR ".format(where_expression,fila_expresion)


        m = m + 1

    return where_expression


def expresion_2(data,campos):
    m = 0
    where_expression = ""
    cant_campos=len(campos)



    for fila in data:
        if (m + 1) == len(data):
            fila_expresion=""
            n = 0
            for campo in campos:


                if (n+1)==len(campos):

                    if campos[n][1]=="TEXT":
                        fila_expresion = u"""{} \"{nombre_campo}\"='{data}'  """.format(fila_expresion,nombre_campo=campos[n][0],data=fila[n])

                    else:
                        fila_expresion = u"""{} \"{nombre_campo}\"={data}  """.format(fila_expresion ,nombre_campo=campos[n][0], data=fila[n])

                else:
                    if campos[n][1]=="TEXT":
                        fila_expresion = u"""{} \"{nombre_campo}\"='{data}' AND """.format(fila_expresion,nombre_campo=campos[n][0],data=fila[n])
                    else:
                        fila_expresion =  u"""{} \"{nombre_campo}\"={data} AND """.format(fila_expresion,nombre_campo=campos[n][0], data=fila[n])
                n=n+1
            #where_expression = where_expression + "("+fila_expresion+")"
            where_expression = u"{} ({})".format(where_expression,fila_expresion)

        else:
            fila_expresion = ""
            n = 0
            for campo in campos:

                if (n+1) == len(campos):
                    if campos[n][1] == "TEXT":
                        fila_expresion =  u"""{} \"{nombre_campo}\"=\'{data}\'  """.format(fila_expresion ,nombre_campo=campos[n][0],data=fila[n])
                    else:
                        fila_expresion =  u"""{} \"{nombre_campo}\"={data} """.format(fila_expresion ,nombre_campo=campos[n][0], data=fila[n])
                else:
                    if campos[n][1]=="TEXT":
                        fila_expresion =   u"""{} \"{nombre_campo}\"=\'{data}\' AND """.format(fila_expresion,nombre_campo=campos[n][0],data=fila[n])
                    else:
                        fila_expresion =  u"""{} \"{nombre_campo}\"={data} AND """.format(fila_expresion ,nombre_campo=campos[n][0], data=fila[n])
                n = n + 1

            #where_expression = where_expression + "("+fila_expresion + ") OR "
            where_expression =  u"{} ({}) OR ".format(where_expression,fila_expresion)


        m = m + 1

    return where_expression


def expresion_sql(data,campos):
    m = 0
    where_expression = ""
    cant_campos=len(campos)



    for fila in data:
        if (m + 1) == len(data):
            fila_expresion=""
            n = 0
            for campo in campos:
                if (n+1)==len(campos):
                    if campos[n][1]=="TEXT":
                        fila_expresion = u"""{} {nombre_campo}=\'{data}\'  """.format(fila_expresion,nombre_campo=campos[n][0],data=fila[n])

                    else:
                        fila_expresion = u"""{} {nombre_campo}={data}  """.format(fila_expresion ,nombre_campo=campos[n][0], data=fila[n])

                else:
                    if campos[n][1]=="TEXT":
                        fila_expresion = u"""{} {nombre_campo}=\'{data}\' AND """.format(fila_expresion,nombre_campo=campos[n][0],data=fila[n])
                    else:
                        fila_expresion =  u"""{} {nombre_campo}={data} AND """.format(fila_expresion,nombre_campo=campos[n][0], data=fila[n])
                n=n+1
            #where_expression = where_expression + "("+fila_expresion+")"
            where_expression = u"{} ({})".format(where_expression,fila_expresion)

        else:
            fila_expresion = ""
            n = 0
            for campo in campos:

                if (n+1) == len(campos):
                    if campos[n][1] == "TEXT":
                        fila_expresion =  u"""{} {nombre_campo}=\'{data}\'  """.format(fila_expresion ,nombre_campo=campos[n][0],data=fila[n])
                    else:
                        fila_expresion =  u"""{} {nombre_campo}={data}  """.format(fila_expresion ,nombre_campo=campos[n][0], data=fila[n])
                else:
                    if campos[n][1]=="TEXT":
                        fila_expresion =   u"""{} {nombre_campo}=\'{data}\' AND """.format(fila_expresion,nombre_campo=campos[n][0],data=fila[n])

                    else:
                        fila_expresion =  u"""{} {nombre_campo}={data} AND """.format(fila_expresion ,nombre_campo=campos[n][0], data=fila[n])
                n = n + 1

            #where_expression = where_expression + "("+fila_expresion + ") OR "
            where_expression =  u"{} ({}) OR ".format(where_expression,fila_expresion)


        m = m + 1

    return where_expression


def crear_fraseo(texto,tamanio_max):
    texto="OBSERVACIONES: "+texto
    limite = tamanio_max
    tamanio_frase = len(texto)
    pos_ini = 0
    posiciones = []
    obs_1_temp = texto
    obs1_final = ""
    #return obs_1_temp
    while len(obs_1_temp) > limite:
        pos_salto = 0

        try:
            while True:
                # print obs_1_temp[pos_ini:(pos_ini + limite)]
                pos_salto = obs_1_temp[pos_ini:(pos_ini + limite)].index(' ', pos_salto + 1)
                #        #print str(pos_salto)
        except ValueError:
            "fin"
        # print obs_1_temp[pos_ini:(pos_ini+limite)]
        # print (obs_1_temp[pos_ini:(pos_ini + limite)][::-1].replace(' ','\n',1))[::-1][:pos_salto]
        reglon = (obs_1_temp[pos_ini:(pos_ini + limite)][::-1].replace(' ', '\n', 1))[::-1][:pos_salto + 1]
        obs_1_temp = obs_1_temp[(pos_salto+1):]
        obs1_final = obs1_final + reglon
    obs1_final = obs1_final + obs_1_temp
    return obs1_final


def expresion_ubigeos_importacion(where_list):
    m=0
    where_expression = ""
    for x in where_list:
        if (m + 1) == len(where_list):
            where_expression = where_expression + ' "UBIGEO"=%s ' % where_list[m]
        else:
            where_expression = where_expression + ' "UBIGEO"=%s OR' % (where_list[m])

        m = m + 1

    return where_expression



def etiqueta_zona(zona):
    rango_equivalencia=[[1,'A'],[2,'B'],[3,'C'],[4,'D'],[5,'E'],[6,'F'],[7,'G'],[8,'H'],[9,'I'],[10,'J'],[11,'K'],[12,'L'],[13,'M'],[14,'N'],[15,'O'],[16,'P'],[17,'Q']]


    zona_temp=zona[0:3]
    zona_int=int(zona[3:])
    zona_int_eq=""

    for el in rango_equivalencia:
        if (el[0]==zona_int):
            zona_int_eq=el[1]

    zona_temp=zona_temp+str(zona_int_eq)

    return zona_temp

