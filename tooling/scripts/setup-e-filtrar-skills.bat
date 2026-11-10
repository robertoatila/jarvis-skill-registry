@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
@echo off
cls

title SETUP E FILTRAR SKILLS - v31.2 STABLE BATCH + QUALITY

set "VERSION=31.2"
set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

set "USER_HOME=%USERPROFILE%"
if not defined USER_HOME set "USER_HOME=C:\Users\alunos"
call :detect_hd
call :detect_desktop

set "BASE=%HD%\.gemini"
set "BAU=%BASE%\baude-skills-brutas"
set "PACKAGE=%BASE%\pacote-escola-skills"
set "CACHE=%TEMP%\cache-setup-skills-v31.2-%RANDOM%%RANDOM%"
set "LOG=%DESKTOP%\setup-skills-v31.2.txt"
set "MISS=%DESKTOP%\setup-skills-v31.2-faltando.txt"
set "ACTIVE_LIST=%DESKTOP%\setup-skills-v31.2-ativas.txt"
set "SOURCE_MANIFEST=%DESKTOP%\setup-skills-v31.2-manifest.csv"
set "UNMANAGED=%DESKTOP%\setup-skills-v31.2-nao-gerenciadas.txt"
set "MANAGED_STATE=%BASE%\config\arsenal-managed-v31.txt"
set "MANAGED_NEW=%TEMP%\arsenal-managed-v31-%RANDOM%%RANDOM%.txt"
set "LEGACY_LIST=%TEMP%\arsenal-legacy-v31-%RANDOM%%RANDOM%.txt"
set "TARGET=165"
set "COUNT_ADDED=0"
set "COPY_FAIL=0"
set "PACKAGE_FAIL=0"
set "RESERVA_CONTEXTO=routers locais, regras do projeto e margem contra truncamento"

mkdir "%BASE%\config" >nul 2>nul
if exist "%CACHE%" rmdir /s /q "%CACHE%" >nul 2>nul
mkdir "%CACHE%" >nul 2>nul
> "%MISS%" echo Skills faltando - setup v%VERSION%
> "%ACTIVE_LIST%" echo # Skills ativas - setup v%VERSION%
> "%SOURCE_MANIFEST%" echo nome,sha256,source
type nul > "%MANAGED_NEW%"
type nul > "%LEGACY_LIST%"
> "%UNMANAGED%" echo Skills nao gerenciadas preservadas - v%VERSION%
> "%LOG%" echo SETUP SKILLS v%VERSION% - %DATE% %TIME%
>> "%LOG%" echo HD=%HD%
>> "%LOG%" echo BAU=%BAU%
>> "%LOG%" echo TARGET=%TARGET%

call :build_legacy_list

echo ============================================================
echo  SETUP E FILTRAR SKILLS - v%VERSION%
echo ============================================================
echo Drive:          %HD%
echo Usuario:        %USER_HOME%
echo Bau:            %BAU%
echo Target global:  %TARGET% skills
echo Estrategia:     arquitetura BAT estavel + arsenal curado atual
echo.
echo Mecanica restaurada para o modelo direto que ja funcionava no Windows.
echo Este BAT somente seleciona, valida e instala o arsenal global.
echo Nao usa /MIR nos roots globais: skills nao gerenciadas sao preservadas.
echo Arsenal atual: 165 skills globais; routers do Markitos continuam separados.
echo Meta pratica de contexto: ocupar o maximo seguro sem ultrapassar 100%%.
echo ============================================================
echo.

if not exist "%BAU%\" (
  echo [ERRO] Bau nao encontrado: %BAU%
  echo Rode primeiro o instalador-repo-v31.0.bat.
  goto failed
)

set "DECLARED_CALLS=0"
for /f %%C in ('findstr /R /B /C:"call :ADDNAME " "%~f0" ^| find /C /V ""') do set "DECLARED_CALLS=%%C"
if not "%DECLARED_CALLS%"=="%TARGET%" (
  echo [ERRO INTERNO] O BAT declara %DECLARED_CALLS% skills, mas TARGET=%TARGET%.
  echo Corrija o arquivo antes de continuar.
  >> "%LOG%" echo ERRO_INTERNO_DECLARADAS=%DECLARED_CALLS% TARGET=%TARGET%
  goto failed
)

