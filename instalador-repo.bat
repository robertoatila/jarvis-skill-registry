@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cls

title INSTALADOR DE REPOSITORIOS - v31.2 QUALITY GATE

set "VERSION=31.2"
set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

call :detect_hd
call :desktop
call :find_git
if errorlevel 1 goto failed
"%GIT_EXE%" --version >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Git foi encontrado, mas nao executou corretamente.
  goto failed
)

set "BASE=%HD%\.gemini"
set "BAU=%BASE%\baude-skills-brutas"
set "REPO_ROOT=%BAU%\__github-repos"
set "LOG=%DESKTOP%\log-instalador-repo-v31.2.txt"
set "OKLIST=%DESKTOP%\repos-ok-v31.2.txt"
set "FAILLIST=%DESKTOP%\repos-falharam-v31.2.txt"
set "LOCK=%BAU%\repos-lock-v31.2.csv"
set "TOTAL_EXPECTED=205"

rem v31.2 quality gate: a lista declarada deve continuar exatamente em 205 repos.
set "DECLARED_SYNCS=0"
for /f %%C in ('findstr /R /B /C:"call :sync " "%~f0" ^| find /C /V ""') do set "DECLARED_SYNCS=%%C"
if not "%DECLARED_SYNCS%"=="%TOTAL_EXPECTED%" (
  echo [ERRO INTERNO] O BAT declara %DECLARED_SYNCS% repos, mas TOTAL_EXPECTED=%TOTAL_EXPECTED%.
  goto failed
)

mkdir "%BASE%" >nul 2>nul
mkdir "%BAU%" >nul 2>nul
mkdir "%REPO_ROOT%" >nul 2>nul

> "%LOG%" echo INSTALADOR DE REPOSITORIOS v%VERSION% - %DATE% %TIME%
> "%OKLIST%" echo OK - %DATE% %TIME%
> "%FAILLIST%" echo FALHAS - %DATE% %TIME%
> "%LOCK%" echo alias,url,branch,commit

set "GIT_TERMINAL_PROMPT=0"
set "GIT_ASKPASS=echo"
set "GIT_LFS_SKIP_SMUDGE=1"
set /a TOTAL=0
set /a CLONED=0
set /a UPDATED=0
set /a FAILED=0

echo ============================================================
echo  INSTALADOR DE REPOSITORIOS - v%VERSION%
echo ============================================================
echo HD:          %HD%\
echo Bau:         %BAU%
echo Repos cache: %REPO_ROOT%
echo Repos:       %TOTAL_EXPECTED% aprovados
echo Acao:        atualizar cache bruto e registrar SHA exato
echo.
echo Nao altera git config --global.
echo O cache bruto NAO e ativado diretamente: o setup decide o arsenal.
echo Reparo de cache: repos divergentes em __github-repos podem sofrer reset --hard.
echo Nenhum repositorio fora do cache gerenciado e alterado por esse reparo.
echo ============================================================
echo.

REM ===== MIGRACAO v31.2: REMOVER CACHES APOSENTADOS =====
call :retire "gsd-build_get-shit-done"
call :retire "lllyasviel_Fooocus"

