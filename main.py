import os
import sys
import time
from mpi4py import MPI
from src.parser import process_play, get_sort_key

# Asegurar compatibilidad de salida UTF-8 en terminales modernas
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def main():
    """
    Función principal donde configuramos MPI para trabajar en paralelo.
    """
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    start_time = time.time()
    
    lines = []
    output_filename = "salida.txt"

    # En un entorno distribuido, SOLO el proceso Maestro (Rank 0) interactúa con el disco
    # para leer la entrada y coordinar el trabajo, evitando colisiones de I/O.
    if rank == 0:
        input_file = None
        
        # Archivo pasado como argumento por terminal
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
            if len(sys.argv) > 2:
                output_filename = sys.argv[2]
        # Respaldo: Si no se pasa argumento, busca archivos por defecto
        elif os.path.exists("input.txt"):
            input_file = "input.txt"
        elif os.path.exists(os.path.expanduser("~/input.txt")):
            input_file = os.path.expanduser("~/input.txt")

        if input_file and os.path.exists(input_file):
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        clean_line = line.strip()
                        if clean_line:
                            lines.append(clean_line)
            except Exception as e:
                print(f"[Rank 0 - ERROR] No se pudo leer el archivo '{input_file}': {e}")
                comm.Abort(1)
        else:
            print("[Rank 0 - ERROR] No se proporciono archivo de entrada ni se encontro 'input.txt'.")
            print("Uso: mpiexec -n <procesos> python main.py <archivo_entrada> [archivo_salida]")
            comm.Abort(1)
            
    # Dispersar datos: El proceso Raíz (Rank 0) reparte las jugadas entre todos los procesos (Scatter)
    if rank == 0:
        chunks = [[] for _ in range(size)]
        for i, line in enumerate(lines):
            chunks[i % size].append(line)
    else:
        chunks = None
    
    # Repartir las jugadas a cada proceso
    local_lines = comm.scatter(chunks, root=0)
    
    # Procesar jugadas locales en paralelo
    local_results = [process_play(line) for line in local_lines]
            
    # Recolectar resultados: Todos devuelven su trabajo al Raíz (Gather)
    gathered_results = comm.gather(local_results, root=0)
    
    # Únicamente el nodo Maestro (Rank 0) consolida, formatea y escribe el archivo unificado
    if rank == 0:
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Aplanar y ordenar resultados por ID de jugada
        flat_results = []
        for res_list in gathered_results:  # type: ignore
            flat_results.extend(res_list)
            
        flat_results.sort(key=get_sort_key)
        
        # Última línea: Fecha inicio | Fecha fin | Tiempo en segundos
        start_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
        end_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
        time_summary = f"{start_str} | {end_str} | {elapsed:.4f}"

        # Escribir en el archivo de salida unificado
        try:
            with open(output_filename, 'w', encoding='utf-8') as out_f:
                for res in flat_results:
                    out_f.write(res[1] + "\n")
                out_f.write(time_summary + "\n")
                
            print(f"[Rank 0] Resultados guardados exitosamente en: {output_filename}")
        except Exception as e:
            print(f"[Rank 0 - ERROR] No se pudo escribir en el archivo de salida: {e}")


if __name__ == '__main__':
    main()

