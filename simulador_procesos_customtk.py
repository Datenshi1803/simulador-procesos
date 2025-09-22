#!/usr/bin/env python3
"""
Simulador de Estados de Procesos con CustomTkinter
==================================================

Un simulador profesional de gestión de procesos que implementa los estados:
NEW, READY, RUNNING, BLOCKED, ZOMBIE, TERMINATED

Autor: Simulador de Procesos v1.0
Fecha: 2025
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass, field
from collections import deque
from typing import Dict, List, Optional, Tuple
import random
import time
import csv
import threading
import queue
from datetime import datetime

# Configuración de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Colores para estados de procesos
STATE_COLORS = {
    'NEW': '#FFD966',        # Amarillo claro
    'READY': '#B6D7A8',      # Verde claro
    'RUNNING': '#9FC5E8',    # Azul/cian
    'BLOCKED': '#E6B8AF',    # Rojo/rosado claro
    'ZOMBIE': '#C27BA0',     # Morado
    'TERMINATED': '#D9D9D9'  # Gris claro
}

@dataclass
class Process:
    """Clase que representa un proceso en el sistema."""
    pid: int
    name: str
    state: str = 'NEW'
    total_burst: int = 0
    remaining_burst: int = 0
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

class SimulatorEngine:
    """Motor de simulación que maneja la lógica de estados de procesos."""
    
    def __init__(self):
        self.tick = 0
        self.pid_counter = 1
        self.process_table: Dict[int, Process] = {}
        self.ready_queue = deque()
        self.blocked_list = []
        self.zombie_list = []
        
        # Métricas
        self.context_switches = 0
        self.cpu_busy_ticks = 0
        self.idle_ticks = 0
        
        # Configuración
        self.quantum = 3
        self.p_block = 0.1  # Probabilidad de bloqueo
        self.p_create = 0.05  # Probabilidad de auto-crear
        self.auto_reap_after = 10  # Ticks para auto-reap
        
        # Estado actual
        self.current_running_pid: Optional[int] = None
        self.current_quantum_used = 0
        
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
            created_tick=0
        )
        self.process_table[0] = init_process
        self.log_event(f"Proceso init (PID 0) creado")
    
    def create_process(self, name: str = None, burst: int = None, parent_pid: int = None) -> int:
        """Crea un nuevo proceso en estado NEW."""
        pid = self.pid_counter
        self.pid_counter += 1
        
        if name is None:
            name = f"P{pid}"
        if burst is None:
            burst = random.randint(5, 15)
        
        process = Process(
            pid=pid,
            name=name,
            state='NEW',
            total_burst=burst,
            remaining_burst=burst,
            parent_pid=parent_pid,
            created_tick=self.tick
        )
        
        self.process_table[pid] = process
        
        # Agregar como hijo al padre
        if parent_pid and parent_pid in self.process_table:
            self.process_table[parent_pid].children.append(pid)
        
        self.log_event(f"Proceso {name} (PID {pid}) creado con burst {burst}")
        return pid
    
    def move_new_to_ready(self):
        """Mueve todos los procesos NEW a READY."""
        moved = 0
        for process in self.process_table.values():
            if process.state == 'NEW':
                process.state = 'READY'
                self.ready_queue.append(process.pid)
                moved += 1
                self.log_event(f"Proceso {process.name} (PID {process.pid}) movido a READY")
        return moved
    
    def force_block_process(self, pid: int, io_time: int = None):
        """Fuerza el bloqueo de un proceso."""
        if pid not in self.process_table:
            return False
        
        process = self.process_table[pid]
        if process.state not in ['READY', 'RUNNING']:
            return False
        
        if io_time is None:
            io_time = random.randint(2, 6)
        
        process.state = 'BLOCKED'
        process.io_remaining = io_time
        process.blocked_count += 1
        
        # Si estaba corriendo, liberar CPU
        if self.current_running_pid == pid:
            self.current_running_pid = None
            self.current_quantum_used = 0
        
        # Remover de ready_queue si estaba ahí
        if pid in self.ready_queue:
            temp_queue = deque()
            while self.ready_queue:
                p = self.ready_queue.popleft()
                if p != pid:
                    temp_queue.append(p)
            self.ready_queue = temp_queue
        
        self.blocked_list.append(pid)
        self.log_event(f"Proceso {process.name} (PID {pid}) bloqueado por {io_time} ticks")
        return True
    
    def force_terminate_process(self, pid: int):
        """Fuerza la terminación de un proceso."""
        if pid not in self.process_table or pid == 0:  # No terminar init
            return False
        
        process = self.process_table[pid]
        if process.state == 'TERMINATED':
            return False
        
        # Liberar CPU si estaba corriendo
        if self.current_running_pid == pid:
            self.current_running_pid = None
            self.current_quantum_used = 0
        
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
        # Remover de ready_queue
        if pid in self.ready_queue:
            temp_queue = deque()
            while self.ready_queue:
                p = self.ready_queue.popleft()
                if p != pid:
                    temp_queue.append(p)
            self.ready_queue = temp_queue
        
        # Remover de blocked_list
        if pid in self.blocked_list:
            self.blocked_list.remove(pid)
        
        # Remover de zombie_list
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
        
        # 5. Auto-crear procesos si está en modo auto
        # (esto se maneja desde la GUI)
    
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
                        self.ready_queue.append(pid)
                        unblocked.append(pid)
                        self.log_event(f"Proceso {process.name} (PID {pid}) desbloqueado -> READY")
        
        # Remover de blocked_list
        for pid in unblocked:
            self.blocked_list.remove(pid)
    
    def _schedule_processes(self):
        """Implementa el scheduler Round-Robin."""
        # Si no hay proceso corriendo y hay procesos en ready
        if self.current_running_pid is None and self.ready_queue:
            # Tomar siguiente proceso de la cola
            pid = self.ready_queue.popleft()
            if pid in self.process_table:
                process = self.process_table[pid]
                process.state = 'RUNNING'
                self.current_running_pid = pid
                self.current_quantum_used = 0
                self.context_switches += 1
                
                if process.start_tick is None:
                    process.start_tick = self.tick
                
                self.log_event(f"Proceso {process.name} (PID {pid}) ejecutándose")
        
        # Ejecutar proceso actual
        if self.current_running_pid is not None:
            self._execute_current_process()
        else:
            self.idle_ticks += 1
    
    def _execute_current_process(self):
        """Ejecuta el proceso actual por un sub-tick."""
        pid = self.current_running_pid
        if pid not in self.process_table:
            self.current_running_pid = None
            return
        
        process = self.process_table[pid]
        self.cpu_busy_ticks += 1
        self.current_quantum_used += 1
        
        # Decrementar burst
        process.remaining_burst -= 1
        
        # Verificar si el proceso termina
        if process.remaining_burst <= 0:
            process.end_tick = self.tick
            self.current_running_pid = None
            self.current_quantum_used = 0
            
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
            self.current_running_pid = None
            self.current_quantum_used = 0
            self.log_event(f"Proceso {process.name} (PID {pid}) bloqueado aleatoriamente por {io_time} ticks")
            return
        
        # Verificar preempción por quantum
        if self.current_quantum_used >= self.quantum:
            process.state = 'READY'
            process.preempt_count += 1
            self.ready_queue.append(pid)
            self.current_running_pid = None
            self.current_quantum_used = 0
            self.context_switches += 1
            self.log_event(f"Proceso {process.name} (PID {pid}) preemptado -> READY")
    
    def _auto_reap_zombies(self):
        """Auto-reapea zombies después de N ticks."""
        for pid in self.zombie_list[:]:  # Copia para modificar
            if pid in self.process_table:
                process = self.process_table[pid]
                if process.end_tick and (self.tick - process.end_tick) >= self.auto_reap_after:
                    process.state = 'TERMINATED'
                    process.reaped = True
                    self.zombie_list.remove(pid)
                    self.log_event(f"Proceso {process.name} (PID {pid}) auto-reapeado")
    
    def log_event(self, message: str):
        """Registra un evento en el log."""
        timestamp = f"Tick {self.tick:04d}"
        self.event_logs.append(f"[{timestamp}] {message}")
    
    def get_metrics(self) -> Dict:
        """Calcula y retorna métricas del sistema."""
        total_processes = len([p for p in self.process_table.values() if p.pid != 0])
        terminated_processes = [p for p in self.process_table.values() 
                              if p.state == 'TERMINATED' and p.pid != 0]
        
        cpu_utilization = (self.cpu_busy_ticks / max(self.tick, 1)) * 100
        
        turnaround_times = []
        waiting_times = []
        
        for process in terminated_processes:
            if process.end_tick and process.created_tick:
                turnaround = process.end_tick - process.created_tick
                turnaround_times.append(turnaround)
                
                # Tiempo de espera = turnaround - tiempo de ejecución
                execution_time = process.total_burst
                waiting_time = turnaround - execution_time
                waiting_times.append(max(0, waiting_time))
        
        return {
            'tick': self.tick,
            'total_processes': total_processes,
            'cpu_utilization': cpu_utilization,
            'context_switches': self.context_switches,
            'zombies_count': len(self.zombie_list),
            'avg_turnaround': sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0,
            'avg_waiting': sum(waiting_times) / len(waiting_times) if waiting_times else 0,
            'ready_queue_size': len(self.ready_queue),
            'blocked_count': len(self.blocked_list)
        }

class ProcessSimulatorGUI:
    """Interfaz gráfica principal del simulador."""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Simulador de Estados de Procesos — Gestión de Estados")
        self.root.geometry("1400x900")
        
        # Motor de simulación
        self.engine = SimulatorEngine()
        
        # Variables de control
        self.auto_mode = tk.BooleanVar(value=False)
        self.is_running = False
        self.speed_var = tk.DoubleVar(value=0.5)
        self.quantum_var = tk.IntVar(value=3)
        self.auto_create_var = tk.BooleanVar(value=False)
        self.seed_var = tk.StringVar(value="42")
        
        # Queue para comunicación con threads
        self.update_queue = queue.Queue()
        
        self._setup_ui()
        self._create_initial_processes()
        self._update_display()
        
        # Configurar seed inicial
        random.seed(42)
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Header
        self._create_header()
        
        # Panel principal (dividido)
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Panel izquierdo (tabla + controles)
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self._create_process_table(left_frame)
        
        # Panel derecho (acciones + métricas)
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="y", padx=5, pady=5)
        
        self._create_action_panel(right_frame)
        self._create_metrics_panel(right_frame)
        
        # Panel inferior (logs)
        self._create_log_panel()
    
    def _create_header(self):
        """Crea el panel de header con controles globales."""
        header = ctk.CTkFrame(self.root)
        header.pack(fill="x", padx=10, pady=5)
        
        # Título
        title = ctk.CTkLabel(header, text="🖥️ Simulador de Estados de Procesos", 
                           font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=10)
        
        # Controles
        controls_frame = ctk.CTkFrame(header)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Fila 1: Controles principales
        row1 = ctk.CTkFrame(controls_frame)
        row1.pack(fill="x", pady=2)
        
        self.start_btn = ctk.CTkButton(row1, text="▶️ Start Auto", command=self._start_auto)
        self.start_btn.pack(side="left", padx=5)
        
        self.pause_btn = ctk.CTkButton(row1, text="⏸️ Pause", command=self._pause_auto)
        self.pause_btn.pack(side="left", padx=5)
        
        self.reset_btn = ctk.CTkButton(row1, text="🔄 Reset", command=self._reset_simulation)
        self.reset_btn.pack(side="left", padx=5)
        
        # Modo
        mode_frame = ctk.CTkFrame(row1)
        mode_frame.pack(side="left", padx=10)
        
        ctk.CTkLabel(mode_frame, text="Modo:").pack(side="left", padx=5)
        self.mode_switch = ctk.CTkSwitch(mode_frame, text="Auto", variable=self.auto_mode)
        self.mode_switch.pack(side="left", padx=5)
        
        # Fila 2: Configuraciones
        row2 = ctk.CTkFrame(controls_frame)
        row2.pack(fill="x", pady=2)
        
        # Quantum
        quantum_frame = ctk.CTkFrame(row2)
        quantum_frame.pack(side="left", padx=5)
        ctk.CTkLabel(quantum_frame, text="Quantum:").pack(side="left")
        self.quantum_spinbox = ctk.CTkEntry(quantum_frame, width=60, textvariable=self.quantum_var)
        self.quantum_spinbox.pack(side="left", padx=5)
        
        # Speed
        speed_frame = ctk.CTkFrame(row2)
        speed_frame.pack(side="left", padx=5)
        ctk.CTkLabel(speed_frame, text="Velocidad:").pack(side="left")
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=0.05, to=2.0, 
                                        variable=self.speed_var, width=100)
        self.speed_slider.pack(side="left", padx=5)
        
        # Auto-create
        self.auto_create_switch = ctk.CTkSwitch(row2, text="Auto-crear", 
                                              variable=self.auto_create_var)
        self.auto_create_switch.pack(side="left", padx=10)
        
        # Seed
        seed_frame = ctk.CTkFrame(row2)
        seed_frame.pack(side="left", padx=5)
        ctk.CTkLabel(seed_frame, text="Seed:").pack(side="left")
        seed_entry = ctk.CTkEntry(seed_frame, width=60, textvariable=self.seed_var)
        seed_entry.pack(side="left", padx=5)
        
        # Botón aplicar seed
        apply_seed_btn = ctk.CTkButton(row2, text="Aplicar Seed", 
                                     command=self._apply_seed, width=80)
        apply_seed_btn.pack(side="left", padx=5)
    
    def _create_process_table(self, parent):
        """Crea la tabla de procesos."""
        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(table_frame, text="📋 Tabla de Procesos", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Crear Treeview con estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores para estados
        for state, color in STATE_COLORS.items():
            style.configure(f"{state}.Treeview", background=color, foreground="black")
        
        columns = ('PID', 'Nombre', 'Estado', 'Restante', 'Total', 'Padre', 
                  'IO_Rem', 'Creado', 'Inicio', 'Fin', '#Bloq', '#Preempt')
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        widths = [50, 80, 80, 70, 60, 60, 60, 60, 60, 60, 50, 70]
        for col, width in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree y scrollbars
        self.tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Bind selección
        self.tree.bind('<<TreeviewSelect>>', self._on_process_select)
    
    def _create_action_panel(self, parent):
        """Crea el panel de acciones."""
        action_frame = ctk.CTkFrame(parent)
        action_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(action_frame, text="🎮 Acciones", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Información del proceso seleccionado
        self.selected_info = ctk.CTkLabel(action_frame, text="Selecciona un proceso")
        self.selected_info.pack(pady=5)
        
        # Botones de acción
        buttons = [
            ("➕ Crear Proceso", self._create_process_dialog),
            ("👶 Crear Hijo", self._create_child_dialog),
            ("🔄 NEW → READY", self._move_new_to_ready),
            ("⏸️ Forzar Bloqueo", self._force_block_dialog),
            ("❌ Forzar Terminar", self._force_terminate_dialog),
            ("👻 Wait (Reap)", self._wait_dialog),
            ("🌳 Ver Árbol", self._show_process_tree),
            ("📊 Tick Manual", self._manual_tick)
        ]
        
        for text, command in buttons:
            btn = ctk.CTkButton(action_frame, text=text, command=command, width=200)
            btn.pack(pady=2)
    
    def _create_metrics_panel(self, parent):
        """Crea el panel de métricas."""
        metrics_frame = ctk.CTkFrame(parent)
        metrics_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(metrics_frame, text="📈 Métricas del Sistema", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Métricas en tiempo real
        self.metrics_text = ctk.CTkTextbox(metrics_frame, height=200, width=300)
        self.metrics_text.pack(fill="both", expand=True, pady=5)
        
        # Colas y listas
        queues_frame = ctk.CTkFrame(metrics_frame)
        queues_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(queues_frame, text="📋 Colas y Estados", 
                   font=ctk.CTkFont(size=14, weight="bold")).pack()
        
        self.queues_text = ctk.CTkTextbox(queues_frame, height=150)
        self.queues_text.pack(fill="both", expand=True, pady=5)
        
        # Botones de exportación
        export_frame = ctk.CTkFrame(metrics_frame)
        export_frame.pack(fill="x", pady=5)
        
        export_csv_btn = ctk.CTkButton(export_frame, text="📄 Export CSV", 
                                     command=self._export_csv)
        export_csv_btn.pack(side="left", padx=5)
        
        summary_btn = ctk.CTkButton(export_frame, text="📊 Resumen", 
                                  command=self._show_summary)
        summary_btn.pack(side="right", padx=5)
    
    def _create_log_panel(self):
        """Crea el panel de logs."""
        log_frame = ctk.CTkFrame(self.root)
        log_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(log_frame, text="📝 Log de Eventos", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.log_text = ctk.CTkTextbox(log_frame, height=100)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _create_initial_processes(self):
        """Crea los 5 procesos iniciales."""
        for i in range(5):
            self.engine.create_process()
        self.engine.log_event("5 procesos iniciales creados")
    
    def _update_display(self):
        """Actualiza toda la interfaz."""
        self._update_process_table()
        self._update_metrics()
        self._update_queues()
        self._update_logs()
        
        # Programar siguiente actualización
        self.root.after(100, self._update_display)
    
    def _update_process_table(self):
        """Actualiza la tabla de procesos."""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Agregar procesos (excepto init)
        for process in self.engine.process_table.values():
            if process.pid == 0:  # Skip init process
                continue
                
            values = (
                process.pid,
                process.name,
                process.state,
                process.remaining_burst,
                process.total_burst,
                process.parent_pid or "-",
                process.io_remaining if process.io_remaining > 0 else "-",
                process.created_tick,
                process.start_tick or "-",
                process.end_tick or "-",
                process.blocked_count,
                process.preempt_count
            )
            
            item = self.tree.insert('', 'end', values=values)
            
            # Aplicar color según estado
            if process.state in STATE_COLORS:
                self.tree.set(item, 'Estado', process.state)
                # Configurar tag para color
                tag = f"state_{process.state}"
                self.tree.item(item, tags=(tag,))
                
                # Configurar color del tag
                color = STATE_COLORS[process.state]
                self.tree.tag_configure(tag, background=color, foreground="black")
    
    def _update_metrics(self):
        """Actualiza las métricas del sistema."""
        metrics = self.engine.get_metrics()
        
        text = f"""🕐 Tick Actual: {metrics['tick']}
