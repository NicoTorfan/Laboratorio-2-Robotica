import csv
import matplotlib.pyplot as plt
import os

# Ruta del CSV generado por Webots
ruta_csv = os.path.join(os.path.dirname(__file__), 'sensor_data.csv')

time_log = []

raw_log = {'ps0': [], 'ps7': [], 'ps2': [], 'ps5': []}
simple_log = {'ps0': [], 'ps7': [], 'ps2': [], 'ps5': []}
kalman_log = {'ps0': [], 'ps7': [], 'ps2': [], 'ps5': []}

# Leer CSV
with open(ruta_csv, 'r') as f:
    reader = csv.DictReader(f)

    for row in reader:
        time_log.append(float(row['tiempo']))

        for name in ['ps0', 'ps7', 'ps2', 'ps5']:
            raw_log[name].append(float(row[f'{name}_raw']))
            simple_log[name].append(float(row[f'{name}_simple']))
            kalman_log[name].append(float(row[f'{name}_kal']))

# =====================================================
# FIGURA 1: CRUDA VS KALMAN
# =====================================================

fig1, axes1 = plt.subplots(2, 2, figsize=(12, 8))
fig1.suptitle('Señal Cruda vs Estimación Kalman', fontsize=14)

configs = [
    ('ps0', 'Frontal Derecho',   axes1[0, 0]),
    ('ps7', 'Frontal Izquierdo', axes1[0, 1]),
    ('ps2', 'Lateral Derecho',   axes1[1, 0]),
    ('ps5', 'Lateral Izquierdo', axes1[1, 1]),
]

for name, titulo, ax in configs:
    ax.plot(
        time_log,
        raw_log[name],
        color='red',
        alpha=0.6,
        linewidth=1,
        label='Cruda'
    )

    ax.plot(
        time_log,
        kalman_log[name],
        color='blue',
        linewidth=1.8,
        label='Kalman'
    )

    ax.set_title(titulo)
    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Valor sensor')
    ax.grid(True)
    ax.legend()

plt.tight_layout()

# =====================================================
# FIGURA 2: CRUDA VS FILTRO SIMPLE VS KALMAN
# =====================================================

fig2, axes2 = plt.subplots(2, 2, figsize=(12, 8))
fig2.suptitle('Comparación de Métodos de Filtrado', fontsize=14)

configs = [
    ('ps0', 'Frontal Derecho',   axes2[0, 0]),
    ('ps7', 'Frontal Izquierdo', axes2[0, 1]),
    ('ps2', 'Lateral Derecho',   axes2[1, 0]),
    ('ps5', 'Lateral Izquierdo', axes2[1, 1]),
]

for name, titulo, ax in configs:

    ax.plot(
        time_log,
        raw_log[name],
        color='red',
        alpha=0.5,
        linewidth=1,
        label='Cruda'
    )

    ax.plot(
        time_log,
        simple_log[name],
        color='green',
        linewidth=1.5,
        label='Filtro Simple'
    )

    ax.plot(
        time_log,
        kalman_log[name],
        color='blue',
        linewidth=2,
        label='Kalman'
    )

    ax.set_title(titulo)
    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Valor sensor')
    ax.grid(True)
    ax.legend()

plt.tight_layout()
plt.show()