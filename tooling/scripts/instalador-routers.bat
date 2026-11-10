@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cls

title INSTALADOR DE ROUTERS GENERICOS - v31.2 STABLE BATCH

set "VERSION=31.2"
set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"
if /I "%~2"=="--no-pause" set "NO_PAUSE=1"

set "PROJECT_DIR="
if not "%~1"=="" if /I not "%~1"=="--no-pause" for %%A in ("%~1") do set "PROJECT_DIR=%%~fA"

if not defined PROJECT_DIR (
  for /f "delims=" %%G in ('git -C "%CD%" rev-parse --show-toplevel 2^>nul') do if not defined PROJECT_DIR set "PROJECT_DIR=%%G"
)
if not defined PROJECT_DIR for %%A in ("%CD%") do set "PROJECT_DIR=%%~fA"

call :desktop
set "LOG=%DESKTOP%\instalador-routers-v31.2.txt"
> "%LOG%" echo INSTALADOR DE ROUTERS GENERICOS v%VERSION% - %DATE% %TIME%
>> "%LOG%" echo PROJECT_DIR=%PROJECT_DIR%

call :guard "%PROJECT_DIR%"
if errorlevel 1 goto failed

call :detect_stack
>> "%LOG%" echo STACK=%STACK%

set "D1=%PROJECT_DIR%\.agents\skills"
set "D2=%PROJECT_DIR%\.gemini\skills"
set "D3=%PROJECT_DIR%\.codex\skills"
set "D4=%PROJECT_DIR%\.claude\skills"

for %%D in ("%D1%" "%D2%" "%D3%" "%D4%") do (
  mkdir "%%~D" >nul 2>nul
  if not exist "%%~D" goto failed
)

echo ============================================================
echo  INSTALADOR DE ROUTERS GENERICOS - v%VERSION%
echo ============================================================
echo Projeto: %PROJECT_DIR%
echo Stack:   %STACK%
echo.
echo Arsenal de referencia: 165 skills globais da v31.2.
echo Gera 7 routers genericos para qualquer projeto.
echo ============================================================
echo.

call :mk_auto || goto failed
call :mk_route "projects-ui-router" "UI, frontend, React, Next.js, CSS, Tailwind, acessibilidade, design, animacao, GSAP e Three.js." "UI_FRONTEND" || goto failed
call :mk_route "projects-security-router" "Seguranca, auth, APIs, AppSec, supply chain, DevSecOps, AWS security, IAM e secrets." "SECURITY" || goto failed
call :mk_route "projects-backend-router" "Backend, APIs, Node.js, TypeScript, Java, Spring Boot, Python, FastAPI e PHP." "BACKEND" || goto failed
call :mk_route "projects-database-router" "Banco de dados, SQL, schema, migrations, ORM, PostgreSQL/Supabase, MySQL e multi-tenancy." "DATABASE" || goto failed
call :mk_route "projects-deploy-router" "Deploy, CI/CD, Docker, AWS/EC2/serverless, Cloudflare, Vercel, observabilidade e Linux." "DEPLOY" || goto failed
call :mk_route "projects-review-router" "Review, GitNexus, impacto, PDG, testes, debugging, performance, verificacao, qualidade, specs e manutencao." "REVIEW" || goto failed

call :agents_note

echo.
echo ============================================================
echo  ROUTERS GENERICOS CONCLUIDOS - v%VERSION%
echo ============================================================
echo Contextos unicos: 7
echo Copias SKILL.md: 28
echo Stack:            %STACK%
echo Log:              %LOG%
echo ============================================================
>> "%LOG%" echo RESULTADO=OK
>> "%LOG%" echo ROUTERS=7
>> "%LOG%" echo SKILL_MD=28
if not "%NO_PAUSE%"=="1" pause
exit /b 0