👥 Total Procesos: {metrics['total_processes']}
🖥️ CPU Utilización: {metrics['cpu_utilization']:.1f}%
🔄 Context Switches: {metrics['context_switches']}
👻 Zombies Activos: {metrics['zombies_count']}
⏱️ Turnaround Promedio: {metrics['avg_turnaround']:.1f}
⌛ Tiempo Espera Promedio: {metrics['avg_waiting']:.1f}
📊 Cola READY: {metrics['ready_queue_size']}
🚫 Procesos Bloqueados: {metrics['blocked_count']}"""
        
        self.metrics_text.delete("1.0", "end")
        self.metrics_text.insert("1.0", text)
    
    def _update_queues(self):
        """Actualiza la información de colas."""
        ready_names = []
        for pid in self.engine.ready_queue:
            if pid in self.engine.process_table:
                ready_names.append(f"{self.engine.process_table[pid].name}({pid})")
        
        blocked_info = []
        for pid in self.engine.blocked_list:
            if pid in self.engine.process_table:
                process = self.engine.process_table[pid]
                blocked_info.append(f"{process.name}({pid}): {process.io_remaining}")
        
        zombie_names = []
        for pid in self.engine.zombie_list:
            if pid in self.engine.process_table:
                zombie_names.append(f"{self.engine.process_table[pid].name}({pid})")
        
        current_running = "Ninguno"
        if self.engine.current_running_pid and self.engine.current_running_pid in self.engine.process_table:
            process = self.engine.process_table[self.engine.current_running_pid]
            current_running = f"{process.name}({process.pid}) - Q:{self.engine.current_quantum_used}/{self.engine.quantum}"
        
        text = f"""🏃 EJECUTANDO:
{current_running}