REM ===== REPOSITORIOS APROVADOS =====
call :sync "https://github.com/google/skills.git" "google_skills"
call :sync "https://github.com/openai/skills.git" "openai_skills"
call :sync "https://github.com/anthropics/skills.git" "anthropics_skills"
call :sync "https://github.com/anthropics/claude-plugins-official.git" "anthropics_claude-plugins-official"
call :sync "https://github.com/addyosmani/agent-skills.git" "addyosmani_agent-skills"
call :sync "https://github.com/affaan-m/ECC.git" "affaan-m_ECC"
call :sync "https://github.com/alibaba/arthas.git" "alibaba_arthas"
call :sync "https://github.com/sickn33/agentic-awesome-skills.git" "sickn33_antigravity-awesome-skills"
call :sync "https://github.com/wshobson/agents.git" "wshobson_agents"
call :sync "https://github.com/VoltAgent/awesome-agent-skills.git" "VoltAgent_awesome-agent-skills"
call :sync "https://github.com/github/awesome-copilot.git" "github_awesome-copilot"
call :sync "https://github.com/ComposioHQ/awesome-claude-skills.git" "ComposioHQ_awesome-claude-skills"
call :sync "https://github.com/vercel-labs/skills.git" "vercel-labs_skills"
call :sync "https://github.com/Leonxlnx/taste-skill.git" "Leonxlnx_taste-skill"
call :sync "https://github.com/alchaincyf/huashu-design.git" "alchaincyf_huashu-design"
call :sync "https://github.com/pbakaus/impeccable.git" "pbakaus_impeccable"
call :sync "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git" "nextlevelbuilder_ui-ux-pro-max-skill"
call :sync "https://github.com/nexu-io/open-design.git" "nexu-io_open-design"
call :sync "https://github.com/multica-ai/andrej-karpathy-skills.git" "multica-ai_andrej-karpathy-skills"
call :sync "https://github.com/OthmanAdi/planning-with-files.git" "OthmanAdi_planning-with-files"
call :sync "https://github.com/mattpocock/skills.git" "mattpocock_skills"
call :sync "https://github.com/anthropics/knowledge-work-plugins.git" "anthropics_knowledge-work-plugins"
call :sync "https://github.com/obra/superpowers.git" "obra_superpowers"
call :sync "https://github.com/garrytan/gstack.git" "garrytan_gstack"
call :sync "https://github.com/open-gsd/gsd-core.git" "open-gsd_gsd-core"
call :sync "https://github.com/cursor/plugins.git" "cursor_plugins"
call :sync "https://github.com/vercel-labs/agent-skills.git" "vercel-labs_agent-skills"
call :sync "https://github.com/mvanhorn/last30days-skill.git" "mvanhorn_last30days-skill"
call :sync "https://github.com/alirezarezvani/claude-skills.git" "alirezarezvani_claude-skills"
call :sync "https://github.com/snarktank/ralph.git" "snarktank_ralph"
call :sync "https://github.com/anthropics/claude-code-security-review.git" "anthropics_claude-code-security-review"
call :sync "https://github.com/browserbase/stagehand.git" "browserbase_stagehand"
call :sync "https://github.com/browser-use/browser-use.git" "browser-use_browser-use"
call :sync "https://github.com/microsoft/playwright-cli.git" "microsoft_playwright-cli"
call :sync "https://github.com/microsoft/playwright-mcp.git" "microsoft_playwright-mcp"
call :sync "https://github.com/modelcontextprotocol/servers.git" "modelcontextprotocol_servers"
call :sync "https://github.com/thedotmack/claude-mem.git" "thedotmack_claude-mem"
call :sync "https://github.com/alexgreensh/token-optimizer.git" "alexgreensh_token-optimizer"
call :sync "https://github.com/JuliusBrussee/caveman.git" "JuliusBrussee_caveman"
call :sync "https://github.com/humanlayer/12-factor-agents.git" "humanlayer_12-factor-agents"
call :sync "https://github.com/microsoft/markitdown.git" "microsoft_markitdown"
call :sync "https://github.com/anomalyco/opencode.git" "anomalyco_opencode"
call :sync "https://github.com/docling-project/docling.git" "docling-project_docling"
call :sync "https://github.com/mksglu/context-mode.git" "mksglu_context-mode"
call :sync "https://github.com/rtk-ai/rtk.git" "rtk-ai_rtk"
call :sync "https://github.com/googleworkspace/cli.git" "googleworkspace_cli"
call :sync "https://github.com/AlexsJones/llmfit.git" "AlexsJones_llmfit"
call :sync "https://github.com/firecrawl/pdf-inspector.git" "firecrawl_pdf-inspector"
call :sync "https://github.com/vercel-labs/agent-browser.git" "vercel-labs_agent-browser"
call :sync "https://github.com/upstash/context7.git" "upstash_context7"
call :sync "https://github.com/unclecode/crawl4ai.git" "unclecode_crawl4ai"
call :sync "https://github.com/jina-ai/reader.git" "jina-ai_reader"
call :sync "https://github.com/firecrawl/firecrawl.git" "firecrawl_firecrawl"
call :sync "https://github.com/headroomlabs-ai/headroom.git" "headroomlabs-ai_headroom"
call :sync "https://github.com/ChromeDevTools/chrome-devtools-mcp.git" "ChromeDevTools_chrome-devtools-mcp"
call :sync "https://github.com/kepano/obsidian-skills.git" "kepano_obsidian-skills"
call :sync "https://github.com/hesreallyhim/awesome-claude-code.git" "hesreallyhim_awesome-claude-code"
call :sync "https://github.com/VoltAgent/awesome-design-md.git" "VoltAgent_awesome-design-md"
call :sync "https://github.com/mukul975/Anthropic-Cybersecurity-Skills.git" "mukul975_Anthropic-Cybersecurity-Skills"
call :sync "https://github.com/hardikpandya/stop-slop.git" "hardikpandya_stop-slop"
call :sync "https://github.com/janderson-fagner/spec-a23.git" "janderson-fagner_spec-a23"
call :sync "https://github.com/Imbad0202/academic-research-skills.git" "Imbad0202_academic-research-skills"
call :sync "https://github.com/coreyhaines31/marketingskills.git" "coreyhaines31_marketingskills"
call :sync "https://github.com/humanstudioacademy/skills.git" "humanstudioacademy_skills"
call :sync "https://github.com/alchaincyf/nuwa-skill.git" "alchaincyf_nuwa-skill"
call :sync "https://github.com/K-Dense-AI/scientific-agent-skills.git" "K-Dense-AI_scientific-agent-skills"
call :sync "https://github.com/Yuan1z0825/nature-skills.git" "Yuan1z0825_nature-skills"
call :sync "https://github.com/calesthio/OpenMontage.git" "calesthio_OpenMontage"
call :sync "https://github.com/VoltAgent/awesome-openclaw-skills.git" "VoltAgent_awesome-openclaw-skills"
call :sync "https://github.com/Shubhamsaboo/awesome-llm-apps.git" "Shubhamsaboo_awesome-llm-apps"
call :sync "https://github.com/virgiliojr94/book-to-skill.git" "virgiliojr94_book-to-skill"
call :sync "https://github.com/MadsLorentzen/ai-job-search.git" "MadsLorentzen_ai-job-search"
call :sync "https://github.com/ayghri/i-have-adhd.git" "ayghri_i-have-adhd"
call :sync "https://github.com/LottieFiles/motion-design-skill.git" "LottieFiles_motion-design-skill"
call :sync "https://github.com/zanwei/design-dna.git" "zanwei_design-dna"
call :sync "https://github.com/greensock/gsap-skills.git" "greensock_gsap-skills"
call :sync "https://github.com/CloudAI-X/threejs-skills.git" "CloudAI-X_threejs-skills"
call :sync "https://github.com/assistant-ui/skills.git" "assistant-ui_skills"
call :sync "https://github.com/vercel-labs/web-interface-guidelines.git" "vercel-labs_web-interface-guidelines"
call :sync "https://github.com/shadcn-ui/ui.git" "shadcn-ui_ui"
call :sync "https://github.com/emilkowalski/skills.git" "emilkowalski_skills"
call :sync "https://github.com/rohitg00/awesome-claude-code-toolkit.git" "rohitg00_awesome-claude-code-toolkit"
call :sync "https://github.com/rebelytics/one-skill-to-rule-them-all.git" "rebelytics_one-skill-to-rule-them-all"
call :sync "https://github.com/phuryn/pm-skills.git" "phuryn_pm-skills"
call :sync "https://github.com/ConardLi/garden-skills.git" "ConardLi_garden-skills"
call :sync "https://github.com/numman-ali/openskills.git" "numman-ali_openskills"
call :sync "https://github.com/Jeffallan/claude-skills.git" "Jeffallan_claude-skills"
call :sync "https://github.com/huggingface/skills.git" "huggingface_skills"
call :sync "https://github.com/nidhinjs/prompt-master.git" "nidhinjs_prompt-master"
call :sync "https://github.com/Orchestra-Research/AI-Research-SKILLs.git" "Orchestra-Research_AI-Research-SKILLs"
call :sync "https://github.com/MiniMax-AI/skills.git" "MiniMax-AI_skills"
call :sync "https://github.com/travisvn/awesome-claude-skills.git" "travisvn_awesome-claude-skills"
call :sync "https://github.com/composio-community/awesome-codex-skills.git" "composio-community_awesome-codex-skills"
call :sync "https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering.git" "muratcankoylan_Agent-Skills-for-Context-Engineering"
call :sync "https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep.git" "wanshuiyin_Auto-claude-code-research-in-sleep"
call :sync "https://github.com/wagoodman/dive.git" "wagoodman_dive"
call :sync "https://github.com/AnmolSaini16/mapcn.git" "AnmolSaini16_mapcn"
call :sync "https://github.com/mukul975/cve-mcp-server.git" "mukul975_cve-mcp-server"
call :sync "https://github.com/Skyvern-AI/skyvern.git" "Skyvern-AI_skyvern"
call :sync "https://github.com/jackwener/OpenCLI.git" "jackwener_OpenCLI"
call :sync "https://github.com/apify/crawlee.git" "apify_crawlee"
call :sync "https://github.com/lightpanda-io/browser.git" "lightpanda-io_browser"
call :sync "https://github.com/D4Vinci/Scrapling.git" "D4Vinci_Scrapling"
call :sync "https://github.com/microsoft/playwright.git" "microsoft_playwright"
call :sync "https://github.com/bytedance/UI-TARS-desktop.git" "bytedance_UI-TARS-desktop"
call :sync "https://github.com/punkpeye/awesome-mcp-servers.git" "punkpeye_awesome-mcp-servers"
call :sync "https://github.com/colbymchenry/codegraph.git" "colbymchenry_codegraph"
call :sync "https://github.com/tirth8205/code-review-graph.git" "tirth8205_code-review-graph"
call :sync "https://github.com/can1357/oh-my-pi.git" "can1357_oh-my-pi"
call :sync "https://github.com/Egonex-AI/Understand-Anything.git" "Egonex-AI_Understand-Anything"
call :sync "https://github.com/nashsu/llm_wiki.git" "nashsu_llm_wiki"
call :sync "https://github.com/builderz-labs/mission-control.git" "builderz-labs_mission-control"
call :sync "https://github.com/paperclipai/paperclip.git" "paperclipai_paperclip"
call :sync "https://github.com/openclaw/openclaw.git" "openclaw_openclaw"
call :sync "https://github.com/ollama/ollama.git" "ollama_ollama"
call :sync "https://github.com/openai/whisper.git" "openai_whisper"
call :sync "https://github.com/yt-dlp/yt-dlp.git" "yt-dlp_yt-dlp"
call :sync "https://github.com/heygen-com/hyperframes.git" "heygen-com_hyperframes"
call :sync "https://github.com/cloudflare/agentic-inbox.git" "cloudflare_agentic-inbox"
call :sync "https://github.com/abhigyanpatwari/GitNexus.git" "abhigyanpatwari_GitNexus"
call :sync "https://github.com/Comfy-Org/ComfyUI.git" "Comfy-Org_ComfyUI"
call :sync "https://github.com/OpenBMB/VoxCPM.git" "OpenBMB_VoxCPM"
call :sync "https://github.com/HKUDS/ViMax.git" "HKUDS_ViMax"
call :sync "https://github.com/supertone-inc/supertonic.git" "supertone-inc_supertonic"
call :sync "https://github.com/tinyhumansai/openhuman.git" "tinyhumansai_openhuman"
call :sync "https://github.com/ruvnet/ruflo.git" "ruvnet_ruflo"
call :sync "https://github.com/elie222/inbox-zero.git" "elie222_inbox-zero"
call :sync "https://github.com/crowdsecurity/crowdsec.git" "crowdsecurity_crowdsec"
call :sync "https://github.com/gitroomhq/postiz-app.git" "gitroomhq_postiz-app"
call :sync "https://github.com/tldraw/tldraw.git" "tldraw_tldraw"
call :sync "https://github.com/Crosstalk-Solutions/project-nomad.git" "Crosstalk-Solutions_project-nomad"
call :sync "https://github.com/zhayujie/CowAgent.git" "zhayujie_CowAgent"
call :sync "https://github.com/zylon-ai/private-gpt.git" "zylon-ai_private-gpt"
call :sync "https://github.com/bytedance/deer-flow.git" "bytedance_deer-flow"
call :sync "https://github.com/TencentCloud/TencentDB-Agent-Memory.git" "TencentCloud_TencentDB-Agent-Memory"
call :sync "https://github.com/openinterpreter/openinterpreter.git" "openinterpreter_openinterpreter"
call :sync "https://github.com/multica-ai/multica.git" "multica-ai_multica"
call :sync "https://github.com/excalidraw/excalidraw.git" "excalidraw_excalidraw"
call :sync "https://github.com/ScrapeGraphAI/Scrapegraph-ai.git" "ScrapeGraphAI_Scrapegraph-ai"
call :sync "https://github.com/21st-dev/magic-mcp.git" "21st-dev_magic-mcp"
call :sync "https://github.com/assistant-ui/assistant-ui.git" "assistant-ui_assistant-ui"
call :sync "https://github.com/creativetimofficial/ui.git" "creativetimofficial_ui"
call :sync "https://github.com/satnaing/shadcn-admin.git" "satnaing_shadcn-admin"
call :sync "https://github.com/wasp-lang/open-saas.git" "wasp-lang_open-saas"
call :sync "https://github.com/nextjs/saas-starter.git" "nextjs_saas-starter"
call :sync "https://github.com/MemTensor/MemOS.git" "MemTensor_MemOS"
call :sync "https://github.com/AgriciDaniel/claude-seo.git" "AgriciDaniel_claude-seo"
call :sync "https://github.com/lsdefine/GenericAgent.git" "lsdefine_GenericAgent"
call :sync "https://github.com/NanmiCoder/cc-haha.git" "NanmiCoder_cc-haha"
call :sync "https://github.com/NVIDIA/SkillSpector.git" "NVIDIA_SkillSpector"
call :sync "https://github.com/millionco/react-doctor.git" "millionco_react-doctor"
call :sync "https://github.com/yusufkaraaslan/Skill_Seekers.git" "yusufkaraaslan_Skill_Seekers"
call :sync "https://github.com/microsoft/SkillOpt.git" "microsoft_SkillOpt"
call :sync "https://github.com/teng-lin/notebooklm-py.git" "teng-lin_notebooklm-py"
call :sync "https://github.com/usestrix/strix.git" "usestrix_strix"
call :sync "https://github.com/infoslack/awesome-web-hacking.git" "infoslack_awesome-web-hacking"
call :sync "https://github.com/swisskyrepo/PayloadsAllTheThings.git" "swisskyrepo_PayloadsAllTheThings"
call :sync "https://github.com/The-Art-of-Hacking/h4cker.git" "The-Art-of-Hacking_h4cker"
call :sync "https://github.com/reddelexc/hackerone-reports.git" "reddelexc_hackerone-reports"
call :sync "https://github.com/redhuntlabs/Awesome-Asset-Discovery.git" "redhuntlabs_Awesome-Asset-Discovery"
call :sync "https://github.com/jivoi/awesome-ml-for-cybersecurity.git" "jivoi_awesome-ml-for-cybersecurity"
call :sync "https://github.com/sherlock-project/sherlock.git" "sherlock-project_sherlock"
call :sync "https://github.com/soxoj/maigret.git" "soxoj_maigret"
call :sync "https://github.com/sundowndev/phoneinfoga.git" "sundowndev_phoneinfoga"
call :sync "https://github.com/reconurge/flowsint.git" "reconurge_flowsint"
call :sync "https://github.com/PurpleAILAB/Decepticon.git" "PurpleAILAB_Decepticon"
call :sync "https://github.com/x64dbg/x64dbg.git" "x64dbg_x64dbg"
call :sync "https://github.com/WerWolv/ImHex.git" "WerWolv_ImHex"
call :sync "https://github.com/zhaoxuya520/reverse-skill.git" "zhaoxuya520_reverse-skill"
call :sync "https://github.com/agentskills/agentskills.git" "agentskills_agentskills"
call :sync "https://github.com/donnemartin/system-design-primer.git" "donnemartin_system-design-primer"
call :sync "https://github.com/iluwatar/java-design-patterns.git" "iluwatar_java-design-patterns"
call :sync "https://github.com/mingrammer/diagrams.git" "mingrammer_diagrams"
call :sync "https://github.com/thedaviddias/Front-End-Design-Checklist.git" "thedaviddias_Front-End-Design-Checklist"
call :sync "https://github.com/birobirobiro/awesome-shadcn-ui.git" "birobirobiro_awesome-shadcn-ui"
call :sync "https://github.com/gztchan/awesome-design.git" "gztchan_awesome-design"
call :sync "https://github.com/lissy93/personal-security-checklist.git" "lissy93_personal-security-checklist"
call :sync "https://github.com/farhanashrafdev/90DaysOfCyberSecurity.git" "farhanashrafdev_90DaysOfCyberSecurity"
call :sync "https://github.com/CarterPerez-dev/Cybersecurity-Projects.git" "CarterPerez-dev_Cybersecurity-Projects"
call :sync "https://github.com/rohitg00/ai-engineering-from-scratch.git" "rohitg00_ai-engineering-from-scratch"
call :sync "https://github.com/google/eng-practices.git" "google_eng-practices"
call :sync "https://github.com/public-apis/public-apis.git" "public-apis_public-apis"
call :sync "https://github.com/trimstray/the-book-of-secret-knowledge.git" "trimstray_the-book-of-secret-knowledge"
call :sync "https://github.com/trimstray/test-your-sysadmin-skills.git" "trimstray_test-your-sysadmin-skills"
call :sync "https://github.com/AllThingsSmitty/css-protips.git" "AllThingsSmitty_css-protips"
call :sync "https://github.com/florinpop17/app-ideas.git" "florinpop17_app-ideas"
call :sync "https://github.com/Chalarangelo/30-seconds-of-code.git" "Chalarangelo_30-seconds-of-code"
call :sync "https://github.com/microsoft/skills.git" "microsoft_skills"
call :sync "https://github.com/antfu/skills.git" "antfu_skills"
call :sync "https://github.com/cloudflare/skills.git" "cloudflare_skills"
call :sync "https://github.com/getsentry/skills.git" "getsentry_skills"
call :sync "https://github.com/BuilderIO/skills.git" "BuilderIO_skills"
call :sync "https://github.com/greptileai/skills.git" "greptileai_skills"
call :sync "https://github.com/aws/agent-toolkit-for-aws.git" "aws_agent-toolkit-for-aws"
call :sync "https://github.com/railwayapp/railway-skills.git" "railwayapp_railway-skills"
call :sync "https://github.com/supabase/agent-skills.git" "supabase_agent-skills"
call :sync "https://github.com/cisco-ai-defense/skill-scanner.git" "cisco-ai-defense_skill-scanner"
call :sync "https://github.com/snyk/agent-scan.git" "snyk_agent-scan"
call :sync "https://github.com/xtt1997/skillgrade.git" "xtt1997_skillgrade"
call :sync "https://github.com/NVIDIA/skills.git" "NVIDIA_skills"
call :sync "https://github.com/expo/skills.git" "expo_skills"
call :sync "https://github.com/oracle/skills.git" "oracle_skills"
call :sync "https://github.com/browserbase/skills.git" "browserbase_skills"
call :sync "https://github.com/remotion-dev/skills.git" "remotion-dev_skills"
call :sync "https://github.com/browser-act/skills.git" "browser-act_skills"
echo.
echo ============================================================
echo  CONCLUIDO - v%VERSION%
echo ============================================================
echo Processados: !TOTAL!/%TOTAL_EXPECTED%
echo Clonados:    !CLONED!
echo Atualizados: !UPDATED!
echo Falhas:      !FAILED!
echo Lock:        %LOCK%
echo Log:         %LOG%
echo OK:          %OKLIST%
echo Falhas:      %FAILLIST%
echo ============================================================

