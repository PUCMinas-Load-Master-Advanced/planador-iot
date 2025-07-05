"""
Gerencia a leitura e o processamento de dados de sensores, como o MPU6050.

Este modulo fornece um `SensorManager` que abstrai a fonte dos dados, permitindo
utilizar um sensor real (MPU6050) ou um sensor simulado para fins de teste,
sem a necessidade de alterar o codigo principal.
"""

import time
import math
import struct
from machine import I2C, Pin
import micropython
from config import I2C_SDA, I2C_SCL, MPU6050_ADDR, SYSTEM_CONFIG
import custom_logging as logging

logger = logging.getLogger(__name__)


class MPU6050:
    """Driver para o sensor de movimento MPU6050."

    Attributes:
        i2c (I2C): Instancia do barramento I2C.
        available (bool): Indica se o sensor MPU6050 foi inicializado com sucesso.
    """

    def __init__(self):
        """Inicializa a comunicacao I2C e configura o MPU6050."

        Returns:
            None

        Raises:
            Exception: Se houver um erro ao inicializar o I2C ou configurar o MPU6050.
        """
        self.i2c = None
        self.available = False
        try:
            self.i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=SYSTEM_CONFIG['i2c_frequency'])
            self._configure_mpu6050()
            if self._test_communication():
                self.available = True
                logger.info("MPU6050 conectado e configurado.")
            else:
                logger.warning("MPU6050 nao responde.")
        except Exception as e:
            logger.error(f"Erro ao inicializar MPU6050: {e}")
            self.available = False

    def _configure_mpu6050(self):
        """Configura os registradores principais do MPU6050."

        Returns:
            None

        Raises:
            Exception: Se houver um erro na escrita dos registradores I2C.
        """
        try:
            self.i2c.writeto_mem(MPU6050_ADDR, 0x6B, b'\x00')
            time.sleep_ms(100)
            self.i2c.writeto_mem(MPU6050_ADDR, 0x1C, b'\x00')
            self.i2c.writeto_mem(MPU6050_ADDR, 0x1B, b'\x00')
            self.i2c.writeto_mem(MPU6050_ADDR, 0x1A, b'\x02')
        except Exception as e:
            logger.error(f"Erro na configuracao MPU6050: {e}")
            raise

    def _test_communication(self):
        """Verifica a comunicacao lendo o registrador WHO_AM_I do MPU6050."

        Returns:
            bool: True se a comunicacao for bem-sucedida e o WHO_AM_I for 0x68, False caso contrario.
        """
        try:
            return self.i2c.readfrom_mem(MPU6050_ADDR, 0x75, 1)[0] == 0x68
        except:
            return False

    @micropython.native
    def read_raw_data(self):
        """Le e processa os dados brutos de acelerometro e giroscopio do MPU6050."

        Returns:
            tuple: Uma tupla (ax, ay, az, gz) contendo os valores de aceleracao
                   (em g) e velocidade angular (em graus/s), ou None se o sensor
                   nao estiver disponivel ou houver erro de leitura.
        """
        if not self.available: return None
        try:
            data = self.i2c.readfrom_mem(MPU6050_ADDR, 0x3B, 14)
            ax = struct.unpack('>h', data[0:2])[0] / 16384.0
            ay = struct.unpack('>h', data[2:4])[0] / 16384.0
            az = struct.unpack('>h', data[4:6])[0] / 16384.0
            gz = struct.unpack('>h', data[12:14])[0] / 131.0
            return (ax, ay, az, gz)
        except Exception:
            return None

    @micropython.native
    def calculate_attitude(self, ax, ay, az):
        """Calcula os angulos de roll e pitch a partir dos dados do acelerometro."

        Args:
            ax (float): Componente X da aceleracao.
            ay (float): Componente Y da aceleracao.
            az (float): Componente Z da aceleracao.

        Returns:
            tuple: Uma tupla (roll, pitch) em graus.
        """
        RAD_TO_DEG = 57.2958
        roll = math.atan2(ay, az) * RAD_TO_DEG
        pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az)) * RAD_TO_DEG
        return (roll, pitch)


