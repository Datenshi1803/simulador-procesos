"""
Punto de entrada principal del Simulador de Estados de Procesos.
"""
import sys
import argparse
from src.gui.main_window import MainWindow

def main():
    """Función principal de la aplicación."""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Simulador de Estados de Procesos')
    parser.add_argument('--demo', action='store_true', 
                       help='Inicia en modo demo automático')
    parser.add_argument('--quantum', type=int, default=3,
                       help='Quantum inicial para Round-Robin (default: 3)')
    parser.add_argument('--speed', type=float, default=1.0,
                       help='Velocidad inicial de simulación (default: 1.0)')
    
    args = parser.parse_args()
    
    try:
        # Crear y configurar la ventana principal
        app = MainWindow()
        
        # Aplicar configuraciones de línea de comandos
        if args.quantum != 3:
            app.simulator.set_quantum(args.quantum)
            app.control_panel.quantum_var.set(args.quantum)
        
        if args.speed != 1.0:
            app.speed = args.speed
            app.control_panel.speed_var.set(args.speed)
        
        # Modo demo
        if args.demo:
            print("🎮 Iniciando en modo DEMO automático...")
            # Crear algunos procesos para demostración
            app._create_initial_processes(3)  # Solo 3 procesos para demo
            app.control_panel.is_auto_mode.set(True)
            app.control_panel.auto_create_enabled.set(True)
            app.auto_create_enabled = True
            # Iniciar automáticamente después de un breve delay
            app.root.after(1000, app._start_auto_simulation)
        
        # Ejecutar la aplicación
        print("🚀 Iniciando Simulador de Estados de Procesos...")
        print("📋 Sistema inicializado sin procesos")
        print("💡 Usa el botón 'Crear Proceso' para agregar procesos al sistema")
        
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Simulación interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
