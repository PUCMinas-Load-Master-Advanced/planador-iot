"""
Script de inicializacao para o sistema do planador.

Permite ao usuario selecionar entre diferentes modos de operacao (modular,
monolitico, ou teste de hardware) durante a inicializacao do dispositivo.

Example:
    Este script e executado automaticamente na inicializacao do MicroPython.
    Ele apresenta um menu de opcoes no console serial.
"""

import time
import gc
import custom_logging as logging

logger = logging.getLogger(__name__)

logger.info("Sistema Planador ESP32")
logger.info("Escolha a versao do sistema:")
logger.info("1. Sistema Modular (Recomendado)")
logger.info("2. Sistema Original (Monolitico)")
logger.info("3. Teste de Hardware")
logger.info("Aguardando 5 segundos... (pressione CTRL+C para escolher)")

try:
    time.sleep(5)
    escolha = 1
except KeyboardInterrupt:
    logger.info("Escolha uma opcao (1-3):")
    try:
        escolha = int(input())
    except ValueError:
        escolha = 1

logger.info(f"Iniciando opcao {escolha}...")

gc.collect()
initial_ram = gc.mem_free()
logger.info(f"RAM inicial: {initial_ram} bytes")

if escolha == 1:
    logger.info("Carregando Sistema Modular...")
    try:
        from main_modular import main
        main()
    except ImportError as e:
        logger.error(f"Erro ao importar sistema modular: {e}")
        logger.info("Tentando carregar sistema original...")
        try:
            from main import main
            main()
        except Exception as e_run:
            logger.exception(e_run)
    except Exception as e_run:
        logger.exception(e_run)

elif escolha == 2:
    logger.info("Carregando Sistema Original...")
    try:
        from main import main
        main()
    except Exception as e_run:
        logger.exception(e_run)
        
elif escolha == 3:
    logger.info("Carregando Teste de Hardware...")
    try:
        from hardware_test import test_all_hardware
        test_all_hardware()
    except ImportError:
        logger.warning("Modulo de teste de hardware nao encontrado. Executando teste basico.")
        from machine import Pin
        import time
        logger.info("Testando LEDs basicos...")
        leds = [Pin(15, Pin.OUT), Pin(4, Pin.OUT), Pin(19, Pin.OUT), Pin(5, Pin.OUT)]
        for i, led in enumerate(leds):
            logger.info(f"LED {i+1}...")
            led.value(1)
            time.sleep(0.5)
            led.value(0)
        logger.info("Teste basico de LEDs concluido.")
    except Exception as e_test:
        logger.exception(e_test)
        
else:
    logger.warning("Opcao invalida. Usando sistema modular por padrao.")
    try:
        from main_modular import main
        main()
    except Exception as e_run:
        logger.exception(e_run)