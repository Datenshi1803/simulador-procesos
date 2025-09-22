"""
Tests unitarios para el planificador Round-Robin.
"""
import unittest
from src.core.scheduler import RoundRobinScheduler
from src.models.process import Process

class TestRoundRobinScheduler(unittest.TestCase):
    """Tests para el planificador Round-Robin."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.scheduler = RoundRobinScheduler(quantum=3)
        self.process_table = {
            1: Process(pid=1, name="P1", state="READY"),
            2: Process(pid=2, name="P2", state="READY"),
            3: Process(pid=3, name="P3", state="READY")
        }
    
    def test_scheduler_initialization(self):
        """Test de inicialización del scheduler."""
        self.assertEqual(self.scheduler.quantum, 3)
        self.assertEqual(len(self.scheduler.ready_queue), 0)
        self.assertIsNone(self.scheduler.current_running_pid)
        self.assertEqual(self.scheduler.current_quantum_used, 0)
    
    def test_add_to_ready_queue(self):
        """Test de agregar procesos a la cola de listos."""
        self.scheduler.add_to_ready(1)
        self.scheduler.add_to_ready(2)
        
        self.assertEqual(len(self.scheduler.ready_queue), 2)
        self.assertIn(1, self.scheduler.ready_queue)
        self.assertIn(2, self.scheduler.ready_queue)
    
    def test_get_next_process(self):
        """Test de obtener el siguiente proceso."""
        self.scheduler.add_to_ready(1)
        self.scheduler.add_to_ready(2)
        
        next_pid = self.scheduler.get_next_process()
        self.assertEqual(next_pid, 1)  # FIFO
        
        next_pid = self.scheduler.get_next_process()
        self.assertEqual(next_pid, 2)
    
    def test_set_running_process(self):
        """Test de establecer proceso en ejecución."""
        success = self.scheduler.set_running(1, self.process_table)
        
        self.assertTrue(success)
        self.assertEqual(self.scheduler.current_running_pid, 1)
        self.assertEqual(self.process_table[1].state, "RUNNING")
        self.assertEqual(self.scheduler.current_quantum_used, 0)
    
    def test_preemption_by_quantum(self):
        """Test de preempción por quantum."""
        # Establecer proceso en ejecución
        self.scheduler.set_running(1, self.process_table)
        
        # Simular uso de quantum
        for _ in range(3):  # quantum = 3
            self.scheduler.tick()
        
        # Intentar preempción
        preempted = self.scheduler.preempt_current(self.process_table)
        
        self.assertTrue(preempted)
        self.assertEqual(self.process_table[1].state, "READY")
        self.assertIsNone(self.scheduler.current_running_pid)
        self.assertIn(1, self.scheduler.ready_queue)
    
    def test_remove_from_ready(self):
        """Test de remover proceso de la cola de listos."""
        self.scheduler.add_to_ready(1)
        self.scheduler.add_to_ready(2)
        self.scheduler.add_to_ready(3)
        
        self.scheduler.remove_from_ready(2)
        
        self.assertEqual(len(self.scheduler.ready_queue), 2)
        self.assertNotIn(2, self.scheduler.ready_queue)
        self.assertIn(1, self.scheduler.ready_queue)
        self.assertIn(3, self.scheduler.ready_queue)
    
    def test_scheduler_reset(self):
        """Test de reinicio del scheduler."""
        # Configurar estado
        self.scheduler.add_to_ready(1)
        self.scheduler.set_running(2, self.process_table)
        self.scheduler.context_switches = 5
        
        # Reiniciar
        self.scheduler.reset()
        
        # Verificar estado limpio
        self.assertEqual(len(self.scheduler.ready_queue), 0)
        self.assertIsNone(self.scheduler.current_running_pid)
        self.assertEqual(self.scheduler.current_quantum_used, 0)
        self.assertEqual(self.scheduler.context_switches, 0)

if __name__ == '__main__':
    unittest.main()
