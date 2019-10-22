# -*- coding: utf-8 -*-
def to_dict(cursor):
    desc = [col[0] for col in cursor.description]
    datos = cursor.fetchall()
    result_dict = [dict(zip(desc, dato)) for dato in datos]
    return result_dict

def obtener_zonas(cursor,cnn,cant_zonas):
    query_zonas = """
            begin
                declare @table TABLE(
                ubigeo varchar(6),
                zona varchar(6)
                );
                
                select top {cant_zonas} a.UBIGEO,a.ZONA from sde.TB_ZONA a
                where a.flag_proc_segm=0 
                order by 1,2
                
                insert @table
                select top {cant_zonas}  a.UBIGEO,a.ZONA from sde.TB_ZONA a
                where a.flag_proc_segm = 0  
                order by 1,2
                
                update  a
                set a.flag_proc_segm = 2
                from sde.TB_ZONA a
                where ubigeo+zona in (select UBIGEO+ZONA from @table) 
                
            end
    """.format(cant_zonas=cant_zonas)
    zonas = to_dict(cursor.execute(query_zonas))
    cnn.commit()
    return zonas




def actualizar_flag_proc_segm(cursor,cnn,ubigeo,zona,flag,equipo='',error=''):
    QUERY_ACTUALIZAR_FLAG_PROC_SEGM = """
    begin
    update a
    set a.flag_proc_segm={flag},a.fec_proc_segm=GETDATE(),a.equipo_proc_segm='{equipo}',a.error='{error}'
    from [sde].[TB_ZONA] a
    where a.ubigeo='{ubigeo}' and a.zona='{zona}' 
    end
    """.format(ubigeo=ubigeo,zona=zona,flag=flag,equipo=equipo,error=error)


    cursor.execute(QUERY_ACTUALIZAR_FLAG_PROC_SEGM)
    cnn.commit()

def obtener_distritos(cursor,cnn,cant=1):
    query_distritos = """
            begin
                declare @table TABLE(
                ubigeo varchar(6)
               
                )
                
                select top {cant} a.UBIGEO from sde.TB_DISTRITO a
                where a.flag_proc_segm=0 
                order by 1
                
                insert @table
                select top {cant}  a.UBIGEO from sde.TB_DISTRITO a
                where a.flag_proc_segm = 0   
                order by 1
                
                update  a
                set a.flag_proc_segm = 2
                from sde.TB_DISTRITO a
                where ubigeo in (select UBIGEO from @table) 

            end
    """.format(cant=cant)
    zonas = to_dict(cursor.execute(query_distritos))
    cnn.commit()
    return zonas


def actualizar_flag_proc_segm_distrito(cursor,cnn,ubigeo,flag,equipo='',error=''):
    QUERY_ACTUALIZAR_FLAG_PROC_SEGM = """
    begin
    update a
    set a.flag_proc_segm={flag},a.fec_proc_segm=GETDATE(),a.equipo_proc_segm='{equipo}',a.error='{error}'
    from [sde].[TB_DISTRITO] a
    where a.ubigeo='{ubigeo}'
    end
    """.format(ubigeo=ubigeo,flag=flag,equipo=equipo,error=error)

    cursor.execute(QUERY_ACTUALIZAR_FLAG_PROC_SEGM)
    cnn.commit()