:mk_auto
set "NAME=projects-auto-router"
for %%D in ("%D1%" "%D2%" "%D3%" "%D4%") do (
  mkdir "%%~D\!NAME!" >nul 2>nul
  set "FILE=%%~D\!NAME!\SKILL.md"
  > "!FILE!" echo ---
  >> "!FILE!" echo name: !NAME!
  >> "!FILE!" echo description: "Router generico de entrada. Classifica a tarefa entre UI, seguranca, backend, banco, deploy e review usando o arsenal global atual. Stack detectada: %STACK%."
  >> "!FILE!" echo ---
  >> "!FILE!" echo.
  >> "!FILE!" echo # Projects Auto Router
  >> "!FILE!" echo.
  >> "!FILE!" echo Use este router somente para escolher o dominio minimo necessario.
  >> "!FILE!" echo Nao carregue todos os routers nem todas as skills ao mesmo tempo.
  >> "!FILE!" echo.
  >> "!FILE!" echo ## Roteamento
  >> "!FILE!" echo.
  >> "!FILE!" echo - UI, frontend, React, Next.js, CSS, Tailwind, design, a11y, animacao -^> `projects-ui-router`
  >> "!FILE!" echo - auth, AppSec, API security, secrets, IAM, vulnerabilidades -^> `projects-security-router`
  >> "!FILE!" echo - APIs, servicos, Node.js, Java, Spring, Python, PHP -^> `projects-backend-router`
  >> "!FILE!" echo - SQL, schema, migrations, ORM, PostgreSQL, MySQL -^> `projects-database-router`
  >> "!FILE!" echo - CI/CD, Docker, AWS, Cloudflare, Vercel, Linux, observabilidade -^> `projects-deploy-router`
  >> "!FILE!" echo - testes, bugs, review, debugging, performance, verificacao -^> `projects-review-router`
  >> "!FILE!" echo.
  >> "!FILE!" echo Se a tarefa cruzar dominios, carregue no maximo os dois routers diretamente relevantes.
  if not exist "!FILE!" exit /b 1
)
>> "%LOG%" echo OK=%NAME%
echo [OK] %NAME%
exit /b 0

:mk_route
set "NAME=%~1"
set "DESC=%~2"
set "GROUP=%~3"
for %%D in ("%D1%" "%D2%" "%D3%" "%D4%") do (
  mkdir "%%~D\!NAME!" >nul 2>nul
  set "FILE=%%~D\!NAME!\SKILL.md"
  > "!FILE!" echo ---
  >> "!FILE!" echo name: !NAME!
  >> "!FILE!" echo description: "!DESC! Escolha apenas as skills relevantes do arsenal global atual. Stack detectada: %STACK%."
  >> "!FILE!" echo ---
  >> "!FILE!" echo.
  >> "!FILE!" echo # !NAME!
  >> "!FILE!" echo.
  >> "!FILE!" echo Stack detectada: %STACK%
  >> "!FILE!" echo.
  >> "!FILE!" echo ## Skills atuais priorizadas
  >> "!FILE!" echo.
  call :write_group "!GROUP!" "!FILE!"
  >> "!FILE!" echo.
  >> "!FILE!" echo ## Politica
  >> "!FILE!" echo.
  >> "!FILE!" echo 1. Prefira a skill mais especifica para a tarefa.
  >> "!FILE!" echo 2. Nao carregue duas skills com a mesma funcao sem necessidade.
  >> "!FILE!" echo 3. Combine skills apenas quando as capacidades forem complementares.
  >> "!FILE!" echo 4. Para decisoes de alto impacto, associe verificacao ou review quando aplicavel.
  >> "!FILE!" echo 5. Nomes desta lista correspondem ao arsenal global v31.2 com 165 skills.
  if not exist "!FILE!" exit /b 1
)
>> "%LOG%" echo OK=%NAME%
echo [OK] %NAME%
exit /b 0

:write_group
set "GROUP=%~1"
set "FILE=%~2"
if /I "%GROUP%"=="UI_FRONTEND" goto group_ui
if /I "%GROUP%"=="SECURITY" goto group_security
if /I "%GROUP%"=="BACKEND" goto group_backend
if /I "%GROUP%"=="DATABASE" goto group_database
if /I "%GROUP%"=="DEPLOY" goto group_deploy
if /I "%GROUP%"=="REVIEW" goto group_review
exit /b 1