rem v31.2 quality gate: processados, contabilizados e lock devem fechar matematicamente.
set /a ACCOUNTED=CLONED+UPDATED+FAILED
if not "!TOTAL!"=="%TOTAL_EXPECTED%" (
  echo [ERRO QUALITY] Processados !TOTAL!, esperado %TOTAL_EXPECTED%.
  >> "%LOG%" echo QUALITY_TOTAL_MISMATCH=!TOTAL! EXPECTED=%TOTAL_EXPECTED%
  goto failed_after_run
)
if not "!ACCOUNTED!"=="!TOTAL!" (
  echo [ERRO QUALITY] Contabilidade inconsistente: !ACCOUNTED!/!TOTAL!.
  >> "%LOG%" echo QUALITY_ACCOUNTING_MISMATCH=!ACCOUNTED! TOTAL=!TOTAL!
  goto failed_after_run
)
set "LOCK_LINES=0"
for /f %%C in ('find /C /V "" ^< "%LOCK%"') do set "LOCK_LINES=%%C"
set /a LOCK_ROWS=LOCK_LINES-1
set /a SUCCESS=CLONED+UPDATED
if not "!LOCK_ROWS!"=="!SUCCESS!" (
  echo [ERRO QUALITY] Lock incompleto: !LOCK_ROWS! registros para !SUCCESS! repos com sucesso.
  >> "%LOG%" echo QUALITY_LOCK_MISMATCH=!LOCK_ROWS! SUCCESS=!SUCCESS!
  goto failed_after_run
)
findstr /C:"(unknown)" "%LOCK%" >nul 2>nul
if not errorlevel 1 (
  echo [ERRO QUALITY] O lock contem commit desconhecido.
  >> "%LOG%" echo QUALITY_LOCK_UNKNOWN_COMMIT=1
  goto failed_after_run
)
>> "%LOG%" echo QUALITY_GATE=OK ^| TOTAL=!TOTAL! ^| SUCCESS=!SUCCESS! ^| FAILED=!FAILED! ^| LOCK_ROWS=!LOCK_ROWS!
if !FAILED! GTR 0 goto failed_after_run
if not "%NO_PAUSE%"=="1" pause
exit /b 0

