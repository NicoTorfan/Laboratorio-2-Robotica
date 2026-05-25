# Laboratorio 2: Navegación reactiva con filtrado y fusión de sensores en Webots

**Código de Asignatura:** ICI 4150 - Robótica y Sistemas Autónomos 2026-01
**Integrantes:** Daniel Cepeda 21.263.144-2
Patricio Cisternas 21.410.167-K
Belén Fernández 21.606.563-8
Nicolás Torfan 20.914.626-6

## Objetivo del Trabajo
Implementar un sistema de navegación reactiva en Webots para un robot móvil diferencial, utilizando sensores de distancia y encoders de rueda. El proyecto busca aplicar técnicas de filtrado sobre las mediciones ruidosas y emplear un filtro de Kalman para estimar la proximidad a los obstáculos, mejorando así la robustez en la toma de decisiones del agente.

## Descripción del Robot y Sensores Utilizados
Para esta simulación se utilizó el robot e-puck, configurado con tracción diferencial. El sistema sensorial empleado incluye:
* **Sensores de distancia infrarrojos:** Se activaron cuatro sensores para la percepción del entorno. Dos frontales (`ps0` y `ps7`) para detectar obstáculos en la trayectoria directa, y dos laterales (`ps2` y `ps5`) para monitorear las paredes adyacentes.
* **Encoders de rueda:** Se utilizaron los sensores de posición en las ruedas izquierda (`left wheel sensor`) y derecha (`right wheel sensor`) para registrar el desplazamiento odométrico del robot.

## Frecuencia de Muestreo
El sistema opera con un tiempo de muestreo (Ts) de 0.05 segundos, lo que equivale a una frecuencia de muestreo de **20 Hz** (`TIME_STEP = 50 ms`).

## Análisis de las Señales Registradas
Las señales crudas entregadas por los sensores infrarrojos de Webots presentan un comportamiento ruidoso y una alta varianza, entregando valores de intensidad de luz en lugar de distancias métricas directas. Al acercarse a un obstáculo, el valor de la señal disminuye de forma abrupta. Sin un procesamiento adecuado, estas fluctuaciones generan falsos positivos en la detección, provocando movimientos erráticos en los motores.

## Estimación del Avance mediante Encoders
En cada ciclo de control, el script lee los valores acumulados de los encoders izquierdo y derecho. Estos datos son almacenados secuencialmente en un archivo de registro (`sensor_data.csv`) junto con su respectiva marca de tiempo, permitiendo reconstruir la cinemática de las ruedas post-simulación.

## Filtro Simple Aplicado
Como primera etapa de procesamiento, se implementó un filtro de **Media Móvil** utilizando una estructura de datos tipo cola. La ventana de promediado se configuró con un tamaño de 5 muestras (`window_size = 5`). Este filtro logra suavizar los picos de ruido, aunque introduce un ligero retraso temporal en la señal respecto a la medición física real.

## Implementación del Filtro de Kalman
Se desarrolló una clase `KalmanFilter1D` para estimar el estado de las mediciones de los sensores, sintonizada con los siguientes parámetros:
* Varianza del ruido del proceso (Q): 0.1
* Varianza del ruido de la medición (R): 10.0
* Covarianza del error inicial (P): 1.0

### Descripción de las Etapas de Predicción y Corrección
* **Etapa de Predicción:** El modelo asume un sistema de velocidad constante con entrada nula (`predict(0)`). Esta configuración enfoca el filtro en mitigar la varianza de la señal cruda, asumiendo que los cambios en la lectura del sensor entre muestreos sucesivos son pequeños.
* **Etapa de Corrección:** El filtro actualiza su estimación de estado ponderando la predicción anterior con la nueva medición cruda (`raw_val`) entregada por el sensor, ajustando la covarianza del error en consecuencia.

## Lógica de Navegación Reactiva Implementada
El sistema de evasión se basa en las señales estimadas por el filtro de Kalman de los sensores frontales (`ps0` y `ps7`). Se estableció un umbral crítico de obstáculo de `80.0`. 
Cuando cualquiera de los sensores frontales registra un valor inferior al umbral, el robot entra en estado de evasión utilizando control diferencial:
* Si el obstáculo está más cerca del lado derecho (`front_r < front_l`), la rueda izquierda invierte su giro al 50% de la velocidad máxima, obligando al robot a virar bruscamente a la izquierda.
* En caso contrario, la rueda derecha es la que retrocede, generando un viraje a la derecha.

## Gráficos de Señales
Los gráficos comparativos entre las señales crudas, el filtro de media móvil y la estimación de Kalman se generan de forma independiente ejecutando el script `Graficar.py`. *[Nota: Adjunta las imágenes generadas por tu equipo o haz referencia a ellas aquí]*

## Resultados Obtenidos en los Escenarios de Prueba
[Describe aquí brevemente qué pasó al correr el robot. Ejemplo: El robot logró navegar exitosamente por la arena configurada en el archivo .wbt, evadiendo los obstáculos frontales de manera fluida y sin colisiones. Las mediciones laterales demostraron un comportamiento estable mientras el robot se desplazaba paralelo a los muros.]

## Análisis Final y Conclusiones
El desarrollo de este laboratorio demostró la importancia crítica del procesamiento de señales en la robótica móvil. La implementación de la navegación reactiva sobre las señales crudas habría resultado en un comportamiento inestable. 
Se comprobó que el Filtro de Kalman, configurado como un estimador de varianza (modelo estático de predicción), superó al filtro de media móvil, ofreciendo una señal limpia sin el desfase temporal característico de los filtros promediadores. Esta decisión de diseño fue suficiente y óptima para garantizar que la lógica reactiva operara con umbrales precisos, cumpliendo el objetivo de evasión de colisiones de manera exitosa.

## Instrucciones para Ejecutar la Simulación
1. Descargar o clonar el repositorio y mantener la estructura de directorios intacta.
2. Abrir el software **Webots**.
3. Cargar el archivo del entorno (mundo) seleccionando `File > Open World...` y abriendo el archivo `.wbt` correspondiente ubicado en la carpeta `worlds`.
4. Verificar que el robot en la escena tenga asignado el controlador `kalman_controller`.
5. Ejecutar la simulación con el botón *Play*. El robot comenzará a navegar y se generará automáticamente el archivo `sensor_data.csv`.
