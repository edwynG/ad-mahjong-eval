import sys
import time
from mpi4py import MPI
from src.parser import process_play, get_sort_key


def main():
    """
    Función principal donde configuramos MPI para trabajar en paralelo.
    """
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    start_time = time.time()
    
    lines = []
    if rank == 0:
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        clean_line = line.strip()
                        if clean_line:
                            lines.append(clean_line)
            except FileNotFoundError:
                print(f"Error: Archivo {input_file} no encontrado.")
                comm.Abort(1)
        else:
            print("Uso: mpiexec -n <procesos> python main.py <archivo_entrada>")
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
    
    # Procesar jugadas locales
    local_results = [process_play(line) for line in local_lines]
            
    # Recolectar resultados: Todos devuelven su trabajo al Raíz (Gather)
    gathered_results = comm.gather(local_results, root=0)
    
    if rank == 0:
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Aplanar y ordenar resultados
        flat_results = []
        for res_list in gathered_results:  # type: ignore
            flat_results.extend(res_list)
            
        flat_results.sort(key=get_sort_key)
        
        # Imprimir salida
        for res in flat_results:
            print(res[1])
            
        # Última línea: Fecha inicio | Fecha fin | Tiempo en segundos
        start_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
        end_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
        print(f"{start_str} | {end_str} | {elapsed:.4f}")


if __name__ == '__main__':
    main()

