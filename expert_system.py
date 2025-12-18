#!/usr/bin/env python3
"""
SISTEMA EXPERTO PARA CONTROL DE CLIMA ESP32
Maneja reglas de seguridad, emergencias y optimización
"""

from experta import *
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import time

# ========================================
# CONFIGURACIÓN
# ========================================

MQTT_HOST = "e311193c90544b20aa5e2fc9b1c06df5.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "esp32user"
MQTT_PASS = "Esp32pass123"

# ========================================
# DEFINICIÓN DEL SISTEMA EXPERTO
# ========================================

class SistemaExpertoClima(KnowledgeEngine):
    """
    Sistema Experto basado en reglas para control inteligente
    """
    
    def __init__(self):
        super().__init__()
        self.alertas = []
        self.acciones = []
        
    @DefFacts()
    def _initial_action(self):
        """Hechos iniciales"""
        yield Fact(action="analizar_sistema")
        yield Fact(modo="experto")
    
    # ========================================
    # REGLAS DE EMERGENCIA CRÍTICA
    # ========================================
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(temperatura=MATCH.temp),
          TEST(lambda temp: temp > 40))
    def emergencia_temperatura_extrema_alta(self, temp):
        """Temperatura peligrosamente alta"""
        print("🚨🚨🚨 EMERGENCIA CRÍTICA: Temperatura extrema alta!")
        self.declare(Fact(
            alerta="EMERGENCIA_TEMP_EXTREMA",
            severidad="CRÍTICA",
            mensaje=f"Temperatura crítica: {temp}°C"
        ))
        self.declare(Fact(accion="ventilador_máximo_urgente"))
        self.declare(Fact(accion="apagar_calefactor_inmediato"))
        self.declare(Fact(accion="notificar_telegram_urgente"))
        self.alertas.append({
            'tipo': 'EMERGENCIA_TEMP_ALTA',
            'temp': temp,
            'timestamp': datetime.now().isoformat()
        })
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(temperatura=MATCH.temp),
          TEST(lambda temp: temp < 5))
    def emergencia_temperatura_extrema_baja(self, temp):
        """Temperatura peligrosamente baja"""
        print("🚨🚨🚨 EMERGENCIA CRÍTICA: Riesgo de congelamiento!")
        self.declare(Fact(
            alerta="EMERGENCIA_TEMP_EXTREMA_BAJA",
            severidad="CRÍTICA",
            mensaje=f"Riesgo de congelamiento: {temp}°C"
        ))
        self.declare(Fact(accion="calefactor_máximo_urgente"))
        self.declare(Fact(accion="apagar_ventilador_inmediato"))
        self.declare(Fact(accion="notificar_telegram_urgente"))
    
    # ========================================
    # REGLAS DE ALERTA ALTA
    # ========================================
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(temperatura=MATCH.temp),
          TEST(lambda temp: 35 < temp <= 40))
    def alerta_temperatura_muy_alta(self, temp):
        """Temperatura muy alta pero no crítica"""
        print(f"⚠️ ALERTA ALTA: Temperatura elevada ({temp}°C)")
        self.declare(Fact(
            alerta="TEMP_MUY_ALTA",
            severidad="ALTA",
            mensaje=f"Temperatura muy alta: {temp}°C"
        ))
        self.declare(Fact(accion="incrementar_ventilador"))
        self.declare(Fact(accion="reducir_calefactor"))
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(temperatura=MATCH.temp),
          TEST(lambda temp: 5 <= temp < 12))
    def alerta_temperatura_muy_baja(self, temp):
        """Temperatura muy baja pero no crítica"""
        print(f"⚠️ ALERTA ALTA: Temperatura muy baja ({temp}°C)")
        self.declare(Fact(
            alerta="TEMP_MUY_BAJA",
            severidad="ALTA",
            mensaje=f"Temperatura muy baja: {temp}°C"
        ))
        self.declare(Fact(accion="incrementar_calefactor"))
        self.declare(Fact(accion="reducir_ventilador"))
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(humedad=MATCH.hum),
          TEST(lambda hum: hum > 85))
    def alerta_humedad_critica(self, hum):
        """Humedad excesiva - riesgo de moho"""
        print(f"⚠️ ALERTA: Humedad excesiva ({hum}%) - Riesgo de moho")
        self.declare(Fact(
            alerta="HUMEDAD_CRÍTICA",
            severidad="MEDIA",
            mensaje=f"Humedad excesiva: {hum}%"
        ))
        self.declare(Fact(accion="apagar_humidificador"))
        self.declare(Fact(accion="activar_ventilador_para_secar"))
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(humedad=MATCH.hum),
          TEST(lambda hum: hum < 20))
    def alerta_humedad_muy_baja(self, hum):
        """Humedad muy baja - ambiente muy seco"""
        print(f"⚠️ ALERTA: Ambiente muy seco ({hum}%)")
        self.declare(Fact(
            alerta="HUMEDAD_MUY_BAJA",
            severidad="MEDIA",
            mensaje=f"Ambiente muy seco: {hum}%"
        ))
        self.declare(Fact(accion="activar_humidificador"))
    
    # ========================================
    # REGLAS DE EFICIENCIA ENERGÉTICA
    # ========================================
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(temperatura=MATCH.temp),
          Fact(setpoint=MATCH.sp),
          TEST(lambda temp, sp: abs(temp - sp) < 0.5))
    def temperatura_optima_alcanzada(self, temp, sp):
        """Temperatura objetivo alcanzada"""
        print(f"✅ Temperatura óptima alcanzada: {temp:.1f}°C (objetivo: {sp}°C)")
        self.declare(Fact(
            estado="TEMPERATURA_ÓPTIMA",
            mensaje="Temperatura en rango objetivo"
        ))
        self.declare(Fact(accion="modo_ahorro_energía"))
        self.declare(Fact(accion="reducir_potencia_actuadores"))
    
    @Rule(Fact(accion="modo_ahorro_energía"))
    def activar_modo_ahorro(self):
        """Activa modo de bajo consumo"""
        print("💡 Activando modo ahorro de energía")
        self.acciones.append({
            'tipo': 'AHORRO_ENERGÍA',
            'timestamp': datetime.now().isoformat()
        })
    
    # ========================================
    # REGLAS DE CONFLICTO DE ACTUADORES
    # ========================================
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(relay1_estado="ON"),
          Fact(relay2_estado="ON"))
    def conflicto_ventilador_calefactor(self):
        """Detecta si ventilador y calefactor están encendidos simultáneamente"""
        print("⚠️ CONFLICTO: Ventilador y calefactor encendidos simultáneamente")
        self.declare(Fact(
            alerta="CONFLICTO_ACTUADORES",
            severidad="MEDIA",
            mensaje="Ventilador y calefactor activos - desperdicio energético"
        ))
        self.declare(Fact(accion="resolver_conflicto_actuadores"))
    
    @Rule(Fact(accion="resolver_conflicto_actuadores"),
          Fact(temperatura=MATCH.temp),
          Fact(setpoint=MATCH.sp),
          TEST(lambda temp, sp: temp > sp))
    def resolver_conflicto_favor_enfriamiento(self, temp, sp):
        """Si hace calor, priorizar enfriamiento"""
        print("🔧 Resolviendo conflicto: Priorizando enfriamiento")
        self.declare(Fact(accion="apagar_calefactor"))
        self.declare(Fact(accion="mantener_ventilador"))
    
    @Rule(Fact(accion="resolver_conflicto_actuadores"),
          Fact(temperatura=MATCH.temp),
          Fact(setpoint=MATCH.sp),
          TEST(lambda temp, sp: temp < sp))
    def resolver_conflicto_favor_calentamiento(self, temp, sp):
        """Si hace frío, priorizar calentamiento"""
        print("🔧 Resolviendo conflicto: Priorizando calentamiento")
        self.declare(Fact(accion="apagar_ventilador"))
        self.declare(Fact(accion="mantener_calefactor"))
    
    # ========================================
    # REGLAS DE MANTENIMIENTO PREVENTIVO
    # ========================================
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(relay1_tiempo_uso=MATCH.tiempo),
          TEST(lambda tiempo: tiempo > 36000))  # 10 horas
    def mantenimiento_ventilador(self, tiempo):
        """Ventilador con mucho uso"""
        horas = tiempo / 3600
        print(f"🔧 MANTENIMIENTO: Ventilador ha estado activo {horas:.1f} horas")
        self.declare(Fact(
            mantenimiento="VENTILADOR",
            mensaje=f"Revisar ventilador - uso prolongado ({horas:.1f}h)"
        ))
    
    # ========================================
    # REGLAS DE CONFORT
    # ========================================
    
    @Rule(Fact(action='analizar_sistema'),
          Fact(temperatura=MATCH.temp),
          Fact(humedad=MATCH.hum),
          TEST(lambda temp: 22 <= temp <= 25),
          TEST(lambda hum: 40 <= hum <= 60))
    def condiciones_confort_optimas(self, temp, hum):
        """Condiciones ideales de confort"""
        print(f"😊 Condiciones óptimas de confort: {temp:.1f}°C, {hum:.0f}%")
        self.declare(Fact(
            estado="CONFORT_ÓPTIMO",
            mensaje="Temperatura y humedad en rango ideal"
        ))
    
    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================
    
    def obtener_alertas(self):
        """Retorna lista de alertas generadas"""
        return self.alertas
    
    def obtener_acciones(self):
        """Retorna lista de acciones recomendadas"""
        return self.acciones
    
    def limpiar_estado(self):
        """Limpia alertas y acciones acumuladas"""
        self.alertas = []
        self.acciones = []

