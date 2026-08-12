import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
from engine import MotorDNS

class AplicacaoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bloqueador DNS - Interface")
        self.root.geometry("400x550")
        self.root.resizable(False, False)
        
        # Verifica privilégios de Admin
        if not self._is_admin():
            messagebox.showerror("Acesso Negado", "Execute este script como Administrador!")
            self.root.destroy()
            sys.exit()

        # Instancia o nosso backend importado do outro arquivo
        self.motor = MotorDNS()
        self.criar_widgets()
        
        # Se fechar no "X", garante que o motor pare antes da janela sumir
        self.root.protocol("WM_DELETE_WINDOW", self.fechar_app)

    def _is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def criar_widgets(self):
        tk.Label(self.root, text="Controle de Foco", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(self.root, text="Domínios a bloquear:").pack()
        self.texto_sites = tk.Text(self.root, height=6, width=40)
        self.texto_sites.pack(pady=5)
        self.texto_sites.insert(tk.END, "tiktok.com\nx.com\nreddit.com")

        tk.Label(self.root, text="Dias da semana:").pack(pady=5)
        self.frame_dias = tk.Frame(self.root)
        self.frame_dias.pack()
        
        dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        self.vars_dias = []
        for i, dia in enumerate(dias):
            var = tk.BooleanVar(value=True if i < 5 else False)
            chk = tk.Checkbutton(self.frame_dias, text=dia, variable=var)
            chk.grid(row=0, column=i)
            self.vars_dias.append(var)

        tk.Label(self.root, text="Horário:").pack(pady=10)
        frame_horas = tk.Frame(self.root)
        frame_horas.pack()
        
        tk.Label(frame_horas, text="Das").grid(row=0, column=0)
        self.spin_inicio = tk.Spinbox(frame_horas, from_=0, to=23, width=5)
        self.spin_inicio.delete(0, "end"); self.spin_inicio.insert(0, "9")
        self.spin_inicio.grid(row=0, column=1)
        
        tk.Label(frame_horas, text="h às").grid(row=0, column=2)
        self.spin_fim = tk.Spinbox(frame_horas, from_=0, to=23, width=5)
        self.spin_fim.delete(0, "end"); self.spin_fim.insert(0, "17")
        self.spin_fim.grid(row=0, column=3)
        tk.Label(frame_horas, text="h").grid(row=0, column=4)

        self.lbl_status = tk.Label(self.root, text="STATUS: DESLIGADO", fg="red", font=("Arial", 12, "bold"))
        self.lbl_status.pack(pady=20)

        self.btn_acao = tk.Button(self.root, text="LIGAR BLOQUEADOR", bg="green", fg="white", 
                                  font=("Arial", 12, "bold"), command=self.alternar_estado)
        self.btn_acao.pack(pady=10, fill=tk.X, padx=50)

    def extrair_dados_interface(self):
        """Pega o que o usuário digitou e limpa para enviar ao motor."""
        conteudo = self.texto_sites.get("1.0", tk.END).strip()
        linhas = [linha.strip().lower() for linha in conteudo.split('\n') if linha.strip()]
        
        sites = set()
        for site in linhas:
            site = site.replace("http://", "").replace("https://", "").split('/')[0]
            if site.startswith("www."): site = site[4:]
            sites.add(site)
            
        dias = [i for i, var in enumerate(self.vars_dias) if var.get()]
        hora_inicio = int(self.spin_inicio.get())
        hora_fim = int(self.spin_fim.get())
        
        return list(sites), dias, hora_inicio, hora_fim

    def alternar_estado(self):
        if not self.motor.rodando:
            sites, dias, h_inicio, h_fim = self.extrair_dados_interface()
            
            # Envia os dados para o Backend e dá a partida
            self.motor.configurar_regras(sites, dias, h_inicio, h_fim)
            self.motor.iniciar()
            
            self.lbl_status.config(text="STATUS: ATIVO (DNS SINKHOLE)", fg="green")
            self.btn_acao.config(text="DESLIGAR BLOQUEADOR", bg="red")
            self.texto_sites.config(state=tk.DISABLED)
        else:
            # Manda o Backend parar
            self.motor.parar()
            
            self.lbl_status.config(text="STATUS: DESLIGADO", fg="red")
            self.btn_acao.config(text="LIGAR BLOQUEADOR", bg="green")
            self.texto_sites.config(state=tk.NORMAL)

    def fechar_app(self):
        self.motor.parar() # Segurança extra
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacaoGUI(root)
    root.mainloop()