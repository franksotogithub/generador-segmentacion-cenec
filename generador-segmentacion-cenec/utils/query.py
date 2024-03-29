# -*- coding: utf-8 -*-
def to_dict(cursor):
    desc = [col[0] for col in cursor.description]
    datos = cursor.fetchall()
    result_dict = [dict(zip(desc, dato)) for dato in datos]
    return result_dict
## estado -1 no se procesa en la etapa
## estado 0 no proceso y listo para procesar
## estado 2 en proceso
##
def obtener_zonas(cursor,cnn,cod_oper='01',cant_zonas=100):
    query_zonas = """
            begin
                declare @table TABLE(
                ubigeo varchar(6),
                zona varchar(6)
                );
                
                select top {cant_zonas} a.UBIGEO,a.ZONA from sde.TB_OPER_ZONA a
                where ISNULL(a.flag_proc_segm,0)=0 AND a.COD_OPER={cod_oper}
                order by 1,2
                
                insert @table
                select top {cant_zonas}  a.UBIGEO,a.ZONA from sde.TB_OPER_ZONA a
                where ISNULL(a.flag_proc_segm,0) = 0 AND a.COD_OPER={cod_oper}  
                order by 1,2
                
                update  a
                set a.flag_proc_segm = 2
                from sde.TB_OPER_ZONA a
                where ubigeo+zona in (select UBIGEO+ZONA from @table)  AND a.COD_OPER={cod_oper}
                  
            end
    """.format(cant_zonas=cant_zonas,cod_oper=cod_oper)
    zonas = to_dict(cursor.execute(query_zonas))
    cnn.commit()
    return zonas




def actualizar_flag_proc_segm(cursor,cnn,ubigeo,zona,flag,equipo='',error=''):
    QUERY_ACTUALIZAR_FLAG_PROC_SEGM = """
    begin
    update a
    set a.flag_proc_segm={flag},a.fec_proc_segm=GETDATE()
    from [sde].[TB_OPER_ZONA] a
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

def obtener_sedes(cursor,cod_oper='01'):
    query_sedes="""
    select distinct a.codsede 
    from [sde].[SEGM_RUTA_EMP_PERIODO] a  
    WHERE a.COD_OPER='{cod_oper}' 
    order by 1
    """.format(cod_oper= cod_oper)
    sedes = to_dict(cursor.execute(query_sedes))
    return sedes

def obtener_brigada_periodo(cursor,cod_oper='01',cant=1):

    query_sedes="""
                declare @table TABLE(cod_oper varchar(2), periodo int,codsede varchar(2),brigada varchar(3) )
                
                select top {cant} cod_oper , periodo,codsede ,brigada,cod_oper + cast (periodo as varchar ) + codsede+ brigada pk   from sde.SEGM_BRIGADA_PERIODO a
                where ISNULL(a.proc_croquis,0)=0 and a.cod_oper = {cod_oper} 
                order by 1
                
                insert @table
                select top {cant} cod_oper , periodo,codsede ,brigada from sde.SEGM_BRIGADA_PERIODO a
                where ISNULL(a.proc_croquis,0)=0 and a.cod_oper = {cod_oper} 
                order by 1

                update  a
                set a.proc_croquis = 2
                from sde.SEGM_BRIGADA_PERIODO a
                where cod_oper + cast (periodo as varchar ) + codsede+ brigada in 
                (select distinct cod_oper + cast (periodo as varchar ) + codsede+ brigada from @table) 
    
    """.format(cod_oper = cod_oper , cant = cant)
    sedes = to_dict(cursor.execute(query_sedes))
    return sedes


def actualizar_flag_proc_croquis_brigada_periodo(cursor,cnn,pk,flag):
    QUERY_ACTUALIZAR_FLAG_PROC_SEGM = """
    begin
    update a
    set a.proc_croquis={flag}
    from sde.SEGM_BRIGADA_PERIODO  a
    where cod_oper + cast (periodo as varchar ) + codsede+ brigada ='{pk}'
    end
    """.format(pk=pk,flag=flag)
    cursor.execute(QUERY_ACTUALIZAR_FLAG_PROC_SEGM)
    cnn.commit()
