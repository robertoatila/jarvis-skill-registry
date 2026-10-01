# HUD, dados e voz: limites atuais

Este documento descreve o que o HUD pode afirmar com base nos contratos presentes no código. A implementação local pode estar atrás desta branch; confirme o commit e o estado dos provedores antes de interpretar a interface como evidência de execução.

## Chat

O HUD envia mensagens a `POST /api/chat`. O servidor só encaminha inferência em nuvem quando `JARVIS_CHAT_ALLOW_CLOUD=1`, um token `JARVIS_CHAT_TOKEN` válido é apresentado, o provedor escolhido pertence a `JARVIS_CHAT_PROVIDERS`, e o modelo explícito e a credencial daquele provedor estão disponíveis. Sem essas condições, a resposta deve indicar bloqueio/configuração ausente. A chave do provedor e o token de acesso ao servidor são credenciais diferentes. Veja o [limite de inferência do servidor](SERVER_INFERENCE_BOUNDARY.md).

O chat não lê automaticamente o catálogo de skills, os favoritos do GitHub, arquivos do workspace ou memória local. A busca e a leitura dos dados do catálogo acontecem nas telas correspondentes. As mensagens também não são memorizadas automaticamente; registros locais são adicionados na tela de Memória.

## Voz

O HUD distingue duas capacidades independentes:

- **Síntese de fala (TTS):** usa `speechSynthesis` e vozes instaladas/disponíveis no navegador e sistema operacional. A interface informa quando o navegador não oferece TTS, quando ainda não há vozes carregadas ou quando o perfil escolhido não tem voz compatível.
- **Ditado (STT):** usa `SpeechRecognition` ou `webkitSpeechRecognition`, quando exposto pelo navegador. Essa API tem suporte desigual entre navegadores e pode usar serviço de reconhecimento de rede; este repositório não inclui um mecanismo local de transcrição. O texto reconhecido é inserido para revisão e não é enviado ao chat automaticamente.

Compatibilidade precisa ser validada no navegador e dispositivo de destino; presença de um controle de microfone não prova que o serviço está disponível.

## Atualidade e proveniência dos dados

- O Radar de repositórios de 100k+ exibe o `generated_at` incluído no próprio arquivo de catálogo. Esse horário indica a geração do snapshot, não atualização ao vivo.
- O catálogo de repositórios favoritados é cache local. Se não carrega uma data confiável da fonte, o HUD diz que a data não foi registrada e não trata contagens de estrelas como atuais.
- O catálogo de skills e seus rótulos são dados carregados localmente. `PASS` é apenas um rótulo do catálogo, não certificação independente nem garantia de segurança.
- Hashes, fases e contagens de snapshots históricos não são apresentados como estado atual sem evidência compatível com o catálogo carregado. Uma raiz Merkle indisponível não pode ser copiada como se fosse válida.
- Indicadores de agentes começam sem estado confirmado; o endpoint e o resultado de execução devem fornecer o valor observado. Histórico de quarentena desconhecido aparece como `—`, não como zero.

## Verificação deste ajuste

O teste de navegação com Playwright cobre carregamento do HUD, indicação de configuração do chat, degradação quando reconhecimento de fala não existe, inserção de ditado sem envio e data de geração do Radar 100k+. `python jarvis.py --full-test` cobre a bateria Python do repositório. Esses testes verificam a branch e seus fixtures; não configuram provedores, vozes do sistema nem atualizam o checkout/serviço local do usuário.