# ========================================
# INTEGRACIÓN CON MQTT
# ========================================

class ControladorExpertoMQTT:
    def __init__(self):
        # Cliente MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.mqtt_client.tls_set()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Sistema experto
        self.motor_experto = SistemaExpertoClima()
        
        # Estado actual
        self.temp_actual = 24.0
        self.hum_actual = 50.0
        self.setpoint = 24.0
        self.relay_estados = {
            'relay1': 'OFF',
            'relay2': 'OFF',
            'relay3': 'OFF',
            'relay4': 'OFF'
        }
        self.relay_tiempos = {
            'relay1': 0,
            'relay2': 0,
            'relay3': 0,
            'relay4': 0
        }
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Sistema Experto conectado a MQTT")
            
            # Suscribirse a topics
            client.subscribe("esp32/sensores")
            client.subscribe("esp32/config")
            client.subscribe("esp32/relay/status")
            
            print("📡 Suscrito a topics de monitoreo")
        else:
            print(f"❌ Error de conexión (rc={rc})")
    
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            
            if topic == "esp32/sensores":
                # Recibir datos de sensores
                data = json.loads(msg.payload.decode())
                self.temp_actual = data.get('temp', self.temp_actual)
                self.hum_actual = data.get('hum', self.hum_actual)
                
                # Ejecutar motor de inferencia
                self.ejecutar_analisis()
                
            elif topic == "esp32/config":
                # Actualizar configuración
                data = json.loads(msg.payload.decode())
                if 'setpoint' in data:
                    self.setpoint = data['setpoint']
                    
            elif topic == "esp32/relay/status":
                # Actualizar estados de relays
                data = json.loads(msg.payload.decode())
                for relay, info in data.items():
                    if isinstance(info, dict):
                        self.relay_estados[relay] = 'ON' if info.get('state', False) else 'OFF'
                        self.relay_tiempos[relay] = info.get('time', 0)
                
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    def ejecutar_analisis(self):
        """Ejecuta el motor de inferencia del sistema experto"""
        try:
            # Reiniciar motor
            self.motor_experto.reset()
            self.motor_experto.limpiar_estado()
            
            # Declarar hechos
            self.motor_experto.declare(Fact(action="analizar_sistema"))
            self.motor_experto.declare(Fact(temperatura=self.temp_actual))
            self.motor_experto.declare(Fact(humedad=self.hum_actual))
            self.motor_experto.declare(Fact(setpoint=self.setpoint))
            
            # Estados de relays
            self.motor_experto.declare(Fact(relay1_estado=self.relay_estados.get('r1', 'OFF')))
            self.motor_experto.declare(Fact(relay2_estado=self.relay_estados.get('r2', 'OFF')))
            self.motor_experto.declare(Fact(relay1_tiempo_uso=self.relay_tiempos.get('r1', 0)))
            
            # Ejecutar inferencia
            self.motor_experto.run()
            
            # Publicar resultados
            self.publicar_analisis()
            
        except Exception as e:
            print(f"❌ Error en análisis experto: {e}")
    
    def publicar_analisis(self):
        """Publica los resultados del análisis experto"""
        try:
            alertas = self.motor_experto.obtener_alertas()
            acciones = self.motor_experto.obtener_acciones()
            
            resultado = {
                'timestamp': datetime.now().isoformat(),
                'entradas': {
                    'temperatura': self.temp_actual,
                    'humedad': self.hum_actual,
                    'setpoint': self.setpoint
                },
                'alertas': alertas,
                'acciones_recomendadas': acciones,
                'num_reglas_activadas': len(alertas) + len(acciones)
            }
            
            # Publicar a MQTT
            self.mqtt_client.publish(
                "esp32/experto/analisis",
                json.dumps(resultado),
                qos=1
            )
            
            # Si hay alertas, notificar
            if alertas:
                self.mqtt_client.publish(
                    "esp32/experto/alertas",
                    json.dumps(alertas),
                    qos=1
                )
            
        except Exception as e:
            print(f"❌ Error publicando análisis: {e}")
    
    def iniciar(self):
        """Inicia el sistema experto"""
        try:
            print(f"\n🔌 Conectando a MQTT: {MQTT_HOST}:{MQTT_PORT}")
            self.mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
            
            print("\n" + "="*70)
            print("🧠 SISTEMA EXPERTO DE CONTROL INICIADO")
            print("="*70)
            print(f"📊 Monitoreando condiciones ambientales")
            print(f"🎯 Setpoint inicial: {self.setpoint}°C")
            print("="*70 + "\n")
            
            # Loop infinito
            self.mqtt_client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Deteniendo sistema experto...")
            self.mqtt_client.disconnect()
            print("✅ Desconectado exitosamente")
            
        except Exception as e:
            print(f"❌ Error conectando: {e}")

