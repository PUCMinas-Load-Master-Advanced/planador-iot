"""
Implementa um controlador PID (Proporcional, Integral, Derivativo) otimizado.

Este modulo e responsavel pela logica de estabilizacao do planador, calculando
as correcoes necessarias para os servos com base nos dados dos sensores e no
modo de voo atual.
"""

import micropython
from config import FLIGHT_MODES, SAFETY_LIMITS
import custom_logging as logging

logger = logging.getLogger(__name__)


class PIDController:
    """Controlador PID otimizado para estabilizacao de 3 eixos (roll, pitch, yaw)."

    Attributes:
        integral (list): Acumuladores do termo integral para cada eixo.
        prev_error (list): Erros anteriores para o calculo do termo derivativo.
        flight_mode (int): Indice do modo de voo atual, que define os ganhos e alvos.
    """

    def __init__(self):
        """Inicializa o controlador PID com estados zerados e o modo de voo padrao."

        Returns:
            None
        """
        self.integral = [0.0, 0.0, 0.0]
        self.prev_error = [0.0, 0.0, 0.0]
        self.flight_mode = 0
        logger.info("Controlador PID inicializado.")

    def set_flight_mode(self, mode_index):
        """Define o modo de voo atual e reseta os estados internos do PID."

        Args:
            mode_index (int): O indice do novo modo de voo (0, 1, 2, etc.).

        Returns:
            bool: True se o modo de voo foi alterado com sucesso, False caso contrario.
        """
        if 0 <= mode_index < len(FLIGHT_MODES):
            if self.flight_mode != mode_index:
                self.flight_mode = mode_index
                self.reset()
            return True
        return False

    def get_flight_mode_info(self):
        """Retorna o dicionario de configuracao para o modo de voo atual."

        Returns:
            dict: Dicionario contendo 'name', 'gains', 'limits', 'target', 'flaps'.
        """
        return FLIGHT_MODES[self.flight_mode]

    def reset(self):
        """Reseta os estados internos do PID (integral e erros anteriores) para zero."

        Returns:
            None
        """
        self.integral = [0.0, 0.0, 0.0]
        self.prev_error = [0.0, 0.0, 0.0]

    @micropython.native
    def calculate(self, roll, pitch, yaw_rate, dt=0.1):
        """
        Calcula a saida do PID para os tres eixos (roll, pitch, yaw).

        Args:
            roll (float): Angulo de roll atual em graus.
            pitch (float): Angulo de pitch atual em graus.
            yaw_rate (float): Velocidade angular de yaw em graus/s.
            dt (float, optional): Intervalo de tempo em segundos desde o ultimo calculo. Padrao e 0.1.

        Returns:
            tuple: Uma tupla (roll_output, pitch_output, yaw_output) com as saidas do PID.

        Example:
            >>> pid_output = pid_controller.calculate(10.0, 5.0, 2.0, 0.05)
            >>> print(pid_output)
            (output_roll, output_pitch, output_yaw)
        """
        mode = FLIGHT_MODES[self.flight_mode]
        gains = mode['gains']
        limits = mode['limits']
        target = mode['target']

        errors = (
            target[0] - roll,
            target[1] - pitch,
            -yaw_rate
        )

        for i in range(3):
            self.integral[i] += errors[i] * dt
            self.integral[i] = max(-SAFETY_LIMITS['max_pid_integral'], min(SAFETY_LIMITS['max_pid_integral'], self.integral[i]))

        derivatives = tuple((errors[i] - self.prev_error[i]) / dt for i in range(3))
        self.prev_error = errors

        roll_out = (gains[0] * errors[0] + gains[1] * self.integral[0] + gains[2] * derivatives[0])
        pitch_out = (gains[3] * errors[1] + gains[4] * self.integral[1] + gains[5] * derivatives[1])
        yaw_out = (gains[6] * errors[2] + gains[7] * self.integral[2] + gains[8] * derivatives[2])

        return (
            self._limit_output(roll_out, limits[0]),
            self._limit_output(pitch_out, limits[1]),
            self._limit_output(yaw_out, limits[2])
        )

    @micropython.native
    def _limit_output(self, output, limit):
        """Limita um valor de saida a um limite simetrico."

        Args:
            output (float): O valor de saida a ser limitado.
            limit (float): O limite maximo (positivo e negativo) para a saida.

        Returns:
            float: O valor de saida limitado.
        """
        return max(-limit, min(limit, output))

    @micropython.native
    def calculate_servo_commands(self, roll, pitch, yaw_rate):
        """
        Calcula os angulos finais para os servos com base na saida do PID.

        Args:
            roll (float): Angulo de roll atual em graus.
            pitch (float): Angulo de pitch atual em graus.
            yaw_rate (float): Velocidade angular de yaw em graus/s.

        Returns:
            list: Uma lista de angulos em graus para os servos
                  [flaps_left, flaps_right, elevator, rudder].

        Example:
            >>> commands = pid_controller.calculate_servo_commands(5.0, -2.0, 1.0)
            >>> print(commands)
            [95, 85, 92, 91]
        """
        pid_out = self.calculate(roll, pitch, yaw_rate)
        mode = FLIGHT_MODES[self.flight_mode]
        flaps_base = mode['flaps']

        flaps_left = SAFETY_LIMITS['servo_neutral_angle'] + flaps_base - pid_out[0]
        flaps_right = SAFETY_LIMITS['servo_neutral_angle'] + flaps_base + pid_out[0]
        elevator = SAFETY_LIMITS['servo_neutral_angle'] - pid_out[1]
        rudder = SAFETY_LIMITS['servo_neutral_angle'] + pid_out[2]

        commands = [flaps_left, flaps_right, elevator, rudder]
        for i, cmd in enumerate(commands):
            commands[i] = int(max(SAFETY_LIMITS['servo_min_angle'], min(SAFETY_LIMITS['servo_max_angle'], cmd)))

        return commands

    def get_pid_status(self):
        """Retorna um dicionario com o estado atual do controlador PID."

        Returns:
            dict: Um dicionario contendo o modo de voo, nome do modo, estado integral e ganhos.
        """
        mode = FLIGHT_MODES[self.flight_mode]
        return {
            'flight_mode': self.flight_mode,
            'mode_name': mode['name'],
            'integral_state': self.integral,
            'gains': mode['gains']
        }

    def emergency_stop(self):
        """Para o controlador PID e reseta seus estados em uma emergencia."

        Returns:
            None
        """
        self.reset()
        logger.warning("PID parado - controle manual.")