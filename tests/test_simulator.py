"""
Tests unitarios para el motor de simulación.
"""
import unittest
from src.core.simulator import SimulatorEngine

class TestSimulatorEngine(unittest.TestCase):
    """Tests para el motor de simulación."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.simulator = SimulatorEngine()
    
    def test_simulator_initialization(self):
        """Test de inicialización del simulador."""
        self.assertEqual(self.simulator.tick, 0)
        self.assertEqual(self.simulator.pid_counter, 1)
        self.assertIn(0, self.simulator.process_table)  # Proceso init
        self.assertEqual(self.simulator.process_table[0].name, "init")
    
    def test_create_process(self):
        """Test de creación de procesos."""
        pid = self.simulator.create_process("TestProcess", 10)
        
        self.assertEqual(pid, 1)
        self.assertIn(pid, self.simulator.process_table)
        
        process = self.simulator.process_table[pid]
        self.assertEqual(process.name, "TestProcess")
        self.assertEqual(process.total_burst, 10)
        self.assertEqual(process.state, "NEW")
    
    def test_create_child_process(self):
        """Test de creación de procesos hijo."""
        # Crear proceso padre
        parent_pid = self.simulator.create_process("Parent")
        
        # Crear proceso hijo
        child_pid = self.simulator.create_process("Child", parent_pid=parent_pid)
        
        parent = self.simulator.process_table[parent_pid]
        child = self.simulator.process_table[child_pid]
        
        self.assertEqual(child.parent_pid, parent_pid)
        self.assertIn(child_pid, parent.children)
    
    def test_move_new_to_ready(self):
        """Test de transición NEW → READY."""
        # Crear algunos procesos
        pid1 = self.simulator.create_process()
        pid2 = self.simulator.create_process()
        
        # Mover a READY
        count = self.simulator.move_new_to_ready()
        
        self.assertEqual(count, 2)
        self.assertEqual(self.simulator.process_table[pid1].state, "READY")
        self.assertEqual(self.simulator.process_table[pid2].state, "READY")
    
    def test_force_block_process(self):
        """Test de forzar bloqueo de proceso."""
        # Crear y preparar proceso
        pid = self.simulator.create_process()
        self.simulator.move_new_to_ready()
        
        # Forzar bloqueo
        success = self.simulator.force_block_process(pid, 5)
        
        self.assertTrue(success)
        self.assertEqual(self.simulator.process_table[pid].state, "BLOCKED")
        self.assertEqual(self.simulator.process_table[pid].io_remaining, 5)
        self.assertIn(pid, self.simulator.blocked_list)
    
    def test_force_terminate_process(self):
        """Test de forzar terminación de proceso."""
        # Crear proceso
        pid = self.simulator.create_process()
        
        # Forzar terminación
        success = self.simulator.force_terminate_process(pid)
        
        self.assertTrue(success)
        process = self.simulator.process_table[pid]
        self.assertIn(process.state, ["TERMINATED", "ZOMBIE"])
        self.assertEqual(process.remaining_burst, 0)
    
    def test_wait_for_child(self):
        """Test de operación wait() para reapear zombies."""
        # Crear padre e hijo
        parent_pid = self.simulator.create_process("Parent")
        child_pid = self.simulator.create_process("Child", parent_pid=parent_pid)
        
        # Hacer que el hijo sea zombie
        child = self.simulator.process_table[child_pid]
        child.state = "ZOMBIE"
        self.simulator.zombie_list.append(child_pid)
        
        # Ejecutar wait
        reaped = self.simulator.wait_for_child(parent_pid)
        
        self.assertEqual(len(reaped), 1)
        self.assertEqual(reaped[0], child_pid)
        self.assertEqual(child.state, "TERMINATED")
        self.assertTrue(child.reaped)
        self.assertNotIn(child_pid, self.simulator.zombie_list)
    
    def test_tick_simulation(self):
        """Test de ejecución de tick de simulación."""
        initial_tick = self.simulator.tick
        
        # Crear algunos procesos
        self.simulator.create_process()
        self.simulator.create_process()
        
        # Ejecutar tick
        self.simulator.tick_simulation()
        
        # Verificar que el tick avanzó
        self.assertEqual(self.simulator.tick, initial_tick + 1)
    
    def test_get_metrics(self):
        """Test de obtención de métricas."""
        # Crear algunos procesos
        self.simulator.create_process()
        self.simulator.create_process()
        
        metrics = self.simulator.get_metrics()
        
        # Verificar que las métricas tienen las claves esperadas
        expected_keys = [
            'tick', 'total_processes', 'running', 'ready', 'blocked',
            'zombie', 'terminated', 'cpu_utilization', 'context_switches',
            'avg_turnaround', 'avg_waiting'
        ]
        
        for key in expected_keys:
            self.assertIn(key, metrics)
    
    def test_reset_simulator(self):
        """Test de reinicio del simulador."""
        # Crear algunos procesos y avanzar simulación
        self.simulator.create_process()
        self.simulator.create_process()
        self.simulator.tick_simulation()
        
        # Reiniciar
        self.simulator.reset()
        
        # Verificar estado inicial
        self.assertEqual(self.simulator.tick, 0)
        self.assertEqual(self.simulator.pid_counter, 1)
        self.assertEqual(len(self.simulator.process_table), 1)  # Solo init
        self.assertIn(0, self.simulator.process_table)  # Proceso init

if __name__ == '__main__':
    unittest.main()