echo Montando cache validado com %TARGET% skills...
echo.
call :ADDNAME "openai-docs" "%BAU%\__github-repos\openai_skills\skills\.system\openai-docs"
call :ADDNAME "using-agent-skills" "%BAU%\__github-repos\addyosmani_agent-skills\skills\using-agent-skills"
call :ADDNAME "agent-skill-stack" "%BAU%\__github-repos\github_awesome-copilot\skills\agent-skill-stack"
call :ADDNAME "agent-supply-chain" "%BAU%\__github-repos\github_awesome-copilot\skills\agent-supply-chain"
call :ADDNAME "spec-driven-development" "%BAU%\__github-repos\addyosmani_agent-skills\skills\spec-driven-development"
call :ADDNAME "source-driven-development" "%BAU%\__github-repos\addyosmani_agent-skills\skills\source-driven-development"
call :ADDNAME "deprecation-and-migration" "%BAU%\__github-repos\addyosmani_agent-skills\skills\deprecation-and-migration"
call :ADDNAME "api-and-interface-design" "%BAU%\__github-repos\addyosmani_agent-skills\skills\api-and-interface-design"
call :ADDNAME "performance-optimization" "%BAU%\__github-repos\addyosmani_agent-skills\skills\performance-optimization"
call :ADDNAME "frontend-design" "%BAU%\__github-repos\anthropics_skills\skills\frontend-design"
call :ADDNAME "webapp-testing" "%BAU%\__github-repos\anthropics_skills\skills\webapp-testing"
call :ADDNAME "domain-modeling" "%BAU%\__github-repos\mattpocock_skills\skills\engineering\domain-modeling"
call :ADDNAME "dispatching-parallel-agents" "%BAU%\__github-repos\obra_superpowers\skills\dispatching-parallel-agents"
rem v31.2: GitNexus para inteligencia estrutural; workflow universal preservado fora dele
call :ADDNAME "gitnexus-impact-analysis" "%BAU%\__github-repos\abhigyanpatwari_GitNexus\.claude\skills\gitnexus-impact-analysis"
call :ADDNAME "gitnexus-exploring" "%BAU%\__github-repos\abhigyanpatwari_GitNexus\.claude\skills\gitnexus-exploring"
call :ADDNAME "gitnexus-pdg-query" "%BAU%\__github-repos\abhigyanpatwari_GitNexus\.claude\skills\gitnexus\gitnexus-pdg-query"
call :ADDNAME "gitnexus-review" "%BAU%\__github-repos\abhigyanpatwari_GitNexus\.claude\skills\gitnexus-review"
call :ADDNAME "gitnexus-plan" "%BAU%\__github-repos\abhigyanpatwari_GitNexus\.claude\skills\gitnexus-plan"
call :ADDNAME "incremental-implementation"
call :ADDNAME "gitnexus-refactoring" "%BAU%\__github-repos\abhigyanpatwari_GitNexus\.claude\skills\gitnexus-refactoring"
call :ADDNAME "gitnexus-debugging" "%BAU%\__github-repos\abhigyanpatwari_GitNexus\.claude\skills\gitnexus-debugging"
call :ADDNAME "gitnexus-cli" "%BAU%\__github-repos\abhigyanpatwari_GitNexus\.claude\skills\gitnexus-cli"
call :ADDNAME "use-railway" "%BAU%\__github-repos\railwayapp_railway-skills\plugins\railway\skills\use-railway"
call :ADDNAME "codex-antigravity-skill-policy"
call :ADDNAME "ui-ux-pro-max"
call :ADDNAME "impeccable"
call :ADDNAME "testing-api-for-broken-object-level-authorization"
call :ADDNAME "testing-oauth2-implementation-flaws"
call :ADDNAME "performing-api-inventory-and-discovery"
call :ADDNAME "implementing-devsecops-security-scanning"
call :ADDNAME "integrating-sast-into-github-actions-pipeline"
call :ADDNAME "performing-sca-dependency-scanning-with-snyk"
call :ADDNAME "securing-serverless-functions"
call :ADDNAME "integrating-dast-with-owasp-zap-in-pipeline"
call :ADDNAME "chrome-devtools" "%BAU%\__github-repos\ChromeDevTools_chrome-devtools-mcp\skills\chrome-devtools"
call :ADDNAME "agentic-actions-auditor"
call :ADDNAME "broken-authentication"
call :ADDNAME "react-best-practices" "%BAU%\__github-repos\vercel-labs_agent-skills\skills\react-best-practices"
call :ADDNAME "api-fuzzing-bug-bounty"
call :ADDNAME "docker-expert"
call :ADDNAME "frontend-ui-engineering"
call :ADDNAME "javascript-typescript-typescript-scaffold"
call :ADDNAME "mock-hunter"
call :ADDNAME "test-driven-development"
call :ADDNAME "backend-dev-guidelines"
call :ADDNAME "ai-engineering-toolkit"
call :ADDNAME "frontend-api-integration-patterns"
call :ADDNAME "frontend-mobile-security-xss-scan"
call :ADDNAME "arthas" "%BAU%\__github-repos\alibaba_arthas\skills"
call :ADDNAME "typescript-advanced-types"
call :ADDNAME "skill-installer"
call :ADDNAME "claude-code-expert"
call :ADDNAME "git-pr-workflows-pr-enhance"
call :ADDNAME "shipping-and-launch"
call :ADDNAME "ci-cd-and-automation"
call :ADDNAME "react-doctor" "%BAU%\__github-repos\millionco_react-doctor\.agents\skills\react-doctor"
call :ADDNAME "mcp-builder" "%BAU%\__github-repos\anthropics_skills\skills\mcp-builder"
call :ADDNAME "git-workflow-and-versioning"
call :ADDNAME "openapi-spec-generation"
call :ADDNAME "sql-injection-testing"
call :ADDNAME "backend-development-feature-development"
call :ADDNAME "react-state-management"
call :ADDNAME "aws-compute" "%BAU%\__github-repos\aws_agent-toolkit-for-aws\skills\core-skills\aws-compute"
call :ADDNAME "aws-serverless" "%BAU%\__github-repos\aws_agent-toolkit-for-aws\skills\core-skills\aws-serverless"
call :ADDNAME "bash-defensive-patterns" "%BAU%\__github-repos\wshobson_agents\plugins\shell-scripting\skills\bash-defensive-patterns"
call :ADDNAME "context-engineering"
call :ADDNAME "backend-security-coder"
call :ADDNAME "laravel-security-audit"
call :ADDNAME "nodejs-backend-patterns"
call :ADDNAME "python-pro"
call :ADDNAME "cloud-architect"
call :ADDNAME "api-documenter"
call :ADDNAME "api-security-best-practices"
call :ADDNAME "zod-validation-expert"
call :ADDNAME "java-pro"
call :ADDNAME "context-compression" "%BAU%\__github-repos\muratcankoylan_Agent-Skills-for-Context-Engineering\skills\context-compression"
call :ADDNAME "codebase-audit-pre-push"
call :ADDNAME "database-migrations-sql-migrations"
call :ADDNAME "javascript-testing-patterns"
call :ADDNAME "ai-engineer"
call :ADDNAME "api-endpoint-builder"
call :ADDNAME "typescript-expert"
call :ADDNAME "gemini-api-integration"
call :ADDNAME "api-security-testing"
call :ADDNAME "gh-fix-ci" "%BAU%\__github-repos\openai_skills\skills\.curated\gh-fix-ci"
call :ADDNAME "gh-address-comments" "%BAU%\__github-repos\openai_skills\skills\.curated\gh-address-comments"
call :ADDNAME "chatgpt-apps" "%BAU%\__github-repos\openai_skills\skills\.curated\chatgpt-apps"
call :ADDNAME "figma-implement-design" "%BAU%\__github-repos\openai_skills\skills\.curated\figma-implement-design"
call :ADDNAME "error-handling-patterns"
call :ADDNAME "sql-pro"
call :ADDNAME "web-security-testing"
call :ADDNAME "sql-optimization-patterns"
call :ADDNAME "database-architect"
call :ADDNAME "k6-load-testing"
call :ADDNAME "supabase-postgres-best-practices" "%BAU%\__github-repos\supabase_agent-skills\skills\supabase-postgres-best-practices"
call :ADDNAME "auth-implementation-patterns"
call :ADDNAME "privacy-by-design"
call :ADDNAME "frontend-security-coder"
call :ADDNAME "git-advanced-workflows"
call :ADDNAME "production-audit"
call :ADDNAME "workers-best-practices" "%BAU%\__github-repos\cloudflare_skills\skills\workers-best-practices"
call :ADDNAME "fastapi-pro"
call :ADDNAME "php-pro"
call :ADDNAME "devops-deploy"
call :ADDNAME "linux-troubleshooting"
call :ADDNAME "skill-creator" "%BAU%\__github-repos\openai_skills\skills\.system\skill-creator"
call :ADDNAME "assistant-ui" "%BAU%\__github-repos\assistant-ui_skills\assistant-ui\skills\assistant-ui"
call :ADDNAME "huggingface-best" "%BAU%\__github-repos\huggingface_skills\skills\huggingface-best"
call :ADDNAME "react-modernization"
call :ADDNAME "javascript-pro"
call :ADDNAME "devops-troubleshooter"
call :ADDNAME "database-optimizer"
call :ADDNAME "network-engineer"
call :ADDNAME "backend-architect"
call :ADDNAME "bash-linux"
call :ADDNAME "database-design"
call :ADDNAME "github-actions-templates"
call :ADDNAME "database-migrations-migration-observability"
call :ADDNAME "api-patterns"
call :ADDNAME "database-admin"
call :ADDNAME "distributed-tracing"
call :ADDNAME "aws-security" "%BAU%\__github-repos\aws_agent-toolkit-for-aws\skills\core-skills\aws-security"
call :ADDNAME "aws-secrets-rotation"
call :ADDNAME "deploy-to-vercel" "%BAU%\__github-repos\vercel-labs_agent-skills\skills\deploy-to-vercel"
call :ADDNAME "sqlmap-database-pentesting"
call :ADDNAME "burp-suite-testing"
call :ADDNAME "springboot-tdd" "%BAU%\__github-repos\affaan-m_ECC\skills\springboot-tdd"
call :ADDNAME "springboot-verification" "%BAU%\__github-repos\affaan-m_ECC\skills\springboot-verification"
call :ADDNAME "springboot-security" "%BAU%\__github-repos\affaan-m_ECC\skills\springboot-security"
call :ADDNAME "jpa-patterns" "%BAU%\__github-repos\affaan-m_ECC\skills\jpa-patterns"
call :ADDNAME "mysql-patterns" "%BAU%\__github-repos\affaan-m_ECC\skills\mysql-patterns"
call :ADDNAME "react-testing" "%BAU%\__github-repos\affaan-m_ECC\skills\react-testing"
call :ADDNAME "java-coding-standards" "%BAU%\__github-repos\affaan-m_ECC\skills\java-coding-standards"
call :ADDNAME "security-review" "%BAU%\__github-repos\affaan-m_ECC\skills\security-review"
call :ADDNAME "security-scan" "%BAU%\__github-repos\affaan-m_ECC\skills\security-scan"
call :ADDNAME "spring-boot-testing"
call :ADDNAME "nextjs-app-router-patterns" "%BAU%\__github-repos\wshobson_agents\plugins\frontend-mobile-development\skills\nextjs-app-router-patterns"
call :ADDNAME "tailwind-patterns"
call :ADDNAME "tailwind-design-system"
call :ADDNAME "shadcn" "%BAU%\__github-repos\shadcn-ui_ui\skills\shadcn"
call :ADDNAME "saas-multi-tenant"
call :ADDNAME "observability-and-instrumentation"
call :ADDNAME "systematic-debugging" "%BAU%\__github-repos\obra_superpowers\skills\systematic-debugging"
call :ADDNAME "verification-before-completion" "%BAU%\__github-repos\obra_superpowers\skills\verification-before-completion"
call :ADDNAME "planning-with-files" "%BAU%\__github-repos\OthmanAdi_planning-with-files\skills\planning-with-files"
call :ADDNAME "using-git-worktrees" "%BAU%\__github-repos\obra_superpowers\skills\using-git-worktrees"
call :ADDNAME "code-simplification" "%BAU%\__github-repos\addyosmani_agent-skills\skills\code-simplification"
call :ADDNAME "documentation-and-adrs" "%BAU%\__github-repos\addyosmani_agent-skills\skills\documentation-and-adrs"
call :ADDNAME "springboot-patterns" "%BAU%\__github-repos\affaan-m_ECC\skills\springboot-patterns"
call :ADDNAME "frontend-a11y" "%BAU%\__github-repos\affaan-m_ECC\skills\frontend-a11y"
call :ADDNAME "playwright-cli" "%BAU%\__github-repos\microsoft_playwright\packages\playwright-core\src\tools\skills\playwright-cli"
call :ADDNAME "context-budget" "%BAU%\__github-repos\affaan-m_ECC\skills\context-budget"
call :ADDNAME "subagent-driven-development" "%BAU%\__github-repos\obra_superpowers\skills\subagent-driven-development"
call :ADDNAME "book-to-skill" "%BAU%\__github-repos\virgiliojr94_book-to-skill"
call :ADDNAME "vercel-optimize" "%BAU%\__github-repos\vercel-labs_agent-skills\skills\vercel-optimize"
call :ADDNAME "web-design-guidelines" "%BAU%\__github-repos\vercel-labs_agent-skills\skills\web-design-guidelines"
call :ADDNAME "vercel-composition-patterns" "%BAU%\__github-repos\vercel-labs_agent-skills\skills\composition-patterns"
call :ADDNAME "motion-design" "%BAU%\__github-repos\LottieFiles_motion-design-skill\skills\motion-design"
call :ADDNAME "design-dna" "%BAU%\__github-repos\zanwei_design-dna"
call :ADDNAME "gsap-core" "%BAU%\__github-repos\greensock_gsap-skills\skills\gsap-core"
call :ADDNAME "gsap-react" "%BAU%\__github-repos\greensock_gsap-skills\skills\gsap-react"
call :ADDNAME "gsap-performance" "%BAU%\__github-repos\greensock_gsap-skills\skills\gsap-performance"
call :ADDNAME "gsap-scrolltrigger" "%BAU%\__github-repos\greensock_gsap-skills\skills\gsap-scrolltrigger"
call :ADDNAME "threejs-fundamentals" "%BAU%\__github-repos\CloudAI-X_threejs-skills\skills\threejs-fundamentals"
call :ADDNAME "threejs-animation" "%BAU%\__github-repos\CloudAI-X_threejs-skills\skills\threejs-animation"
set "CACHE_COUNT=0"
for /d %%S in ("%CACHE%\*") do if exist "%%~fS\SKILL.md" set /a CACHE_COUNT+=1
if not "!CACHE_COUNT!"=="%TARGET%" (
  echo.
  echo [ERRO] Cache incompleto: !CACHE_COUNT!/%TARGET%.
  echo Nada foi apagado.
  echo Veja: %MISS%
  goto failed_keep_cache
)

