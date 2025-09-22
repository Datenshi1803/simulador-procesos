"""
Componente de tabla de procesos para la interfaz gráfica.
"""
import customtkinter as ctk
from tkinter import ttk
from typing import Dict, List, Optional, Callable
from ...models.process import Process

class ProcessTable(ctk.CTkFrame):
    """Tabla de procesos con funcionalidad de selección."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.selected_pid: Optional[int] = None
        self.selection_callback: Optional[Callable] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="📋 Tabla de Procesos", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Frame para la tabla
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Crear Treeview con estilo personalizado
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configurar colores para el tema oscuro
        style.configure("Treeview", 
                       background="#2b2b2b",
                       foreground="white",
                       fieldbackground="#2b2b2b",
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background="#1f538d",
                       foreground="white",
                       borderwidth=1)
        style.map("Treeview.Heading",
                 background=[('active', '#14375e')])
        style.map("Treeview",
                 background=[('selected', '#1f538d')])
        
        # Definir columnas
        columns = ("PID", "Nombre", "Estado", "Restante", "Total", "Padre", 
                  "IO_Rem", "Creado", "Inicio", "Fin", "#Bloq", "#Preempt")
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        # Configurar encabezados
        column_widths = {
            "PID": 50, "Nombre": 80, "Estado": 90, "Restante": 70, "Total": 60,
            "Padre": 60, "IO_Rem": 60, "Creado": 60, "Inicio": 60, "Fin": 60,
            "#Bloq": 50, "#Preempt": 70
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 80), minwidth=50)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack elementos
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Bind eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)
    
    def _on_selection_change(self, event):
        """Maneja el cambio de selección en la tabla."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            try:
                self.selected_pid = int(item['values'][0])  # PID está en la primera columna
                if self.selection_callback:
                    self.selection_callback(self.selected_pid)
            except (ValueError, IndexError):
                self.selected_pid = None
        else:
            self.selected_pid = None
    
    def set_selection_callback(self, callback: Callable):
        """Establece el callback para cambios de selección."""
        self.selection_callback = callback
    
    def update_processes(self, process_table: Dict[int, Process]):
        """Actualiza la tabla con los procesos actuales."""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Colores por estado
        state_colors = {
            'NEW': '#FFA500',      # Naranja
            'READY': '#00CED1',    # Turquesa
            'RUNNING': '#32CD32',  # Verde lima
            'BLOCKED': '#FF6347',  # Rojo tomate
            'ZOMBIE': '#9370DB',   # Violeta medio
            'TERMINATED': '#696969' # Gris oscuro
        }
        
        # Agregar procesos
        for pid, process in sorted(process_table.items()):
            if pid == 0:  # Saltar proceso init en la tabla
                continue
                
            values = (
                process.pid,
                process.name,
                process.state,
                process.remaining_burst if process.remaining_burst > 0 else "-",
                process.total_burst,
                process.parent_pid if process.parent_pid else "-",
                process.io_remaining if process.io_remaining > 0 else "-",
                process.created_tick,
                process.start_tick if process.start_tick else "-",
                process.end_tick if process.end_tick else "-",
                process.blocked_count,
                process.preempt_count
            )
            
            item_id = self.tree.insert("", "end", values=values)
            
            # Aplicar color según estado
            state_color = state_colors.get(process.state, '#FFFFFF')
            self.tree.set(item_id, "Estado", process.state)
            
            # Configurar tags para colores
            tag_name = f"state_{process.state}"
            if tag_name not in self.tree.tag_names():
                self.tree.tag_configure(tag_name, background=state_color, foreground='black')
            self.tree.item(item_id, tags=(tag_name,))
    
    def get_selected_pid(self) -> Optional[int]:
        """Obtiene el PID del proceso seleccionado."""
        return self.selected_pid
    
    def clear_selection(self):
        """Limpia la selección actual."""
        self.tree.selection_remove(self.tree.selection())
        self.selected_pid = None
