"""
Utilidades para formatear y mostrar árboles de procesos.
"""
from typing import Dict, List
from ..models.process import Process

class ProcessTreeFormatter:
    """Formateador para árboles de procesos."""
    
    @staticmethod
    def format_tree_text(tree: Dict, show_details: bool = False) -> str:
        """Formatea un árbol de procesos como texto."""
        if not tree:
            return "No hay procesos en el árbol"
        
        result = "🌳 Árbol de Procesos\n"
        result += "=" * 50 + "\n\n"
        
        for pid, subtree in tree.items():
            result += ProcessTreeFormatter._format_subtree(subtree, 0, show_details)
        
        return result
    
    @staticmethod
    def _format_subtree(subtree: Dict, level: int, show_details: bool) -> str:
        """Formatea un subárbol recursivamente."""
        if 'process' not in subtree:
            return ""
        
        process = subtree['process']
        indent = "  " * level
        
        # Símbolo del nodo
        if level == 0:
            symbol = "🔸"
        else:
            symbol = "├─"
        
        # Información básica
        result = f"{indent}{symbol} PID {process.pid}: {process.name} [{process.state}]"
        
        # Detalles adicionales si se solicitan
        if show_details:
            result += f" (Burst: {process.remaining_burst}/{process.total_burst})"
            if process.parent_pid:
                result += f" (Padre: {process.parent_pid})"
        
        result += "\n"
        
        # Procesar hijos
        if subtree['children']:
            for child_pid, child_subtree in subtree['children'].items():
                result += ProcessTreeFormatter._format_subtree(child_subtree, level + 1, show_details)
        
        return result
    
    @staticmethod
    def get_process_hierarchy(process_table: Dict[int, Process]) -> List[Dict]:
        """Obtiene la jerarquía de procesos como lista."""
        hierarchy = []
        
        # Encontrar procesos raíz (sin padre o padre no existe)
        root_processes = []
        for pid, process in process_table.items():
            if process.parent_pid is None or process.parent_pid not in process_table:
                root_processes.append(process)
        
        # Construir jerarquía para cada raíz
        for root in root_processes:
            hierarchy.append(ProcessTreeFormatter._build_hierarchy_node(root, process_table))
        
        return hierarchy
    
    @staticmethod
    def _build_hierarchy_node(process: Process, process_table: Dict[int, Process]) -> Dict:
        """Construye un nodo de jerarquía."""
        node = {
            'pid': process.pid,
            'name': process.name,
            'state': process.state,
            'children': []
        }
        
        # Agregar hijos
        for child_pid in process.children:
            if child_pid in process_table:
                child_process = process_table[child_pid]
                child_node = ProcessTreeFormatter._build_hierarchy_node(child_process, process_table)
                node['children'].append(child_node)
        
        return node