call :validate_cache
if errorlevel 1 (
  echo [ERRO] Quality gate estrutural falhou. Nada foi apagado.
  goto failed_keep_cache
)

echo.
echo [OK] Cache valido: !CACHE_COUNT!/%TARGET%


set "DEST1=%USER_HOME%\.agent\skills"
set "DEST2=%USER_HOME%\.agents\skills"
set "DEST3=%USER_HOME%\.codex\skills"
set "DEST4=%USER_HOME%\.claude\skills"
set "DEST5=%USER_HOME%\.gemini\skills"
set "DEST6=%USER_HOME%\.gemini\config\skills"
set "DEST7=%USER_HOME%\.gemini\antigravity-ide\skills"
set "DEST8=%USER_HOME%\antigravity\skills"
set "DEST9=%BASE%\skills"
set "DEST10=%BASE%\config\skills"
set "DEST11=%BASE%\antigravity-ide\skills"
set "DEST12=%BASE%\antigravity\skills"

echo.
echo Instalando somente o arsenal gerenciado nos 12 destinos ativos...
for %%D in (
  "%DEST1%"
  "%DEST2%"
  "%DEST3%"
  "%DEST4%"
  "%DEST5%"
  "%DEST6%"
  "%DEST7%"
  "%DEST8%"
  "%DEST9%"
  "%DEST10%"
  "%DEST11%"
  "%DEST12%"
) do (
  call :deploy_root "%%~D"
  if errorlevel 1 set /a COPY_FAIL+=1
)

