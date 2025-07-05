"""
Sistema monolitico para o controle do planador ESP32.

Este modulo integra todas as funcionalidades (hardware, sensores, PID, liberacao)
em uma unica classe para operacao simplificada.
"""

import time
import math
import struct
from machine import Pin, PWM, I2C
import gc
import custom_logging as logging

logger = logging.getLogger(__name__)

# Importar configuracoes do arquivo config.py
from config import (
    PLANADOR_SERVOS, RELEASE_SERVO_PIN, LED_SYSTEM_ACTIVE, LED_ALERT,
    LED_RELEASE, RC_RELEASE_PIN, I2C_SDA,
    I2C_SCL, MPU6050_ADDR, STABILIZATION_GAINS, STABILIZATION_LIMITS, RELEASE_CONFIG, SAFETY_LIMITS
)


class PlanadorESP32:
    """Classe principal que encapsula toda a logica do planador."""

    def __init__(self):
        """Inicializa o sistema do planador, incluindo hardware e estados."""
        logger.info("Iniciando o sistema compacto do planador ESP32.")

        self.system_active = True
        self.loop_count = 0
        self.last_telemetry_time = 0

        self.pid_integral = [0, 0, 0]
        self.pid_prev_error = [0, 0, 0]

        self.servos = {}
        self.sensors_available = False
        
        self.release_servo = None
        self.release_state = 'LOCKED'
        self.release_armed_time = 0
        self.release_time = 0
        self.rc_signal_pin = None
        self.last_rc_read = 0

        gc.collect()
        self.run_tests()

    def run_tests(self):
        """Executa testes iniciais completos para verificar o hardware."""
        logger.info("=== INICIANDO TESTES DE STARTUP ===")
        tests_ok = 0
        
        if self.init_hardware():
            logger.info("Hardware OK.")
            tests_ok += 1
            self.test_leds()
        else:
            logger.warning("Hardware com problemas.")
            
        if self.init_release_system():
            logger.info("Sistema de liberacao OK.")
            tests_ok += 1
            self.test_release_servo()
        else:
            logger.warning("Sistema de liberacao com problemas.")
            
        if self.init_sensors():
            logger.info("Sensores OK.")
            tests_ok += 1
            self.test_sensors()
        else:
            logger.warning("Modo simulacao ativado para sensores.")
            
        if self.init_servos():
            logger.info("Servos OK.")
            tests_ok += 1
            self.test_servos()
        else:
            logger.warning("Servos com problemas.")
            
        logger.info(f"=== TESTES CONCLUIDOS: {tests_ok}/4 sistemas funcionando ===")
        self.startup_success_indication(tests_ok)
        gc.collect()

    def init_hardware(self):
        """Inicializa os pinos de hardware basicos como LEDs e botoes."""
        try:
            self.led_system_active = Pin(LED_SYSTEM_ACTIVE, Pin.OUT)
            self.led_alert = Pin(LED_ALERT, Pin.OUT)
            self.led_release = Pin(LED_RELEASE, Pin.OUT)
            
            # Inicializar LEDs apagados
            for led in [self.led_system_active, self.led_alert, self.led_release]:
                led.value(0)
                
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar hardware: {e}")
            return False
            
    def init_release_system(self):
        """Inicializa o servo de liberacao e o pino de sinal RC."""
        try:
            self.release_servo = PWM(Pin(RELEASE_SERVO_PIN), freq=50)
            self.release_servo.duty(self.angle_to_duty(RELEASE_CONFIG['locked_position']))
            self.release_state = 'LOCKED'
            
            self.rc_signal_pin = Pin(RC_RELEASE_PIN, Pin.IN)
            
            self.led_release.value(1)
            
            logger.info(f"Sistema de liberacao TRAVADO (servo em {RELEASE_CONFIG['locked_position']} graus).")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema de liberacao: {e}")
            return False

    def init_sensors(self):
        """Inicializa a comunicacao I2C e tenta configurar o MPU6050."""
        try:
            self.i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=100000)
            
            try:
                self.i2c.writeto_mem(MPU6050_ADDR, 0x6B, b'\x00')
                time.sleep_ms(50)
                who_am_i = self.i2c.readfrom_mem(MPU6050_ADDR, 0x75, 1)[0]
                if who_am_i == 0x68:
                    self.sensors_available = True
                    return True
            except:
                pass
                
            self.sensors_available = False
            return False
        except Exception as e:
            logger.error(f"Erro ao inicializar sensores: {e}")
            self.i2c = None
            self.sensors_available = False
            return False

    def init_servos(self):
        """Inicializa os servos do planador e os coloca em posicao neutra."""
        self.servos = {}
        servos_ok = 0
        
        for name, pin in PLANADOR_SERVOS.items():
            try:
                servo = PWM(Pin(pin), freq=50)
                servo.duty(self.angle_to_duty(90))
                self.servos[name] = servo
                servos_ok += 1
            except Exception as e:
                logger.error(f"Erro ao inicializar servo {name}: {e}")
                
        return servos_ok == len(PLANADOR_SERVOS)

    @micropython.native
    def angle_to_duty(self, angle):
        """Converte um angulo (0-180) para um valor de duty cycle PWM."""
        return int(40 + (angle * 75) // 180)


    @micropython.native
    def read_sensors(self):
        """Le os dados do MPU6050 ou simula se nao disponivel."""
        if not self.sensors_available:
            t = time.ticks_ms() / 5000.0
            return (math.sin(t) * 5, math.cos(t) * 3, math.sin(t * 0.5) * 2, False)
            
        try:
            data = self.i2c.readfrom_mem(MPU6050_ADDR, 0x3B, 14)
            
            ax = (data[0] << 8 | data[1]) / 16384.0
            if ax > 2.0: ax -= 4.0
            ay = (data[2] << 8 | data[3]) / 16384.0
            if ay > 2.0: ay -= 4.0
            az = (data[4] << 8 | data[5]) / 16384.0
            if az > 2.0: az -= 4.0
            gz = (data[12] << 8 | data[13]) / 131.0
            if gz > 250.0: gz -= 500.0
            
            roll = math.atan2(ay, az) * 57.2958
            pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az)) * 57.2958
            
            return (roll, pitch, gz, True)
        except Exception as e:
            logger.error(f"Erro na leitura do MPU6050: {e}")
            t = time.ticks_ms() / 5000.0
            return (math.sin(t) * 5, math.cos(t) * 3, math.sin(t * 0.5) * 2, False)

    @micropython.native  
    def read_rc_signal(self):
        """Le o sinal PWM do receptor RC - versao nao-bloqueante."""
        if not self.rc_signal_pin:
            return 1500
            
        try:
            if self.rc_signal_pin.value() == 0:
                return 1500
                
            start_time = time.ticks_us()
            timeout = 0
            while self.rc_signal_pin.value() == 1 and timeout < 100:
                timeout += 1
                
            pulse_width = time.ticks_diff(time.ticks_us(), start_time)
            
            if 800 <= pulse_width <= 2200:
                return pulse_width
            else:
                return 1500
                
        except:
            return 1500

    @micropython.native
    def calculate_pid(self, roll, pitch, yaw_rate):
        """Calcula as saidas do PID para estabilizacao - otimizado."""
        gains = STABILIZATION_GAINS
        limits = STABILIZATION_LIMITS
        
        roll_error = -roll
        pitch_error = -pitch
        yaw_error = -yaw_rate
        
        self.pid_integral[0] += roll_error * 0.02
        self.pid_integral[1] += pitch_error * 0.02
        self.pid_integral[2] += yaw_error * 0.02
        
        self.pid_integral[0] = max(-10, min(10, self.pid_integral[0]))
        self.pid_integral[1] = max(-10, min(10, self.pid_integral[1]))
        self.pid_integral[2] = max(-10, min(10, self.pid_integral[2]))
        
        roll_out = gains[0] * roll_error + gains[1] * self.pid_integral[0]
        pitch_out = gains[3] * pitch_error + gains[4] * self.pid_integral[1]
        yaw_out = gains[6] * yaw_error + gains[7] * self.pid_integral[2]
        
        roll_out = max(-limits[0], min(limits[0], roll_out))
        pitch_out = max(-limits[1], min(limits[1], pitch_out))
        yaw_out = max(-limits[2], min(limits[2], yaw_out))
        
        return (roll_out, pitch_out, yaw_out)

    @micropython.native
    def calculate_commands(self, roll, pitch, yaw_rate):
        """Calcula os comandos finais para os servos - otimizado."""
        pid_out = self.calculate_pid(roll, pitch, yaw_rate)
        
        flaps_left = 90 - pid_out[0]
        flaps_right = 90 + pid_out[0]
        elevator = 90 - pid_out[1]
        rudder = 90 + pid_out[2]
        
        return [
            max(30, min(150, int(flaps_left))),
            max(30, min(150, int(flaps_right))),
            max(30, min(150, int(elevator))),
            max(30, min(150, int(rudder)))
        ]

    def update_release_system(self):
        """Atualiza o estado do sistema de liberacao."""
        if not self.release_servo:
            return
            
        current_time = time.ticks_ms()
        rc_signal = self.read_rc_signal()
        
        if self.release_state == 'LOCKED':
            self.led_release.value(1)
            if rc_signal > RELEASE_CONFIG['rc_threshold']:
                self.release_state = 'ARMED'
                self.release_armed_time = current_time
                logger.info("Sistema de liberacao ARMADO.")
                
        elif self.release_state == 'ARMED':
            self.led_release.value((current_time // 200) % 2)
            if rc_signal < RELEASE_CONFIG['rc_threshold']:
                self.release_state = 'LOCKED'
                logger.info("Sistema de liberacao DESARMADO.")
                return
                
            if time.ticks_diff(current_time, self.release_armed_time) >= RELEASE_CONFIG['safety_delay']:
                if rc_signal > RELEASE_CONFIG['rc_threshold']:
                    self.release_state = 'RELEASING'
                    self.release_time = current_time
                    logger.info("Liberando planador!")
                    
        elif self.release_state == 'RELEASING':
            self.led_release.value(0)
            self.release_servo.duty(self.angle_to_duty(RELEASE_CONFIG['release_position']))
            if time.ticks_diff(current_time, self.release_time) >= 500:
                self.release_state = 'RELEASED'
                logger.info("Planador LIBERADO!")
                
        elif self.release_state == 'RELEASED':
            self.led_release.value((current_time // 1000) % 2)
            if time.ticks_diff(current_time, self.release_time) >= RELEASE_CONFIG['auto_lock_time']:
                self.lock_release_system()
                
    def lock_release_system(self):
        """Trava o sistema de liberacao."""
        if self.release_servo:
            self.release_servo.duty(self.angle_to_duty(RELEASE_CONFIG['locked_position']))
            self.release_state = 'LOCKED'
            self.led_release.value(1)
            logger.info("Sistema de liberacao TRAVADO.")
            
    def emergency_release(self):
        """Ativa a liberacao de emergencia via botao."""
        if RELEASE_CONFIG['emergency_override'] and self.release_servo:
            logger.warning("Liberacao de emergencia ativada!")
            self.release_servo.duty(self.angle_to_duty(RELEASE_CONFIG['release_position']))
            self.release_state = 'RELEASED'
            self.release_time = time.ticks_ms()
            
            for _ in range(5):
                self.led_alert.value(1)
                time.sleep_ms(100)
                self.led_alert.value(0)
                time.sleep_ms(100)

    def handle_controls(self):
        """Sistema sempre ativo - sem controles por botao."""
        pass

    def set_neutral(self):
        """Coloca todos os servos em posicao neutra."""
        neutral = self.angle_to_duty(90)
        for servo in self.servos.values():
            servo.duty(neutral)

    @micropython.native
    def apply_commands(self, commands):
        """Aplica os comandos calculados aos servos."""
        servo_names = ['flaps_left', 'flaps_right', 'elevator', 'rudder']
        for i, name in enumerate(servo_names):
            if name in self.servos:
                self.servos[name].duty(self.angle_to_duty(commands[i]))

    def update_leds(self):
        """Atualiza o estado dos LEDs de acordo com o sistema."""
        if hasattr(self, 'led_system_active'):
            self.led_system_active.value(1 if self.system_active else 0)

    def log_status(self, roll, pitch, yaw_rate, sensors_valid):
        """Registra o status atual do sistema para telemetria."""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_telemetry_time) >= 3000:
            self.last_telemetry_time = current_time
            sensor_text = "REAL" if sensors_valid else "SIMULADO"
            status_text = "ATIVO" if self.system_active else "INATIVO"
            release_text = self.release_state
            rc_signal = self.read_rc_signal()
            logger.info(f"ESTABILIZACAO | R:{roll:.1f} P:{pitch:.1f} Y:{yaw_rate:.1f} | Status:{status_text} | Sensor:{sensor_text} | Liberacao:{release_text} RC:{rc_signal}")
            gc.collect()

    def main_loop(self):
        """Executa um ciclo completo de operacao do planador."""
        self.loop_count += 1
        try:
            roll, pitch, yaw_rate, sensors_valid = self.read_sensors()
            commands = self.calculate_commands(roll, pitch, yaw_rate)
            self.apply_commands(commands)
            self.update_release_system()
            self.update_leds()
            if self.loop_count % 1000 == 0:
                self.log_status(roll, pitch, yaw_rate, sensors_valid)
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            self.set_neutral()

    def run(self):
        """Inicia o loop de execucao principal do planador."""
        logger.info("Sistema Planador ESP32 - Iniciado")
        logger.info("Sistema ATIVO automaticamente")
        logger.info("Controle apenas via RC para liberacao")
        logger.info("LED VERDE: Sistema Ativo")
        
        try:
            while True:
                self.main_loop()
        except KeyboardInterrupt:
            logger.info("Parando o sistema...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Realiza a limpeza final dos componentes de hardware."""
        logger.info("Finalizando o sistema...")
        self.set_neutral()
        
        if self.release_servo:
            try:
                self.release_servo.duty(self.angle_to_duty(RELEASE_CONFIG['locked_position']))
                logger.info("Sistema de liberacao travado por seguranca.")
            except:
                pass
        
        if hasattr(self, 'led_system_active'):
            try:
                self.led_system_active.value(0)
                self.led_alert.value(0)
                self.led_release.value(0)
            except:
                pass
        
        for servo in self.servos.values():
            try:
                servo.deinit()
            except:
                pass
                
        if self.release_servo:
            try:
                self.release_servo.deinit()
            except:
                pass
                
        logger.info("Sistema finalizado.")

    def test_leds(self):
        """Testa todos os LEDs disponíveis."""
        logger.info("Testando LEDs...")
        leds = []
        led_names = []
        
        if hasattr(self, 'led_system_active'):
            leds.append(self.led_system_active)
            led_names.append("Sistema")
        if hasattr(self, 'led_alert'):
            leds.append(self.led_alert)
            led_names.append("Alerta")
        if hasattr(self, 'led_release'):
            leds.append(self.led_release)
            led_names.append("Liberacao")
        
        # Teste individual
        for i, (led, name) in enumerate(zip(leds, led_names)):
            logger.info(f"Testando LED {name}...")
            led.value(1)
            time.sleep_ms(300)
            led.value(0)
            time.sleep_ms(100)
        
        # Teste sequencial rápido
        for _ in range(3):
            for led in leds:
                led.value(1)
                time.sleep_ms(100)
                led.value(0)
                time.sleep_ms(50)
        
        logger.info(f"Teste de LEDs concluido ({len(leds)} LEDs testados)")

    def test_servos(self):
        """Testa todos os servos movimentando-os em sequência."""
        logger.info("Testando movimentacao dos servos...")
        
        if not self.servos:
            logger.warning("Nenhum servo disponivel para teste")
            return
        
        servo_names = list(self.servos.keys())
        logger.info(f"Testando {len(servo_names)} servos: {servo_names}")
        
        # Posições de teste
        test_positions = [60, 120, 90]  # Esquerda, Direita, Centro
        
        for position in test_positions:
            logger.info(f"Movendo servos para {position} graus...")
            for name, servo in self.servos.items():
                servo.duty(self.angle_to_duty(position))
            time.sleep_ms(800)
        
        # Sequência individual por servo
        for name, servo in self.servos.items():
            logger.info(f"Teste individual do servo {name}...")
            servo.duty(self.angle_to_duty(45))
            time.sleep_ms(300)
            servo.duty(self.angle_to_duty(135))
            time.sleep_ms(300)
            servo.duty(self.angle_to_duty(90))
            time.sleep_ms(200)
        
        logger.info("Teste de servos concluido")

    def test_release_servo(self):
        """Testa o servo de liberação."""
        if not self.release_servo:
            logger.warning("Servo de liberacao nao disponivel")
            return
        
        logger.info("Testando servo de liberacao...")
        
        # Posição travado
        logger.info("Posicao TRAVADO...")
        self.release_servo.duty(self.angle_to_duty(RELEASE_CONFIG['locked_position']))
        time.sleep_ms(1000)
        
        # Posição liberado
        logger.info("Posicao LIBERADO...")
        self.release_servo.duty(self.angle_to_duty(RELEASE_CONFIG['release_position']))
        time.sleep_ms(1000)
        
        # Volta para travado
        logger.info("Retornando para TRAVADO...")
        self.release_servo.duty(self.angle_to_duty(RELEASE_CONFIG['locked_position']))
        time.sleep_ms(500)
        
        logger.info("Teste do servo de liberacao concluido")

    def test_sensors(self):
        """Testa a leitura dos sensores."""
        logger.info("Testando leitura dos sensores...")
        
        # Fazer algumas leituras para verificar funcionamento
        for i in range(5):
            roll, pitch, yaw_rate, valid = self.read_sensors()
            sensor_type = "REAL" if valid else "SIMULADO"
            logger.info(f"Leitura {i+1}: R:{roll:.1f} P:{pitch:.1f} Y:{yaw_rate:.1f} ({sensor_type})")
            time.sleep_ms(200)
        
        logger.info("Teste de sensores concluido")

    def startup_success_indication(self, tests_passed):
        """Indica o resultado dos testes através de LEDs."""
        if not hasattr(self, 'led_system_active'):
            return
        
        if tests_passed == 4:
            # Todos os testes passaram - LED verde fixo
            logger.info("STARTUP COMPLETO - Sistema 100% funcional")
            self.led_system_active.value(1)
            
            # Celebração com todos os LEDs
            if hasattr(self, 'led_alert') and hasattr(self, 'led_release'):
                for _ in range(5):
                    for led in [self.led_system_active, self.led_alert, self.led_release]:
                        led.value(1)
                    time.sleep_ms(100)
                    for led in [self.led_system_active, self.led_alert, self.led_release]:
                        led.value(0)
                    time.sleep_ms(100)
                
                self.led_system_active.value(1)  # Deixar sistema ativo ligado
                
        elif tests_passed >= 2:
            # Sistema parcialmente funcional
            logger.warning("STARTUP PARCIAL - Sistema funcional com limitacoes")
            self.led_system_active.value(1)
            
            # Piscar LED de alerta
            if hasattr(self, 'led_alert'):
                for _ in range(tests_passed):
                    self.led_alert.value(1)
                    time.sleep_ms(200)
                    self.led_alert.value(0)
                    time.sleep_ms(200)
        else:
            # Sistema com muitos problemas
            logger.error("STARTUP FALHOU - Sistema com problemas criticos")
            
            # Piscar LED de alerta rapidamente
            if hasattr(self, 'led_alert'):
                for _ in range(10):
                    self.led_alert.value(1)
                    time.sleep_ms(100)
                    self.led_alert.value(0)
                    time.sleep_ms(100)

def main():
    """Ponto de entrada para iniciar o sistema do planador."""
    logger.info("Iniciando o sistema do planador...")
    try:
        planador = PlanadorESP32()
        planador.run()
    except Exception as e:
        logger.error(f"Erro critico: {e}")
        import sys
        sys.print_exception(e)

if __name__ == "__main__":
    main()
