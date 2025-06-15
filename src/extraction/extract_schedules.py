import pandas as pd
import re
import json
import os
from typing import Dict, List, Optional

def read_excel_file(file_path: str) -> pd.DataFrame:
    """Lee el archivo Excel y devuelve un DataFrame."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo {file_path} no existe.")
    
    try:
        df = pd.read_excel(file_path)
        expected_columns = ['#', 'Sucursal', 'Dirección', 'Horario de Atención']
        if not all(col in df.columns for col in expected_columns):
            raise ValueError(f"El archivo Excel debe contener las columnas: {expected_columns}")
        return df
    except Exception as e:
        raise ValueError(f"Error al leer el archivo Excel: {str(e)}")

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia el DataFrame eliminando filas con NaN y recortando espacios en blanco."""
    df = df.dropna(subset=['Sucursal', 'Dirección', 'Horario de Atención'])
    df['Sucursal'] = df['Sucursal'].str.strip()
    df['Dirección'] = df['Dirección'].str.strip()
    df['Horario de Atención'] = df['Horario de Atención'].str.strip()
    return df

def parse_schedule(schedule: str) -> Dict[str, Optional[str]]:
    """Parsea el string de horario en un diccionario de días y horas."""
    parsed_schedule: Dict[str, Optional[str]] = {
        "lunes": None,
        "martes": None,
        "miercoles": None,
        "jueves": None,
        "viernes": None,
        "sabado": None,
        "domingo": None
    }
    
    # Divide horarios múltiples (e.g., L-V y S-D)
    schedules = schedule.split(' / ')
    
    for sched in schedules:
        # Coincide con patrones como "L-D: 7:00 a.m. - 10:00 p.m." o "S: 7:00 a.m. - 1:00 p.m."
        match = re.match(r'(\w+-\w+|S|D): (\d{1,2}:\d{2} [ap]\.m\.) - (\d{1,2}:\d{2} [ap]\.m\.)', sched)
        if not match:
            print(f"Advertencia: No se pudo parsear el horario: {sched}")
            continue
        
        days, start_time, end_time = match.groups()
        
        # Mapea rangos de días a días individuales
        day_mapping = {
            'L-D': ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'],
            'L-V': ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
            'L-S': ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'],
            'S-D': ['sabado', 'domingo'],
            'S': ['sabado'],
            'D': ['domingo']
        }
        
        day_list = day_mapping.get(days, [])
        hours = f"{start_time} - {end_time}"
        
        # Asigna las horas a los días correspondientes
        for day in day_list:
            parsed_schedule[day] = hours
    
    return parsed_schedule

def process_data(df: pd.DataFrame) -> List[Dict]:
    """Procesa el DataFrame en una lista de diccionarios para la salida JSON."""
    result = []
    for _, row in df.iterrows():
        branch_info = {
            "sucursal": row['Sucursal'],
            "direccion": row['Dirección'],
            "horario": parse_schedule(row['Horario de Atención'])
        }
        result.append(branch_info)
    return result

def save_to_json(data: List[Dict], output_file: str) -> None:
    """Guarda los datos procesados en un archivo JSON."""
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Datos guardados exitosamente en {output_file}")
    except Exception as e:
        raise IOError(f"Error al guardar el archivo JSON: {str(e)}")

if __name__ == "__main__":
    try:
        # Define las rutas de los archivos de entrada y salida
        input_file = "data/raw/Horarios.xlsx"
        output_file = "data/processed/cleaned_horarios.json"
        
        # Lee y limpia los datos
        df = read_excel_file(input_file)
        df = clean_dataframe(df)
        
        # Procesa los datos
        processed_data = process_data(df)
        
        # Guarda en JSON
        save_to_json(processed_data, output_file)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)