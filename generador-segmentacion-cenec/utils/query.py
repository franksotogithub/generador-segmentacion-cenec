def to_dict(cursor):
    desc = [col[0] for col in cursor.description]
    datos = cursor.fetchall()
    result_dict = [dict(zip(desc, dato)) for dato in datos]
    return result_dict
