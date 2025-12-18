#!/usr/bin/env python3
"""
CONTROLADOR DE LÓGICA DIFUSA PARA ESP32
Sistema de control inteligente de temperatura y humedad
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# ========================================
# CONFIGURACIÓN MQTT
# ========================================

import os

# Leer de variables de entorno (para Railway)
MQTT_HOST = os.getenv("MQTT_HOST", "e311193c90544b20aa5e2fc9b1c06df5.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER", "esp32user")
MQTT_PASS = os.getenv("MQTT_PASS", "Esp32pass123")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://eiwyyyjmfjfxbibecsuf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "tu_api_key_aqui")

# ========================================
# DEFINIR VARIABLES LINGÜÍSTICAS
# ========================================

print("🧠 Inicializando Sistema de Lógica Difusa...")

# ENTRADA 1: Temperatura (15-35°C)
temperatura = ctrl.Antecedent(np.arange(15, 36, 0.1), 'temperatura')
temperatura['muy_fria'] = fuzz.trimf(temperatura.universe, [15, 15, 20])
temperatura['fria'] = fuzz.trimf(temperatura.universe, [18, 21, 24])
temperatura['confortable'] = fuzz.trimf(temperatura.universe, [22, 24, 26])
temperatura['caliente'] = fuzz.trimf(temperatura.universe, [24, 27, 30])
temperatura['muy_caliente'] = fuzz.trimf(temperatura.universe, [28, 35, 35])

# ENTRADA 2: Humedad (0-100%)
humedad = ctrl.Antecedent(np.arange(0, 101, 1), 'humedad')
humedad['muy_baja'] = fuzz.trimf(humedad.universe, [0, 0, 30])
humedad['baja'] = fuzz.trimf(humedad.universe, [20, 35, 50])
humedad['normal'] = fuzz.trimf(humedad.universe, [40, 50, 60])
humedad['alta'] = fuzz.trimf(humedad.universe, [50, 65, 80])
humedad['muy_alta'] = fuzz.trimf(humedad.universe, [70, 100, 100])

# ENTRADA 3: Diferencia con setpoint (-10 a +10°C)
diff_temp = ctrl.Antecedent(np.arange(-10, 11, 0.1), 'diff_temp')
diff_temp['muy_baja'] = fuzz.trimf(diff_temp.universe, [-10, -10, -3])
diff_temp['baja'] = fuzz.trimf(diff_temp.universe, [-5, -2, 0])
diff_temp['ok'] = fuzz.trimf(diff_temp.universe, [-1, 0, 1])
diff_temp['alta'] = fuzz.trimf(diff_temp.universe, [0, 2, 5])
diff_temp['muy_alta'] = fuzz.trimf(diff_temp.universe, [3, 10, 10])

# SALIDA 1: Potencia Ventilador (0-100%)
ventilador = ctrl.Consequent(np.arange(0, 101, 1), 'ventilador')
ventilador['apagado'] = fuzz.trimf(ventilador.universe, [0, 0, 10])
ventilador['bajo'] = fuzz.trimf(ventilador.universe, [5, 25, 45])
ventilador['medio'] = fuzz.trimf(ventilador.universe, [35, 50, 65])
ventilador['alto'] = fuzz.trimf(ventilador.universe, [55, 75, 95])
ventilador['maximo'] = fuzz.trimf(ventilador.universe, [85, 100, 100])

# SALIDA 2: Potencia Calefactor (0-100%)
calefactor = ctrl.Consequent(np.arange(0, 101, 1), 'calefactor')
calefactor['apagado'] = fuzz.trimf(calefactor.universe, [0, 0, 10])
calefactor['bajo'] = fuzz.trimf(calefactor.universe, [5, 25, 45])
calefactor['medio'] = fuzz.trimf(calefactor.universe, [35, 50, 65])
calefactor['alto'] = fuzz.trimf(calefactor.universe, [55, 75, 95])
calefactor['maximo'] = fuzz.trimf(calefactor.universe, [85, 100, 100])

# SALIDA 3: Potencia Humidificador (0-100%)
humidificador = ctrl.Consequent(np.arange(0, 101, 1), 'humidificador')
humidificador['apagado'] = fuzz.trimf(humidificador.universe, [0, 0, 10])
humidificador['bajo'] = fuzz.trimf(humidificador.universe, [5, 30, 55])
humidificador['alto'] = fuzz.trimf(humidificador.universe, [45, 75, 100])

# ========================================
# REGLAS DIFUSAS
# ========================================

print("📋 Creando reglas difusas...")

reglas = [
    # === REGLAS DE VENTILADOR (enfriar cuando hace calor) ===
    ctrl.Rule(diff_temp['muy_alta'], ventilador['maximo']),
    ctrl.Rule(diff_temp['alta'], ventilador['alto']),
    ctrl.Rule(diff_temp['ok'], ventilador['bajo']),
    ctrl.Rule(diff_temp['baja'] | diff_temp['muy_baja'], ventilador['apagado']),
    
    # === REGLAS DE CALEFACTOR (calentar cuando hace frío) ===
    ctrl.Rule(diff_temp['muy_baja'], calefactor['maximo']),
    ctrl.Rule(diff_temp['baja'], calefactor['alto']),
    ctrl.Rule(diff_temp['ok'], calefactor['bajo']),
    ctrl.Rule(diff_temp['alta'] | diff_temp['muy_alta'], calefactor['apagado']),
    
    # === REGLAS DE HUMIDIFICADOR (basado en humedad) ===
    ctrl.Rule(humedad['muy_baja'], humidificador['alto']),
    ctrl.Rule(humedad['baja'], humidificador['bajo']),
    ctrl.Rule(humedad['normal'] | humedad['alta'] | humedad['muy_alta'], 
              humidificador['apagado']),
    
    # === REGLAS COMBINADAS (temperatura + humedad) ===
    ctrl.Rule(temperatura['muy_caliente'] & humedad['muy_alta'], 
              [ventilador['maximo'], calefactor['apagado']]),
    ctrl.Rule(temperatura['muy_fria'] & humedad['muy_baja'], 
              [calefactor['maximo'], humidificador['alto']]),
    
    # === REGLAS DE CONFORT ===
    ctrl.Rule(temperatura['confortable'] & humedad['normal'],
              [ventilador['bajo'], calefactor['bajo'], humidificador['apagado']]),
]

# Crear sistema de control
sistema_ctrl = ctrl.ControlSystem(reglas)
sistema = ctrl.ControlSystemSimulation(sistema_ctrl)

print(f"✅ Sistema difuso creado con {len(reglas)} reglas")

# ========================================
# FUNCIÓN PRINCIPAL DE CÁLCULO
# ========================================

def calcular_control_difuso(temp_actual, hum_actual, setpoint):
    """
    Calcula las salidas del sistema difuso.
    
    Args:
        temp_actual (float): Temperatura actual en °C
        hum_actual (float): Humedad actual en %
        setpoint (float): Temperatura objetivo en °C
    
    Returns:
        dict: {
            'ventilador': 0-100,
            'calefactor': 0-100, 
            'humidificador': 0-100,
            'estado': 'OK'/'ERROR',
            'diff': diferencia con setpoint
        }
    """
    try:
        # Calcular diferencia con setpoint
        diff = temp_actual - setpoint
        
        # Asignar entradas al sistema
        sistema.input['temperatura'] = temp_actual
        sistema.input['humedad'] = hum_actual
        sistema.input['diff_temp'] = diff
        
        # Computar salidas
        sistema.compute()
        
        # Obtener resultados
        resultado = {
            'ventilador': round(sistema.output['ventilador'], 1),
            'calefactor': round(sistema.output['calefactor'], 1),
            'humidificador': round(sistema.output['humidificador'], 1),
            'estado': 'OK',
            'diff': round(diff, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n🧠 LÓGICA DIFUSA [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"   📊 Temp={temp_actual:.1f}°C, Setpoint={setpoint:.1f}°C, Diff={diff:+.1f}°C")
        print(f"   💧 Humedad={hum_actual:.0f}%")
        print(f"   ➜ Ventilador: {resultado['ventilador']:.0f}%")
        print(f"   ➜ Calefactor: {resultado['calefactor']:.0f}%")
        print(f"   ➜ Humidificador: {resultado['humidificador']:.0f}%")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Error en lógica difusa: {e}")
        return {
            'ventilador': 0,
            'calefactor': 0,
            'humidificador': 0,
            'estado': 'ERROR',
            'diff': 0,
            'error': str(e)
        }

# ========================================
# CONTROLADOR MQTT
# ========================================

class ControladorFuzzyMQTT:
    def __init__(self):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.mqtt_client.tls_set()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Estado actual
        self.temp_actual = 24.0
        self.hum_actual = 50.0
        self.setpoint = 24.0
        
        # Configuración
        self.umbral_activacion = 30  # Umbral para encender dispositivos
        self.modo_activo = True  # Si está en modo automático
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ MQTT conectado exitosamente")
            
            # Suscribirse a topics
            client.subscribe("esp32/sensores")
            client.subscribe("esp32/config")
            client.subscribe("esp32/fuzzy/control")
            
            print("📡 Suscrito a topics MQTT")
        else:
            print(f"❌ Error de conexión MQTT (rc={rc})")
        
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            
            if topic == "esp32/sensores":
                # Recibir datos de sensores
                data = json.loads(msg.payload.decode())
                self.temp_actual = data.get('temp', self.temp_actual)
                self.hum_actual = data.get('hum', self.hum_actual)
                
                # Calcular control difuso
                if self.modo_activo:
                    control = calcular_control_difuso(
                        self.temp_actual, 
                        self.hum_actual, 
                        self.setpoint
                    )
                    
                    # Publicar decisiones
                    self.publicar_decisiones(control)
                
            elif topic == "esp32/config":
                # Actualizar configuración
                data = json.loads(msg.payload.decode())
                if 'setpoint' in data:
                    self.setpoint = data['setpoint']
                    print(f"⚙️ Setpoint actualizado: {self.setpoint}°C")
                    
            elif topic == "esp32/fuzzy/control":
                # Control manual del sistema difuso
                data = json.loads(msg.payload.decode())
                if 'activo' in data:
                    self.modo_activo = data['activo']
                    estado = "ACTIVADO" if self.modo_activo else "DESACTIVADO"
                    print(f"🔄 Sistema difuso {estado}")
                
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    def publicar_decisiones(self, control):
        """Publica las decisiones del sistema difuso"""
        try:
            # Convertir porcentajes a comandos ON/OFF con umbral
            comandos = {
                'relay1': 'ON' if control['ventilador'] > self.umbral_activacion else 'OFF',
                'relay2': 'ON' if control['calefactor'] > self.umbral_activacion else 'OFF',
                'relay3': 'ON' if control['humidificador'] > self.umbral_activacion else 'OFF',
            }
            
            # Publicar comandos individuales a los relays
            for relay_num, estado in comandos.items():
                relay_id = relay_num[-1]  # Extraer número (1, 2, 3)
                topic = f"esp32/relay/{relay_id}/cmd"
                self.mqtt_client.publish(topic, estado, qos=1)
            
            # Publicar estado completo del sistema difuso
            estado_fuzzy = {
                'timestamp': datetime.now().isoformat(),
                'entradas': {
                    'temperatura': self.temp_actual,
                    'humedad': self.hum_actual,
                    'setpoint': self.setpoint,
                    'diferencia': control['diff']
                },
                'salidas': {
                    'ventilador': control['ventilador'],
                    'calefactor': control['calefactor'],
                    'humidificador': control['humidificador']
                },
                'comandos': comandos,
                'estado': control['estado']
            }
            
            self.mqtt_client.publish(
                "esp32/fuzzy/estado", 
                json.dumps(estado_fuzzy),
                qos=1
            )

                                                    
            # Mostrar comandos enviados
            activos = [k for k, v in comandos.items() if v == 'ON']
            if activos:
                print(f"   🔌 Dispositivos ON: {', '.join(activos)}")
            else:
                print(f"   🔌 Todos los dispositivos OFF")

            self.guardar_decision_en_supabase(control)                
        except Exception as e:
            print(f"❌ Error publicando decisiones: {e}")
        
    def guardar_decision_en_supabase(self, control):
        """Guarda decisión en Supabase"""
        try:
            from supabase import create_client
            
            supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
            
            data = {
                "temperatura_actual": self.temp_actual,
                "humedad_actual": self.hum_actual,
                "setpoint": self.setpoint,
                "diferencia_temp": control['diff'],
                "potencia_ventilador": control['ventilador'],
                "potencia_calefactor": control['calefactor'],
                "potencia_humidificador": control['humidificador'],
                "comando_ventilador": "ON" if control['ventilador'] > 30 else "OFF",
                "comando_calefactor": "ON" if control['calefactor'] > 30 else "OFF",
                "comando_humidificador": "ON" if control['humidificador'] > 30 else "OFF",
                "estado": control['estado']
            }
            
            supabase.table('fuzzy_decisions').insert(data).execute()
            print("💾 Decisión guardada en Supabase")
            
        except Exception as e:
            print(f"⚠️ No se pudo guardar en Supabase: {e}")


    def iniciar(self):
        """Conectar y mantener el sistema funcionando"""
        try:
            print(f"\n🔌 Conectando a MQTT: {MQTT_HOST}:{MQTT_PORT}")
            self.mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
            
            print("\n" + "="*70)
            print("🧠 CONTROLADOR DIFUSO INICIADO")
            print("="*70)
            print(f"📊 Modo: {'AUTOMÁTICO' if self.modo_activo else 'MANUAL'}")
            print(f"🎯 Setpoint inicial: {self.setpoint}°C")
            print(f"⚡ Umbral de activación: {self.umbral_activacion}%")
            print("="*70 + "\n")
            
            # Loop infinito procesando mensajes MQTT
            self.mqtt_client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Deteniendo controlador difuso...")
            self.mqtt_client.disconnect()
            print("✅ Desconectado exitosamente")
            
        except Exception as e:
            print(f"❌ Error conectando: {e}")

# ========================================
# FUNCIÓN DE PRUEBA (sin MQTT)
# ========================================

def prueba_sin_mqtt():
    """Prueba el sistema difuso sin necesidad de MQTT"""
    print("\n🧪 MODO PRUEBA (sin MQTT)")
    print("="*70)
    
    # Escenarios de prueba
    escenarios = [
        {"nombre": "Mucho calor", "temp": 32, "hum": 60, "setpoint": 24},
        {"nombre": "Mucho frío", "temp": 16, "hum": 40, "setpoint": 24},
        {"nombre": "Confortable", "temp": 24, "hum": 50, "setpoint": 24},
        {"nombre": "Caliente y húmedo", "temp": 30, "hum": 80, "setpoint": 24},
        {"nombre": "Frío y seco", "temp": 18, "hum": 25, "setpoint": 24},
    ]
    
    for escenario in escenarios:
        print(f"\n📍 Escenario: {escenario['nombre']}")
        control = calcular_control_difuso(
            escenario['temp'],
            escenario['hum'],
            escenario['setpoint']
        )
        time.sleep(1)
    
    print("\n" + "="*70)
    print("✅ Pruebas completadas")

# ========================================
# PUNTO DE ENTRADA
# ========================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("🧠 SISTEMA DE CONTROL DIFUSO PARA ESP32")
    print("="*70)
    print("Autor: Sistema de Control Inteligente")
    print("Versión: 1.0")
    print("="*70 + "\n")
    
    # Verificar si se quiere modo prueba
    if len(sys.argv) > 1 and sys.argv[1] == "--prueba":
        prueba_sin_mqtt()
    else:
        # Modo normal con MQTT
        controlador = ControladorFuzzyMQTT()
        controlador.iniciar()