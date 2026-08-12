# Bloqueador de Domínios (DNS Sinkhole)

Aplicativo em Python com interface gráfica (Tkinter) que atua como um servidor DNS local para bloquear o acesso a domínios específicos no Windows com base em regras de agendamento.

## Status do Projeto

⚠️ **Em desenvolvimento contínuo:** Este software está em caráter experimental e continua em desenvolvimento ativo. O foco das próximas atualizações e refatorações é justamente solucionar e mitigar os problemas e limitações de arquitetura descritos no final deste documento.

## O que o projeto faz

1. **Alteração de Rota:** Ao ser ativado, o script identifica a placa de rede ativa no Windows via `wmic` e utiliza comandos `netsh` para alterar o servidor DNS primário (IPv4 e IPv6) do sistema para a própria máquina (`127.0.0.1` e `::1`).
2. **Interceptação:** Um servidor UDP rodando em segundo plano escuta a porta 53. Ele analisa as requisições DNS originadas pelo sistema.
3. **Bloqueio ou Repasse:** 
   * Se o domínio requisitado corresponder à lista de bloqueio e o sistema estiver dentro do horário/dia agendado, o script retorna um pacote forjado apontando o domínio para `localhost`, bloqueando o acesso.
   * Se o domínio for permitido (ou estiver fora do horário de bloqueio), o pacote é encaminhado para o DNS público do Google (`8.8.8.8`), resolvido e devolvido ao usuário.
4. **Restauração:** Ao clicar no botão de desativar ou ao fechar a interface, o script executa novos comandos `netsh` para devolver as configurações do adaptador de rede para o modo automático (DHCP).

## Problemas e Limitações Conhecidas

Este projeto possui limitações estruturais devido à forma como sistemas operacionais e navegadores modernos lidam com tráfego de rede:

* **Inútil contra DNS Seguro (DoH):** Navegadores modernos (Chrome, Edge, Firefox, Brave) vêm com "Secure DNS" (DNS over HTTPS) ativado por padrão. Isso faz o navegador ignorar as configurações de rede do Windows e enviar as requisições DNS diretamente para servidores em nuvem via porta 443. Para o bloqueador funcionar, o usuário **precisa** desativar o DNS Seguro manualmente nas configurações do navegador.
* **Risco de Perda de Conexão:** Se o processo do Python for encerrado de forma abrupta (ex: fechado via Gerenciador de Tarefas, queda de energia ou erro fatal no script), a função de restauração não será executada. O Windows continuará com o DNS apontado para `127.0.0.1`, deixando a máquina sem navegação na internet até que o usuário reverta as configurações manualmente no Painel de Controle.
* **Exclusividade Windows:** O código backend (`motor_dns.py`) é totalmente dependente de utilitários nativos do Windows (`netsh` e `wmic` via `subprocess`). Não funcionará em Linux ou macOS.
* **Exigência de Privilégios:** O programa recusa a execução se não for aberto via terminal com privilégios de Administrador, o que impede a criação de atalhos simples de um clique para usuários comuns.
* **DNS Upstream Fixo:** O servidor DNS de encaminhamento para tráfego legítimo está fixado (hardcoded) no IP `8.8.8.8` (Google). Se o usuário estiver em uma rede que bloqueia o DNS do Google, a internet inteira deixará de funcionar enquanto o bloqueador estiver ativo.
