import socket
import threading
import subprocess
from datetime import datetime
from dnslib import DNSRecord, QTYPE, RR, A, AAAA

class MotorDNS:
    def __init__(self):
        self.ip_local = '127.0.0.1'
        self.porta_dns = 53
        self.dns_verdadeiro = '8.8.8.8'
        self.rodando = False
        self.thread_dns = None
        self.interface_rede = "Ethernet"
        
        # Variáveis que a interface vai preencher
        self.sites_bloqueados = []
        self.dias_bloqueio = []
        self.hora_inicio = 0
        self.hora_fim = 24

    def obter_interface_ativa(self):
        try:
            comando = 'wmic nic where "netenabled=true" get netconnectionid'
            resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
            linhas = resultado.stdout.strip().split('\n')
            if len(linhas) > 1:
                return linhas[1].strip()
        except:
            pass
        return "Wi-Fi"

    def configurar_regras(self, sites, dias, inicio, fim):
        """Recebe as configurações vindas da Interface Gráfica."""
        self.sites_bloqueados = sites
        self.dias_bloqueio = dias
        self.hora_inicio = inicio
        self.hora_fim = fim

    def iniciar(self):
        """Altera as rotas do Windows e liga o servidor em segundo plano."""
        if self.rodando: return
        
        self.rodando = True
        
        print(f"[*] Tentando assumir o controle da interface: {self.interface_rede}")
        
        # Roda o comando e captura a resposta do Windows
        comando = f'netsh interface ipv4 set dnsservers "{self.interface_rede}" static {self.ip_local} primary'
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        
        if resultado.returncode != 0:
            print(f"[ERRO NETSH] O Windows bloqueou a mudança de rede!\nDetalhes: {resultado.stderr}")
        else:
            print("[*] DNS alterado com sucesso no Windows!")

        subprocess.run('ipconfig /flushdns', shell=True, capture_output=True)
        
        self.thread_dns = threading.Thread(target=self._loop_servidor)
        self.thread_dns.daemon = True
        self.thread_dns.start()

    def parar(self):
        """Desliga o servidor e restaura a internet do Windows."""
        if not self.rodando: return
        
        self.rodando = False
        subprocess.run(f'netsh interface ipv4 set dnsservers "{self.interface_rede}" dhcp', shell=True, capture_output=True)
        subprocess.run('ipconfig /flushdns', shell=True, capture_output=True)

    def _loop_servidor(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((self.ip_local, self.porta_dns))
            sock.settimeout(1.0) 
        except Exception as e:
            print(f"Erro no socket: {e}")
            return

        while self.rodando:
            try:
                dados, endereco = sock.recvfrom(512)
                threading.Thread(target=self._processar_pacote, args=(sock, dados, endereco)).start()
            except socket.timeout:
                continue
            except Exception:
                pass
        sock.close()

    def _processar_pacote(self, sock, dados, endereco):
        try:
            requisicao = DNSRecord.parse(dados)
            nome_dominio = str(requisicao.q.qname).strip('.').lower()
            tipo_req = requisicao.q.qtype

            agora = datetime.now()
            bloquear = False
            
            # Verifica se está no horário e dia
            if agora.weekday() in self.dias_bloqueio and self.hora_inicio <= agora.hour < self.hora_fim:
                for site in self.sites_bloqueados:
                    if nome_dominio == site or nome_dominio.endswith('.' + site):
                        bloquear = True
                        break

            if bloquear:
                resposta = requisicao.reply()
                if tipo_req == QTYPE.A:
                    resposta.add_answer(RR(nome_dominio, QTYPE.A, rdata=A(self.ip_local)))
                elif tipo_req == QTYPE.AAAA:
                    resposta.add_answer(RR(nome_dominio, QTYPE.AAAA, rdata=AAAA("::1")))
                sock.sendto(resposta.pack(), endereco)
            else:
                sock_forward = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock_forward.settimeout(2.0)
                try:
                    sock_forward.sendto(dados, (self.dns_verdadeiro, 53))
                    resp, _ = sock_forward.recvfrom(4096)
                    sock.sendto(resp, endereco)
                except: pass
                finally: sock_forward.close()
        except: pass