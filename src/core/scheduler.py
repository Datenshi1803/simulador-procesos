"""
Scheduler con Prioridades para el simulador de procesos.
"""
import random
from collections import deque, defaultdict
from typing import Dict, List, Optional, Tuple
from ..models.process import Process

class PriorityScheduler:
    """Implementa el algoritmo de scheduling con Prioridades + Round-Robin por nivel."""
    
    def __init__(self, quantum: int = 3):
        self.quantum = quantum
        # Diccionario de colas por prioridad (0 = mayor prioridad)
        self.priority_queues: Dict[int, deque] = defaultdict(deque)
        self.current_running_pid: Optional[int] = None
        self.current_quantum_used = 0
        self.context_switches = 0
        
        # Configuración de prioridades
        self.max_priority_levels = 10  # 0-9, donde 0 es la más alta
        self.priority_boost_interval = 20  # Cada cuántos ticks hacer boost de prioridad
        self.priority_boost_counter = 0
        
    def add_to_ready(self, pid: int, process_table: Dict[int, Process] = None):
        """Agrega un proceso a la cola de listos según su prioridad."""
        if process_table and pid in process_table:
            priority = process_table[pid].priority
            # Asegurar que la prioridad esté en rango válido
            priority = max(0, min(priority, self.max_priority_levels - 1))
            
            if pid not in self.priority_queues[priority]:
                self.priority_queues[priority].append(pid)
        else:
            # Fallback: agregar a prioridad media si no hay tabla de procesos
            if pid not in self.priority_queues[5]:
                self.priority_queues[5].append(pid)
    
    def remove_from_ready(self, pid: int):
        """Remueve un proceso de todas las colas de prioridad."""
        for priority, queue in self.priority_queues.items():
            if pid in queue:
                temp_queue = deque()
                while queue:
                    current_pid = queue.popleft()
                    if current_pid != pid:
                        temp_queue.append(current_pid)
                self.priority_queues[priority] = temp_queue
                break
    
    def get_next_process(self) -> Optional[int]:
        """Obtiene el siguiente proceso a ejecutar (mayor prioridad primero)."""
        # Buscar en orden de prioridad (0 = más alta)
        for priority in sorted(self.priority_queues.keys()):
            if self.priority_queues[priority]:
                return self.priority_queues[priority].popleft()
        return None
    
    def preempt_current(self, process_table: Dict[int, Process]) -> bool:
        """Preempta el proceso actual si es necesario."""
        if self.current_running_pid is None:
            return False
        
        # Verificar si hay proceso de mayor prioridad esperando
        current_process = process_table.get(self.current_running_pid)
        if current_process:
            current_priority = current_process.priority
            
            # Buscar procesos de mayor prioridad en ready
            for priority in range(0, current_priority):
                if self.priority_queues[priority]:
                    # Hay un proceso de mayor prioridad esperando
                    self._preempt_process(current_process, process_table)
                    return True
        
        # Preempción por quantum agotado
        if self.current_quantum_used >= self.quantum:
            if current_process:
                self._preempt_process(current_process, process_table)
                return True
        
        return False
    
    def _preempt_process(self, process: Process, process_table: Dict[int, Process]):
        """Preempta el proceso actual."""
        process.state = 'READY'
        process.preempt_count += 1
        self.add_to_ready(process.pid, process_table)
        self.current_running_pid = None
        self.current_quantum_used = 0
        self.context_switches += 1
    
    def set_running(self, pid: int, process_table: Dict[int, Process]) -> bool:
        """Establece un proceso como el actual en ejecución."""
        if pid in process_table:
            process = process_table[pid]
            process.state = 'RUNNING'
            self.current_running_pid = pid
            self.current_quantum_used = 0
            self.context_switches += 1
            return True
        return False
    
    def tick(self, process_table: Dict[int, Process] = None):
        """Incrementa el quantum usado y maneja aging de prioridades."""
        if self.current_running_pid is not None:
            self.current_quantum_used += 1
        
        # Aging: incrementar prioridad de procesos que esperan mucho
        self.priority_boost_counter += 1
        if self.priority_boost_counter >= self.priority_boost_interval:
            self._priority_aging(process_table)
            self.priority_boost_counter = 0
    
    def _priority_aging(self, process_table: Dict[int, Process]):
        """Implementa aging para evitar starvation."""
        if not process_table:
            return
            
        # Buscar procesos en colas de baja prioridad y moverlos a mayor prioridad
        for priority in range(self.max_priority_levels - 1, 0, -1):  # De menor a mayor prioridad
            if self.priority_queues[priority]:
                # Mover algunos procesos a prioridad más alta
                queue = self.priority_queues[priority]
                temp_queue = deque()
                
                while queue:
                    pid = queue.popleft()
                    if pid in process_table:
                        process = process_table[pid]
                        # Mover a prioridad más alta (decrementar número)
                        if random.random() < 0.3:  # 30% de probabilidad
                            new_priority = max(0, priority - 1)
                            process.priority = new_priority
                            self.priority_queues[new_priority].append(pid)
                        else:
                            temp_queue.append(pid)
                    else:
                        temp_queue.append(pid)
                
                self.priority_queues[priority] = temp_queue
    
    def adjust_priority(self, pid: int, new_priority: int, process_table: Dict[int, Process]):
        """Ajusta la prioridad de un proceso específico."""
        if pid not in process_table:
            return False
            
        process = process_table[pid]
        old_priority = process.priority
        new_priority = max(0, min(new_priority, self.max_priority_levels - 1))
        
        # Actualizar prioridad en el proceso
        process.priority = new_priority
        
        # Si está en ready, mover a la nueva cola
        if process.state == 'READY':
            self.remove_from_ready(pid)
            self.add_to_ready(pid, process_table)
        
        return True
    
    def get_ready_queue_info(self) -> Dict[int, int]:
        """Obtiene información sobre las colas de prioridad."""
        return {priority: len(queue) for priority, queue in self.priority_queues.items() if queue}
    
    def reset(self):
        """Reinicia el scheduler."""
        self.priority_queues.clear()
        self.current_running_pid = None
        self.current_quantum_used = 0
        self.context_switches = 0
        self.priority_boost_counter = 0

# Mantener el RoundRobinScheduler para compatibilidad
class RoundRobinScheduler(PriorityScheduler):
    """Wrapper para mantener compatibilidad con código existente."""
    
    def __init__(self, quantum: int = 3):
        super().__init__(quantum)
        # En modo Round-Robin, todos los procesos tienen la misma prioridad
        self._round_robin_mode = True
    
    def add_to_ready(self, pid: int, process_table: Dict[int, Process] = None):
        """En modo RR, todos van a la misma cola."""
        if pid not in self.priority_queues[5]:  # Prioridad media
            self.priority_queues[5].append(pid)
