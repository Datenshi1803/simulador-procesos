"""
Panel de control principal de la interfaz gráfica.
"""
import customtkinter as ctk
from typing import Callable, Optional

class ControlPanel(ctk.CTkFrame):
    """Panel de control con botones principales."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Callbacks
        self.start_auto_callback: Optional[Callable] = None
        self.pause_callback: Optional[Callable] = None
        self.reset_callback: Optional[Callable] = None
        self.tick_manual_callback: Optional[Callable] = None
        self.quantum_change_callback: Optional[Callable] = None
        self.speed_change_callback: Optional[Callable] = None
        self.auto_create_callback: Optional[Callable] = None
        self.seed_apply_callback: Optional[Callable] = None
        
        # Variables
        self.is_auto_mode = ctk.BooleanVar(value=False)
        self.auto_create_enabled = ctk.BooleanVar(value=False)
        self.quantum_var = ctk.IntVar(value=3)
        self.speed_var = ctk.DoubleVar(value=1.0)
        self.seed_var = ctk.StringVar(value="42")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="🎮 Simulador de Estados de Procesos", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(15, 10))
        
        # Frame principal de controles
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        # Primera fila: Botones principales
        buttons_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=10)
        
        self.start_button = ctk.CTkButton(
            buttons_frame,
            text="▶ Start Auto",
            command=self._on_start_auto,
            width=120,
            height=35
        )
        self.start_button.pack(side="left", padx=5)
        
        self.pause_button = ctk.CTkButton(
            buttons_frame,
            text="⏸ Pause",
            command=self._on_pause,
            width=100,
            height=35,
            state="disabled"
        )
        self.pause_button.pack(side="left", padx=5)
        
        self.reset_button = ctk.CTkButton(
            buttons_frame,
            text="🔄 Reset",
            command=self._on_reset,
            width=100,
            height=35
        )
        self.reset_button.pack(side="left", padx=5)
        
        # Switch de modo
        mode_label = ctk.CTkLabel(buttons_frame, text="Modo:")
        mode_label.pack(side="left", padx=(20, 5))
        
        self.mode_switch = ctk.CTkSwitch(
            buttons_frame,
            text="Auto",
            variable=self.is_auto_mode,
            command=self._on_mode_change
        )
        self.mode_switch.pack(side="left", padx=5)
        
        # Segunda fila: Configuraciones
        config_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        config_frame.pack(fill="x", pady=5)
        
        # Quantum
        quantum_label = ctk.CTkLabel(config_frame, text="Quantum:")
        quantum_label.pack(side="left", padx=(0, 5))
        
        self.quantum_entry = ctk.CTkEntry(
            config_frame,
            textvariable=self.quantum_var,
            width=60,
            height=28
        )
        self.quantum_entry.pack(side="left", padx=5)
        self.quantum_entry.bind("<Return>", self._on_quantum_change)
        
        # Velocidad
        speed_label = ctk.CTkLabel(config_frame, text="Velocidad:")
        speed_label.pack(side="left", padx=(20, 5))
        
        self.speed_slider = ctk.CTkSlider(
            config_frame,
            from_=0.1,
            to=5.0,
            variable=self.speed_var,
            command=self._on_speed_change,
            width=120,
            height=20
        )
        self.speed_slider.pack(side="left", padx=5)
        
        # Auto-crear
        self.auto_create_switch = ctk.CTkSwitch(
            config_frame,
            text="Auto-crear",
            variable=self.auto_create_enabled,
            command=self._on_auto_create_change
        )
        self.auto_create_switch.pack(side="left", padx=(20, 5))
        
        # Seed
        seed_label = ctk.CTkLabel(config_frame, text="Seed:")
        seed_label.pack(side="left", padx=(20, 5))
        
        self.seed_entry = ctk.CTkEntry(
            config_frame,
            textvariable=self.seed_var,
            width=60,
            height=28
        )
        self.seed_entry.pack(side="left", padx=5)
        
        self.seed_button = ctk.CTkButton(
            config_frame,
            text="Aplicar Seed",
            command=self._on_seed_apply,
            width=100,
            height=28
        )
        self.seed_button.pack(side="left", padx=5)
    
    def _on_start_auto(self):
        """Maneja el botón Start Auto."""
        if self.start_auto_callback:
            self.start_auto_callback()
        self._set_auto_running(True)
    
    def _on_pause(self):
        """Maneja el botón Pause."""
        if self.pause_callback:
            self.pause_callback()
        self._set_auto_running(False)
    
    def _on_reset(self):
        """Maneja el botón Reset."""
        if self.reset_callback:
            self.reset_callback()
        self._set_auto_running(False)
    
    def _on_mode_change(self):
        """Maneja el cambio de modo."""
        # El modo se maneja automáticamente por la variable
        pass
    
    def _on_quantum_change(self, event=None):
        """Maneja el cambio de quantum."""
        try:
            quantum = max(1, self.quantum_var.get())
            self.quantum_var.set(quantum)
            if self.quantum_change_callback:
                self.quantum_change_callback(quantum)
        except:
            self.quantum_var.set(3)  # Valor por defecto
    
    def _on_speed_change(self, value):
        """Maneja el cambio de velocidad."""
        if self.speed_change_callback:
            self.speed_change_callback(float(value))
    
    def _on_auto_create_change(self):
        """Maneja el cambio de auto-crear."""
        if self.auto_create_callback:
            self.auto_create_callback(self.auto_create_enabled.get())
    
    def _on_seed_apply(self):
        """Maneja la aplicación del seed."""
        try:
            seed = int(self.seed_var.get())
            if self.seed_apply_callback:
                self.seed_apply_callback(seed)
        except ValueError:
            pass  # Ignorar seeds inválidos
    
    def _set_auto_running(self, running: bool):
        """Establece el estado de ejecución automática."""
        if running:
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
        else:
            self.start_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
    
    def add_manual_tick_button(self, parent_frame):
        """Agrega el botón de tick manual al frame especificado."""
        self.tick_manual_button = ctk.CTkButton(
            parent_frame,
            text="⚡ Tick Manual",
            command=self._on_tick_manual,
            width=120,
            height=35
        )
        return self.tick_manual_button
    
    def _on_tick_manual(self):
        """Maneja el tick manual."""
        if self.tick_manual_callback:
            self.tick_manual_callback()
    
    # Métodos para establecer callbacks
    def set_start_auto_callback(self, callback: Callable):
        self.start_auto_callback = callback
    
    def set_pause_callback(self, callback: Callable):
        self.pause_callback = callback
    
    def set_reset_callback(self, callback: Callable):
        self.reset_callback = callback
    
    def set_tick_manual_callback(self, callback: Callable):
        self.tick_manual_callback = callback
    
    def set_quantum_change_callback(self, callback: Callable):
        self.quantum_change_callback = callback
    
    def set_speed_change_callback(self, callback: Callable):
        self.speed_change_callback = callback
    
    def set_auto_create_callback(self, callback: Callable):
        self.auto_create_callback = callback
    
    def set_seed_apply_callback(self, callback: Callable):
        self.seed_apply_callback = callback
