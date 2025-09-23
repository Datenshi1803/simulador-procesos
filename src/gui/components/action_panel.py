"""
Panel de acciones para interactuar con procesos.
"""
import customtkinter as ctk
from typing import Callable, Optional

class ActionPanel(ctk.CTkFrame):
    """Panel de acciones para manipular procesos."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Callbacks
        self.create_process_callback: Optional[Callable] = None
        self.create_child_callback: Optional[Callable] = None
        self.change_priority_callback: Optional[Callable] = None
        self.new_to_ready_callback: Optional[Callable] = None
        self.force_block_callback: Optional[Callable] = None
        self.force_terminate_callback: Optional[Callable] = None
        self.wait_reap_callback: Optional[Callable] = None
        self.show_tree_callback: Optional[Callable] = None
        self.tick_manual_callback: Optional[Callable] = None
        
        # Estado
        self.selected_pid: Optional[int] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Título - más compacto
        title_label = ctk.CTkLabel(
            self, 
            text="⚙️ Acciones", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(8, 8))
        
        # Label de proceso seleccionado - más compacto
        self.selection_label = ctk.CTkLabel(
            self,
            text="Selecciona un proceso",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.selection_label.pack(pady=(0, 8))
        
        # Frame de botones - más compacto
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(fill="both", expand=True, padx=6)
        
        # Botones de creación - más pequeños
        create_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        create_frame.pack(fill="x", pady=3)
        
        self.create_button = ctk.CTkButton(
            create_frame,
            text="➕ Crear Proceso",
            command=self._on_create_process,
            width=115,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9)
        )
        self.create_button.pack(pady=1)
        
        self.create_child_button = ctk.CTkButton(
            create_frame,
            text="👶 Crear Hijo",
            command=self._on_create_child,
            width=115,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9),
            state="disabled"
        )
        self.create_child_button.pack(pady=1)
        
        self.priority_button = ctk.CTkButton(
            create_frame,
            text="🎯 Cambiar Prioridad",
            command=self._on_change_priority,
            width=115,
            height=26,
            font=ctk.CTkFont(size=9),
            state="disabled"
        )
        self.priority_button.pack(pady=1)
        
        # Separador - más pequeño
        separator1 = ctk.CTkFrame(buttons_frame, height=1, fg_color="gray")
        separator1.pack(fill="x", pady=6)
        
        # Botones de transición - más compactos
        transition_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        transition_frame.pack(fill="x", pady=3)
        
        self.new_to_ready_button = ctk.CTkButton(
            transition_frame,
            text="🔄 NEW → READY",
            command=self._on_new_to_ready,
            width=115,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9)
        )
        self.new_to_ready_button.pack(pady=1)
        
        # Botones de forzado - más compactos
        force_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        force_frame.pack(fill="x", pady=3)
        
        self.force_block_button = ctk.CTkButton(
            force_frame,
            text="⏸ Forzar Bloqueo",
            command=self._on_force_block,
            width=115,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9),
            state="disabled"
        )
        self.force_block_button.pack(pady=1)
        
        self.force_terminate_button = ctk.CTkButton(
            force_frame,
            text="❌ Forzar Terminar",
            command=self._on_force_terminate,
            width=115,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9),
            state="disabled"
        )
        self.force_terminate_button.pack(pady=1)
        
        # Separador - más pequeño
        separator2 = ctk.CTkFrame(buttons_frame, height=1, fg_color="gray")
        separator2.pack(fill="x", pady=6)
        
        # Botones de gestión - más compactos
        management_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        management_frame.pack(fill="x", pady=3)
        
        self.wait_button = ctk.CTkButton(
            management_frame,
            text="⏳ Wait (Reap)",
            command=self._on_wait_reap,
            width=115,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9),
            state="disabled"
        )
        self.wait_button.pack(pady=1)
        
        self.tree_button = ctk.CTkButton(
            management_frame,
            text="🌳 Ver Árbol",
            command=self._on_show_tree,
            width=115,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9)
        )
        self.tree_button.pack(pady=1)
        
        self.tick_button = ctk.CTkButton(
            management_frame,
            text="⚡ Tick Manual",
            command=self._on_tick_manual,
            width=115,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9)
        )
        self.tick_button.pack(pady=1)
    
    def update_selection(self, pid: Optional[int], process_name: str = None):
        """Actualiza la selección actual."""
        self.selected_pid = pid
        
        if pid is not None:
            self.selection_label.configure(
                text=f"Seleccionado: PID {pid}" + (f" ({process_name})" if process_name else ""),
                text_color="white"
            )
            
            # Habilitar botones que requieren selección
            self.create_child_button.configure(state="normal")
            self.priority_button.configure(state="normal")
            self.force_block_button.configure(state="normal")
            self.force_terminate_button.configure(state="normal")
            self.wait_button.configure(state="normal")
        else:
            self.selection_label.configure(
                text="Selecciona un proceso",
                text_color="gray"
            )
            
            # Deshabilitar botones que requieren selección
            self.create_child_button.configure(state="disabled")
            self.priority_button.configure(state="disabled")
            self.force_block_button.configure(state="disabled")
            self.force_terminate_button.configure(state="disabled")
            self.wait_button.configure(state="disabled")
    
    def _on_create_process(self):
        """Maneja la creación de un nuevo proceso."""
        if self.create_process_callback:
            self.create_process_callback()
    
    def _on_create_child(self):
        """Maneja la creación de un proceso hijo."""
        if self.create_child_callback and self.selected_pid is not None:
            self.create_child_callback(self.selected_pid)
    
    def _on_change_priority(self):
        """Maneja el cambio de prioridad de un proceso."""
        if self.change_priority_callback and self.selected_pid is not None:
            self.change_priority_callback(self.selected_pid)
    
    def _on_new_to_ready(self):
        """Maneja la transición NEW → READY."""
        if self.new_to_ready_callback:
            self.new_to_ready_callback()
    
    def _on_force_block(self):
        """Maneja el forzado de bloqueo."""
        if self.force_block_callback and self.selected_pid is not None:
            self.force_block_callback(self.selected_pid)
    
    def _on_force_terminate(self):
        """Maneja el forzado de terminación."""
        if self.force_terminate_callback and self.selected_pid is not None:
            self.force_terminate_callback(self.selected_pid)
    
    def _on_wait_reap(self):
        """Maneja la operación wait/reap."""
        if self.wait_reap_callback and self.selected_pid is not None:
            self.wait_reap_callback(self.selected_pid)
    
    def _on_show_tree(self):
        """Maneja la visualización del árbol."""
        if self.show_tree_callback:
            self.show_tree_callback()
    
    def _on_tick_manual(self):
        """Maneja el tick manual."""
        if self.tick_manual_callback:
            self.tick_manual_callback()
    
    # Métodos para establecer callbacks
    def set_create_process_callback(self, callback: Callable):
        self.create_process_callback = callback
    
    def set_create_child_callback(self, callback: Callable):
        self.create_child_callback = callback
    
    def set_change_priority_callback(self, callback: Callable):
        self.change_priority_callback = callback
    
    def set_new_to_ready_callback(self, callback: Callable):
        self.new_to_ready_callback = callback
    
    def set_force_block_callback(self, callback: Callable):
        self.force_block_callback = callback
    
    def set_force_terminate_callback(self, callback: Callable):
        self.force_terminate_callback = callback
    
    def set_wait_reap_callback(self, callback: Callable):
        self.wait_reap_callback = callback
    
    def set_show_tree_callback(self, callback: Callable):
        self.show_tree_callback = callback
    
    def set_tick_manual_callback(self, callback: Callable):
        self.tick_manual_callback = callback