:retire
set "RETIRED_NAME=%~1"
set "RETIRED_DEST=%REPO_ROOT%\%~1"
if not exist "%RETIRED_DEST%\" exit /b 0
echo [RETIRE] %RETIRED_NAME%
>> "%LOG%" echo RETIRE=%RETIRED_NAME% ^| %RETIRED_DEST%
rmdir /s /q "%RETIRED_DEST%" >nul 2>nul
if exist "%RETIRED_DEST%\" (
  echo [AVISO] Nao foi possivel remover cache aposentado: %RETIRED_NAME%
  >> "%LOG%" echo RETIRE_FALHOU=%RETIRED_NAME%
) else (
  echo [RETIRADO] %RETIRED_NAME%
  >> "%LOG%" echo RETIRADO=%RETIRED_NAME%
)
exit /b 0

:sync
set /a TOTAL+=1
set "URL=%~1"
set "NAME=%~2"
set "DEST=%REPO_ROOT%\%~2"
echo [!TOTAL!/%TOTAL_EXPECTED%] !NAME!
>> "%LOG%" echo [!TOTAL!/%TOTAL_EXPECTED%] !NAME! - !URL!

if exist "!DEST!\.git\" (
  call :update_repo
  exit /b 0
)

if exist "!DEST!\" (
  echo [LIMPEZA] Pasta sem repositorio Git: !NAME!
  >> "%LOG%" echo PASTA_INVALIDA=!DEST!
  rmdir /s /q "!DEST!" >nul 2>nul
)

