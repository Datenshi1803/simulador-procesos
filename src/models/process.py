"""
Modelo de datos para procesos del sistema.
"""
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Process:
    """Clase que representa un proceso en el sistema."""
    pid: int
    name: str
    state: str = 'NEW'
    total_burst: int = 0
    remaining_burst: int = 0
    priority: int = 0  # Prioridad del proceso (0=más alta, mayor número=menor prioridad)
    parent_pid: Optional[int] = None
    children: List[int] = field(default_factory=list)
    
    # Métricas de tiempo
    created_tick: int = 0
    start_tick: Optional[int] = None
    end_tick: Optional[int] = None
    
    # Contadores
    blocked_count: int = 0
    preempt_count: int = 0
    io_remaining: int = 0
    
    # Estados de espera
    waiting_for_child: bool = False
    reaped: bool = False
    
    def get_turnaround_time(self) -> Optional[int]:
        """Calcula el turnaround time del proceso."""
        if self.end_tick is not None:
            return self.end_tick - self.created_tick
        return None
    
    def get_waiting_time(self) -> Optional[int]:
        """Calcula el waiting time del proceso."""
        if self.start_tick is not None and self.end_tick is not None:
            return self.get_turnaround_time() - self.total_burst
        return None
    
    def is_finished(self) -> bool:
        """Verifica si el proceso ha terminado."""
        return self.state in ['TERMINATED', 'ZOMBIE']