:group_ui
>> "!FILE!" echo - `ui-ux-pro-max`
>> "!FILE!" echo - `impeccable`
>> "!FILE!" echo - `frontend-ui-engineering`
>> "!FILE!" echo - `frontend-design`
>> "!FILE!" echo - `vercel-react-best-practices`
>> "!FILE!" echo - `react-doctor`
>> "!FILE!" echo - `react-state-management`
>> "!FILE!" echo - `react-modernization`
>> "!FILE!" echo - `react-testing`
>> "!FILE!" echo - `nextjs-app-router-patterns`
>> "!FILE!" echo - `tailwind-patterns`
>> "!FILE!" echo - `tailwind-design-system`
>> "!FILE!" echo - `shadcn`
>> "!FILE!" echo - `frontend-a11y`
>> "!FILE!" echo - `playwright-cli`
>> "!FILE!" echo - `webapp-testing`
>> "!FILE!" echo - `web-design-guidelines`
>> "!FILE!" echo - `vercel-composition-patterns`
>> "!FILE!" echo - `motion-design`
>> "!FILE!" echo - `design-dna`
>> "!FILE!" echo - `gsap-core`
>> "!FILE!" echo - `gsap-react`
>> "!FILE!" echo - `gsap-performance`
>> "!FILE!" echo - `gsap-scrolltrigger`
>> "!FILE!" echo - `threejs-fundamentals`
>> "!FILE!" echo - `threejs-animation`
>> "!FILE!" echo - `frontend-api-integration-patterns`
exit /b 0

:group_security
>> "!FILE!" echo - `agent-supply-chain`
>> "!FILE!" echo - `aws-security`
>> "!FILE!" echo - `broken-authentication`
>> "!FILE!" echo - `backend-security-coder`
>> "!FILE!" echo - `frontend-security-coder`
>> "!FILE!" echo - `frontend-mobile-security-xss-scan`
>> "!FILE!" echo - `security-review`
>> "!FILE!" echo - `security-scan`
>> "!FILE!" echo - `gitnexus-pdg-query`
>> "!FILE!" echo - `gitnexus-impact-analysis`
>> "!FILE!" echo - `gitnexus-review`
>> "!FILE!" echo - `api-security-best-practices`
>> "!FILE!" echo - `api-security-testing`
>> "!FILE!" echo - `web-security-testing`
>> "!FILE!" echo - `auth-implementation-patterns`
>> "!FILE!" echo - `privacy-by-design`
>> "!FILE!" echo - `agentic-actions-auditor`
>> "!FILE!" echo - `testing-api-for-broken-object-level-authorization`
>> "!FILE!" echo - `testing-oauth2-implementation-flaws`
>> "!FILE!" echo - `performing-api-inventory-and-discovery`
>> "!FILE!" echo - `implementing-devsecops-security-scanning`
>> "!FILE!" echo - `integrating-sast-into-github-actions-pipeline`
>> "!FILE!" echo - `performing-sca-dependency-scanning-with-snyk`
>> "!FILE!" echo - `securing-serverless-functions`
>> "!FILE!" echo - `integrating-dast-with-owasp-zap-in-pipeline`
>> "!FILE!" echo - `sql-injection-testing`
>> "!FILE!" echo - `api-fuzzing-bug-bounty`
>> "!FILE!" echo - `aws-secrets-rotation`
>> "!FILE!" echo - `burp-suite-testing`
>> "!FILE!" echo - `sqlmap-database-pentesting`
exit /b 0

:group_backend
>> "!FILE!" echo - `backend-dev-guidelines`
>> "!FILE!" echo - `backend-development-feature-development`
>> "!FILE!" echo - `backend-architect`
>> "!FILE!" echo - `api-endpoint-builder`
>> "!FILE!" echo - `api-patterns`
>> "!FILE!" echo - `api-documenter`
>> "!FILE!" echo - `openapi-spec-generation`
>> "!FILE!" echo - `api-and-interface-design`
>> "!FILE!" echo - `error-handling-patterns`
>> "!FILE!" echo - `nodejs-backend-patterns`
>> "!FILE!" echo - `typescript-expert`
>> "!FILE!" echo - `typescript-advanced-types`
>> "!FILE!" echo - `zod-validation-expert`
>> "!FILE!" echo - `javascript-pro`
>> "!FILE!" echo - `java-pro`
>> "!FILE!" echo - `java-coding-standards`
>> "!FILE!" echo - `springboot-patterns`
>> "!FILE!" echo - `springboot-tdd`
>> "!FILE!" echo - `springboot-verification`
>> "!FILE!" echo - `springboot-security`
>> "!FILE!" echo - `spring-boot-testing`
>> "!FILE!" echo - `jpa-patterns`
>> "!FILE!" echo - `fastapi-pro`
>> "!FILE!" echo - `python-pro`
>> "!FILE!" echo - `php-pro`
exit /b 0