class SimulatedSensor:
    """Fornece dados de sensor simulados para testes sem hardware."

    Attributes:
        start_time (int): Timestamp de inicio da simulacao.
    """

    def __init__(self):
        """Inicializa o sensor simulado."

        Returns:
            None
        """
        self.start_time = time.ticks_ms()
        logger.warning("Usando sensor simulado.")

    @micropython.native
    def read_raw_data(self):
        """Gera dados simulados que representam um movimento suave."

        Returns:
            tuple: Uma tupla (ax, ay, az, gz) com valores simulados.
        """
        t = time.ticks_diff(time.ticks_ms(), self.start_time) / 5000.0
        ax = math.sin(t * 0.3) * 0.1
        ay = math.cos(t * 0.2) * 0.1
        az = 1.0 + math.sin(t * 0.1) * 0.05
        gz = math.sin(t * 0.4) * 2.0
        return (ax, ay, az, gz)

    def calculate_attitude(self, ax, ay, az):
        """Calcula a atitude a partir dos dados simulados."

        Args:
            ax (float): Componente X da aceleracao simulada.
            ay (float): Componente Y da aceleracao simulada.
            az (float): Componente Z da aceleracao simulada.

        Returns:
            tuple: Uma tupla (roll, pitch) em graus, calculada a partir dos dados simulados.
        """
        RAD_TO_DEG = 57.2958
        roll = math.atan2(ay, az) * RAD_TO_DEG
        pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az)) * RAD_TO_DEG
        return (roll, pitch)


class SensorManager:
    """Gerencia o sensor de movimento, alternando para um simulador em caso de falha."

    Attributes:
        mpu6050 (MPU6050): Instancia do driver MPU6050.
        sensor (MPU6050 or SimulatedSensor): O sensor ativo (real ou simulado).
        using_real_sensor (bool): True se estiver usando o sensor real, False se for o simulado.
    """

    def __init__(self):
        """Tenta inicializar o MPU6050 e recorre a um sensor simulado se falhar."

        Returns:
            None
        """
        logger.info("Inicializando sensores...")
        self.mpu6050 = MPU6050()
        if self.mpu6050.available:
            self.sensor = self.mpu6050
            self.using_real_sensor = True
        else:
            self.sensor = SimulatedSensor()
            self.using_real_sensor = False

    @micropython.native
    def read_attitude(self):
        """
        Le a atitude do sensor ativo (real ou simulado).

        Returns:
            tuple: Uma tupla (roll, pitch, yaw_rate, is_valid).
                   roll (float): Angulo de roll em graus.
                   pitch (float): Angulo de pitch em graus.
                   yaw_rate (float): Taxa de guinada em graus/s.
                   is_valid (bool): True se os dados vierem de um sensor real, False se for simulado.

        Example:
            >>> roll, pitch, yaw_rate, is_valid = sensor_manager.read_attitude()
            >>> print(f"Roll: {roll:.2f}, Pitch: {pitch:.2f}")
        """
        try:
            raw_data = self.sensor.read_raw_data()
            if raw_data is None:
                if self.using_real_sensor:
                    logger.warning("Sensor real falhou, usando simulacao.")
                    self.sensor = SimulatedSensor()
                    self.using_real_sensor = False
                    raw_data = self.sensor.read_raw_data()
                else:
                    return (0.0, 0.0, 0.0, False)
            ax, ay, az, gz = raw_data
            roll, pitch = self.sensor.calculate_attitude(ax, ay, az)
            return (roll, pitch, gz, self.using_real_sensor)
        except Exception as e:
            logger.error(f"Erro na leitura do sensor: {e}")
            return (0.0, 0.0, 0.0, False)

    def get_sensor_status(self):
        """Retorna um dicionario com o status atual do sensor."

        Returns:
            dict: Um dicionario contendo:
                  - 'mpu6050_available' (bool): Se o MPU6050 foi detectado na inicializacao.
                  - 'using_real_sensor' (bool): Se o sistema esta usando o sensor real atualmente.
                  - 'sensor_type' (str): O tipo de sensor em uso (MPU6050 ou Simulado).
        """
        return {
            'mpu6050_available': self.mpu6050.available,
            'using_real_sensor': self.using_real_sensor,
            'sensor_type': 'MPU6050' if self.using_real_sensor else 'Simulado'
        }

    def calibrate(self, samples=100):
        """Executa um ciclo de calibracao para o sensor (ainda nao implementado).

        Args:
            samples (int, optional): Numero de amostras a serem coletadas para calibracao. Padrao e 100.

        Returns:
            None

        Example:
            >>> sensor_manager.calibrate(200)
            Calibrando sensores (200 amostras)...
        """
        logger.info(f"Calibrando sensores ({samples} amostras)...")
        if not self.using_real_sensor:
            logger.warning("Calibracao nao disponivel no modo simulado.")
            return
        for i in range(samples):
            self.read_attitude()
            if i % 20 == 0:
                logger.info(f"Calibracao: {i//20*20}%")
            time.sleep_ms(10)
        logger.info("Calibracao concluida.")