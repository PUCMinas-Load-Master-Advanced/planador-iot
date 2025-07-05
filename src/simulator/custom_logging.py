"""
Sistema de logging compatível para o simulador
"""

import logging
import sys
from datetime import datetime

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

def getLogger(name):
    """Retorna um logger configurado"""
    return logging.getLogger(name)

# Compatibilidade com o sistema original
logger = getLogger(__name__)