if !COPY_FAIL! GTR 0 (
  echo [ERRO] Falha em !COPY_FAIL! destino(s). O cache foi preservado.
  goto failed_keep_cache
)

copy /y "%MANAGED_NEW%" "%MANAGED_STATE%" >nul
if errorlevel 1 (
  echo [ERRO] Nao foi possivel gravar o estado gerenciado.
  goto failed_keep_cache
)

for %%D in ("%DEST1%" "%DEST2%" "%DEST3%" "%DEST4%" "%DEST5%" "%DEST6%" "%DEST7%" "%DEST8%" "%DEST9%" "%DEST10%" "%DEST11%" "%DEST12%") do call :report_unmanaged "%%~D"

echo Montando pacote escola...
if exist "%PACKAGE%" rmdir /s /q "%PACKAGE%" >nul 2>nul
set "PKG1=%PACKAGE%\.agent\skills"
set "PKG2=%PACKAGE%\.agents\skills"
set "PKG3=%PACKAGE%\.codex\skills"
set "PKG4=%PACKAGE%\.claude\skills"
set "PKG5=%PACKAGE%\.gemini\skills"
set "PKG6=%PACKAGE%\.gemini\config\skills"
set "PKG7=%PACKAGE%\.gemini\antigravity-ide\skills"
set "PKG8=%PACKAGE%\antigravity\skills"
for %%D in (
  "%PKG1%"
  "%PKG2%"
  "%PKG3%"
  "%PKG4%"
  "%PKG5%"
  "%PKG6%"
  "%PKG7%"
  "%PKG8%"
) do (
  mkdir "%%~D" >nul 2>nul
  robocopy "%CACHE%" "%%~D" /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP /XD .git node_modules dist build .venv venv target coverage __pycache__ .next .turbo >nul
  if errorlevel 8 (
    set /a PACKAGE_FAIL+=1
    >> "%LOG%" echo FALHA_PACOTE=%%~D
  )
)

set "PKGCOUNT=0"
for /d %%S in ("%PKG1%\*") do if exist "%%~fS\SKILL.md" set /a PKGCOUNT+=1
if not "!PKGCOUNT!"=="%TARGET%" set /a PACKAGE_FAIL+=1
if !PACKAGE_FAIL! GTR 0 (
  echo [ERRO] Falha ao montar o pacote escola.
  goto failed_keep_cache
)

if exist "%CACHE%" rmdir /s /q "%CACHE%" >nul 2>nul
del /f /q "%MANAGED_NEW%" "%LEGACY_LIST%" >nul 2>nul

echo.
echo ============================================================
echo  SETUP CONCLUIDO - v%VERSION%
echo ============================================================
echo Skills globais gerenciadas: %TARGET%
echo Pacote escola:              !PKGCOUNT!
echo Lista:                       %ACTIVE_LIST%
echo Manifesto SHA-256:           %SOURCE_MANIFEST%
echo Nao gerenciadas preservadas: %UNMANAGED%
echo Estado gerenciado:           %MANAGED_STATE%
echo Log:                         %LOG%
echo ============================================================
echo Feche totalmente os agentes e abra novamente.
if not "%NO_PAUSE%"=="1" pause
exit /b 0

:ADDNAME
@echo off
set "NAME=%~1"
set "EXPLICIT_SRC=%~2"
if "%NAME%"=="" exit /b 0
if !COUNT_ADDED! GEQ !TARGET! exit /b 0
if exist "%CACHE%\%NAME%\SKILL.md" exit /b 0
set "SRC="

if defined EXPLICIT_SRC if exist "%EXPLICIT_SRC%\SKILL.md" set "SRC=%EXPLICIT_SRC%"

