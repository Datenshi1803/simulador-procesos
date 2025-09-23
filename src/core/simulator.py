"""
Motor principal de simulación de procesos.
"""
import random
from collections import deque
from typing import Dict, List, Optional, Tuple
from ..models.process import Process
from .scheduler import PriorityScheduler

class SimulatorEngine:
    """Motor de simulación que maneja la lógica de estados de procesos."""
    
    def __init__(self):
        self.tick = 0
        self.pid_counter = 1
        self.process_table: Dict[int, Process] = {}
        self.scheduler = PriorityScheduler()
        self.blocked_list = []
        self.zombie_list = []
        
        # Métricas
        self.cpu_busy_ticks = 0
        self.idle_ticks = 0
        
        # Configuración
        self.p_block = 0.1  # Probabilidad de bloqueo
        self.p_create = 0.05  # Probabilidad de auto-crear
        self.auto_reap_after = 10  # Ticks para auto-reap
        
        # Logs
        self.event_logs = deque(maxlen=50)
        
        # Crear proceso init (PID 0)
        self._create_init_process()
    
    def _create_init_process(self):
        """Crea el proceso init (PID 0) que adopta procesos huérfanos."""
        init_process = Process(
            pid=0,
            name="init",
            state="RUNNING",
            total_burst=999999,
            remaining_burst=999999,
            priority=0,  # Máxima prioridad
            created_tick=0
        )
        self.process_table[0] = init_process
        self.log_event(f"Proceso init (PID 0) creado con prioridad máxima")
    
    def create_process(self, name: str = None, burst: int = None, parent_pid: int = None, priority: int = None) -> int:
        """Crea un nuevo proceso en estado NEW."""
        pid = self.pid_counter
        self.pid_counter += 1
        
        if name is None:
            name = f"P{pid}"
        if burst is None:
            burst = random.randint(5, 15)
        if priority is None:
            # Asignar prioridad aleatoria: 0-2 alta, 3-5 media, 6-8 baja, 9 muy baja
            priority = random.randint(0, 8)
        
        process = Process(
            pid=pid,
            name=name,
            state='NEW',
            total_burst=burst,
            remaining_burst=burst,
            priority=priority,
            parent_pid=parent_pid,
            created_tick=self.tick
        )
        
        self.process_table[pid] = process
        
        # Agregar como hijo al padre
        if parent_pid and parent_pid in self.process_table:
            self.process_table[parent_pid].children.append(pid)
        
        self.log_event(f"Proceso {name} (PID {pid}) creado con burst {burst}, prioridad {priority}")
        return pid
    
    def move_new_to_ready(self):
        """Mueve todos los procesos NEW a READY."""
        moved_count = 0
        for pid, process in self.process_table.items():
            if process.state == 'NEW':
                process.state = 'READY'
                self.scheduler.add_to_ready(pid, self.process_table)
                moved_count += 1
                self.log_event(f"Proceso {process.name} (PID {pid}) NEW -> READY (prioridad {process.priority})")
        return moved_count
    
    def force_block_process(self, pid: int, io_time: int = None) -> bool:
        """Fuerza el bloqueo de un proceso."""
        if pid not in self.process_table or pid == 0:  # No bloquear init
            return False
        
        process = self.process_table[pid]
        if process.state not in ['READY', 'RUNNING']:
            return False
        
        if io_time is None:
            io_time = random.randint(3, 8)
        
        # Liberar CPU si estaba corriendo
        if self.scheduler.current_running_pid == pid:
            self.scheduler.current_running_pid = None
            self.scheduler.current_quantum_used = 0
        
        # Remover de ready queue
        self.scheduler.remove_from_ready(pid)
        
        # Marcar como bloqueado
        process.state = 'BLOCKED'
        process.io_remaining = io_time
        process.blocked_count += 1
        self.blocked_list.append(pid)
        
        self.log_event(f"Proceso {process.name} (PID {pid}) forzado a BLOCKED por {io_time} ticks")
        return True
    
    def force_terminate_process(self, pid: int) -> bool:
        """Fuerza la terminación de un proceso."""
        if pid not in self.process_table or pid == 0:  # No terminar init
            return False
        
        process = self.process_table[pid]
        if process.state == 'TERMINATED':
            return False
        
        # Liberar CPU si estaba corriendo
        if self.scheduler.current_running_pid == pid:
            self.scheduler.current_running_pid = None
            self.scheduler.current_quantum_used = 0
        
        # Remover de colas
        self._remove_from_queues(pid)
        
        # Marcar como terminado
        process.remaining_burst = 0
        process.end_tick = self.tick
        
        # Verificar si debe ser zombie
        if process.parent_pid and process.parent_pid in self.process_table:
            parent = self.process_table[process.parent_pid]
            if not parent.waiting_for_child:
                process.state = 'ZOMBIE'
                self.zombie_list.append(pid)
                self.log_event(f"Proceso {process.name} (PID {pid}) terminado -> ZOMBIE")
            else:
                process.state = 'TERMINATED'
                process.reaped = True
                self.log_event(f"Proceso {process.name} (PID {pid}) terminado -> TERMINATED")
        else:
            process.state = 'TERMINATED'
            self.log_event(f"Proceso {process.name} (PID {pid}) terminado -> TERMINATED")
        
        return True
    
    def wait_for_child(self, parent_pid: int) -> List[int]:
        """Implementa la llamada wait() para reapear procesos zombie."""
        if parent_pid not in self.process_table:
            return []
        
        parent = self.process_table[parent_pid]
        reaped_children = []
        
        # Buscar hijos zombie
        for child_pid in parent.children[:]:  # Copia para modificar durante iteración
            if child_pid in self.process_table:
                child = self.process_table[child_pid]
                if child.state == 'ZOMBIE':
                    child.state = 'TERMINATED'
                    child.reaped = True
                    if child_pid in self.zombie_list:
                        self.zombie_list.remove(child_pid)
                    reaped_children.append(child_pid)
                    self.log_event(f"Proceso {child.name} (PID {child_pid}) reapeado por padre {parent.name}")
        
        return reaped_children
    
    def _remove_from_queues(self, pid: int):
        """Remueve un proceso de todas las colas."""
        self.scheduler.remove_from_ready(pid)
        if pid in self.blocked_list:
            self.blocked_list.remove(pid)
        if pid in self.zombie_list:
            self.zombie_list.remove(pid)
    
    def tick_simulation(self):
        """Ejecuta un tick de simulación."""
        self.tick += 1
        
        # 1. Gestionar procesos bloqueados
        self._handle_blocked_processes()
        
        # 2. Mover NEW a READY automáticamente
        self.move_new_to_ready()
        
        # 3. Scheduler Round-Robin
        self._schedule_processes()
        
        # 4. Auto-reap zombies si está configurado
        if self.auto_reap_after > 0:
            self._auto_reap_zombies()
    
    def _handle_blocked_processes(self):
        """Maneja los procesos bloqueados."""
        unblocked = []
        for pid in self.blocked_list[:]:  # Copia para modificar durante iteración
            if pid in self.process_table:
                process = self.process_table[pid]
                if process.io_remaining > 0:
                    process.io_remaining -= 1
                if process.io_remaining == 0:
                    process.state = 'READY'
                    self.scheduler.add_to_ready(pid, self.process_table)
                    unblocked.append(pid)
                    self.log_event(f"Proceso {process.name} (PID {pid}) desbloqueado -> READY (prioridad {process.priority})")        # Remover de blocked_list
        for pid in unblocked:
            self.blocked_list.remove(pid)
    
    def _schedule_processes(self):
        """Implementa el scheduler Round-Robin."""
        # Si no hay proceso corriendo y hay procesos en ready
        if self.scheduler.current_running_pid is None:
            next_pid = self.scheduler.get_next_process()
            if next_pid and next_pid in self.process_table:
                process = self.process_table[next_pid]
                self.scheduler.set_running(next_pid, self.process_table)
                
                if process.start_tick is None:
                    process.start_tick = self.tick
                
                self.log_event(f"Proceso {process.name} (PID {next_pid}) ejecutándose")
        
        # Ejecutar proceso actual
        if self.scheduler.current_running_pid is not None:
            self._execute_current_process()
        else:
            self.idle_ticks += 1
    
    def _execute_current_process(self):
        """Ejecuta el proceso actual por un sub-tick."""
        pid = self.scheduler.current_running_pid
        if pid not in self.process_table:
            self.scheduler.current_running_pid = None
            return
        
        process = self.process_table[pid]
        self.cpu_busy_ticks += 1
        self.scheduler.tick(self.process_table)  # Pasar process_table
        
        # Decrementar burst
        process.remaining_burst -= 1
        
        # Verificar si el proceso termina
        if process.remaining_burst <= 0:
            process.end_tick = self.tick
            self.scheduler.current_running_pid = None
            self.scheduler.current_quantum_used = 0
            
            # Verificar si debe ser zombie
            if process.parent_pid and process.parent_pid in self.process_table:
                parent = self.process_table[process.parent_pid]
                if not parent.waiting_for_child:
                    process.state = 'ZOMBIE'
                    self.zombie_list.append(pid)
                    self.log_event(f"Proceso {process.name} (PID {pid}) terminado -> ZOMBIE")
                else:
                    process.state = 'TERMINATED'
                    process.reaped = True
                    self.log_event(f"Proceso {process.name} (PID {pid}) terminado -> TERMINATED")
            else:
                process.state = 'TERMINATED'
                self.log_event(f"Proceso {process.name} (PID {pid}) terminado -> TERMINATED")
            return
        
        # Verificar bloqueo aleatorio
        if random.random() < self.p_block:
            io_time = random.randint(2, 5)
            process.state = 'BLOCKED'
            process.io_remaining = io_time
            process.blocked_count += 1
            self.blocked_list.append(pid)
            self.scheduler.current_running_pid = None
            self.scheduler.current_quantum_used = 0
            self.log_event(f"Proceso {process.name} (PID {pid}) bloqueado aleatoriamente por {io_time} ticks")
            return
        
        # Verificar preempción por quantum
        self.scheduler.preempt_current(self.process_table)
        if self.scheduler.current_running_pid != pid:  # Fue preemptado
            self.log_event(f"Proceso {process.name} (PID {pid}) preemptado -> READY")
    
    def _auto_reap_zombies(self):
        """Auto-reapea zombies después de cierto tiempo."""
        for pid in self.zombie_list[:]:  # Copia para modificar durante iteración
            if pid in self.process_table:
                process = self.process_table[pid]
                zombie_age = self.tick - (process.end_tick or 0)
                if zombie_age >= self.auto_reap_after:
                    process.state = 'TERMINATED'
                    process.reaped = True
                    self.zombie_list.remove(pid)
                    self.log_event(f"Proceso {process.name} (PID {pid}) auto-reapeado")
    
    def log_event(self, message: str):
        """Registra un evento en el log."""
        timestamp = f"[T{self.tick:03d}]"
        self.event_logs.append(f"{timestamp} {message}")
    
    def get_metrics(self) -> Dict:
        """Obtiene las métricas del sistema."""
        total_processes = len(self.process_table)
        running_processes = sum(1 for p in self.process_table.values() if p.state == 'RUNNING')
        ready_processes = sum(len(queue) for queue in self.scheduler.priority_queues.values())
        blocked_processes = len(self.blocked_list)
        zombie_processes = len(self.zombie_list)
        terminated_processes = sum(1 for p in self.process_table.values() if p.state == 'TERMINATED')
        
        # Información de colas de prioridad
        priority_queues_info = self.scheduler.get_ready_queue_info()
        priority_info = ", ".join([f"P{p}:{c}" for p, c in sorted(priority_queues_info.items()) if c > 0])
        if not priority_info:
            priority_info = "Vacía"
        
        # Calcular CPU utilization
        total_ticks = max(1, self.tick)
        cpu_utilization = (self.cpu_busy_ticks / total_ticks) * 100
        
        # Calcular turnaround promedio
        finished_processes = [p for p in self.process_table.values() if p.is_finished() and p.pid != 0]
        if finished_processes:
            turnaround_times = [p.get_turnaround_time() for p in finished_processes if p.get_turnaround_time() is not None]
            avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
            
            waiting_times = [p.get_waiting_time() for p in finished_processes if p.get_waiting_time() is not None]
            avg_waiting = sum(waiting_times) / len(waiting_times) if waiting_times else 0
        else:
            avg_turnaround = 0
            avg_waiting = 0
        
        return {
            'tick': self.tick,
            'total_processes': total_processes,
            'running': running_processes,
            'ready': ready_processes,
            'priority_info': priority_info,
            'blocked': blocked_processes,
            'zombie': zombie_processes,
            'terminated': terminated_processes,
            'cpu_utilization': cpu_utilization,
            'context_switches': self.scheduler.context_switches,
            'avg_turnaround': avg_turnaround,
            'avg_waiting': avg_waiting
        }
    
    def reset(self):
        """Reinicia el simulador."""
        self.tick = 0
        self.pid_counter = 1
        self.process_table.clear()
        self.scheduler.reset()
        self.blocked_list.clear()
        self.zombie_list.clear()
        self.cpu_busy_ticks = 0
        self.idle_ticks = 0
        self.event_logs.clear()
        self._create_init_process()
    
    def set_quantum(self, quantum: int):
        """Establece el quantum del scheduler."""
        self.scheduler.quantum = max(1, quantum)
    
    def get_process_tree(self) -> Dict:
        """Obtiene el árbol de procesos."""
        tree = {}
        for pid, process in self.process_table.items():
            if process.parent_pid is None or process.parent_pid not in self.process_table:
                tree[pid] = self._build_subtree(pid)
        return tree
    
    def _build_subtree(self, pid: int) -> Dict:
        """Construye un subárbol de procesos."""
        if pid not in self.process_table:
            return {}
        
        process = self.process_table[pid]
        subtree = {
            'process': process,
            'children': {}
        }
        
        for child_pid in process.children:
            subtree['children'][child_pid] = self._build_subtree(child_pid)
        
        return subtree