:group_database
>> "!FILE!" echo - `sql-pro`
>> "!FILE!" echo - `sql-optimization-patterns`
>> "!FILE!" echo - `database-architect`
>> "!FILE!" echo - `database-optimizer`
>> "!FILE!" echo - `database-design`
>> "!FILE!" echo - `database-admin`
>> "!FILE!" echo - `database-migrations-sql-migrations`
>> "!FILE!" echo - `database-migrations-migration-observability`
>> "!FILE!" echo - `supabase-postgres-best-practices`
>> "!FILE!" echo - `mysql-patterns`
>> "!FILE!" echo - `jpa-patterns`
>> "!FILE!" echo - `saas-multi-tenant`
exit /b 0

:group_deploy
>> "!FILE!" echo - `docker-expert`
>> "!FILE!" echo - `aws-compute`
>> "!FILE!" echo - `aws-serverless`
>> "!FILE!" echo - `aws-security`
>> "!FILE!" echo - `cloud-architect`
>> "!FILE!" echo - `workers-best-practices`
>> "!FILE!" echo - `devops-deploy`
>> "!FILE!" echo - `devops-troubleshooter`
>> "!FILE!" echo - `github-actions-templates`
>> "!FILE!" echo - `gh-fix-ci`
>> "!FILE!" echo - `gh-address-comments`
>> "!FILE!" echo - `deploy-to-vercel`
>> "!FILE!" echo - `use-railway`
>> "!FILE!" echo - `vercel-optimize`
>> "!FILE!" echo - `ci-cd-and-automation`
>> "!FILE!" echo - `shipping-and-launch`
>> "!FILE!" echo - `k6-load-testing`
>> "!FILE!" echo - `distributed-tracing`
>> "!FILE!" echo - `observability-and-instrumentation`
>> "!FILE!" echo - `linux-troubleshooting`
>> "!FILE!" echo - `bash-defensive-patterns`
>> "!FILE!" echo - `bash-linux`
>> "!FILE!" echo - `network-engineer`
exit /b 0

:group_review
>> "!FILE!" echo - `gitnexus-plan`
>> "!FILE!" echo - `gitnexus-review`
>> "!FILE!" echo - `gitnexus-impact-analysis`
>> "!FILE!" echo - `gitnexus-exploring`
>> "!FILE!" echo - `gitnexus-debugging`
>> "!FILE!" echo - `gitnexus-refactoring`
>> "!FILE!" echo - `gitnexus-pdg-query`
>> "!FILE!" echo - `gitnexus-cli`
>> "!FILE!" echo - `production-audit`
>> "!FILE!" echo - `codebase-audit-pre-push`
>> "!FILE!" echo - `mock-hunter`
>> "!FILE!" echo - `test-driven-development`
>> "!FILE!" echo - `incremental-implementation`
>> "!FILE!" echo - `javascript-testing-patterns`
>> "!FILE!" echo - `react-testing`
>> "!FILE!" echo - `spring-boot-testing`
>> "!FILE!" echo - `systematic-debugging`
>> "!FILE!" echo - `verification-before-completion`
>> "!FILE!" echo - `performance-optimization`
>> "!FILE!" echo - `code-simplification`
>> "!FILE!" echo - `documentation-and-adrs`
>> "!FILE!" echo - `source-driven-development`
>> "!FILE!" echo - `spec-driven-development`
>> "!FILE!" echo - `deprecation-and-migration`
>> "!FILE!" echo - `domain-modeling`
>> "!FILE!" echo - `context-budget`
>> "!FILE!" echo - `dispatching-parallel-agents`
>> "!FILE!" echo - `subagent-driven-development`
>> "!FILE!" echo - `agent-skill-stack`
>> "!FILE!" echo - `using-agent-skills`
exit /b 0