rem Prioridade v31.2: fonte explicita e upstreams primarios antes de agregadores/mirrors.
for %%P in (
  "%BAU%\__github-repos\google_skills\skills\%NAME%"
  "%BAU%\__github-repos\openai_skills\skills\.system\%NAME%"
  "%BAU%\__github-repos\openai_skills\skills\.curated\%NAME%"
  "%BAU%\__github-repos\anthropics_skills\skills\%NAME%"
  "%BAU%\__github-repos\microsoft_skills\skills\%NAME%"
  "%BAU%\__github-repos\github_awesome-copilot\skills\%NAME%"
  "%BAU%\__github-repos\addyosmani_agent-skills\skills\%NAME%"
  "%BAU%\__github-repos\aws_agent-toolkit-for-aws\skills\core-skills\%NAME%"
  "%BAU%\__github-repos\cloudflare_skills\skills\%NAME%"
  "%BAU%\__github-repos\supabase_agent-skills\skills\%NAME%"
  "%BAU%\__github-repos\vercel-labs_agent-skills\skills\%NAME%"
  "%BAU%\__github-repos\getsentry_skills\skills\%NAME%"
  "%BAU%\__github-repos\BuilderIO_skills\skills\%NAME%"
  "%BAU%\__github-repos\obra_superpowers\skills\%NAME%"
  "%BAU%\__github-repos\wshobson_agents\skills\%NAME%"
  "%BAU%\__github-repos\affaan-m_ECC\skills\%NAME%"
  "%BAU%\__github-repos\OthmanAdi_planning-with-files\skills\%NAME%"
  "%BAU%\__github-repos\greensock_gsap-skills\skills\%NAME%"
  "%BAU%\__github-repos\CloudAI-X_threejs-skills\skills\%NAME%"
  "%BAU%\__github-repos\LottieFiles_motion-design-skill\skills\%NAME%"
  "%BAU%\__github-repos\assistant-ui_skills\assistant-ui\skills\%NAME%"
  "%BAU%\__github-repos\ChromeDevTools_chrome-devtools-mcp\skills\%NAME%"
  "%BAU%\__github-repos\shadcn-ui_ui\skills\%NAME%"
  "%BAU%\__github-repos\ConardLi_garden-skills\skills\%NAME%"
  "%BAU%\__github-repos\Jeffallan_claude-skills\skills\%NAME%"
  "%BAU%\__github-repos\huggingface_skills\skills\%NAME%"
  "%BAU%\__github-repos\muratcankoylan_Agent-Skills-for-Context-Engineering\skills\%NAME%"
  "%BAU%\__github-repos\millionco_react-doctor\.agents\skills\%NAME%"
  "%BAU%\__github-repos\emilkowalski_skills\skills\%NAME%"
  "%BAU%\__github-repos\rohitg00_awesome-claude-code-toolkit\skills\%NAME%"
  "%BAU%\__github-repos\phuryn_pm-skills\skills\%NAME%"
  "%BAU%\__github-repos\sickn33_antigravity-awesome-skills\skills\%NAME%"
  "%BAU%\addyosmani_agent-skills__%NAME%"
  "%BAU%\github_awesome-copilot__%NAME%"
  "%USER_HOME%\.agent\skills\%NAME%"
  "%USER_HOME%\.agents\skills\%NAME%"
  "%USER_HOME%\.codex\skills\%NAME%"
  "%USER_HOME%\.claude\skills\%NAME%"
  "%USER_HOME%\.gemini\skills\%NAME%"
  "%USER_HOME%\.gemini\config\skills\%NAME%"
  "%USER_HOME%\.gemini\antigravity-ide\skills\%NAME%"
  "%BASE%\skills\%NAME%"
  "%BASE%\config\skills\%NAME%"
  "%BASE%\antigravity-ide\skills\%NAME%"
  "%BASE%\antigravity\skills\%NAME%"
  "%BAU%\__local-active-skills\%NAME%"
  "%PACKAGE%\.agent\skills\%NAME%"
) do (
  if not defined SRC if exist "%%~P\SKILL.md" set "SRC=%%~P"
)

if not defined SRC goto ADD_FAIL
robocopy "%SRC%" "%CACHE%\%NAME%" /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP /XD .git node_modules dist build .venv venv target coverage __pycache__ .next .turbo >nul
if errorlevel 8 goto ADD_FAIL
if not exist "%CACHE%\%NAME%\SKILL.md" goto ADD_FAIL

set "HASH_FILE=%CACHE%\%NAME%\SKILL.md"
set "HASH="
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath $env:HASH_FILE).Hash" 2^>nul`) do if not defined HASH set "HASH=%%H"
if not defined HASH goto ADD_FAIL

set /a COUNT_ADDED+=1
echo [OK !COUNT_ADDED!/!TARGET!] %NAME%
>> "%ACTIVE_LIST%" echo %NAME%
>> "%MANAGED_NEW%" echo %NAME%
>> "%SOURCE_MANIFEST%" echo "%NAME%","%HASH%","%SRC%"
>> "%LOG%" echo OK=%NAME% ^| %HASH% ^| %SRC%
exit /b 0

:ADD_FAIL
@echo off
echo [FALTA/INVALIDA] %NAME%
>> "%MISS%" echo %NAME%
>> "%LOG%" echo FALTA_OU_INVALIDA=%NAME%
if exist "%CACHE%\%NAME%" rmdir /s /q "%CACHE%\%NAME%" >nul 2>nul
exit /b 0

:validate_cache
@echo off
set "VALIDATE_ROOT=%CACHE%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $seen=@{}; $bad=$false; Get-ChildItem -LiteralPath $env:VALIDATE_ROOT -Directory | ForEach-Object { $f=Join-Path $_.FullName 'SKILL.md'; $line=Get-Content -LiteralPath $f -TotalCount 60 | Where-Object { $_ -match '^\s*name\s*:\s*(.+?)\s*$' } | Select-Object -First 1; if(-not $line) { Write-Host ('[INVALIDA] sem name: ' + $_.Name); $bad=$true } else { $n=($line -replace '^\s*name\s*:\s*','').Trim().Trim([char]34,[char]39); if($seen.ContainsKey($n)) { Write-Host ('[DUPLICATE YAML NAME] ' + $n + ' em ' + $_.Name + ' e ' + $seen[$n]); $bad=$true } else { $seen[$n]=$_.Name } } }; $bin=Get-ChildItem -LiteralPath $env:VALIDATE_ROOT -Recurse -File | Where-Object { $_.Extension -in '.exe','.dll','.msi','.scr','.com' }; if($bin) { $bin | ForEach-Object { Write-Host ('[BINARIO BLOQUEADO] ' + $_.FullName) }; $bad=$true }; if($bad) { exit 2 } else { exit 0 }" >> "%LOG%" 2>&1
exit /b %ERRORLEVEL%