✅ COLA READY:
{', '.join(ready_names) if ready_names else 'Vacía'}

🚫 BLOQUEADOS:
{chr(10).join(blocked_info) if blocked_info else 'Ninguno'}

👻 ZOMBIES:
{', '.join(zombie_names) if zombie_names else 'Ninguno'}"""
        
        self.queues_text.delete("1.0", "end")
        self.queues_text.insert("1.0", text)
    
    def _update_logs(self):
        """Actualiza el log de eventos."""
        # Mostrar últimos 10 eventos
        recent_logs = list(self.engine.event_logs)[-10:]
        log_text = "\n".join(recent_logs)
        
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", log_text)
        
        # Auto-scroll al final
        self.log_text.see("end")
    
    def _on_process_select(self, event):
        """Maneja la selección de un proceso en la tabla."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            pid = int(self.tree.item(item)['values'][0])
            
            if pid in self.engine.process_table:
                process = self.engine.process_table[pid]
                info = f"Seleccionado: {process.name} (PID {pid})\nEstado: {process.state}"
                self.selected_info.configure(text=info)
                self.selected_pid = pid
            else:
                self.selected_info.configure(text="Proceso no encontrado")
                self.selected_pid = None
        else:
            self.selected_info.configure(text="Selecciona un proceso")
            self.selected_pid = None
    
    # Métodos de control de simulación
    def _start_auto(self):
        """Inicia el modo automático."""
        if not self.is_running:
            self.is_running = True
            self.auto_mode.set(True)
            self._auto_tick()
            self.start_btn.configure(text="🏃 Ejecutando...")
    
    def _pause_auto(self):
        """Pausa el modo automático."""
        self.is_running = False
        self.start_btn.configure(text="▶️ Start Auto")
    
    def _reset_simulation(self):
        """Reinicia la simulación."""
        result = messagebox.askyesno("Confirmar Reset", 
                                   "¿Estás seguro de que quieres reiniciar la simulación?")
        if result:
            self.is_running = False
            self.engine = SimulatorEngine()
            self._create_initial_processes()
            self.start_btn.configure(text="▶️ Start Auto")
    
    def _auto_tick(self):
        """Ejecuta ticks automáticos."""
        if self.is_running and self.auto_mode.get():
            # Actualizar configuraciones
            self.engine.quantum = self.quantum_var.get()
            
            # Auto-crear procesos si está habilitado
            if self.auto_create_var.get() and random.random() < self.engine.p_create:
                self.engine.create_process()
            
            # Ejecutar tick
            self.engine.tick_simulation()
            
            # Programar siguiente tick
            delay = int(self.speed_var.get() * 1000)  # Convertir a ms
            self.root.after(delay, self._auto_tick)
    
    def _manual_tick(self):
        """Ejecuta un tick manual."""
        self.engine.quantum = self.quantum_var.get()
        self.engine.tick_simulation()
    
    def _apply_seed(self):
        """Aplica una nueva semilla."""
        try:
            seed = int(self.seed_var.get())
            random.seed(seed)
            messagebox.showinfo("Seed Aplicada", f"Semilla {seed} aplicada correctamente")
        except ValueError:
            messagebox.showerror("Error", "La semilla debe ser un número entero")
    
    # Diálogos de acciones
    def _create_process_dialog(self):
        """Diálogo para crear un nuevo proceso."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Crear Nuevo Proceso")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Campos
        ctk.CTkLabel(dialog, text="Nombre (opcional):").pack(pady=5)
        name_entry = ctk.CTkEntry(dialog, width=200)
        name_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Burst Total (opcional):").pack(pady=5)
        burst_entry = ctk.CTkEntry(dialog, width=200)
        burst_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="PID Padre (opcional):").pack(pady=5)
        parent_entry = ctk.CTkEntry(dialog, width=200)
        parent_entry.pack(pady=5)
        
        def create():
            name = name_entry.get().strip() or None
            burst = None
            parent = None
            
            try:
                if burst_entry.get().strip():
                    burst = int(burst_entry.get())
                if parent_entry.get().strip():
                    parent = int(parent_entry.get())
                    if parent not in self.engine.process_table:
                        messagebox.showerror("Error", "El proceso padre no existe")
                        return
            except ValueError:
                messagebox.showerror("Error", "Los valores numéricos deben ser enteros")
                return
            
            pid = self.engine.create_process(name, burst, parent)
            messagebox.showinfo("Éxito", f"Proceso creado con PID {pid}")
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Crear", command=create).pack(pady=10)
        ctk.CTkButton(dialog, text="Cancelar", command=dialog.destroy).pack(pady=5)
    
    def _create_child_dialog(self):
        """Diálogo para crear un proceso hijo."""
        if not hasattr(self, 'selected_pid') or self.selected_pid is None:
            messagebox.showwarning("Advertencia", "Selecciona un proceso padre primero")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Crear Proceso Hijo")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        parent_process = self.engine.process_table[self.selected_pid]
        ctk.CTkLabel(dialog, text=f"Padre: {parent_process.name} (PID {self.selected_pid})").pack(pady=10)
        
        ctk.CTkLabel(dialog, text="Nombre del hijo (opcional):").pack(pady=5)
        name_entry = ctk.CTkEntry(dialog, width=200)
        name_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Burst Total (opcional):").pack(pady=5)
        burst_entry = ctk.CTkEntry(dialog, width=200)
        burst_entry.pack(pady=5)
        
        def create_child():
            name = name_entry.get().strip() or None
            burst = None
            
            try:
                if burst_entry.get().strip():
                    burst = int(burst_entry.get())
            except ValueError:
                messagebox.showerror("Error", "El burst debe ser un entero")
                return
            
            pid = self.engine.create_process(name, burst, self.selected_pid)
            messagebox.showinfo("Éxito", f"Proceso hijo creado con PID {pid}")
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Crear Hijo", command=create_child).pack(pady=10)
        ctk.CTkButton(dialog, text="Cancelar", command=dialog.destroy).pack(pady=5)
    
    def _move_new_to_ready(self):
        """Mueve todos los procesos NEW a READY."""
        moved = self.engine.move_new_to_ready()
        messagebox.showinfo("Resultado", f"{moved} procesos movidos a READY")
    
    def _force_block_dialog(self):
        """Diálogo para forzar bloqueo."""
        if not hasattr(self, 'selected_pid') or self.selected_pid is None:
            messagebox.showwarning("Advertencia", "Selecciona un proceso primero")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Forzar Bloqueo")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        process = self.engine.process_table[self.selected_pid]
        ctk.CTkLabel(dialog, text=f"Bloquear: {process.name} (PID {self.selected_pid})").pack(pady=10)
        
        ctk.CTkLabel(dialog, text="Tiempo de I/O (ticks):").pack(pady=5)
        io_entry = ctk.CTkEntry(dialog, width=100)
        io_entry.insert(0, "3")
        io_entry.pack(pady=5)
        
        def block():
            try:
                io_time = int(io_entry.get())
                if io_time <= 0:
                    raise ValueError
                
                success = self.engine.force_block_process(self.selected_pid, io_time)
                if success:
                    messagebox.showinfo("Éxito", f"Proceso bloqueado por {io_time} ticks")
                else:
                    messagebox.showerror("Error", "No se pudo bloquear el proceso")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "El tiempo debe ser un entero positivo")
        
        ctk.CTkButton(dialog, text="Bloquear", command=block).pack(pady=10)
        ctk.CTkButton(dialog, text="Cancelar", command=dialog.destroy).pack(pady=5)
    
    def _force_terminate_dialog(self):
        """Diálogo para forzar terminación."""
        if not hasattr(self, 'selected_pid') or self.selected_pid is None:
            messagebox.showwarning("Advertencia", "Selecciona un proceso primero")
            return
        
        process = self.engine.process_table[self.selected_pid]
        result = messagebox.askyesno("Confirmar Terminación", 
                                   f"¿Terminar el proceso {process.name} (PID {self.selected_pid})?")
        if result:
            success = self.engine.force_terminate_process(self.selected_pid)
            if success:
                messagebox.showinfo("Éxito", "Proceso terminado")
            else:
                messagebox.showerror("Error", "No se pudo terminar el proceso")
    
    def _wait_dialog(self):
        """Diálogo para hacer wait (reapear zombies)."""
        if not hasattr(self, 'selected_pid') or self.selected_pid is None:
            messagebox.showwarning("Advertencia", "Selecciona un proceso padre primero")
            return
        
        reaped = self.engine.wait_for_child(self.selected_pid)
        if reaped:
            names = [self.engine.process_table[pid].name for pid in reaped]
            messagebox.showinfo("Éxito", f"Procesos reapeados: {', '.join(names)}")
        else:
            messagebox.showinfo("Información", "No hay procesos zombie para reapear")
    
    def _show_process_tree(self):
        """Muestra el árbol de procesos."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Árbol de Procesos")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        text_widget = ctk.CTkTextbox(dialog)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Construir árbol
        tree_text = self._build_process_tree()
        text_widget.insert("1.0", tree_text)
    
    def _build_process_tree(self) -> str:
        """Construye una representación textual del árbol de procesos."""
        def build_subtree(pid, level=0):
            if pid not in self.engine.process_table:
                return ""
            
            process = self.engine.process_table[pid]
            indent = "  " * level
            symbol = "├─" if level > 0 else ""
            
            result = f"{indent}{symbol} {process.name} (PID {pid}) - {process.state}\n"
            
            # Agregar hijos
            for child_pid in process.children:
                result += build_subtree(child_pid, level + 1)
            
            return result
        
        tree = "🌳 ÁRBOL DE PROCESOS\n\n"
        
        # Encontrar procesos raíz (sin padre o padre inexistente)
        root_processes = []
        for process in self.engine.process_table.values():
            if process.pid == 0:  # Skip init
                continue
            if process.parent_pid is None or process.parent_pid not in self.engine.process_table:
                root_processes.append(process.pid)
        
        for root_pid in root_processes:
            tree += build_subtree(root_pid)
        
        return tree
    
    def _export_csv(self):
        """Exporta métricas a CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Guardar métricas como CSV"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Header
                    writer.writerow(['PID', 'Nombre', 'Estado', 'Total_Burst', 'Creado', 
                                   'Inicio', 'Fin', 'Turnaround', 'Tiempo_Espera', 
                                   'Bloqueos', 'Preempciones'])
                    
                    # Datos de procesos
                    for process in self.engine.process_table.values():
                        if process.pid == 0:  # Skip init
                            continue
                        
                        turnaround = (process.end_tick - process.created_tick) if process.end_tick else None
                        waiting_time = (turnaround - process.total_burst) if turnaround else None
                        
                        writer.writerow([
                            process.pid,
                            process.name,
                            process.state,
                            process.total_burst,
                            process.created_tick,
                            process.start_tick or '',
                            process.end_tick or '',
                            turnaround or '',
                            waiting_time or '',
                            process.blocked_count,
                            process.preempt_count
                        ])
                    
                    # Métricas globales
                    writer.writerow([])
                    writer.writerow(['MÉTRICAS GLOBALES'])
                    metrics = self.engine.get_metrics()
                    for key, value in metrics.items():
                        writer.writerow([key, value])
                
                messagebox.showinfo("Éxito", f"Métricas exportadas a {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def _show_summary(self):
        """Muestra resumen de métricas."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Resumen de Métricas")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        text_widget = ctk.CTkTextbox(dialog)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        metrics = self.engine.get_metrics()
        
        summary = f"""📊 RESUMEN DE MÉTRICAS DEL SISTEMA

🕐 Información Temporal:
   • Tick Actual: {metrics['tick']}
   • Ticks de CPU Ocupada: {self.engine.cpu_busy_ticks}
   • Ticks de CPU Idle: {self.engine.idle_ticks}

👥 Procesos:
   • Total de Procesos: {metrics['total_processes']}
   • Procesos en READY: {metrics['ready_queue_size']}
   • Procesos Bloqueados: {metrics['blocked_count']}
   • Zombies Activos: {metrics['zombies_count']}

⚡ Rendimiento:
   • Utilización de CPU: {metrics['cpu_utilization']:.2f}%
   • Context Switches: {metrics['context_switches']}
   • Turnaround Promedio: {metrics['avg_turnaround']:.2f} ticks
   • Tiempo de Espera Promedio: {metrics['avg_waiting']:.2f} ticks

🔧 Configuración Actual:
   • Quantum: {self.engine.quantum}
   • Probabilidad de Bloqueo: {self.engine.p_block:.2f}
   • Auto-reap después de: {self.engine.auto_reap_after} ticks

📈 Estados de Procesos:"""
        
        # Contar procesos por estado
        state_counts = {}
        for process in self.engine.process_table.values():
            if process.pid == 0:  # Skip init
                continue
            state = process.state
            state_counts[state] = state_counts.get(state, 0) + 1
        
        for state, count in state_counts.items():
            summary += f"\n   • {state}: {count}"
        
        text_widget.insert("1.0", summary)
    
    def run(self):
        """Ejecuta la aplicación."""
        self.root.mainloop()

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulador de Estados de Procesos')
    parser.add_argument('--demo', action='store_true', 
                       help='Ejecutar demo automático con seed fijo')
    
    args = parser.parse_args()
    
    app = ProcessSimulatorGUI()
    
    if args.demo:
        # Configurar demo
        random.seed(42)
        app.seed_var.set("42")
        app.auto_mode.set(True)
        app.auto_create_var.set(True)
        app.speed_var.set(0.3)
        app.quantum_var.set(4)
        
        # Crear algunos procesos adicionales
        for i in range(3):
            app.engine.create_process(f"Demo{i}", random.randint(8, 12))
        
        # Iniciar automáticamente
        app.root.after(1000, app._start_auto)
        
        print("🚀 Demo iniciado con configuración automática")
        print("   - Seed: 42")
        print("   - Auto-crear: Activado")
        print("   - Quantum: 4")
        print("   - Velocidad: 0.3s por tick")
    
    app.run()

if __name__ == "__main__":
    main()
