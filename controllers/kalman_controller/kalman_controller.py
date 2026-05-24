from controller import Robot
import csv
import os

# ─────────────────────────────────────────────
# PARÁMETROS GLOBALES
# ─────────────────────────────────────────────
Ts = 0.05
fs = 1.0 / Ts
TIME_STEP = int(Ts * 1000)
MAX_SPEED = 6.28

# ─────────────────────────────────────────────
# INICIALIZAR ROBOT Y MOTORES
# ─────────────────────────────────────────────
robot = Robot()

left_motor  = robot.getDevice('left wheel motor')
right_motor = robot.getDevice('right wheel motor')
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)

# ─────────────────────────────────────────────
# ENCODERS Y SENSORES
# ─────────────────────────────────────────────
left_encoder  = robot.getDevice('left wheel sensor')
right_encoder = robot.getDevice('right wheel sensor')
left_encoder.enable(TIME_STEP)
right_encoder.enable(TIME_STEP)

sensor_names = ['ps0', 'ps7', 'ps2', 'ps5']
sensors = {}
for name in sensor_names:
    s = robot.getDevice(name)
    s.enable(TIME_STEP)
    sensors[name] = s

# ─────────────────────────────────────────────
# FILTRO DE KALMAN 1D (AHORA CON PREDICCIÓN)
# ─────────────────────────────────────────────
class KalmanFilter1D:
    def __init__(self, Q=0.1, R=10.0, P=1.0, x0=0.0):
        self.Q = float(Q)
        self.R = float(R)
        self.P = float(P)
        self.x = float(x0)

    def predict(self, delta_d):
        # Si el robot avanza hacia adelante (delta_d positivo), 
        # la distancia al obstáculo frontal disminuye.
        self.x = self.x - delta_d 
        self.P = self.P + self.Q

    def update(self, z):
        z = float(z)
        K = self.P / (self.P + self.R)
        self.x = self.x + K * (z - self.x)
        self.P = (1 - K) * self.P
        return self.x

kf = {name: KalmanFilter1D(Q=0.5, R=15.0) for name in sensor_names}

# Variables para calcular deltas de encoder
last_enc_l = 0.0
last_enc_r = 0.0
RADIO_RUEDA = 0.0205 # metros para el e-puck

# ─────────────────────────────────────────────
# VARIABLES PARA FILTRO SIMPLE (MEDIA MÓVIL)
# ─────────────────────────────────────────────
WINDOW_SIZE = 5
ma_buffers = {name: [] for name in sensor_names}

# ─────────────────────────────────────────────
# REGISTRO DE DATOS Y RUTAS
# ─────────────────────────────────────────────
n_samples = 0
output_path = os.path.join(os.path.dirname(__file__), 'sensor_data.csv')

csv_file = open(output_path, 'w', newline='')
writer = csv.writer(csv_file)
# Actualizamos el encabezado para incluir el filtro simple
writer.writerow([
    'tiempo',
    'ps0_raw', 'ps0_simple', 'ps0_kal',
    'ps7_raw', 'ps7_simple', 'ps7_kal',
    'ps2_raw', 'ps2_simple', 'ps2_kal',
    'ps5_raw', 'ps5_simple', 'ps5_kal',
    'enc_left', 'enc_right'
])

print(f"[INFO] Ts={Ts}s | fs={fs}Hz | TIME_STEP={TIME_STEP}ms")
print(f"[INFO] Guardando datos dinámicamente en: {output_path}")

# ─────────────────────────────────────────────
# BUCLE PRINCIPAL
# ─────────────────────────────────────────────
while robot.step(TIME_STEP) != -1:
    t = n_samples * Ts

    # 1) LEER SENSORES CRUDOS
    raw = {name: sensors[name].getValue() for name in sensor_names}

    # 2) APLICAR FILTRO SIMPLE (Media Móvil)
    simple = {}
    for name in sensor_names:
        ma_buffers[name].append(raw[name])
        if len(ma_buffers[name]) > WINDOW_SIZE:
            ma_buffers[name].pop(0)
        simple[name] = sum(ma_buffers[name]) / len(ma_buffers[name])

    # 3) LEER ENCODERS Y CALCULAR AVANCE (PREDICCIÓN)
    enc_l = left_encoder.getValue()
    enc_r = right_encoder.getValue()
    n_samples += 1
    
    delta_theta_l = enc_l - last_enc_l
    delta_theta_r = enc_r - last_enc_r
    
    # s = r * theta
    delta_s_l = RADIO_RUEDA * delta_theta_l
    delta_s_r = RADIO_RUEDA * delta_theta_r
    
    # Avance lineal promedio del robot en este paso
    delta_d = (delta_s_l + delta_s_r) / 2.0
    
    last_enc_l = enc_l
    last_enc_r = enc_r

    # Aplicar predicción a los sensores frontales (asumiendo movimiento hacia adelante)
    kf['ps0'].predict(delta_d)
    kf['ps7'].predict(delta_d)
    # Para los laterales, la predicción basada en avance frontal es más compleja, 
    # pero puedes aplicar un delta_d = 0 o ajustar según el giro si quieres ser perfeccionista.
    kf['ps2'].predict(0)
    kf['ps5'].predict(0)

    # 4) APLICAR CORRECCIÓN CON LOS SENSORES (UPDATE)
    filtered = {name: kf[name].update(raw[name]) for name in sensor_names}


    # 5) ESCRIBIR FILA EN CSV
    writer.writerow([
        round(t, 4),
        round(raw['ps0'], 4), round(simple['ps0'], 4), round(filtered['ps0'], 4),
        round(raw['ps7'], 4), round(simple['ps7'], 4), round(filtered['ps7'], 4),
        round(raw['ps2'], 4), round(simple['ps2'], 4), round(filtered['ps2'], 4),
        round(raw['ps5'], 4), round(simple['ps5'], 4), round(filtered['ps5'], 4),
        round(enc_l, 6),      round(enc_r, 6)
    ])
    csv_file.flush()

    # 6) NAVEGACIÓN REACTIVA (Basado en Kalman)
    front_r = filtered['ps0']
    front_l = filtered['ps7']
    side_r  = filtered['ps2']
    side_l  = filtered['ps5']

    OBSTACLE_THRESH = 80.0
    left_speed  = MAX_SPEED
    right_speed = MAX_SPEED

    if front_r > OBSTACLE_THRESH or front_l > OBSTACLE_THRESH:
        left_speed  =  MAX_SPEED * 0.5
        right_speed = -MAX_SPEED * 0.5
    elif side_r > OBSTACLE_THRESH:
        left_speed  = MAX_SPEED * 0.7
        right_speed = MAX_SPEED
    elif side_l > OBSTACLE_THRESH:
        left_speed  = MAX_SPEED
        right_speed = MAX_SPEED * 0.7

    left_motor.setVelocity(left_speed)
    right_motor.setVelocity(right_speed)