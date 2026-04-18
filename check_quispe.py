from database import Database

db = Database()
with db.get_cursor() as cursor:
    cursor.execute("""
        SELECT id, nombre, apellido FROM miembros 
        WHERE nombre LIKE '%Quispe%' OR nombre LIKE '%Ailín%' 
           OR apellido LIKE '%Quispe%' OR apellido LIKE '%Ailín%' 
        LIMIT 10
    """)
    miembros = cursor.fetchall()
    for m in miembros:
        print(f'ID: {m["id"]}, Nombre: [{m["nombre"]}], Apellido: [{m["apellido"]}]')