# ========================================
# FUNCIÓN DE PRUEBA
# ========================================

def prueba_sistema_experto():
    """Prueba el sistema experto con diferentes escenarios"""
    print("\n🧪 MODO PRUEBA - SISTEMA EXPERTO")
    print("="*70)
    
    motor = SistemaExpertoClima()
    
    escenarios = [
        {
            "nombre": "Emergencia - Temperatura extrema",
            "temp": 42,
            "hum": 60,
            "setpoint": 24
        },
        {
            "nombre": "Alerta - Humedad crítica",
            "temp": 25,
            "hum": 90,
            "setpoint": 24
        },
        {
            "nombre": "Confort óptimo",
            "temp": 23,
            "hum": 50,
            "setpoint": 24
        },
        {
            "nombre": "Temperatura muy baja",
            "temp": 8,
            "hum": 40,
            "setpoint": 24
        }
    ]
    
    for escenario in escenarios:
        print(f"\n{'='*70}")
        print(f"📍 Escenario: {escenario['nombre']}")
        print(f"   Temperatura: {escenario['temp']}°C")
        print(f"   Humedad: {escenario['hum']}%")
        print(f"   Setpoint: {escenario['setpoint']}°C")
        print('='*70)
        
        # Reiniciar motor
        motor.reset()
        motor.limpiar_estado()
        
        # Declarar hechos
        motor.declare(Fact(action="analizar_sistema"))
        motor.declare(Fact(temperatura=escenario['temp']))
        motor.declare(Fact(humedad=escenario['hum']))
        motor.declare(Fact(setpoint=escenario['setpoint']))
        
        # Ejecutar
        motor.run()
        
        # Mostrar resultados
        alertas = motor.obtener_alertas()
        acciones = motor.obtener_acciones()
        
        if alertas:
            print(f"\n📢 Alertas generadas: {len(alertas)}")
            for alerta in alertas:
                print(f"   - {alerta}")
        
        if acciones:
            print(f"\n⚡ Acciones recomendadas: {len(acciones)}")
            for accion in acciones:
                print(f"   - {accion}")
        
        time.sleep(2)
    
    print("\n" + "="*70)
    print("✅ Pruebas completadas")

# ========================================
# PUNTO DE ENTRADA
# ========================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("🧠 SISTEMA EXPERTO DE CONTROL DE CLIMA")
    print("="*70)
    print("Basado en: Experta (PyKnow)")
    print("Versión: 1.0")
    print("="*70 + "\n")
    
    # Verificar modo
    if len(sys.argv) > 1 and sys.argv[1] == "--prueba":
        prueba_sistema_experto()
    else:
        # Modo normal con MQTT
        controlador = ControladorExpertoMQTT()
        controlador.iniciar()