:deploy_root
@echo off
set "ROOT=%~1"
mkdir "%ROOT%" >nul 2>nul
if not exist "%ROOT%\" exit /b 1

rem Remove apenas nomes que este ecossistema gerencia; nunca espelha o root inteiro.
for /f "usebackq delims=" %%N in ("%LEGACY_LIST%") do if not "%%N"=="" if exist "%ROOT%\%%N\" rmdir /s /q "%ROOT%\%%N" >nul 2>nul
if exist "%MANAGED_STATE%" for /f "usebackq delims=" %%N in ("%MANAGED_STATE%") do if not "%%N"=="" if exist "%ROOT%\%%N\" rmdir /s /q "%ROOT%\%%N" >nul 2>nul
for /f "usebackq delims=" %%N in ("%MANAGED_NEW%") do if not "%%N"=="" if exist "%ROOT%\%%N\" rmdir /s /q "%ROOT%\%%N" >nul 2>nul

robocopy "%CACHE%" "%ROOT%" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP /XD .git node_modules dist build .venv venv target coverage __pycache__ .next .turbo >nul
if errorlevel 8 (
  >> "%LOG%" echo FALHA_DESTINO=%ROOT%
  exit /b 1
)

set "VERIFY_FAIL=0"
for /f "usebackq delims=" %%N in ("%MANAGED_NEW%") do if not "%%N"=="" if not exist "%ROOT%\%%N\SKILL.md" set "VERIFY_FAIL=1"
if "%VERIFY_FAIL%"=="1" (
  >> "%LOG%" echo VERIFICACAO_FALHOU=%ROOT%
  exit /b 1
)
>> "%LOG%" echo OK_DESTINO=%ROOT%
exit /b 0

:report_unmanaged
@echo off
set "ROOT=%~1"
if not exist "%ROOT%\" exit /b 0
for /d %%S in ("%ROOT%\*") do if exist "%%~fS\SKILL.md" (
  findstr /I /X /L /C:"%%~nxS" "%MANAGED_NEW%" >nul 2>nul
  if errorlevel 1 >> "%UNMANAGED%" echo %%~nxS ^| %%~fS
)
exit /b 0