"%GIT_EXE%" -c core.longpaths=true clone --depth 1 --filter=blob:none --no-tags --single-branch "!URL!" "!DEST!" >> "%LOG%" 2>&1
if errorlevel 1 (
  set /a FAILED+=1
  echo [FALHA] !NAME!
  >> "%FAILLIST%" echo !NAME! - !URL!
  if exist "!DEST!\" rmdir /s /q "!DEST!" >nul 2>nul
  exit /b 0
)
set /a CLONED+=1
echo [CLONE] !NAME!
>> "%OKLIST%" echo CLONE - !NAME! - !URL!
call :record_lock
exit /b 0

:update_repo
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" remote set-url origin "%URL%" >> "%LOG%" 2>&1
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" pull --ff-only --quiet >> "%LOG%" 2>&1
if not errorlevel 1 (
  set /a UPDATED+=1
  echo [UPDATE] %NAME%
  >> "%OKLIST%" echo UPDATE - %NAME% - %URL%
  call :record_lock
  exit /b 0
)

echo [REPARO] %NAME%
>> "%LOG%" echo REPARO=%NAME%
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" fetch --prune --quiet origin >> "%LOG%" 2>&1
if errorlevel 1 goto update_failed

set "HEAD_FILE=%TEMP%\repo-head-v31.2-%RANDOM%%RANDOM%.txt"
set "REMOTE_HEAD="
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" symbolic-ref --quiet --short refs/remotes/origin/HEAD > "%HEAD_FILE%" 2>nul
for /f "usebackq delims=" %%B in ("%HEAD_FILE%") do if not defined REMOTE_HEAD set "REMOTE_HEAD=%%B"
if not defined REMOTE_HEAD (
  "%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" remote set-head origin -a >> "%LOG%" 2>&1
  "%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" symbolic-ref --quiet --short refs/remotes/origin/HEAD > "%HEAD_FILE%" 2>nul
  for /f "usebackq delims=" %%B in ("%HEAD_FILE%") do if not defined REMOTE_HEAD set "REMOTE_HEAD=%%B"
)
if not defined REMOTE_HEAD (
  "%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" branch --show-current > "%HEAD_FILE%" 2>nul
  set "CURRENT_BRANCH="
  for /f "usebackq delims=" %%B in ("%HEAD_FILE%") do if not defined CURRENT_BRANCH set "CURRENT_BRANCH=%%B"
  if defined CURRENT_BRANCH set "REMOTE_HEAD=origin/%CURRENT_BRANCH%"
)
del /f /q "%HEAD_FILE%" >nul 2>nul
if not defined REMOTE_HEAD goto update_failed

