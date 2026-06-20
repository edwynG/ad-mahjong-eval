import sys
import time
from mpi4py import MPI
from parser import decode_play
from mahjong_rules import classify_group
from scorer import evaluate_hand

def main():
    """
    Función principal donde configuramos MPI para trabajar en paralelo
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
    local_lines = []
    if rank == 0:
        chunks = [[] for _ in range(size)]
        for i, line in enumerate(lines):
            chunks[i % size].append(line)
    else:
        chunks = None
    
    # reparte las jugadas a cada proceso
    local_lines = comm.scatter(chunks, root=0)
    
    local_results = []
    for line in local_lines:
        try:
            parsed = decode_play(line)
            parsed['visual'] = line
            # Parseamos cada grupo en detalle
            groups_details = []
            for g in parsed['groups']:
                detailed_group = classify_group(g)
                groups_details.append(detailed_group)
                
            parsed['groups_details'] = groups_details
            
            # Evaluamos la mano completa
            score_data = evaluate_hand(parsed)
            
            # Formato de salida: # Visual Completo | Cuenta Base | Dobles | Total | Estilo de Mano | [Historia/log]
            res_str = f"{line} | {score_data['base']} | {score_data['dobles']} | {score_data['total']} | {score_data['estilo']} | {score_data['log']}"
            local_results.append((parsed['id'], res_str))
        except Exception as e:
            local_results.append((-1, f"{line} | 0 | 0 | 0 | ERROR | ['{str(e)}']"))
            
    # Recolectar resultados: Todos devuelven su trabajo al Raíz (Gather)
    gathered_results = comm.gather(local_results, root=0)
    
    if rank == 0:
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Aplanar y ordenar resultados
        flat_results = []
        for res_list in gathered_results: # type: ignore
            flat_results.extend(res_list)
            
        def get_sort_key(result_item):
            """
            Función auxiliar para ordenar los resultados por su ID
            """
            item_id = result_item[0]
            if str(item_id).isdigit() and int(item_id) != -1:
                return int(item_id)
            else:
                return float('inf')
                
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
