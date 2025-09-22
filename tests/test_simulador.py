#!/usr/bin/env python3
"""
Tests unitarios para el Simulador de Estados de Procesos
========================================================

Pruebas básicas para verificar el funcionamiento correcto
de las funciones principales del simulador.
"""

import unittest
import sys
import os

# Agregar el directorio padre al path para importar el módulo principal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulador_procesos_customtk import SimulatorEngine, Process

class TestSimulatorEngine(unittest.TestCase):
    """Tests para la clase SimulatorEngine."""
    
    def setUp(self):
        """Configuración inicial para cada test."""
        self.engine = SimulatorEngine()
    
    def test_create_process(self):
        """Test creación de procesos."""
        # Test creación básica
        pid = self.engine.create_process()
        self.assertIn(pid, self.engine.process_table)
        self.assertEqual(self.engine.process_table[pid].state, 'NEW')
        
        # Test creación con parámetros
        pid2 = self.engine.create_process("TestProcess", 10, None)
        process = self.engine.process_table[pid2]
        self.assertEqual(process.name, "TestProcess")
        self.assertEqual(process.total_burst, 10)
        self.assertEqual(process.remaining_burst, 10)
    
    def test_create_child_process(self):
        """Test creación de procesos hijo."""
        # Crear padre
        parent_pid = self.engine.create_process("Padre")
        
        # Crear hijo
        child_pid = self.engine.create_process("Hijo", 5, parent_pid)
        
        # Verificar relación padre-hijo
        parent = self.engine.process_table[parent_pid]
        child = self.engine.process_table[child_pid]
        
        self.assertEqual(child.parent_pid, parent_pid)
        self.assertIn(child_pid, parent.children)
    
    def test_move_new_to_ready(self):
        """Test movimiento de NEW a READY."""
        # Crear algunos procesos
        pids = []
        for i in range(3):
            pids.append(self.engine.create_process(f"P{i}"))
        
        # Verificar que están en NEW
        for pid in pids:
            self.assertEqual(self.engine.process_table[pid].state, 'NEW')
        
        # Mover a READY
        moved = self.engine.move_new_to_ready()
        self.assertEqual(moved, 3)
        
        # Verificar que están en READY y en la cola
        for pid in pids:
            self.assertEqual(self.engine.process_table[pid].state, 'READY')
            self.assertIn(pid, self.engine.ready_queue)
    
    def test_force_block_process(self):
        """Test bloqueo forzado de procesos."""
        # Crear y mover proceso a READY
        pid = self.engine.create_process("TestBlock")
        self.engine.move_new_to_ready()
        
        # Bloquear proceso
        success = self.engine.force_block_process(pid, 5)
        self.assertTrue(success)
        
        process = self.engine.process_table[pid]
        self.assertEqual(process.state, 'BLOCKED')
        self.assertEqual(process.io_remaining, 5)
        self.assertIn(pid, self.engine.blocked_list)
        self.assertEqual(process.blocked_count, 1)
    
    def test_force_terminate_process(self):
        """Test terminación forzada de procesos."""
        # Crear proceso
        pid = self.engine.create_process("TestTerminate")
        
        # Terminar proceso
        success = self.engine.force_terminate_process(pid)
        self.assertTrue(success)
        
        process = self.engine.process_table[pid]
        self.assertEqual(process.remaining_burst, 0)
        self.assertIsNotNone(process.end_tick)
        self.assertIn(process.state, ['TERMINATED', 'ZOMBIE'])
    
    def test_zombie_creation(self):
        """Test creación de procesos zombie."""
        # Crear padre e hijo
        parent_pid = self.engine.create_process("Padre")
        child_pid = self.engine.create_process("Hijo", 1, parent_pid)
        
        # Terminar hijo (debería volverse zombie)
        self.engine.force_terminate_process(child_pid)
        
        child = self.engine.process_table[child_pid]
        self.assertEqual(child.state, 'ZOMBIE')
        self.assertIn(child_pid, self.engine.zombie_list)
    
    def test_wait_reap_zombies(self):
        """Test reaping de procesos zombie."""
        # Crear padre e hijo
        parent_pid = self.engine.create_process("Padre")
        child_pid = self.engine.create_process("Hijo", 1, parent_pid)
        
        # Terminar hijo (zombie)
        self.engine.force_terminate_process(child_pid)
        self.assertEqual(self.engine.process_table[child_pid].state, 'ZOMBIE')
        
        # Reapear zombie
        reaped = self.engine.wait_for_child(parent_pid)
        self.assertEqual(len(reaped), 1)
        self.assertEqual(reaped[0], child_pid)
        
        # Verificar que ya no es zombie
        child = self.engine.process_table[child_pid]
        self.assertEqual(child.state, 'TERMINATED')
        self.assertTrue(child.reaped)
        self.assertNotIn(child_pid, self.engine.zombie_list)
    
    def test_blocked_process_unblocking(self):
        """Test desbloqueo automático de procesos."""
        # Crear y bloquear proceso
        pid = self.engine.create_process("TestUnblock")
        self.engine.move_new_to_ready()
        self.engine.force_block_process(pid, 2)  # 2 ticks de I/O
        
        # Simular ticks para desbloquear
        initial_state = self.engine.process_table[pid].state
        self.assertEqual(initial_state, 'BLOCKED')
        
        # Primer tick - aún bloqueado
        self.engine._handle_blocked_processes()
        self.assertEqual(self.engine.process_table[pid].io_remaining, 1)
        self.assertEqual(self.engine.process_table[pid].state, 'BLOCKED')
        
        # Segundo tick - debería desbloquearse
        self.engine._handle_blocked_processes()
        self.assertEqual(self.engine.process_table[pid].io_remaining, 0)
        self.assertEqual(self.engine.process_table[pid].state, 'READY')
        self.assertIn(pid, self.engine.ready_queue)
        self.assertNotIn(pid, self.engine.blocked_list)
    
    def test_scheduler_round_robin(self):
        """Test básico del scheduler Round-Robin."""
        # Crear procesos y moverlos a READY
        pids = []
        for i in range(3):
            pids.append(self.engine.create_process(f"P{i}", 10))
        self.engine.move_new_to_ready()
        
        # Verificar que no hay proceso ejecutándose
        self.assertIsNone(self.engine.current_running_pid)
        
        # Ejecutar scheduler
        self.engine._schedule_processes()
        
        # Debería haber tomado el primer proceso de la cola
        self.assertIsNotNone(self.engine.current_running_pid)
        self.assertEqual(self.engine.current_running_pid, pids[0])
        self.assertEqual(self.engine.process_table[pids[0]].state, 'RUNNING')
    
    def test_metrics_calculation(self):
        """Test cálculo de métricas."""
        # Crear algunos procesos
        for i in range(3):
            self.engine.create_process(f"P{i}", 5)
        
        # Obtener métricas
        metrics = self.engine.get_metrics()
        
        # Verificar métricas básicas
        self.assertIn('tick', metrics)
        self.assertIn('total_processes', metrics)
        self.assertIn('cpu_utilization', metrics)
        self.assertIn('context_switches', metrics)
        self.assertIn('zombies_count', metrics)
        
        # Verificar valores iniciales
        self.assertEqual(metrics['total_processes'], 3)
        self.assertEqual(metrics['context_switches'], 0)
        self.assertEqual(metrics['zombies_count'], 0)

class TestProcess(unittest.TestCase):
    """Tests para la clase Process."""
    
    def test_process_creation(self):
        """Test creación de proceso."""
        process = Process(
            pid=1,
            name="TestProcess",
            total_burst=10,
            remaining_burst=10
        )
        
        self.assertEqual(process.pid, 1)
        self.assertEqual(process.name, "TestProcess")
        self.assertEqual(process.state, 'NEW')  # Estado por defecto
        self.assertEqual(process.total_burst, 10)
        self.assertEqual(process.remaining_burst, 10)
        self.assertIsNone(process.parent_pid)
        self.assertEqual(len(process.children), 0)

def run_tests():
    """Ejecuta todos los tests."""
    print("🧪 Ejecutando tests del Simulador de Procesos...")
    print("=" * 50)
    
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestSimulatorEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestProcess))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ Todos los tests pasaron correctamente!")
    else:
        print(f"❌ {len(result.failures)} tests fallaron")
        print(f"💥 {len(result.errors)} tests tuvieron errores")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests()