"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" rev-parse --verify "%REMOTE_HEAD%" >nul 2>nul
if errorlevel 1 goto update_failed
set "DEFAULT_BRANCH=%REMOTE_HEAD:origin/=%"

rem v31.2: __github-repos e cache gerenciado. Se pull --ff-only falhar,
rem o reparo deve descartar divergencia e mudancas rastreadas SOMENTE dentro desse cache.
echo [REPARO-CACHE] reset hard para %REMOTE_HEAD%
>> "%LOG%" echo REPARO_CACHE_RESET=%NAME% ^| %REMOTE_HEAD%
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" reset --hard "%REMOTE_HEAD%" >> "%LOG%" 2>&1
if errorlevel 1 goto update_failed
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" clean -fd >> "%LOG%" 2>&1
if errorlevel 1 goto update_failed
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" checkout -B "%DEFAULT_BRANCH%" "%REMOTE_HEAD%" >> "%LOG%" 2>&1
if errorlevel 1 goto update_failed
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" branch --set-upstream-to="%REMOTE_HEAD%" "%DEFAULT_BRANCH%" >> "%LOG%" 2>&1
if errorlevel 1 goto update_failed
set /a UPDATED+=1
echo [UPDATE-REPARADO] %NAME%
>> "%OKLIST%" echo UPDATE-REPARADO - %NAME% - %URL%
call :record_lock
exit /b 0

