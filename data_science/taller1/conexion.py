import string
from sqlalchemy import create_engine, text
import psycopg2
import pandas as pd
import io
import os
from dotenv import load_dotenv

load_dotenv()

# Conexión a la base de datos
engine = create_engine('postgresql+psycopg2://root:root@localhost:5432/airQuality')


def new_model(df, name_model) -> None:
    """
    Crea una nueva tabla en la base de datos a partir de un DataFrame.
    Si la tabla existe, la elimina antes de crearla nuevamente.
    El campo 'id' se agrega automáticamente y se define como PRIMARY KEY.
    """
    # Asegurar un índice ID secuencial
    df = df.rename_axis('id').reset_index()
    df['id'] = df.index + 1

    # Conexión directa
    conn = engine.raw_connection()
    cur = conn.cursor()

    # Crear la tabla vacía con el esquema del DataFrame
    df.head(0).to_sql(name_model, engine, if_exists='replace', index=False)

    # Insertar los datos usando COPY (más rápido que inserts)
    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    cur.copy_from(output, name_model, null="")

    # Agregar PRIMARY KEY al campo 'id'
    cur.execute(f"ALTER TABLE {name_model} ADD PRIMARY KEY (id);")
    print(f"Tabla '{name_model}' creada con éxito.")
    conn.commit()
    conn.close()



def add_foreign_key(child_table: str, child_column: str, parent_table: str, parent_column: str, constraint_name: str = None) -> None:
    """
    Agrega una clave foránea entre dos tablas existentes.

    child_table: tabla hija que contendrá la clave foránea.
    child_column: columna en la tabla hija que será la clave foránea.
    parent_table: tabla padre a la que apunta la clave foránea.
    parent_column: columna en la tabla padre que se referencia.
    constraint_name: (opcional) nombre del constraint; si no se da, se genera automáticamente.
    """

    if not constraint_name:
        constraint_name = f"fk_{child_table}_{child_column}_{parent_table}_{parent_column}"

    query = text(f"""
        ALTER TABLE {child_table}
        ADD CONSTRAINT {constraint_name}
        FOREIGN KEY ({child_column})
        REFERENCES {parent_table} ({parent_column})
        ON DELETE CASCADE
        ON UPDATE CASCADE;
    """)

    try:
        with engine.begin() as conn:
            conn.execute(query)
        print(f"Foreign key '{constraint_name}' creada entre {child_table}.{child_column} → {parent_table}.{parent_column}")
    except Exception as e:
        print(f"Error al crear la foreign key: {e}")
