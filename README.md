# 🖥️ Simulador de Estados de Procesos

Un simulador profesional de gestión de procesos con **arquitectura modular** e interfaz moderna que implementa los estados: **NEW**, **READY**, **RUNNING**, **BLOCKED**, **ZOMBIE**, **TERMINATED**.

![Simulador de Procesos](https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-DLcXKmkB5YOnDylZRu2tWk14uDCOYb.png)

## 🚀 Instalación Rápida

\`\`\`bash
# Clonar o descargar el proyecto
git clone <repository-url>
cd simulador-procesos

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el simulador
python main.py

# Modo demo automático
python main.py --demo

# Con configuraciones personalizadas
python main.py --quantum 5 --speed 2.0
\`\`\`

## 🏗️ Arquitectura del Proyecto

### **Estructura Modular Profesional**

\`\`\`
simulador-procesos/
├── main.py                    # Punto de entrada principal
├── requirements.txt           # Dependencias Python
├── README.md                 # Documentación completa
├── src/                      # Código fuente modular
│   ├── __init__.py
│   ├── models/               # Modelos de datos
│   │   ├── __init__.py
│   │   └── process.py        # Clase Process
│   ├── core/                 # Lógica del simulador
│   │   ├── __init__.py
│   │   ├── simulator.py      # Motor principal
│   │   └── scheduler.py      # Planificador Round-Robin
│   ├── gui/                  # Interfaz gráfica
│   │   ├── __init__.py
│   │   ├── main_window.py    # Ventana principal
│   │   └── components/       # Componentes UI
│   │       ├── __init__.py
│   │       ├── process_table.py    # Tabla de procesos
│   │       ├── control_panel.py    # Panel de control
│   │       ├── action_panel.py     # Panel de acciones
│   │       └── metrics_panel.py    # Panel de métricas
│   └── utils/                # Utilidades
│       ├── __init__.py
│       ├── tree_formatter.py # Formateo de árboles
│       └── csv_exporter.py   # Exportación CSV
└── tests/                    # Tests unitarios
    ├── __init__.py
    ├── test_process.py       # Tests del modelo Process
    ├── test_simulator.py     # Tests del simulador
    └── test_scheduler.py     # Tests del planificador
\`\`\`

### **Beneficios de la Arquitectura Modular**

- ✅ **Separación de responsabilidades**: Cada módulo tiene una función específica
- ✅ **Mantenibilidad**: Fácil de modificar y extender
- ✅ **Testabilidad**: Cada componente se puede probar independientemente
- ✅ **Reutilización**: Los módulos se pueden usar en otros proyectos
- ✅ **Escalabilidad**: Fácil agregar nuevas funcionalidades

## 📖 ¿Cómo Funciona el Programa?

### 🎯 Concepto Principal
El simulador emula un **sistema operativo real** donde los procesos pasan por diferentes estados durante su ciclo de vida. Utiliza un **planificador Round-Robin** que asigna tiempo de CPU (quantum) a cada proceso de forma equitativa.

### 🔄 Ciclo de Vida de un Proceso

\`\`\`
NEW → READY → RUNNING → [BLOCKED] → READY → RUNNING → TERMINATED → ZOMBIE → [REAPED]
\`\`\`

1. **NEW** 🟡: Proceso recién creado, aún no listo para ejecutar
2. **READY** 🟢: Proceso listo, esperando su turno de CPU
3. **RUNNING** 🔵: Proceso ejecutándose actualmente (solo uno a la vez)
4. **BLOCKED** 🔴: Proceso esperando operación I/O
5. **TERMINATED** ⚪: Proceso terminado, liberando recursos
6. **ZOMBIE** 🟣: Proceso terminado esperando que su padre lo "reapee"

## 🎮 Guía de Uso Paso a Paso

### 1️⃣ **Panel de Control Superior**

**Controles Principales:**
- **▶️ Start Auto**: Inicia simulación automática (recomendado para principiantes)
- **⏸️ Pause**: Pausa la simulación para observar estados
- **🔄 Reset**: Reinicia todo el sistema

**Configuraciones:**
- **Quantum (3)**: Tiempo de CPU que recibe cada proceso antes de ser interrumpido
- **Velocidad**: Qué tan rápido avanza la simulación (slider)
- **Auto-crear**: Crea procesos nuevos automáticamente durante la simulación
- **Seed (42)**: Número para reproducir exactamente los mismos resultados

### 2️⃣ **Tabla Central de Procesos**

**🔧 SOLUCIÓN AL PROBLEMA DE SELECCIÓN PADRE-HIJO:**
- **Paso 1**: Haz clic en cualquier fila de la tabla para seleccionar un proceso padre
- **Paso 2**: El panel de acciones mostrará "Seleccionado: PID X (Nombre)"
- **Paso 3**: Ahora el botón "👶 Crear Hijo" estará habilitado
- **Paso 4**: Haz clic en "Crear Hijo" para crear un proceso hijo del seleccionado

Cada fila representa un proceso con información detallada:

| Columna | Significado | Ejemplo |
|---------|-------------|---------|
| **PID** | Identificador único | 1, 2, 3... |
| **Nombre** | Nombre del proceso | P1, P2, P3... |
| **Estado** | Estado actual (con color) | NEW, READY, RUNNING |
| **Restante** | Tiempo de CPU que le falta | 5, 8, 12... |
| **Total** | Tiempo total de CPU necesario | 15, 20, 25... |
| **Padre** | Proceso que lo creó | -, 1, 2... |
| **IO_Rem** | Tiempo de I/O restante | -, 3, 7... |
| **#Bloq** | Veces que se ha bloqueado | 0, 1, 2... |
| **#Preempt** | Veces interrumpido por quantum | 0, 1, 3... |

### 3️⃣ **Panel de Acciones (Derecha)**

**Gestión de Procesos:**
- **➕ Crear Proceso**: Añade un nuevo proceso al sistema
- **👶 Crear Hijo**: Crea un proceso hijo del seleccionado *(requiere selección)*
- **🔄 NEW → READY**: Mueve procesos de NEW a READY (necesario para que ejecuten)

**Control de Estados:**
- **⏸️ Forzar Bloqueo**: Simula que un proceso necesita I/O *(requiere selección)*
- **❌ Forzar Terminar**: Termina un proceso inmediatamente *(requiere selección)*
- **👻 Wait (Reap)**: El proceso padre "reapea" a sus hijos zombie *(requiere selección)*

**Herramientas:**
- **🌳 Ver Árbol**: Muestra relaciones padre-hijo
- **📊 Tick Manual**: Avanza un paso en modo manual

### 4️⃣ **Métricas del Sistema (Abajo Derecha)**

Estadísticas en tiempo real:
- **Tick Actual**: Tiempo transcurrido en la simulación
- **Total Procesos**: Cuántos procesos existen
- **CPU Utilización**: Porcentaje de tiempo que la CPU está ocupada
- **Context Switches**: Cambios entre procesos
- **Zombies Activos**: Procesos terminados sin reapear
- **Turnaround Promedio**: Tiempo promedio desde creación hasta terminación

## 🧪 Experimentos Recomendados

### **Experimento 1: Observar Round-Robin**
1. Ejecutar en modo demo: `python main.py --demo`
2. Observar cómo los procesos se turnan en estado RUNNING
3. Cambiar el quantum a 1 y ver preempciones más frecuentes

### **Experimento 2: Gestión de Zombies**
1. Pausar la simulación
2. Crear un proceso padre: "Crear Proceso"
3. **Hacer clic en la fila del proceso padre en la tabla**
4. Verificar que aparece "Seleccionado: PID X" en el panel de acciones
5. Hacer clic en "👶 Crear Hijo" (ahora habilitado)
6. Esperar que el hijo termine (se vuelve ZOMBIE 🟣)
7. **Seleccionar nuevamente el padre** y usar "Wait (Reap)" para limpiarlo

### **Experimento 3: Bloqueos por I/O**
1. **Hacer clic en un proceso** en READY o RUNNING en la tabla
2. Usar "Forzar Bloqueo" (aparecerá en rojo 🔴)
3. Observar cómo regresa a READY cuando termina el I/O

### **Experimento 4: Análisis de Rendimiento**
1. Ejecutar simulación por varios minutos
2. Observar métricas: CPU utilization, context switches
3. Exportar datos a CSV para análisis detallado
4. Cambiar quantum y comparar resultados

## 🎨 Interpretación de Colores

- 🟡 **NEW (Amarillo)**: "Recién nacido, aún no listo"
- 🟢 **READY (Verde)**: "Listo para trabajar, esperando turno"
- 🔵 **RUNNING (Azul)**: "Trabajando activamente"
- 🔴 **BLOCKED (Rojo)**: "Esperando algo (I/O), no puede continuar"
- 🟣 **ZOMBIE (Morado)**: "Terminado pero no limpiado"
- ⚪ **TERMINATED (Gris)**: "Completamente finalizado"

## 🔧 Configuraciones Avanzadas

### **Argumentos de Línea de Comandos**
\`\`\`bash
python main.py --help                    # Ver todas las opciones
python main.py --demo                    # Modo demo automático
python main.py --quantum 5               # Quantum personalizado
python main.py --speed 2.0               # Velocidad personalizada
python main.py --demo --quantum 1        # Combinar opciones
\`\`\`

### **Quantum (Tiempo de CPU)**
- **Quantum bajo (1-2)**: Más interrupciones, mejor respuesta interactiva
- **Quantum alto (10-20)**: Menos interrupciones, mejor throughput

### **Velocidad de Simulación**
- **Rápida (5.0)**: Para análisis de rendimiento
- **Lenta (0.1)**: Para observar transiciones paso a paso

### **Auto-creación de Procesos**
- **Activada**: Simula un sistema real con procesos llegando constantemente
- **Desactivada**: Control total sobre cuándo crear procesos

## 🐛 Solución de Problemas

**"Los procesos no se mueven de NEW"**
→ Usar el botón "NEW → READY" para activarlos

**"No veo procesos RUNNING"**
→ Asegurarse de que hay procesos en READY y la simulación está corriendo

**"No puedo crear procesos hijo"** *(ARREGLADO)*
→ **Hacer clic en una fila de la tabla** para seleccionar el proceso padre primero

**"Los botones están deshabilitados"**
→ Seleccionar un proceso haciendo clic en su fila en la tabla

**"Muchos zombies acumulándose"**
→ Seleccionar procesos padre y usar "Wait (Reap)" regularmente

**"Simulación muy rápida/lenta"**
→ Ajustar el slider de velocidad en el panel superior

## 📊 Casos de Uso Educativos

### **Para Estudiantes de Sistemas Operativos:**
- Visualizar conceptos abstractos de planificación
- Entender el problema de los procesos zombie
- Experimentar con diferentes políticas de quantum
- Analizar métricas de rendimiento

### **Para Profesores:**
- Demostrar Round-Robin scheduling en tiempo real
- Mostrar el impacto del quantum en el rendimiento
- Explicar relaciones padre-hijo entre procesos
- Generar datos para análisis estadístico

### **Para Desarrolladores:**
- Estudiar arquitectura modular de aplicaciones
- Aprender patrones de diseño en Python
- Entender separación de responsabilidades
- Ejemplo de testing unitario

## 🧪 Testing y Desarrollo

### **Ejecutar Tests**
\`\`\`bash
# Ejecutar todos los tests
python -m pytest tests/

# Ejecutar tests específicos
python -m pytest tests/test_simulator.py

# Ejecutar con cobertura
python -m pytest tests/ --cov=src
\`\`\`

### **Estructura de Tests**
- `test_process.py`: Tests del modelo de datos Process
- `test_simulator.py`: Tests del motor de simulación
- `test_scheduler.py`: Tests del planificador Round-Robin

## 🏆 Características Técnicas

- ✅ **Arquitectura modular** con separación clara de responsabilidades
- ✅ **Interfaz moderna** con CustomTkinter y tema oscuro
- ✅ **Planificador Round-Robin** con preempción por quantum
- ✅ **6 estados de proceso** completamente implementados
- ✅ **Gestión de procesos padre-hijo** con árbol visual
- ✅ **Selección de procesos arreglada** - clic en tabla para seleccionar
- ✅ **Métricas detalladas** y exportación CSV
- ✅ **Modo automático y manual** para diferentes usos
- ✅ **Reproducibilidad** con seeds configurables
- ✅ **Logs de eventos** con timestamps precisos
- ✅ **Tests unitarios** para garantizar calidad
- ✅ **Argumentos de línea de comandos** para configuración

## 🔄 Mejoras Implementadas

### **Problema de Selección SOLUCIONADO**
- ✅ **Antes**: No se podía seleccionar procesos padre para crear hijos
- ✅ **Ahora**: Hacer clic en cualquier fila de la tabla selecciona el proceso
- ✅ **Feedback visual**: El panel muestra "Seleccionado: PID X (Nombre)"
- ✅ **Botones inteligentes**: Se habilitan/deshabilitan según la selección

### **Arquitectura Profesional**
- ✅ **Modularización completa**: Código organizado en módulos especializados
- ✅ **Separación de responsabilidades**: UI, lógica, datos y utilidades separados
- ✅ **Fácil mantenimiento**: Cada componente es independiente y testeable
- ✅ **Escalabilidad**: Fácil agregar nuevas funcionalidades

---

**¡Explora el fascinante mundo de la gestión de procesos con arquitectura profesional! 🚀**

*Tip: Comienza con `python main.py --demo` para ver el simulador en acción, luego experimenta en modo manual para entender cada transición de estado.*