:update_failed
set /a FAILED+=1
echo [FALHA-UPDATE] %NAME%
>> "%FAILLIST%" echo UPDATE - %NAME% - %URL%
exit /b 0

:record_lock
set "BRANCH="
set "COMMIT="
set "LOCK_TMP=%TEMP%\repo-lock-v31.2-%RANDOM%%RANDOM%.txt"
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" branch --show-current > "%LOCK_TMP%" 2>nul
for /f "usebackq delims=" %%B in ("%LOCK_TMP%") do if not defined BRANCH set "BRANCH=%%B"
"%GIT_EXE%" -c core.longpaths=true -c "safe.directory=%DEST%" -C "%DEST%" rev-parse HEAD > "%LOCK_TMP%" 2>nul
for /f "usebackq delims=" %%C in ("%LOCK_TMP%") do if not defined COMMIT set "COMMIT=%%C"
del /f /q "%LOCK_TMP%" >nul 2>nul
if not defined BRANCH set "BRANCH=(detached)"
if not defined COMMIT set "COMMIT=(unknown)"
>> "%LOCK%" echo "%NAME%","%URL%","%BRANCH%","%COMMIT%"
exit /b 0

:find_git
set "GIT_EXE="
for %%G in (git.exe) do set "GIT_EXE=%%~$PATH:G"
if not defined GIT_EXE if exist "C:\Program Files\Git\cmd\git.exe" set "GIT_EXE=C:\Program Files\Git\cmd\git.exe"
if not defined GIT_EXE if exist "C:\Program Files\Git\bin\git.exe" set "GIT_EXE=C:\Program Files\Git\bin\git.exe"
if not defined GIT_EXE if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT_EXE=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
if not defined GIT_EXE if exist "%LOCALAPPDATA%\Programs\Git\bin\git.exe" set "GIT_EXE=%LOCALAPPDATA%\Programs\Git\bin\git.exe"
if defined GIT_EXE exit /b 0
echo [ERRO] Git nao encontrado.
echo Instale o Git ou adicione git.exe ao PATH.
exit /b 1