:agents_note
if exist "%PROJECT_DIR%\AGENTS.md" exit /b 0
> "%PROJECT_DIR%\AGENTS.md" echo # AGENTS.md
>> "%PROJECT_DIR%\AGENTS.md" echo.
>> "%PROJECT_DIR%\AGENTS.md" echo Os routers genericos ficam em .agents/skills, .gemini/skills, .codex/skills e .claude/skills.
>> "%PROJECT_DIR%\AGENTS.md" echo Use projects-auto-router para selecionar o dominio e depois somente as skills diretamente relevantes.
>> "%LOG%" echo OK=AGENTS.md
exit /b 0

:detect_stack
set "STACK=generico"
if exist "%PROJECT_DIR%\package.json" set "STACK=%STACK%; Node.js"
if exist "%PROJECT_DIR%\tsconfig.json" set "STACK=%STACK%; TypeScript"
if exist "%PROJECT_DIR%\next.config.js" set "STACK=%STACK%; Next.js"
if exist "%PROJECT_DIR%\next.config.mjs" set "STACK=%STACK%; Next.js"
if exist "%PROJECT_DIR%\next.config.ts" set "STACK=%STACK%; Next.js"
if exist "%PROJECT_DIR%\vite.config.js" set "STACK=%STACK%; Vite"
if exist "%PROJECT_DIR%\vite.config.ts" set "STACK=%STACK%; Vite"
if exist "%PROJECT_DIR%\pom.xml" set "STACK=%STACK%; Java Spring Maven"
if exist "%PROJECT_DIR%\build.gradle" set "STACK=%STACK%; Java Gradle"
if exist "%PROJECT_DIR%\build.gradle.kts" set "STACK=%STACK%; Kotlin Gradle"
if exist "%PROJECT_DIR%\composer.json" set "STACK=%STACK%; PHP"
if exist "%PROJECT_DIR%\requirements.txt" set "STACK=%STACK%; Python"
if exist "%PROJECT_DIR%\pyproject.toml" set "STACK=%STACK%; Python"
if exist "%PROJECT_DIR%\Dockerfile" set "STACK=%STACK%; Docker"
if exist "%PROJECT_DIR%\docker-compose.yml" set "STACK=%STACK%; Docker Compose"
if exist "%PROJECT_DIR%\docker-compose.yaml" set "STACK=%STACK%; Docker Compose"
if exist "%PROJECT_DIR%\railway.json" set "STACK=%STACK%; Railway"
if exist "%PROJECT_DIR%\vercel.json" set "STACK=%STACK%; Vercel"
if exist "%PROJECT_DIR%\prisma\schema.prisma" set "STACK=%STACK%; Prisma"
if exist "%PROJECT_DIR%\supabase" set "STACK=%STACK%; Supabase"
exit /b 0

:guard
set "P=%~1"
if not defined P exit /b 1
for %%A in ("%P%") do set "DRIVE_ROOT=%%~dA\"
if /I "%P%"=="%DRIVE_ROOT%" exit /b 1
if /I "%P%"=="%USERPROFILE%" exit /b 1
if exist "%P%\.git\" exit /b 0
if exist "%P%\package.json" exit /b 0
if exist "%P%\pom.xml" exit /b 0
if exist "%P%\build.gradle" exit /b 0
if exist "%P%\build.gradle.kts" exit /b 0
if exist "%P%\README.md" exit /b 0
echo [ERRO] A pasta nao parece ser uma raiz de projeto: %P%
exit /b 1

:desktop
set "DESKTOP=%USERPROFILE%\Desktop"
if exist "%DESKTOP%\" exit /b 0
if defined OneDrive if exist "%OneDrive%\Desktop\" set "DESKTOP=%OneDrive%\Desktop"
if exist "%DESKTOP%\" exit /b 0
set "DESKTOP=%TEMP%"
exit /b 0

:failed
echo.
echo [ERRO] Nao foi possivel gerar os routers genericos.
echo Consulte: %LOG%
>> "%LOG%" echo RESULTADO=ERRO
if not "%NO_PAUSE%"=="1" pause
exit /b 1
