#!/usr/bin/env python3
"""
Interface Gráfica para o Simulador do Planador

Visualização em tempo real do sistema de estabilização.
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.animation import FuncAnimation
    import numpy as np
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

import threading
import time
from collections import deque
import custom_logging as logging
from planador_simulator import PlanadorSimulator

logger = logging.getLogger(__name__)

class PlanadorGUI:
    """Interface gráfica para visualização do simulador"""
    
    def __init__(self):
        if not GUI_AVAILABLE:
            raise ImportError("GUI não disponível. Instale: pip install matplotlib")
        
        self.root = tk.Tk()
        self.root.title("Simulador Planador ESP32")
        self.root.geometry("1200x800")
        
        # Simulador
        self.simulator = PlanadorSimulator()
        self.running = False
        
        # Dados para gráficos
        self.max_points = 300
        self.time_data = deque(maxlen=self.max_points)
        self.roll_data = deque(maxlen=self.max_points)
        self.pitch_data = deque(maxlen=self.max_points)
        self.yaw_data = deque(maxlen=self.max_points)
        
        self.servo_data = {
            'flaps_left': deque(maxlen=self.max_points),
            'flaps_right': deque(maxlen=self.max_points),
            'elevator': deque(maxlen=self.max_points),
            'rudder': deque(maxlen=self.max_points)
        }
        
        self.setup_ui()
        self.setup_plots()
        
        # Timer para atualização
        self.start_time = time.time()
        self.update_timer()
    
    def setup_ui(self):
        """Configura interface do usuário"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame de controles
        control_frame = ttk.LabelFrame(main_frame, text="Controles", padding=10)
        control_frame.pack(fill=tk.X, pady=(0,5))
        
        # Botões
        self.start_btn = ttk.Button(control_frame, text="Iniciar", command=self.start_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=(0,5))
        
        self.stop_btn = ttk.Button(control_frame, text="Parar", command=self.stop_simulation)
        self.stop_btn.pack(side=tk.LEFT, padx=(0,5))
        
        self.reset_btn = ttk.Button(control_frame, text="Reset", command=self.reset_simulation)
        self.reset_btn.pack(side=tk.LEFT, padx=(0,5))
        
        # RC Control
        ttk.Label(control_frame, text="RC Signal:").pack(side=tk.LEFT, padx=(20,5))
        self.rc_var = tk.IntVar(value=1500)
        self.rc_scale = ttk.Scale(control_frame, from_=800, to=2200, 
                                 variable=self.rc_var, orient=tk.HORIZONTAL, length=200)
        self.rc_scale.pack(side=tk.LEFT, padx=(0,5))
        self.rc_label = ttk.Label(control_frame, text="1500")
        self.rc_label.pack(side=tk.LEFT)
        
        # Perturbação
        ttk.Label(control_frame, text="Perturbação:").pack(side=tk.LEFT, padx=(20,5))
        self.disturbance_var = tk.DoubleVar(value=5.0)
        self.disturbance_scale = ttk.Scale(control_frame, from_=0, to=20, 
                                          variable=self.disturbance_var, orient=tk.HORIZONTAL, length=150)
        self.disturbance_scale.pack(side=tk.LEFT, padx=(0,5))
        
        # Frame de status
        status_frame = ttk.LabelFrame(main_frame, text="Status do Sistema", padding=10)
        status_frame.pack(fill=tk.X, pady=(0,5))
        
        # Labels de status
        self.status_labels = {}
        status_items = [
            ("Loops", "loops"), ("Frequência", "freq"), ("Roll", "roll"),
            ("Pitch", "pitch"), ("Yaw Rate", "yaw"), ("PID Integral", "pid")
        ]
        
        for i, (label, key) in enumerate(status_items):
            ttk.Label(status_frame, text=f"{label}:").grid(row=0, column=i*2, sticky=tk.W, padx=(0,5))
            self.status_labels[key] = ttk.Label(status_frame, text="--", foreground="blue")
            self.status_labels[key].grid(row=0, column=i*2+1, sticky=tk.W, padx=(0,15))
        
        # Frame de servos
        servo_frame = ttk.LabelFrame(main_frame, text="Posição dos Servos", padding=10)
        servo_frame.pack(fill=tk.X, pady=(0,5))
        
        self.servo_labels = {}
        servo_names = ["Flaps L", "Flaps R", "Elevator", "Rudder", "Release"]
        servo_keys = ["flaps_left", "flaps_right", "elevator", "rudder", "release"]
        
        for i, (name, key) in enumerate(zip(servo_names, servo_keys)):
            ttk.Label(servo_frame, text=f"{name}:").grid(row=0, column=i*2, sticky=tk.W, padx=(0,5))
            self.servo_labels[key] = ttk.Label(servo_frame, text="90°", foreground="green")
            self.servo_labels[key].grid(row=0, column=i*2+1, sticky=tk.W, padx=(0,15))
        
        # Frame de LEDs
        led_frame = ttk.LabelFrame(main_frame, text="LEDs", padding=10)
        led_frame.pack(fill=tk.X, pady=(0,5))
        
        self.led_labels = {}
        led_names = [("Sistema", "system_active"), ("Alerta", "alert"), ("Liberação", "release")]
        
        for i, (name, key) in enumerate(led_names):
            ttk.Label(led_frame, text=f"{name}:").grid(row=0, column=i*2, sticky=tk.W, padx=(0,5))
            self.led_labels[key] = ttk.Label(led_frame, text="OFF", background="gray")
            self.led_labels[key].grid(row=0, column=i*2+1, sticky=tk.W, padx=(0,15))
        
        # Frame de gráficos
        self.plot_frame = ttk.Frame(main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)
    
    def setup_plots(self):
        """Configura gráficos matplotlib"""
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 6))
        self.fig.suptitle("Sistema de Estabilização do Planador")
        
        # Configurar eixos
        self.ax1.set_title("Atitude (Roll/Pitch)")
        self.ax1.set_ylabel("Ângulo (°)")
        self.ax1.grid(True)
        self.ax1.legend(["Roll", "Pitch"])
        
        self.ax2.set_title("Yaw Rate")
        self.ax2.set_ylabel("°/s")
        self.ax2.grid(True)
        
        self.ax3.set_title("Servos - Flaps")
        self.ax3.set_ylabel("Ângulo (°)")
        self.ax3.set_xlabel("Tempo (s)")
        self.ax3.grid(True)
        self.ax3.legend(["Esquerdo", "Direito"])
        
        self.ax4.set_title("Servos - Elevator/Rudder")
        self.ax4.set_ylabel("Ângulo (°)")
        self.ax4.set_xlabel("Tempo (s)")
        self.ax4.grid(True)
        self.ax4.legend(["Elevator", "Rudder"])
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        plt.tight_layout()
    
    def start_simulation(self):
        """Inicia simulação"""
        if not self.running:
            self.running = True
            self.simulator.running = True
            self.simulator.start_time = time.time()
            self.start_time = time.time()
            
            # Thread da simulação
            self.sim_thread = threading.Thread(target=self.run_simulation_loop, daemon=True)
            self.sim_thread.start()
            
            logger.info("Simulação iniciada")
    
    def stop_simulation(self):
        """Para simulação"""
        self.running = False
        self.simulator.running = False
        logger.info("Simulação parada")
    
    def reset_simulation(self):
        """Reseta simulação"""
        self.stop_simulation()
        time.sleep(0.1)
        
        # Limpar dados
        self.time_data.clear()
        self.roll_data.clear()
        self.pitch_data.clear()
        self.yaw_data.clear()
        
        for data in self.servo_data.values():
            data.clear()
        
        # Novo simulador
        self.simulator = PlanadorSimulator()
        
        logger.info("Simulação resetada")
    
    def run_simulation_loop(self):
        """Loop principal da simulação"""
        dt = 1.0 / 50.0  # 50 Hz
        
        while self.running:
            loop_start = time.time()
            
            # Atualizar perturbação
            self.simulator.hardware.disturbance_amplitude = self.disturbance_var.get()
            
            # Atualizar RC
            self.simulator.hardware.set_rc_signal(self.rc_var.get())
            
            # Executar iteração
            self.simulator.main_loop_iteration(dt)
            
            # Controlar frequência
            loop_time = time.time() - loop_start
            sleep_time = dt - loop_time
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def update_timer(self):
        """Timer para atualização da interface"""
        if self.running:
            self.update_display()
            self.update_plots()
        
        # RC label
        self.rc_label.config(text=str(self.rc_var.get()))
        
        # Próxima atualização
        self.root.after(100, self.update_timer)
    
    def update_display(self):
        """Atualiza displays de status"""
        status = self.simulator.get_status()
        
        # Status labels
        self.status_labels["loops"].config(text=f"{status['loop_count']}")
        self.status_labels["freq"].config(text=f"{status['frequency']:.1f}Hz")
        self.status_labels["roll"].config(text=f"{status['sensor_data']['roll']:.1f}°")
        self.status_labels["pitch"].config(text=f"{status['sensor_data']['pitch']:.1f}°")
        self.status_labels["yaw"].config(text=f"{status['sensor_data']['yaw_rate']:.1f}°/s")
        
        pid_str = f"[{self.simulator.pid_integral[0]:.1f}, {self.simulator.pid_integral[1]:.1f}, {self.simulator.pid_integral[2]:.1f}]"
        self.status_labels["pid"].config(text=pid_str)
        
        # Servo labels
        for name, angle in status['servo_positions'].items():
            if name in self.servo_labels:
                self.servo_labels[name].config(text=f"{angle:.0f}°")
        
        # LED labels
        for name, state in status['leds'].items():
            if name in self.led_labels:
                color = "green" if state else "gray"
                text = "ON" if state else "OFF"
                self.led_labels[name].config(text=text, background=color)
    
    def update_plots(self):
        """Atualiza gráficos"""
        if not self.running:
            return
        
        # Coletar dados
        current_time = time.time() - self.start_time
        status = self.simulator.get_status()
        
        self.time_data.append(current_time)
        self.roll_data.append(status['sensor_data']['roll'])
        self.pitch_data.append(status['sensor_data']['pitch'])
        self.yaw_data.append(status['sensor_data']['yaw_rate'])
        
        for name in self.servo_data:
            if name in status['servo_positions']:
                self.servo_data[name].append(status['servo_positions'][name])
            else:
                self.servo_data[name].append(90)  # Neutro
        
        # Atualizar gráficos
        if len(self.time_data) > 1:
            time_array = list(self.time_data)
            
            # Atitude
            self.ax1.clear()
            self.ax1.plot(time_array, list(self.roll_data), 'b-', label='Roll')
            self.ax1.plot(time_array, list(self.pitch_data), 'r-', label='Pitch')
            self.ax1.set_title("Atitude (Roll/Pitch)")
            self.ax1.set_ylabel("Ângulo (°)")
            self.ax1.grid(True)
            self.ax1.legend()
            
            # Yaw rate
            self.ax2.clear()
            self.ax2.plot(time_array, list(self.yaw_data), 'g-')
            self.ax2.set_title("Yaw Rate")
            self.ax2.set_ylabel("°/s")
            self.ax2.grid(True)
            
            # Servos flaps
            self.ax3.clear()
            self.ax3.plot(time_array, list(self.servo_data['flaps_left']), 'b-', label='Esquerdo')
            self.ax3.plot(time_array, list(self.servo_data['flaps_right']), 'r-', label='Direito')
            self.ax3.set_title("Servos - Flaps")
            self.ax3.set_ylabel("Ângulo (°)")
            self.ax3.set_xlabel("Tempo (s)")
            self.ax3.grid(True)
            self.ax3.legend()
            
            # Servos elevator/rudder
            self.ax4.clear()
            self.ax4.plot(time_array, list(self.servo_data['elevator']), 'g-', label='Elevator')
            self.ax4.plot(time_array, list(self.servo_data['rudder']), 'm-', label='Rudder')
            self.ax4.set_title("Servos - Elevator/Rudder")
            self.ax4.set_ylabel("Ângulo (°)")
            self.ax4.set_xlabel("Tempo (s)")
            self.ax4.grid(True)
            self.ax4.legend()
            
            self.canvas.draw()
    
    def run(self):
        """Executa interface gráfica"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Interface encerrada pelo usuário")
        finally:
            self.stop_simulation()

def main():
    """Função principal da GUI"""
    if not GUI_AVAILABLE:
        logger.error("Interface gráfica não disponível")
        logger.info("Para instalar: pip install matplotlib")
        return
    
    logger.info("Iniciando interface gráfica do simulador")
    
    try:
        gui = PlanadorGUI()
        gui.run()
    except Exception as e:
        logger.error(f"Erro na interface gráfica: {e}")
        messagebox.showerror("Erro", f"Erro na interface: {e}")

if __name__ == "__main__":
    main()