:detect_hd
set "HD="
set "SCRIPT_DRIVE=%~d0"
if not "%SCRIPT_DRIVE%"=="" if exist "%SCRIPT_DRIVE%\.gemini\" set "HD=%SCRIPT_DRIVE%"
if not defined HD if exist "D:\.gemini\" set "HD=D:"
if not defined HD if exist "E:\.gemini\" set "HD=E:"
if not defined HD for %%D in (F G H I J K L M N O P Q R S T U V W X Y Z C) do if not defined HD if exist "%%D:\.gemini\" set "HD=%%D:"
if not defined HD if not "%SCRIPT_DRIVE%"=="" set "HD=%SCRIPT_DRIVE%"
if not defined HD set "HD=E:"
exit /b 0

:desktop
set "DESKTOP=%USERPROFILE%\Desktop"
if exist "%DESKTOP%\" exit /b 0
if defined OneDrive if exist "%OneDrive%\Desktop\" set "DESKTOP=%OneDrive%\Desktop"
if exist "%DESKTOP%\" exit /b 0
set "DESKTOP=%HD%\Desktop"
mkdir "%DESKTOP%" >nul 2>nul
exit /b 0

:failed_after_run
if not "%NO_PAUSE%"=="1" pause
exit /b 1

:failed
if not "%NO_PAUSE%"=="1" pause
exit /b 1
