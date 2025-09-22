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
        # Título
        title_label = ctk.CTkLabel(
            self, 
            text="📊 Métricas del Sistema", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Frame scrollable para métricas
        self.metrics_frame = ctk.CTkScrollableFrame(self, height=300)
        self.metrics_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Diccionario para almacenar labels de métricas
        self.metric_labels = {}
        
        # Crear labels iniciales
        self._create_metric_labels()
        
        # Botón de exportar
        self.export_button = ctk.CTkButton(
            self,
            text="💾 Exportar CSV",
            command=self._on_export,
            width=120,
            height=30
        )
        self.export_button.pack(pady=10)
    
    def _create_metric_labels(self):
        """Crea los labels para las métricas."""
        metrics_info = [
            ("tick", "⏰ Tick Actual", "0"),
            ("total_processes", "📋 Total Procesos", "0"),
            ("cpu_utilization", "💻 CPU Utilización", "0.0%"),
            ("context_switches", "🔄 Context Switches", "0"),
            ("zombie", "🧟 Zombies Activos", "0"),
            ("avg_turnaround", "⏱️ Turnaround Promedio", "0.0"),
            ("avg_waiting", "⏳ Tiempo Espera Promedio", "0.0"),
            ("ready", "✅ Cola READY", "0"),
            ("blocked", "⏸️ Procesos Bloqueados", "0"),
            ("terminated", "❌ Procesos Terminados", "0")
        ]
        
        for key, label_text, default_value in metrics_info:
            # Frame para cada métrica
            metric_frame = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
            metric_frame.pack(fill="x", pady=2)
            
            # Label de descripción
            desc_label = ctk.CTkLabel(
                metric_frame,
                text=label_text,
                font=ctk.CTkFont(size=12),
                anchor="w"
            )
            desc_label.pack(side="left", fill="x", expand=True)
            
            # Label de valor
            value_label = ctk.CTkLabel(
                metric_frame,
                text=default_value,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="e",
                width=80
            )
            value_label.pack(side="right")
            
            self.metric_labels[key] = value_label
    
    def update_metrics(self, metrics: Dict):
        """Actualiza las métricas mostradas."""
        # Mapeo de métricas a formato de display
        metric_formats = {
            "tick": lambda x: str(x),
            "total_processes": lambda x: str(x),
            "cpu_utilization": lambda x: f"{x:.1f}%",
            "context_switches": lambda x: str(x),
            "zombie": lambda x: str(x),
            "avg_turnaround": lambda x: f"{x:.1f}",
            "avg_waiting": lambda x: f"{x:.1f}",
            "ready": lambda x: str(x),
            "blocked": lambda x: str(x),
            "terminated": lambda x: str(x)
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
