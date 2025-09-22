"""
Scheduler Round-Robin para el simulador de procesos.
"""
import random
from collections import deque
from typing import Dict, List, Optional, Tuple
from ..models.process import Process

class RoundRobinScheduler:
    """Implementa el algoritmo de scheduling Round-Robin."""
    
    def __init__(self, quantum: int = 3):
        self.quantum = quantum
        self.ready_queue = deque()
        self.current_running_pid: Optional[int] = None
        self.current_quantum_used = 0
        self.context_switches = 0
        
    def add_to_ready(self, pid: int):
        """Agrega un proceso a la cola de listos."""
        if pid not in self.ready_queue:
            self.ready_queue.append(pid)
    
    def remove_from_ready(self, pid: int):
        """Remueve un proceso de la cola de listos."""
        if pid in self.ready_queue:
            temp_queue = deque()
            while self.ready_queue:
                current_pid = self.ready_queue.popleft()
                if current_pid != pid:
                    temp_queue.append(current_pid)
            self.ready_queue = temp_queue
    
    def get_next_process(self) -> Optional[int]:
        """Obtiene el siguiente proceso a ejecutar."""
        if self.ready_queue:
            return self.ready_queue.popleft()
        return None
    
    def preempt_current(self, process_table: Dict[int, Process]) -> bool:
        """Preempta el proceso actual si es necesario."""
        if self.current_running_pid is None:
            return False
            
        if self.current_quantum_used >= self.quantum:
            pid = self.current_running_pid
            if pid in process_table:
                process = process_table[pid]
                process.state = 'READY'
                process.preempt_count += 1
                self.add_to_ready(pid)
                self.current_running_pid = None
                self.current_quantum_used = 0
                self.context_switches += 1
                return True
        return False
    
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
    
    def tick(self):
        """Incrementa el quantum usado."""
        if self.current_running_pid is not None:
            self.current_quantum_used += 1
    
    def reset(self):
        """Reinicia el scheduler."""
        self.ready_queue.clear()
        self.current_running_pid = None
        self.current_quantum_used = 0
        self.context_switches = 0
