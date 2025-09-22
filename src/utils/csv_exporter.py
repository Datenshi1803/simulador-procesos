"""
Utilidades para exportar datos a CSV.
"""
import csv
from typing import Dict, List
from datetime import datetime
from ..models.process import Process

class CSVExporter:
    """Exportador de datos a formato CSV."""
    
    @staticmethod
    def export_metrics(metrics: Dict, filename: str):
        """Exporta métricas del sistema a CSV."""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Encabezado
            writer.writerow(['Timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            writer.writerow(['Métricas del Sistema'])
            writer.writerow(['Métrica', 'Valor'])
            
            # Métricas
            for key, value in metrics.items():
                writer.writerow([key, value])
    
    @staticmethod
    def export_processes(process_table: Dict[int, Process], filename: str):
        """Exporta información de procesos a CSV."""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Encabezado
            writer.writerow(['Timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            writer.writerow(['Información de Procesos'])
            writer.writerow([
                'PID', 'Nombre', 'Estado', 'Total_Burst', 'Restante_Burst',
                'Padre_PID', 'Creado_Tick', 'Inicio_Tick', 'Fin_Tick',
                'Turnaround_Time', 'Waiting_Time', 'Blocked_Count', 'Preempt_Count'
            ])
            
            # Procesos (excluyendo init)
            for pid, process in sorted(process_table.items()):
                if pid == 0:  # Saltar proceso init
                    continue
                
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
                    process.get_waiting_time() or '',
                    process.blocked_count,
                    process.preempt_count
                ])
    
    @staticmethod
    def export_complete_report(metrics: Dict, process_table: Dict[int, Process], 
                             event_logs: List[str], filename: str):
        """Exporta un reporte completo del sistema."""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Encabezado del reporte
            writer.writerow(['Reporte Completo del Simulador de Procesos'])
            writer.writerow(['Generado:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Métricas del sistema
            writer.writerow(['=== MÉTRICAS DEL SISTEMA ==='])
            writer.writerow(['Métrica', 'Valor'])
            for key, value in metrics.items():
                writer.writerow([key, value])
            writer.writerow([])
            
            # Información de procesos
            writer.writerow(['=== INFORMACIÓN DE PROCESOS ==='])
            writer.writerow([
                'PID', 'Nombre', 'Estado', 'Total_Burst', 'Restante_Burst',
                'Padre_PID', 'Creado_Tick', 'Inicio_Tick', 'Fin_Tick',
                'Turnaround_Time', 'Waiting_Time', 'Blocked_Count', 'Preempt_Count'
            ])
            
            for pid, process in sorted(process_table.items()):
                if pid == 0:  # Saltar proceso init
                    continue
                
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
                    process.get_waiting_time() or '',
                    process.blocked_count,
                    process.preempt_count
                ])
            
            writer.writerow([])
            
            # Log de eventos (últimos 50)
            writer.writerow(['=== LOG DE EVENTOS (Últimos 50) ==='])
            writer.writerow(['Evento'])
            for event in event_logs:
                writer.writerow([event])
