"""
Tests unitarios para el modelo Process.
"""
import unittest
from src.models.process import Process

class TestProcess(unittest.TestCase):
    """Tests para la clase Process."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.process = Process(
            pid=1,
            name="TestProcess",
            state="NEW",
            total_burst=10,
            remaining_burst=10,
            created_tick=0
        )
    
    def test_process_creation(self):
        """Test de creación de proceso."""
        self.assertEqual(self.process.pid, 1)
        self.assertEqual(self.process.name, "TestProcess")
        self.assertEqual(self.process.state, "NEW")
        self.assertEqual(self.process.total_burst, 10)
        self.assertEqual(self.process.remaining_burst, 10)
    
    def test_turnaround_time_calculation(self):
        """Test de cálculo de turnaround time."""
        # Sin tiempo de fin
        self.assertIsNone(self.process.get_turnaround_time())
        
        # Con tiempo de fin
        self.process.end_tick = 15
        self.assertEqual(self.process.get_turnaround_time(), 15)
    
    def test_waiting_time_calculation(self):
        """Test de cálculo de waiting time."""
        # Sin tiempos de inicio/fin
        self.assertIsNone(self.process.get_waiting_time())
        
        # Con tiempos completos
        self.process.start_tick = 5
        self.process.end_tick = 20
        expected_waiting = 20 - 0 - 10  # end - created - burst
        self.assertEqual(self.process.get_waiting_time(), expected_waiting)
    
    def test_is_finished(self):
        """Test de verificación de proceso terminado."""
        # Proceso nuevo
        self.assertFalse(self.process.is_finished())
        
        # Proceso terminado
        self.process.state = "TERMINATED"
        self.assertTrue(self.process.is_finished())
        
        # Proceso zombie
        self.process.state = "ZOMBIE"
        self.assertTrue(self.process.is_finished())
    
    def test_parent_child_relationship(self):
        """Test de relaciones padre-hijo."""
        parent = Process(pid=1, name="Parent")
        child = Process(pid=2, name="Child", parent_pid=1)
        
        # Agregar hijo al padre
        parent.children.append(child.pid)
        
        self.assertEqual(child.parent_pid, 1)
        self.assertIn(child.pid, parent.children)

if __name__ == '__main__':
    unittest.main()
