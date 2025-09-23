"""
Panel de métricas del sistema.
"""
import customtkinter as ctk
from typing import Dict, Optional, Callable

class MetricsPanel(ctk.CTkFrame):
    """Panel que muestra las métricas del sistema."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.export_callback: Optional[Callable] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Título - más compacto
        title_label = ctk.CTkLabel(
            self, 
            text="📊 Métricas del Sistema", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(8, 5))
        
        # Frame scrollable para métricas - más compacto
        self.metrics_frame = ctk.CTkScrollableFrame(
            self, 
            height=250,
            width=240,  # Más estrecho
            corner_radius=6,
            scrollbar_button_color=("gray70", "gray30"),
            scrollbar_button_hover_color=("gray60", "gray40")
        )
        self.metrics_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        
        # Diccionario para almacenar labels de métricas
        self.metric_labels = {}
        
        # Crear labels iniciales
        self._create_metric_labels()
        
        # Botón de exportar - más compacto
        self.export_button = ctk.CTkButton(
            self,
            text="💾 Exportar CSV",
            command=self._on_export,
            width=100,  # Más estrecho
            height=26,  # Más bajo
            font=ctk.CTkFont(size=9)
        )
        self.export_button.pack(pady=(3, 6))
    
    def _create_metric_labels(self):
        """Crea los labels para las métricas."""
        metrics_info = [
            ("tick", "⏰ Tick Actual", "0"),
            ("total_processes", "📋 Total Procesos", "0"),
            ("running", "🏃 Proceso Ejecutándose", "0"),
            ("ready", "✅ Cola READY", "0"),
            ("priority_info", "🎯 Colas Prioridad", ""),
            ("blocked", "⏸️ Procesos Bloqueados", "0"),
            ("zombie", "🧟 Zombies Activos", "0"),
            ("terminated", "❌ Procesos Terminados", "0"),
            ("cpu_utilization", "💻 CPU Utilización", "0.0%"),
            ("context_switches", "🔄 Context Switches", "0"),
            ("avg_turnaround", "⏱️ Turnaround Promedio", "0.0"),
            ("avg_waiting", "⏳ Tiempo Espera Promedio", "0.0")
        ]
        
        for key, label_text, default_value in metrics_info:
            # Frame para cada métrica - más compacto
            metric_frame = ctk.CTkFrame(self.metrics_frame, fg_color="transparent", height=24)
            metric_frame.pack(fill="x", pady=1, padx=2)
            metric_frame.pack_propagate(False)  # Mantener altura fija
            
            # Configurar grid para mejor alineación
            metric_frame.grid_columnconfigure(0, weight=1)
            metric_frame.grid_columnconfigure(1, weight=0)
            
            # Label de descripción - más pequeño
            desc_label = ctk.CTkLabel(
                metric_frame,
                text=label_text,
                font=ctk.CTkFont(size=9),
                anchor="w"
            )
            desc_label.grid(row=0, column=0, sticky="w", padx=(2, 3))
            
            # Label de valor - más compacto
            value_label = ctk.CTkLabel(
                metric_frame,
                text=default_value,
                font=ctk.CTkFont(size=9, weight="bold"),
                anchor="center",
                width=60,  # Más estrecho
                height=20,  # Más bajo
                fg_color=("gray75", "gray25"),
                corner_radius=3
            )
            value_label.grid(row=0, column=1, sticky="e", padx=(0, 2))
            
            self.metric_labels[key] = value_label
    
    def update_metrics(self, metrics: Dict):
        """Actualiza las métricas mostradas."""
        # Mapeo de métricas a formato de display
        metric_formats = {
            "tick": lambda x: str(x),
            "total_processes": lambda x: str(x),
            "running": lambda x: str(x),
            "ready": lambda x: str(x),
            "priority_info": lambda x: str(x),
            "blocked": lambda x: str(x),
            "zombie": lambda x: str(x),
            "terminated": lambda x: str(x),
            "cpu_utilization": lambda x: f"{x:.1f}%",
            "context_switches": lambda x: str(x),
            "avg_turnaround": lambda x: f"{x:.1f}",
            "avg_waiting": lambda x: f"{x:.1f}"
        }
        
        # Actualizar cada métrica
        for key, formatter in metric_formats.items():
            if key in metrics and key in self.metric_labels:
                formatted_value = formatter(metrics[key])
                self.metric_labels[key].configure(text=formatted_value)
    
    def _on_export(self):
        """Maneja la exportación de métricas."""
        if self.export_callback:
            self.export_callback()
    
    def set_export_callback(self, callback: Callable):
        """Establece el callback para exportar métricas."""
        self.export_callback = callback
