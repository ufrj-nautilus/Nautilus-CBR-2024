from time import sleep
import pymavlink.mavutil as utility
import pymavlink.dialects.v20.all as dialect
import cv2
import numpy as np
from identificar_circulo import identificar_circulos_amarelos
from send_ned_velocity import send_ned_velocity

# Constants
TAKEOFF_ALTITUDE = 2
SPEED = 0.5  # Speed in m/s (adjust as needed)
SPEED_FIND_CENTER = 0.1 
SLEEP_INTERVAL = 0.1  # Interval to send commands

# Connect to drone
drone = utility.mavlink_connection(device="udpin:127.0.0.1:14550")

# Wait for a heartbeat
drone.wait_heartbeat()

# Inform user
print("Connected to system:", drone.target_system, ", component:", drone.target_component)

# Capturar vídeo da webcam
cap = cv2.VideoCapture(0)

# Ensure the drone is in GUIDED mode
print("Setting mode to GUIDED")
drone.mav.command_long_send(
    drone.target_system,
    drone.target_component,
    dialect.MAV_CMD_DO_SET_MODE,
    0,
    0,  # Base mode: GUIDED
    4,  # Custom mode
    0, 0, 0, 0, 0
)

drone.mav.command_long_send(
    drone.target_system,
    drone.target_component,
    utility.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, # Comando
    0,
    1,  # Base mode: GUIDED
    0,  # Custom mode
    0, 0, 0, 0, 0
)

# Give some time to change mode
sleep(2)  

# Create takeoff command
takeoff_command = dialect.MAVLink_command_long_message(
    target_system=drone.target_system,
    target_component=drone.target_component,
    command=dialect.MAV_CMD_NAV_TAKEOFF,
    confirmation=0,
    param1=0,
    param2=0,
    param3=0,
    param4=0,
    param5=0,
    param6=0,
    param7=TAKEOFF_ALTITUDE
)

# Create land command
land_command = dialect.MAVLink_command_long_message(
    target_system=drone.target_system,
    target_component=drone.target_component,
    command=dialect.MAV_CMD_NAV_LAND,
    confirmation=0,
    param1=0,
    param2=0,
    param3=0,
    param4=0,
    param5=0,
    param6=0,
    param7=0
)

# Takeoff the drone
drone.mav.send(takeoff_command)
print("Sent takeoff command to drone")

# Check if takeoff is successful
while True:
    # Ler um frame da webcam
    ret, frame = cap.read()

    if not ret:
        break

    # Identificar círculos amarelos no frame
    imagem, circulo, direcao = identificar_circulos_amarelos(frame)

    # Mostrar o frame original e o resultado
    cv2.imshow('Webcam', imagem)
    cv2.waitKey(1)

    message = drone.recv_match(
        type=dialect.MAVLink_global_position_int_message.msgname, 
        blocking=False)
    
    if message:
        message = message.to_dict()
        relative_altitude = message["relative_alt"] * 1e-3
        print("Relative Altitude", relative_altitude, "meters")

        if TAKEOFF_ALTITUDE - relative_altitude < 1:
            print("Takeoff to", TAKEOFF_ALTITUDE, "meters is successful")
            break

# Moving forward and looking for the platform
print(f"Moving forward and looking for the platform")

while True:
    # Ler um frame da webcam
    ret, frame = cap.read()

    # Se a câmera não estiver funcionando, o loop quebra
    if not ret:
        break

    # Identificar círculos amarelos no frame
    imagem, circulo, direcao = identificar_circulos_amarelos(frame)
    
    # Mostrar o frame original e o resultado
    cv2.imshow('Webcam', imagem)
    cv2.waitKey(1)

    if circulo is not False:
        break

    forward_command = dialect.MAVLink_set_position_target_local_ned_message(
        time_boot_ms=0,
        target_system=drone.target_system,
        target_component=drone.target_component,
        coordinate_frame=dialect.MAV_FRAME_LOCAL_NED,
        type_mask=0b0000111111000111,  # Ignore position, only use velocity components
        x=0.0, y=0.0, z=0.0,
        vx=float(SPEED), vy=0.0, vz=0.0,
        afx=0.0, afy=0.0, afz=0.0,
        yaw=0.0, yaw_rate=0.0
    )
    drone.mav.send(forward_command)
    sleep(SLEEP_INTERVAL)

# Stop the movement
stop_command = dialect.MAVLink_set_position_target_local_ned_message(
    time_boot_ms=0,
    target_system=drone.target_system,
    target_component=drone.target_component,
    coordinate_frame=dialect.MAV_FRAME_LOCAL_NED,
    type_mask=0b111111111000,  # Stop movement
    x=0, y=0, z=0,
    vx=0, vy=0, vz=0,
    afx=0, afy=0, afz=0,
    yaw=0, yaw_rate=0
)

drone.mav.send(stop_command)
print("Platform found, stopped forward movement")

# Centralizando o drone na plataforma
print("Centralizando a plataforma")

while True:
    # Ler um frame da webcam
    ret, frame = cap.read()
    
    # Se a câmera não estiver funcionando, o loop quebra
    if not ret:
        break
    
    # Identificar círculos amarelos no frame
    imagem, circulo, direcao = identificar_circulos_amarelos(frame)

    # Mostrar o frame original e o resultado
    cv2.imshow('Círculos Amarelos Identificados', imagem)
    cv2.waitKey(1)

    # centraliza o circulo na imagem
    if circulo is not False:
        if direcao == "Acima":
            print("Enviar comando pra ir pra frente")
            
            # ENVIAR AQUI O COMANDO
            send_ned_velocity(drone, SPEED_FIND_CENTER, 0, 0, 1)
            sleep(2) # espera alguns instantes antes de verificar o próximo frame

        if direcao == "Abaixo":
            print("Enviar comando pra ir pra trás") # Envia o comando
            
            # ENVIAR AQUI O COMANDO
            send_ned_velocity(drone, SPEED_FIND_CENTER*(-1), 0, 0, 1)
            sleep(2) # espera alguns instantes antes de verificar o próximo frame

        if direcao == "Direita":
            print("Enviar comando pra ir pra a direita") # Envia o comando

            # ENVIAR AQUI O COMANDO
            send_ned_velocity(drone, 0, SPEED_FIND_CENTER, 0, 1)
            sleep(2) # espera alguns instantes antes de verificar o próximo frame

        if direcao == "Esquerda":
            print("Enviar comando pra ir para a esquerda") # Envia o comando

            # ENVIAR AQUI O COMANDO
            send_ned_velocity(drone, 0, SPEED_FIND_CENTER*(-1), 0, 1)
            sleep(2) # espera alguns instantes antes de verificar o próximo frame

        if direcao == "Centro":
            print("Plataforma Centralizada com sucesso!")
            break

# Land the drone
drone.mav.send(land_command)
print("Sent land command to drone")

# Check if landing is successful
while True:

    # Ler um frame da webcam
    ret, frame = cap.read()

    if not ret:
        break

    # Identificar círculos amarelos no frame
    imagem, circulo, direcao = identificar_circulos_amarelos(frame)

    # Mostrar o frame original e o resultado
    cv2.imshow('Webcam', imagem)
    cv2.waitKey(1)

    message = drone.recv_match(type=dialect.MAVLink_global_position_int_message.msgname, blocking=True).to_dict()
    relative_altitude = message["relative_alt"] * 1e-3
    print("Relative Altitude", relative_altitude, "meters")
    if relative_altitude < 1:
        break

# Wait some seconds to ensure landing
sleep(5)
print("Landed successfully")
cap.release()
cv2.destroyAllWindows()
