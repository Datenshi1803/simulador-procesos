"""
Ventana principal de la aplicación.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import time
import random
import csv
from typing import Optional
from ..core.simulator import SimulatorEngine
from .components import ProcessTable, ControlPanel, ActionPanel, MetricsPanel

class MainWindow:
    """Ventana principal del simulador de procesos."""
    
    def __init__(self):
        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("Simulador de Estados de Procesos — Gestión de Estados")
        self.root.geometry("1600x900")
        self.root.minsize(1400, 800)
        
        # Configurar icono (si existe)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Inicializar simulador
        self.simulator = SimulatorEngine()
        
        # Variables de control
        self.is_running = False
        self.auto_thread: Optional[threading.Thread] = None
        self.speed = 1.0
        self.auto_create_enabled = False
        
        # Crear 5 procesos iniciales
        self._create_initial_processes()
        
        # Configurar UI
        self._setup_ui()
        self._setup_callbacks()
        
        # Actualizar interfaz inicial
        self._update_display()
    
    def _create_initial_processes(self):
        """Crea 5 procesos iniciales como especifica la rúbrica."""
        for i in range(1, 6):
            self.simulator.create_process(f"P{i}")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Panel de control superior
        self.control_panel = ControlPanel(self.root)
        self.control_panel.pack(fill="x", padx=10, pady=5)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Configurar grid - más espacio para la tabla
        main_frame.grid_columnconfigure(0, weight=4)  # Tabla de procesos - más espacio
        main_frame.grid_columnconfigure(1, weight=1)  # Panel derecho - compacto
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Tabla de procesos (izquierda)
        self.process_table = ProcessTable(main_frame)
        self.process_table.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Panel derecho
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=0)  # Panel de acciones - tamaño fijo
        right_panel.grid_rowconfigure(1, weight=1)  # Métricas - expandible
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Panel de acciones (arriba derecha)
        self.action_panel = ActionPanel(right_panel)
        self.action_panel.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        
        # Panel de métricas (abajo derecha)
        self.metrics_panel = MetricsPanel(right_panel)
        self.metrics_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 5))
    
    def _setup_callbacks(self):
        """Configura los callbacks de los componentes."""
        # Control panel callbacks
        self.control_panel.set_start_auto_callback(self._start_auto_simulation)
        self.control_panel.set_pause_callback(self._pause_simulation)
        self.control_panel.set_reset_callback(self._reset_simulation)
        self.control_panel.set_quantum_change_callback(self._on_quantum_change)
        self.control_panel.set_speed_change_callback(self._on_speed_change)
        self.control_panel.set_auto_create_callback(self._on_auto_create_change)
        self.control_panel.set_seed_apply_callback(self._on_seed_apply)
        
        # Process table callbacks
        self.process_table.set_selection_callback(self._on_process_selection)
        
        # Action panel callbacks
        self.action_panel.set_create_process_callback(self._create_process)
        self.action_panel.set_create_child_callback(self._create_child_process)
        self.action_panel.set_change_priority_callback(self._change_process_priority)
        self.action_panel.set_new_to_ready_callback(self._move_new_to_ready)
        self.action_panel.set_force_block_callback(self._force_block_process)
        self.action_panel.set_force_terminate_callback(self._force_terminate_process)
        self.action_panel.set_wait_reap_callback(self._wait_reap_process)
        self.action_panel.set_show_tree_callback(self._show_process_tree)
        self.action_panel.set_tick_manual_callback(self._manual_tick)
        
        # Metrics panel callbacks
        self.metrics_panel.set_export_callback(self._export_metrics)
    
    def _on_process_selection(self, pid: int):
        """Maneja la selección de un proceso en la tabla."""
        process_name = None
        if pid in self.simulator.process_table:
            process_name = self.simulator.process_table[pid].name
        
        self.action_panel.update_selection(pid, process_name)
    
    def _start_auto_simulation(self):
        """Inicia la simulación automática."""
        if not self.is_running:
            self.is_running = True
            self.auto_thread = threading.Thread(target=self._auto_simulation_loop, daemon=True)
            self.auto_thread.start()
    
    def _pause_simulation(self):
        """Pausa la simulación automática."""
        self.is_running = False
    
    def _reset_simulation(self):
        """Reinicia la simulación."""
        self.is_running = False
        if self.auto_thread:
            self.auto_thread.join(timeout=1.0)
        
        self.simulator.reset()
        self._create_initial_processes()
        self._update_display()
        
        # Limpiar selección
        self.action_panel.update_selection(None)
    
    def _auto_simulation_loop(self):
        """Loop principal de simulación automática."""
        while self.is_running:
            try:
                # Ejecutar tick
                self.simulator.tick_simulation()
                
                # Auto-crear procesos si está habilitado
                if self.auto_create_enabled and random.random() < self.simulator.p_create:
                    self.simulator.create_process()
                
                # Actualizar interfaz en el hilo principal
                self.root.after(0, self._update_display)
                
                # Esperar según la velocidad
                time.sleep(1.0 / self.speed)
                
            except Exception as e:
                print(f"Error en simulación: {e}")
                break
    
    def _manual_tick(self):
        """Ejecuta un tick manual."""
        self.simulator.tick_simulation()
        self._update_display()
    
    def _update_display(self):
        """Actualiza toda la interfaz."""
        # Actualizar tabla de procesos
        self.process_table.update_processes(self.simulator.process_table)
        
        # Actualizar métricas
        metrics = self.simulator.get_metrics()
        self.metrics_panel.update_metrics(metrics)
    
    def _create_process(self):
        """Crea un nuevo proceso."""
        pid = self.simulator.create_process()
        self._update_display()
        messagebox.showinfo("Proceso Creado", f"Proceso creado con PID {pid}")
    
    def _create_child_process(self, parent_pid: int):
        """Crea un proceso hijo."""
        if parent_pid in self.simulator.process_table:
            parent_name = self.simulator.process_table[parent_pid].name
            child_pid = self.simulator.create_process(parent_pid=parent_pid)
            self._update_display()
            messagebox.showinfo(
                "Proceso Hijo Creado", 
                f"Proceso hijo creado con PID {child_pid}\nPadre: {parent_name} (PID {parent_pid})"
            )
        else:
            messagebox.showerror("Error", "Proceso padre no encontrado")
    
    def _change_process_priority(self, pid: int):
        """Cambia la prioridad de un proceso."""
        if pid not in self.simulator.process_table:
            messagebox.showerror("Error", "Proceso no encontrado")
            return
        
        process = self.simulator.process_table[pid]
        current_priority = process.priority
        
        # Crear ventana de diálogo para cambiar prioridad
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Cambiar Prioridad")
        dialog.geometry("350x280")  # Más alto y más ancho
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar el diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (280 // 2)
        dialog.geometry(f"350x280+{x}+{y}")
        
        # Contenido del diálogo con mejor espaciado
        title_label = ctk.CTkLabel(
            dialog, 
            text=f"Proceso: {process.name} (PID {pid})", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        current_label = ctk.CTkLabel(
            dialog, 
            text=f"Prioridad actual: {current_priority}",
            font=ctk.CTkFont(size=14)
        )
        current_label.pack(pady=5)
        
        instruction_label = ctk.CTkLabel(
            dialog, 
            text="Nueva prioridad (0=máxima, 9=mínima):",
            font=ctk.CTkFont(size=12)
        )
        instruction_label.pack(pady=(10, 5))
        
        # Frame para la entrada
        entry_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        entry_frame.pack(pady=10)
        
        priority_var = ctk.StringVar(value=str(current_priority))
        priority_entry = ctk.CTkEntry(
            entry_frame, 
            textvariable=priority_var, 
            width=120,
            height=35,
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        priority_entry.pack()
        priority_entry.focus_set()  # Foco automático
        
        # Frame para los botones con mejor espaciado
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=(20, 15))
        
        def apply_priority():
            try:
                new_priority = int(priority_var.get())
                if 0 <= new_priority <= 9:
                    old_priority = process.priority
                    self.simulator.scheduler.adjust_priority(pid, new_priority, self.simulator.process_table)
                    self._update_display()
                    dialog.destroy()
                    messagebox.showinfo(
                        "Prioridad Cambiada", 
                        f"Prioridad del proceso {process.name} (PID {pid})\ncambiada de {old_priority} a {new_priority}"
                    )
                else:
                    messagebox.showerror("Error", "La prioridad debe estar entre 0 y 9")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido")
        
        def on_enter(event):
            apply_priority()
        
        priority_entry.bind('<Return>', on_enter)  # Enter para aplicar
        
        apply_button = ctk.CTkButton(
            button_frame, 
            text="✅ Aplicar", 
            command=apply_priority, 
            width=100,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        apply_button.pack(side="left", padx=10)
        
        cancel_button = ctk.CTkButton(
            button_frame, 
            text="❌ Cancelar", 
            command=dialog.destroy, 
            width=100,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        cancel_button.pack(side="left", padx=10)
    
    def _move_new_to_ready(self):
        """Mueve todos los procesos NEW a READY."""
        count = self.simulator.move_new_to_ready()
        self._update_display()
        messagebox.showinfo("Transición Completada", f"{count} procesos movidos de NEW a READY")
    
    def _force_block_process(self, pid: int):
        """Fuerza el bloqueo de un proceso."""
        if self.simulator.force_block_process(pid):
            self._update_display()
            messagebox.showinfo("Proceso Bloqueado", f"Proceso PID {pid} forzado a BLOCKED")
        else:
            messagebox.showerror("Error", "No se pudo bloquear el proceso")
    
    def _force_terminate_process(self, pid: int):
        """Fuerza la terminación de un proceso."""
        if self.simulator.force_terminate_process(pid):
            self._update_display()
            messagebox.showinfo("Proceso Terminado", f"Proceso PID {pid} forzado a terminar")
        else:
            messagebox.showerror("Error", "No se pudo terminar el proceso")
    
    def _wait_reap_process(self, pid: int):
        """Ejecuta wait() para reapear procesos zombie."""
        reaped = self.simulator.wait_for_child(pid)
        self._update_display()
        if reaped:
            messagebox.showinfo(
                "Procesos Reapeados", 
                f"Proceso PID {pid} reapeó {len(reaped)} hijos zombie:\n" + 
                ", ".join(map(str, reaped))
            )
        else:
            messagebox.showinfo("Sin Zombies", f"Proceso PID {pid} no tiene hijos zombie para reapear")
    
    def _show_process_tree(self):
        """Muestra el árbol de procesos."""
        tree = self.simulator.get_process_tree()
        tree_text = self._format_process_tree(tree)
        
        # Crear ventana de árbol
        tree_window = ctk.CTkToplevel(self.root)
        tree_window.title("Árbol de Procesos")
        tree_window.geometry("600x400")
        
        text_widget = ctk.CTkTextbox(tree_window)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", tree_text)
        text_widget.configure(state="disabled")
    
    def _format_process_tree(self, tree: dict, level: int = 0) -> str:
        """Formatea el árbol de procesos para mostrar."""
        result = ""
        for pid, subtree in tree.items():
            if 'process' in subtree:
                process = subtree['process']
                indent = "  " * level
                result += f"{indent}├─ PID {pid}: {process.name} [{process.state}]\n"
                
                # Recursivamente agregar hijos
                if subtree['children']:
                    result += self._format_process_tree(subtree['children'], level + 1)
        
        return result if result else "No hay procesos en el árbol"
    
    def _export_metrics(self):
        """Exporta las métricas a un archivo CSV."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Guardar métricas como..."
            )
            
            if filename:
                metrics = self.simulator.get_metrics()
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Escribir encabezados
                    writer.writerow(['Métrica', 'Valor'])
                    
                    # Escribir métricas
                    for key, value in metrics.items():
                        writer.writerow([key, value])
                    
                    # Escribir información de procesos
                    writer.writerow([])
                    writer.writerow(['Información de Procesos'])
                    writer.writerow(['PID', 'Nombre', 'Estado', 'Total Burst', 'Restante', 
                                   'Padre', 'Creado', 'Inicio', 'Fin', 'Turnaround', 'Waiting'])
                    
                    for pid, process in self.simulator.process_table.items():
                        if pid != 0:  # Saltar proceso init
                            writer.writerow([
                                process.pid,
                                process.name,
                                process.state,
                                process.total_burst,
                                process.remaining_burst,
                                process.parent_pid or '',
                                process.created_tick,
                                process.start_tick or '',
                                process.end_tick or '',
                                process.get_turnaround_time() or '',
                                process.get_waiting_time() or ''
                            ])
                
                messagebox.showinfo("Exportación Exitosa", f"Métricas exportadas a:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"Error al exportar métricas:\n{str(e)}")
    
    def _on_quantum_change(self, quantum: int):
        """Maneja el cambio de quantum."""
        self.simulator.set_quantum(quantum)
    
    def _on_speed_change(self, speed: float):
        """Maneja el cambio de velocidad."""
        self.speed = speed
    
    def _on_auto_create_change(self, enabled: bool):
        """Maneja el cambio de auto-crear procesos."""
        self.auto_create_enabled = enabled
    
    def _on_seed_apply(self, seed: int):
        """Aplica una semilla para reproducibilidad."""
        random.seed(seed)
        messagebox.showinfo("Seed Aplicado", f"Semilla {seed} aplicada para reproducibilidad")
    
    def run(self):
        """Ejecuta la aplicación."""
        self.root.mainloop()
