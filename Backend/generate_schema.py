from eralchemy2 import render_er
from models import Base, Questionnaire, SubmissionRecord
import os

def generate_diagram():
    print("Generando diagrama de base de datos...")
    
    try:
        # Opción A: Generar desde los modelos de Python (Recomendado)
        # Esto usa la estructura definida en tu código
        render_er(Base, 'schema_from_code.png')
        print("✅ Diagrama generado: schema_from_code.png")
        
    except ImportError as e:
        print(f"❌ Error: Necesitas instalar Graphviz. {e}")
    except Exception as e:
        print(f"❌ Error generando desde código: {e}")

    try:
        # Opción B: Generar desde el archivo de base de datos existente
        # Esto usa lo que realmente está guardado en el archivo .db
        db_path = 'sqlite:///questionnaires.db'
        render_er(db_path, 'schema_from_db.png')
        print("✅ Diagrama generado: schema_from_db.png")
        
    except Exception as e:
        print(f"❌ Error generando desde DB: {e}")

if __name__ == '__main__':
    generate_diagram()