:build_legacy_list
@echo off
>> "%LEGACY_LIST%" echo gsd-context-workflow
>> "%LEGACY_LIST%" echo 007
>> "%LEGACY_LIST%" echo openai-docs
>> "%LEGACY_LIST%" echo codex-review
>> "%LEGACY_LIST%" echo using-agent-skills
>> "%LEGACY_LIST%" echo antigravity-skill-orchestrator
>> "%LEGACY_LIST%" echo codex-antigravity-skill-policy
>> "%LEGACY_LIST%" echo taste-skill
>> "%LEGACY_LIST%" echo ui-ux-pro-max
>> "%LEGACY_LIST%" echo impeccable
>> "%LEGACY_LIST%" echo testing-api-for-broken-object-level-authorization
>> "%LEGACY_LIST%" echo testing-oauth2-implementation-flaws
>> "%LEGACY_LIST%" echo performing-api-inventory-and-discovery
>> "%LEGACY_LIST%" echo implementing-devsecops-security-scanning
>> "%LEGACY_LIST%" echo integrating-sast-into-github-actions-pipeline
>> "%LEGACY_LIST%" echo performing-sca-dependency-scanning-with-snyk
>> "%LEGACY_LIST%" echo securing-serverless-functions
>> "%LEGACY_LIST%" echo integrating-dast-with-owasp-zap-in-pipeline
>> "%LEGACY_LIST%" echo chrome-devtools
>> "%LEGACY_LIST%" echo github-automation
>> "%LEGACY_LIST%" echo agentic-actions-auditor
>> "%LEGACY_LIST%" echo broken-authentication
>> "%LEGACY_LIST%" echo react-best-practices
>> "%LEGACY_LIST%" echo ejentum-reasoning-harness
>> "%LEGACY_LIST%" echo security-and-hardening
>> "%LEGACY_LIST%" echo api-fuzzing-bug-bounty
>> "%LEGACY_LIST%" echo docker-expert
>> "%LEGACY_LIST%" echo frontend-ui-engineering
>> "%LEGACY_LIST%" echo code-review-and-quality
>> "%LEGACY_LIST%" echo javascript-typescript-typescript-scaffold
>> "%LEGACY_LIST%" echo mock-hunter
>> "%LEGACY_LIST%" echo test-driven-development
>> "%LEGACY_LIST%" echo backend-dev-guidelines
>> "%LEGACY_LIST%" echo cc-skill-security-review
>> "%LEGACY_LIST%" echo ai-engineering-toolkit
>> "%LEGACY_LIST%" echo frontend-api-integration-patterns
>> "%LEGACY_LIST%" echo frontend-mobile-security-xss-scan
>> "%LEGACY_LIST%" echo arthas
>> "%LEGACY_LIST%" echo typescript-advanced-types
>> "%LEGACY_LIST%" echo skill-installer
>> "%LEGACY_LIST%" echo claude-code-expert
>> "%LEGACY_LIST%" echo git-pr-workflows-pr-enhance
>> "%LEGACY_LIST%" echo shipping-and-launch
>> "%LEGACY_LIST%" echo ci-cd-and-automation
>> "%LEGACY_LIST%" echo react-doctor
>> "%LEGACY_LIST%" echo mcp-builder
>> "%LEGACY_LIST%" echo git-workflow-and-versioning
>> "%LEGACY_LIST%" echo openapi-spec-generation
>> "%LEGACY_LIST%" echo production-code-audit
>> "%LEGACY_LIST%" echo sql-injection-testing
>> "%LEGACY_LIST%" echo backend-development-feature-development
>> "%LEGACY_LIST%" echo react-state-management
>> "%LEGACY_LIST%" echo aws-serverless
>> "%LEGACY_LIST%" echo bash-defensive-patterns
>> "%LEGACY_LIST%" echo context-engineering
>> "%LEGACY_LIST%" echo frontend-dev-guidelines
>> "%LEGACY_LIST%" echo backend-security-coder
>> "%LEGACY_LIST%" echo modern-javascript-patterns
>> "%LEGACY_LIST%" echo laravel-security-audit
>> "%LEGACY_LIST%" echo nodejs-backend-patterns
>> "%LEGACY_LIST%" echo python-pro
>> "%LEGACY_LIST%" echo cloud-architect
>> "%LEGACY_LIST%" echo api-documenter
>> "%LEGACY_LIST%" echo api-security-best-practices
>> "%LEGACY_LIST%" echo test-automator
>> "%LEGACY_LIST%" echo zod-validation-expert
>> "%LEGACY_LIST%" echo java-pro
>> "%LEGACY_LIST%" echo skill-router
>> "%LEGACY_LIST%" echo context-compression
>> "%LEGACY_LIST%" echo codebase-audit-pre-push
>> "%LEGACY_LIST%" echo database-migrations-sql-migrations
>> "%LEGACY_LIST%" echo javascript-testing-patterns
>> "%LEGACY_LIST%" echo parallel-agents
>> "%LEGACY_LIST%" echo sast-configuration
>> "%LEGACY_LIST%" echo ai-engineer
>> "%LEGACY_LIST%" echo api-endpoint-builder
>> "%LEGACY_LIST%" echo typescript-expert
>> "%LEGACY_LIST%" echo gemini-api-integration
>> "%LEGACY_LIST%" echo logic-lens
>> "%LEGACY_LIST%" echo mcp-tool-developer
>> "%LEGACY_LIST%" echo api-security-testing
>> "%LEGACY_LIST%" echo gh-fix-ci
>> "%LEGACY_LIST%" echo gh-address-comments
>> "%LEGACY_LIST%" echo cli-creator
>> "%LEGACY_LIST%" echo chatgpt-apps
>> "%LEGACY_LIST%" echo figma-implement-design
>> "%LEGACY_LIST%" echo api-design-principles
>> "%LEGACY_LIST%" echo error-handling-patterns
>> "%LEGACY_LIST%" echo nodejs-best-practices
>> "%LEGACY_LIST%" echo saas-mvp-launcher
>> "%LEGACY_LIST%" echo sql-pro
>> "%LEGACY_LIST%" echo web-security-testing
>> "%LEGACY_LIST%" echo sql-optimization-patterns
>> "%LEGACY_LIST%" echo database-architect
>> "%LEGACY_LIST%" echo k6-load-testing
>> "%LEGACY_LIST%" echo postgresql-optimization
>> "%LEGACY_LIST%" echo security-audit
>> "%LEGACY_LIST%" echo auth-implementation-patterns
>> "%LEGACY_LIST%" echo lambdatest-agent-skills
>> "%LEGACY_LIST%" echo privacy-by-design
>> "%LEGACY_LIST%" echo squirrel
>> "%LEGACY_LIST%" echo frontend-security-coder
>> "%LEGACY_LIST%" echo git-advanced-workflows
>> "%LEGACY_LIST%" echo production-audit
>> "%LEGACY_LIST%" echo python-fastapi-development
>> "%LEGACY_LIST%" echo bash-pro
>> "%LEGACY_LIST%" echo cloudflare-workers-expert
>> "%LEGACY_LIST%" echo fastapi-pro
>> "%LEGACY_LIST%" echo php-pro
>> "%LEGACY_LIST%" echo skill-sentinel
>> "%LEGACY_LIST%" echo audit-context-building
>> "%LEGACY_LIST%" echo devops-deploy
>> "%LEGACY_LIST%" echo linux-troubleshooting
>> "%LEGACY_LIST%" echo skill-creator
>> "%LEGACY_LIST%" echo assistant-ui
>> "%LEGACY_LIST%" echo huggingface-best
>> "%LEGACY_LIST%" echo hf-cli
>> "%LEGACY_LIST%" echo multi-agent-task-orchestrator
>> "%LEGACY_LIST%" echo react-modernization
>> "%LEGACY_LIST%" echo agent-memory-mcp
>> "%LEGACY_LIST%" echo cloud-devops
>> "%LEGACY_LIST%" echo idor-testing
>> "%LEGACY_LIST%" echo javascript-pro
>> "%LEGACY_LIST%" echo deployment-engineer
>> "%LEGACY_LIST%" echo devops-troubleshooter
>> "%LEGACY_LIST%" echo postgresql
>> "%LEGACY_LIST%" echo unit-testing-test-generate
>> "%LEGACY_LIST%" echo e2e-testing
>> "%LEGACY_LIST%" echo database-optimizer
>> "%LEGACY_LIST%" echo full-stack-orchestration-full-stack-feature
>> "%LEGACY_LIST%" echo network-engineer
>> "%LEGACY_LIST%" echo backend-architect
>> "%LEGACY_LIST%" echo bash-linux
>> "%LEGACY_LIST%" echo database-design
>> "%LEGACY_LIST%" echo github-actions-templates
>> "%LEGACY_LIST%" echo database-migrations-migration-observability
>> "%LEGACY_LIST%" echo api-patterns
>> "%LEGACY_LIST%" echo database-admin
>> "%LEGACY_LIST%" echo distributed-tracing
>> "%LEGACY_LIST%" echo security-auditor
>> "%LEGACY_LIST%" echo zustand-store-ts
>> "%LEGACY_LIST%" echo aws-security-audit
>> "%LEGACY_LIST%" echo aws-iam-best-practices
>> "%LEGACY_LIST%" echo debugging-toolkit-smart-debug
>> "%LEGACY_LIST%" echo senior-architect
>> "%LEGACY_LIST%" echo aws-secrets-rotation
>> "%LEGACY_LIST%" echo cred-omega
>> "%LEGACY_LIST%" echo vercel-deployment
>> "%LEGACY_LIST%" echo testing-api-security-with-owasp-top-10
>> "%LEGACY_LIST%" echo sqlmap-database-pentesting
>> "%LEGACY_LIST%" echo burp-suite-testing
>> "%LEGACY_LIST%" echo affaan-m_ECC__springboot-tdd
>> "%LEGACY_LIST%" echo affaan-m_ECC__springboot-verification
>> "%LEGACY_LIST%" echo affaan-m_ECC__springboot-security
>> "%LEGACY_LIST%" echo affaan-m_ECC__jpa-patterns
>> "%LEGACY_LIST%" echo affaan-m_ECC__mysql-patterns
>> "%LEGACY_LIST%" echo affaan-m_ECC__react-performance
>> "%LEGACY_LIST%" echo affaan-m_ECC__react-testing
>> "%LEGACY_LIST%" echo affaan-m_ECC__frontend-patterns
>> "%LEGACY_LIST%" echo affaan-m_ECC__java-coding-standards
>> "%LEGACY_LIST%" echo affaan-m_ECC__security-review
>> "%LEGACY_LIST%" echo affaan-m_ECC__security-scan
>> "%LEGACY_LIST%" echo spring-boot-testing
>> "%LEGACY_LIST%" echo nextjs-app-router-patterns
>> "%LEGACY_LIST%" echo nextjs-best-practices
>> "%LEGACY_LIST%" echo tailwind-patterns
>> "%LEGACY_LIST%" echo tailwind-design-system
>> "%LEGACY_LIST%" echo shadcn
>> "%LEGACY_LIST%" echo architect-review
>> "%LEGACY_LIST%" echo performance-engineer
>> "%LEGACY_LIST%" echo saas-multi-tenant
>> "%LEGACY_LIST%" echo observability-and-instrumentation
>> "%LEGACY_LIST%" echo systematic-debugging
>> "%LEGACY_LIST%" echo verification-before-completion
>> "%LEGACY_LIST%" echo planning-with-files
>> "%LEGACY_LIST%" echo using-git-worktrees
>> "%LEGACY_LIST%" echo code-simplification
>> "%LEGACY_LIST%" echo documentation-and-adrs
>> "%LEGACY_LIST%" echo springboot-patterns
>> "%LEGACY_LIST%" echo frontend-a11y
>> "%LEGACY_LIST%" echo playwright-cli
>> "%LEGACY_LIST%" echo context-budget
>> "%LEGACY_LIST%" echo skill-stocktake
>> "%LEGACY_LIST%" echo subagent-driven-development
>> "%LEGACY_LIST%" echo book-to-skill
>> "%LEGACY_LIST%" echo vercel-optimize
>> "%LEGACY_LIST%" echo web-design-guidelines
>> "%LEGACY_LIST%" echo vercel-composition-patterns
>> "%LEGACY_LIST%" echo motion-design
>> "%LEGACY_LIST%" echo design-dna
>> "%LEGACY_LIST%" echo gsap-core
>> "%LEGACY_LIST%" echo gsap-react
>> "%LEGACY_LIST%" echo gsap-performance
>> "%LEGACY_LIST%" echo gsap-scrolltrigger
>> "%LEGACY_LIST%" echo threejs-fundamentals
>> "%LEGACY_LIST%" echo threejs-animation
>> "%LEGACY_LIST%" echo spec-driven-development
>> "%LEGACY_LIST%" echo source-driven-development
>> "%LEGACY_LIST%" echo incremental-implementation
>> "%LEGACY_LIST%" echo deprecation-and-migration
>> "%LEGACY_LIST%" echo api-and-interface-design
>> "%LEGACY_LIST%" echo performance-optimization
>> "%LEGACY_LIST%" echo planning-and-task-breakdown
>> "%LEGACY_LIST%" echo frontend-design
>> "%LEGACY_LIST%" echo webapp-testing
>> "%LEGACY_LIST%" echo domain-modeling
>> "%LEGACY_LIST%" echo dispatching-parallel-agents
>> "%LEGACY_LIST%" echo springboot-tdd
>> "%LEGACY_LIST%" echo springboot-verification
>> "%LEGACY_LIST%" echo springboot-security
>> "%LEGACY_LIST%" echo jpa-patterns
>> "%LEGACY_LIST%" echo mysql-patterns
>> "%LEGACY_LIST%" echo react-testing
>> "%LEGACY_LIST%" echo java-coding-standards
>> "%LEGACY_LIST%" echo security-review
>> "%LEGACY_LIST%" echo security-scan
>> "%LEGACY_LIST%" echo vercel-react-best-practices
>> "%LEGACY_LIST%" echo frontend-patterns
>> "%LEGACY_LIST%" echo gitnexus-impact-analysis
>> "%LEGACY_LIST%" echo gitnexus-exploring
>> "%LEGACY_LIST%" echo gitnexus-pdg-query
>> "%LEGACY_LIST%" echo gitnexus-review
>> "%LEGACY_LIST%" echo gitnexus-plan
>> "%LEGACY_LIST%" echo gitnexus-work
>> "%LEGACY_LIST%" echo gitnexus-refactoring
>> "%LEGACY_LIST%" echo gitnexus-debugging
>> "%LEGACY_LIST%" echo gitnexus-cli
>> "%LEGACY_LIST%" echo gitnexus-lfg
>> "%LEGACY_LIST%" echo use-railway
exit /b 0

:detect_hd
@echo off
set "HD=%~d0\"
if exist "%HD%\.gemini\baude-skills-brutas" exit /b 0
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z C) do if exist "%%D:\.gemini\baude-skills-brutas" (
  set "HD=%%D:\"
  exit /b 0
)
if not "%~d0"=="" set "HD=%~d0\"
if not defined HD set "HD=E:\"
exit /b 0

:detect_desktop
@echo off
set "DESKTOP=%USER_HOME%\Desktop"
if exist "%DESKTOP%\" exit /b 0
if defined OneDrive if exist "%OneDrive%\Desktop\" set "DESKTOP=%OneDrive%\Desktop"
if exist "%DESKTOP%\" exit /b 0
set "DESKTOP=%HD%Desktop"
mkdir "%DESKTOP%" >nul 2>nul
exit /b 0

:failed_keep_cache
@echo off
echo Cache preservado: %CACHE%
>> "%LOG%" echo CACHE_PRESERVADO=%CACHE%

:failed
@echo off
del /f /q "%MANAGED_NEW%" "%LEGACY_LIST%" >nul 2>nul
if not "%NO_PAUSE%"=="1" pause
exit /b 1
