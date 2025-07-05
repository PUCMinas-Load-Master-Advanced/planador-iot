"""
Um modulo de logging simplificado e compativel com MicroPython.

Fornece uma implementacao basica de logger para registrar mensagens
com niveis de severidade e timestamps, adequado para ambientes com
recursos limitados.
"""

import utime
import sys


class Logger:
    """Implementa um logger basico para MicroPython."

    Attributes:
        name (str): O nome do logger.
    """

    def __init__(self, name):
        """Inicializa o logger com um nome.

        Args:
            name (str): O nome do logger, geralmente o nome do modulo.

        Returns:
            None
        """
        self.name = name

    def _log(self, level, msg):
        """Metodo interno para formatar e imprimir a mensagem de log.

        Args:
            level (str): O nivel de severidade da mensagem (e.g., INFO, ERROR).
            msg (str): A mensagem a ser registrada.

        Returns:
            None
        """
        timestamp = utime.localtime()
        print(f"{timestamp[0]}-{timestamp[1]:02d}-{timestamp[2]:02d} {timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d} [{level}] {self.name}: {msg}")

    def info(self, msg):
        """Registra uma mensagem informativa.

        Args:
            msg (str): A mensagem informativa.

        Returns:
            None

        Example:
            >>> logger.info("Sistema inicializado com sucesso.")
        """
        self._log("INFO", msg)

    def debug(self, msg):
        """Registra uma mensagem de depuracao.

        Args:
            msg (str): A mensagem de depuracao.

        Returns:
            None

        Example:
            >>> logger.debug("Variavel x: 10")
        """
        self._log("DEBUG", msg)

    def warning(self, msg):
        """Registra uma mensagem de aviso.

        Args:
            msg (str): A mensagem de aviso.

        Returns:
            None

        Example:
            >>> logger.warning("Sensor nao detectado, usando simulacao.")
        """
        self._log("WARNING", msg)

    def error(self, msg):
        """Registra uma mensagem de erro.

        Args:
            msg (str): A mensagem de erro.

        Returns:
            None

        Example:
            >>> logger.error("Falha na comunicacao I2C.")
        """
        self._log("ERROR", msg)

    def exception(self, e):
        """Registra uma excecao, incluindo o traceback.

        Args:
            e (Exception): A excecao a ser registrada.

        Returns:
            None

        Example:
            >>> try:
            >>>     1 / 0
            >>> except Exception as e:
            >>>     logger.exception(e)
        """
        self._log("ERROR", f"Excecao: {e}")
        sys.print_exception(e)

def getLogger(name):
    """Retorna uma instancia de Logger.

    Args:
        name (str): O nome do logger.

    Returns:
        Logger: Uma nova instancia de Logger.

    Example:
        >>> import custom_logging
        >>> logger = custom_logging.getLogger("MeuModulo")
        >>> logger.info("Esta e uma mensagem de informacao.")
    """
    return Logger(name)