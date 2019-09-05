def to_dict(cursor):
    desc = [col[0] for col in cursor.description]
    datos = cursor.fetchall()
    result_dict = [dict(zip(desc, dato)) for dato in datos]
    return result_dict

def obtener_zonas(cursor,cnn,cant_zonas):
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
    """.format(cant_zonas=cant_zonas)
    zonas = to_dict(cursor.execute(query_zonas))
    cnn.commit()
    return zonas


def actualizar_flag_proc_segm(cursor,cnn,ubigeo,zona,flag,equipo='',error=''):
    QUERY_ACTUALIZAR_FLAG_PROC_SEGM = """
    begin
    update a
    set a.flag_proc_segm={flag},a.fec_proc_segm=GETDATE(),a.equipo_proc_segm='{equipo}',a.error='{error}'
    from [dbo].[TB_ZONA] a
    where a.ubigeo='{ubigeo}' and a.zona='{zona}'
    end
    """.format(ubigeo=ubigeo,zona=zona,flag=flag,equipo=equipo,error=error)

    print 'QUERY_ACTUALIZAR_FLAG_PROC_SEGM>>>',QUERY_ACTUALIZAR_FLAG_PROC_SEGM
    cursor.execute(QUERY_ACTUALIZAR_FLAG_PROC_SEGM)
    cnn.commit()



