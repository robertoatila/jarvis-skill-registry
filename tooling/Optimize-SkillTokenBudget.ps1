# ==============================================================================
# J.A.R.V.I.S. // Optimize-SkillTokenBudget.ps1
# Prunes bloated descriptions in C:\Users\Ad\.gemini\config\skills & E:\.skill-registry\skills
# Reclaims ~8,000+ tokens, eliminating the 'token budget exceeded' alert
# ==============================================================================

[CmdletBinding()]
param(
    [string]$SkillsDir = 'C:\Users\Ad\.gemini\config\skills',
    [string]$SovereignSkillsDir = 'E:\.skill-registry\skills',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. // OTIMIZADOR DE TOKEN BUDGET DAS SKILLS (PROD)" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Modo: $(if ($DryRun) { 'DRY-RUN (SIMULACAO)' } else { 'APPLY (ESCRITA NO DISCO)' })" -ForegroundColor Yellow

$curated = @{
    "constraint-driven-development" = "Establishes written quality contracts in CONSTRAINTS.md to enforce standards and stop bar lowering."
    "arbor-computational-neuroscience-simulation" = "Simulates morphologically detailed spiking neural networks with GPU-accelerated multicompartment models."
    "lsp-diagnostic-setup" = "Configures Language Server Protocol diagnostics, linters, and type checkers across codebases."
    "ultrawork-execution-engine" = "Goal-oriented execution loop decomposing complex projects into verifiable, systematic milestones."
    "software-construction-patterns" = "Applies resilient software design patterns, clean architecture, and modular domain modeling."
    "systematic-code-debugging" = "Traces root causes of bugs, memory leaks, and regressions using systematic diagnostics."
    "data-science-toolkit" = "Statistical analysis, feature engineering, exploratory data science, and visualization workflows in Python."
    "analytical-method-validation" = "Validates analytical procedures, assay precision, specificity, linearity, and regulatory compliance standards."
    "deep-technical-research" = "Conducts deep technical research, literature synthesis, paper analysis, and citation verification."
    "bulk-rnaseq-differential-expression" = "Analyzes bulk RNA-seq data: quality control, alignment, normalization, and differential expression."
    "ai-boilerplate-sanitizer" = "Sanitizes and strips AI boilerplate, conversational filler, and redundant outputs."
    "requirements-interview-elicitation" = "Conducts structured requirements elicitation interviews to resolve ambiguity before implementation."
    "ui-micro-interaction-design" = "Designs subtle UI animations, interactive states, micro-interactions, and visual feedback."
    "browser-devtools-inspector" = "Inspects DOM, CSS styles, console logs, and network traffic via Chrome DevTools."
    "neuroimaging-bids-standardization" = "Organizes neuroscience and biomedical datasets according to Brain Imaging Data Structure standards."
    "llm-eval-benchmark-harness" = "Runs promptfoo evaluation suites, model-graded rubrics, and regression test matrices."
    "comprehensive-code-review" = "Systematic code review across security, correctness, architecture, maintainability, and test coverage."
    "audio-transcription-speech-processing" = "Transcribes, translates, and processes multilingual speech and audio using OpenAI Whisper models."
    "clip-multimodal-contrastive-embeddings" = "Zero-shot image classification, image-text matching, and multimodal embeddings using CLIP."
    "vllm-paged-attention-high-throughput-serving" = "Serves LLMs at scale using continuous batching and PagedAttention memory management."
    "vllm-high-throughput-serving" = "High-throughput LLM serving with PagedAttention, vLLM continuous batching, and quantization."
    "nextflow-scalable-scientific-data-pipelines" = "Builds reproducible, containerized scientific data pipelines with Nextflow and workflow orchestrators."
    "nemo-evaluator-safety-guardrails" = "Evaluates LLM safety guardrails, jailbreak resistance, and toxicity using NVIDIA NeMo."
    "agentic-idea-refinement" = "Refines, stress-tests, and expands agentic ideas into concrete technical roadmaps."
    "fsm-grammar-constrained-generation" = "Constrains LLM generation to valid JSON, XML, or Pydantic schemas using FSMs."
    "cross-session-memory-search" = "Searches persistent cross-session memory database for past solutions, patterns, and decisions."
    "guidance-interleaved-token-acceleration" = "Constrains LLM outputs with grammars and regex for structured data generation."
    "dspy-programmatic-prompt-compilation" = "Compiles declarative LM programs, modular RAG systems, and self-optimizing pipelines with DSPy."
    "dspy-declarative-prompt-compilation" = "Builds declarative LM programs, modular RAG systems, and automated prompt optimizers with DSPy."
    "opencode-runtime-qa" = "QAs and verifies OpenCode runtime configs, plugin hooks, and isolated session state."
    "package-pre-publish-audit" = "Audits packages and tarballs before publishing to npm, PyPI, or Crates.io."
    "openrlhf-ray-distributed-reinforcement-learning" = "Distributed RLHF training (PPO, GRPO, DPO) for large models using Ray and vLLM."
    "openpi-physical-intelligence-robotics-policy" = "Fine-tunes and serves OpenPI physical intelligence models for robot policy inference."
    "pdf-document-processing" = "Manipulates PDFs: extracts text and tables, merges, splits, and fills forms."
    "pennylane-quantum-differentiable-programming" = "Differentiable quantum machine learning and hybrid quantum-classical circuit training with PennyLane."
    "autogen" = "Multi-agent conversational orchestration framework for autonomous collaborative LLM task execution."
    "rdkit-cheminformatics-molecular-discovery" = "Cheminformatics toolkit: SMILES/SDF parsing, molecular descriptors, fingerprints, and structure generation."
    "biopython-computational-biology" = "Bioinformatics toolkit: sequence manipulation, FASTA/PDB parsing, phylogenetics, and NCBI Entrez access."
    "speculative-decoding-draft-verification" = "Accelerates LLM inference via speculative decoding, draft verification, and multi-token prediction."
    "particle-image-velocimetry-fluid-dynamics" = "Extracts velocity fields and cross-correlation analysis from Particle Image Velocimetry data."
    "software-internationalization-i18n" = "Software localization pipeline: string extraction, translation validation, formatting, and RTL support."
    "polars-streaming-dataframe-engine" = "High-performance streaming DataFrame engine with lazy query optimization and Apache Arrow integration."
    "flash-attention-kernel-tiling-acceleration" = "Optimizes transformer attention kernels for speedup and memory reduction using FlashAttention."
    "hyperplan-orchestrator" = "Structures multi-phase technical projects into deterministic implementation plans with verification criteria."
    "phoenix-opentelemetry-llm-observability" = "Open-source LLM observability, distributed tracing, and evaluation platform using OpenTelemetry."
    "qformer-multimodal-feature-alignment" = "Bridges frozen vision encoders and LLMs for multimodal image captioning and reasoning."
    "speculative-decoding-acceleration" = "Accelerates LLM inference throughput using speculative decoding and Medusa multi-head draft prediction."
    "simpo-reference-free-preference-optimization" = "Reference-free preference optimization for efficient LLM alignment without a reference model."
    "hqq-fast-kernel-weight-quantization" = "Half-Quadratic Quantization for fast 2/3/4-bit LLM compression without calibration data."
    "brandkit-design-system" = "Generates brand guideline boards, visual identity systems, and design tokens."
    "knowledge-distillation-compression" = "Compresses large language models via teacher-to-student knowledge distillation."
    "llamaindex-hierarchical-query-engine" = "Ingests, indexes, and queries heterogeneous documents for advanced RAG architectures."
    "bigcode-harness-code-evaluation" = "Evaluates code generation models across HumanEval, MBPP, and multi-language benchmarks."
    "crewai-hierarchical-multiagent-teams" = "Orchestrates autonomous multi-agent teams with role-based collaboration and hierarchical execution."
    "flash-attention-kernel-optimization" = "Accelerates transformer attention computation with IO-aware memory access and tiling."
    "gene-regulatory-network-inference" = "Infers gene regulatory networks from bulk and single-cell transcriptomics data."
    "llava-visual-instruction-tuning" = "Multimodal visual instruction tuning combining CLIP vision encoders with large language models."
    "megatron-tensor-pipeline-parallelism" = "Trains massive LLMs using Megatron tensor, pipeline, and sequence parallelism strategies."
    "pytorch-fsdp2-per-parameter-sharding" = "Distributed PyTorch training with per-parameter sharding, mixed precision, and CPU offload."
    "security-research-audit" = "Audits software components for CVEs, exposed secrets, insecure configurations, and dependency risks."
    "aeon-timeseries-ml-forecasting" = "Time series machine learning: classification, regression, clustering, forecasting, and anomaly detection."
    "cellxgene-census-tissue-querying" = "Queries CZ CELLxGENE Census single-cell and spatial transcriptomics datasets programmatically."
    "long-context-rope-scaling-eval" = "Extends transformer context windows using RoPE, YaRN, ALiBi, and position interpolation."
    "qdrant-vector-database-hnsw-indexing" = "High-performance vector similarity search engine with HNSW indexing and metadata filtering."
    "biomedical-literature-semantic-search" = "Searches biomedical literature and extracts structured experimental data via BGPT."
    "persistent-file-planning" = "Maintains persistent task_plan.md, findings.md, and progress.md files across agent sessions."
    "skypilot-multi-cloud-compute-orchestration" = "Multi-cloud compute orchestration and automatic cost optimization for distributed ML workloads."
    "architecture-decision-records" = "Documents significant technical decisions, architectural context, alternatives, and consequences via ADRs."
    "formal-document-engineering" = "Creates, formats, and analyzes formal Word, PDF, and Markdown technical documents."
    "frontend-design-engineering" = "Engineers distinctive frontend UI/UX, intentional typography, harmonious palettes, and responsive layouts."
    "neural-audiocraft-sound-generation" = "Generates music, audio effects, and soundscapes from text descriptions using AudioCraft."
    "vision-language-action-robotics" = "Fine-tunes and serves OpenVLA robot manipulation policies from vision-language inputs."
    "academic-scientific-plotting" = "Generates publication-quality figures, plots, and architecture diagrams for scientific papers."
    "cosmos-physical-ai-world-policy" = "Evaluates NVIDIA Cosmos physical AI policies in simulated robotics environments."
    "developer-productivity-metrics" = "Analyzes developer coding patterns, chat logs, productivity bottlenecks, and learning resources."
    "qdrant-vector-storage-retrieval" = "Vector similarity search and retrieval-augmented generation engine with hybrid filtering."
    "structured-pydantic-llm-outputs" = "Extracts structured data from LLMs with Pydantic type validation and retries."
    "technical-content-synthesis" = "Synthesizes technical articles, research documentation, and tutorials with verified citations."
    "llm-model-merging-techniques" = "Merges multiple fine-tuned LLMs using mergekit without retraining or compute overhead."
    "pydicom-medical-imaging-radiology" = "Reads, inspects, validates, and transforms medical DICOM datasets and pixel data."
    "tensorrt-llm-gpu-kernel-acceleration" = "Accelerates LLM GPU inference throughput with NVIDIA TensorRT-LLM optimized kernels."
    "verl-hybrid-engine-reinforcement-learning" = "Reinforcement learning framework (PPO, GRPO) for post-training large language models."
    "benchling-lims-laboratory-tracking" = "Integrates Benchling API for registry entities, inventory, ELN entries, and laboratory workflows."
    "gguf-tensor-format-serialization" = "Quantizes and serves models in GGUF format for efficient CPU/GPU inference."
    "governed-package-publish" = "Safely publishes packages to npm, PyPI, and Crates.io with two-phase verification."
    "spreadsheet-data-modeling" = "Creates and analyzes spreadsheets: complex formulas, financial modeling, and data visualization."
    "astrophysical-data-analysis" = "Analyzes astronomical data: coordinates, FITS files, celestial tables, and cosmological models."
    "neural-model-pruning-sparsity" = "Prunes neural network weights for sparsity and inference acceleration using Wanda/SparseGPT."
    "sglang-radix-attention-runtime" = "High-throughput LLM serving with RadixAttention prefix caching and structured decoding."
    "coding-agent-sessions" = "Inspects, searches, exports, and reconstructs coding-agent session logs across platforms."
    "deadcode-elimination" = "Detects and prunes dead code, unused functions, orphan modules, and obsolete dependencies."
    "presentation-deck-engineering" = "Designs, edits, and structures presentation decks and slides with visual hierarchy."
    "qiskit-quantum-circuit-algorithms" = "Designs, simulates, transpiles, and executes quantum circuits using IBM Qiskit."
    "skypilot-multicloud-orchestration" = "Multi-cloud compute orchestration and automatic cost optimization for distributed ML workloads."
    "backend-development-feature-development" = "Orchestrates end-to-end backend features: controllers, services, repositories, and migration rollouts."
    "pr-review-resolution" = "Analyzes and systematically resolves pull request review comments and automated checks."
    "ui-redesign-modernizer" = "Modernizes existing web interfaces: aesthetic typography, glassmorphism, responsive grid, and micro-interactions."
    "autonomous-execution-loop" = "Executes structured work plans with evidence ledgers, worktrees, and task validation."
    "bash-defensive-patterns" = "Writes robust, fault-tolerant defensive Bash scripts with error handling and strict flags."
    "bioservices-rest-federation" = "Unified programmatic interface to 40+ bioinformatics databases including UniProt, KEGG, and ChEMBL."
    "github-issue-pr-triage" = "Triages GitHub issues and pull requests, prioritizing bugs and mapping duplicates."
    "awq-activation-quantization" = "Activation-aware weight quantization for 4-bit LLM compression with low latency."
    "backend-security-coder" = "Implements secure backend coding: input validation, authentication, and API security."
    "flaky-test-investigation" = "Detects and quarantines flaky tests through test history and CI log analysis."
    "git-advanced-mastery" = "Mastery of advanced Git: atomic commits, rebase, squash, bisect, and reflog."
    "git-unpublished-changes-audit" = "Audits unpublished commits and tags against release registries across monorepos."
    "mixture-of-experts-routing" = "Trains and serves Mixture of Experts (MoE) models with DeepSpeed and HuggingFace."
    "mlflow-model-registry-lifecycle" = "Tracks ML experiments, versioning, artifacts, and production deployments with MLflow."
    "api-contract-interface-design" = "Designs stable API contracts, boundary types, and robust public interfaces."
    "obsidian-markdown-syntax" = "Creates Obsidian-flavored markdown notes with wikilinks, callouts, and frontmatter properties."
    "responsive-layout-architecture" = "Architects responsive app shell layouts, collapsible sidebars, and adaptive containers."
    "adaptyv-cloud-biolab-protein-assays" = "Submits and monitors automated protein assays via Adaptyv Bio Foundry API."
    "deepspeed-zero-distributed-optimization" = "Scales distributed model training with DeepSpeed ZeRO-1/2/3 and memory offloading."
    "doubt-driven-development" = "Adversarial code review and verification of architectural decisions before commit."
    "subagent-task-qa" = "QAs subagent DAG orchestration, task isolation, and deterministic evidence trails."
    "tech-debt-audit" = "Audits architectural and test debt, generating prioritized remediation scorecards."
    "agent-browser-automation" = "Automates browser workflows: navigation, form interactions, scraping, and verification."
    "ast-grep-search" = "AST-aware code search and structural rewrites across 25 programming languages."
    "image-to-code-synthesizer" = "Translates UI designs and mockups into pixel-perfect, accessible frontend code."
    "single-cell-anndata-genomics" = "Manipulates single-cell genomics matrices and metadata using AnnData structures."
    "json-canvas-visualizer" = "Creates and edits JSON Canvas visual diagrams, flowcharts, and mind maps."
    "segment-anything-visual-masking" = "Zero-shot visual segmentation and mask generation using Segment Anything (SAM)."
    "agent-environment-doctor" = "Diagnoses agent installation health, environment variables, and CLI tooling dependencies."
    "bitsandbytes-8bit-nf4-quantization" = "Quantizes LLMs to 8-bit or 4-bit NormalFloat for memory-efficient GPU inference."
    "git-bugfix-contribution" = "Verifies defects, crafts regression tests, and submits validated upstream bug fixes."
    "headless-browser-research" = "Escalation browsing for Cloudflare/WAF-protected, login-gated, or JS-rendered pages."
    "obsidian-cli-controller" = "Controls Obsidian vaults via CLI: manages notes, properties, searches, and tasks."
    "obsidian-database-bases" = "Designs Obsidian database base files (.base) with tabular views and filters."
    "api-documenter" = "Generates interactive OpenAPI 3.1 documentation, developer portals, and SDK client libraries."
    "api-security-best-practices" = "Hardens API endpoints: authentication, authorization, rate limiting, and OWASP API protection."
    "legacy-codebase-reverse-documentation" = "Reverse-engineers legacy codebases to produce missing architectural specs and diagrams."
    "visual-regression-qa" = "Automates visual regression testing across browsers, responsive viewports, and themes."
    "codex-plugin-qa" = "QAs and tests Codex plugins, lifecycle hooks, and tool handlers in isolation."
    "database-migrations-sql-migrations" = "Executes zero-downtime SQL database migrations with safe rollbacks and locks."
    "multi-agent-teammode" = "Coordinates teams of cooperating Codex agents with script-managed persistent state."
    "ai-engineer" = "Builds production LLM applications, multimodal agents, and vector RAG pipelines."
    "api-endpoint-builder" = "Constructs production-grade REST and GraphQL endpoints with validation and error handling."
    "agentic-coding-heuristics" = "Operational heuristics, startup tips, and working patterns for agentic coding engines."
    "api-security-testing" = "Automates penetration testing of REST and GraphQL APIs against OWASP vulnerabilities."
    "soak-stress-testing" = "Executes extended soak and stress tests to surface memory leaks and fatigue."
    "browser-devtools-testing" = "Automated end-to-end browser testing and console/network inspection via DevTools."
    "react-developer-diagnostics" = "Diagnostics and performance audits for React apps: bundle size, renders, and hooks."
    "testing-api-for-broken-object-level-authorization" = "Tests APIs for BOLA and IDOR object authorization vulnerabilities (OWASP API1)."
    "performing-sca-dependency-scanning-with-snyk" = "Scans and remediates vulnerable third-party open-source dependencies using Snyk."
    "auth-implementation-patterns" = "Implements secure authentication: OAuth2, OIDC, JWT sessions, MFA, and RBAC."
    "llm-redteam-plugin-audit" = "Creates adversarial red-teaming plugins, prompt injection tests, and safety graders."
    "task-dag-orchestrator" = "Defines and executes directed acyclic graphs of interdependent agent tasks."
    "unsloth-fast-kernel-finetuning" = "Fast, memory-efficient LLM fine-tuning using Unsloth LoRA/QLoRA optimized kernels."
    "integrating-sast-into-github-actions-pipeline" = "Integrates CodeQL and Semgrep SAST security scans into GitHub Actions CI."
    "implementing-devsecops-security-scanning" = "Embeds SAST, DAST, SCA, and secrets detection directly into CI/CD pipelines."
    "integrating-dast-with-owasp-zap-in-pipeline" = "Integrates OWASP ZAP dynamic application security testing scans into CI/CD."
    "javascript-typescript-typescript-scaffold" = "Scaffolds production TypeScript projects with modern build tools, linting, and tests."
    "parallel-task-batcher" = "Batches and dispatches parallel agent jobs with dependency resolution."
    "github-bug-reporter" = "Formats and files high-signal bug reports with minimal reproducible testcases."
    "testing-oauth2-implementation-flaws" = "Audits OAuth2 and OIDC flows for token leaks, redirect flaws, and PKCE bypass."
    "developer-onboarding-workflow" = "Automates developer environment onboarding, prerequisites checks, and project tour."
    "deep-project-scaffolder" = "Scaffolds deep project architectures with hierarchical AGENTS.md documentation."
    "tmux-session-terminal-multiplexer" = "Controls tmux terminal sessions programmatically for interactive CLI automation."
    "frontend-mobile-security-xss-scan" = "Detects and prevents Cross-Site Scripting (XSS) across modern frontend frameworks."
    "systematic-refactoring" = "Performs safe, incremental code refactoring without altering existing external behavior."
}

function Clean-Description([string]$name, [string]$rawDesc) {
    if ($curated.ContainsKey($name)) {
        return $curated[$name]
    }
    
    $desc = $rawDesc.Trim() -replace '^["'']', '' -replace '["'']$', ''
    $desc = [regex]::Replace($desc, '^(Use this skill whenever|Use this skill when|Use when|This skill should be used for|Specialized skill for|Comprehensive|Master|Official|Guides stable)\s+', '', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $desc = ($desc -replace '\s+', ' ').Trim()
    
    $words = $desc -split '\s+'
    if ($words.Count -gt 13) {
        if ($desc -match '^(.*?[.?!])\s') {
            $firstSent = $matches[1].Trim()
            if (($firstSent -split '\s+').Count -le 13) {
                return $firstSent
            }
        }
        $truncated = ($words[0..11] -join ' ')
        if (-not $truncated.EndsWith('.')) {
            $truncated += '.'
        }
        return $truncated
    }
    
    if (-not $desc.EndsWith('.')) {
        $desc += '.'
    }
    return $desc
}

function Optimize-TargetDirectory([string]$dirPath, [bool]$doApply) {
    if (-not (Test-Path $dirPath)) { return }
    
    $dirs = Get-ChildItem -Path $dirPath -Directory
    $modified = 0
    $wordsBefore = 0
    $wordsAfter = 0
    
    foreach ($d in $dirs) {
        $skillMd = Join-Path $d.FullName 'SKILL.md'
        if (-not (Test-Path $skillMd)) { continue }
        
        $raw = [System.IO.File]::ReadAllText($skillMd, [System.Text.Encoding]::UTF8)
        if ($raw -match '(?ms)^---\r?\n(.*?)\r?\n---') {
            $fm = $matches[1]
            if ($fm -match '(?ms)^description:\s*(.*?)(?=\r?\n[a-zA-Z0-9_-]+:|\Z)') {
                $origDesc = $matches[1].Trim()
                $origClean = $origDesc -replace '\s+', ' ' -replace '^["'']', '' -replace '["'']$', ''
                $wb = ($origClean -split '\s+').Count
                $wordsBefore += $wb
                
                $newDesc = Clean-Description $d.Name $origClean
                $wa = ($newDesc -split '\s+').Count
                $wordsAfter += $wa
                
                if ($newDesc -ne $origClean) {
                    $modified++
                    if ($doApply) {
                        $newDescLine = "description: $newDesc"
                        $updatedFm = [regex]::Replace($fm, '(?ms)^description:\s*.*?(?=\r?\n[a-zA-Z0-9_-]+:|\Z)', $newDescLine)
                        $newRaw = $raw.Replace($fm, $updatedFm)
                        [System.IO.File]::WriteAllText($skillMd, $newRaw, [System.Text.Encoding]::UTF8)
                    }
                }
            }
        }
    }
    
    $estTokB = [math]::Round($wordsBefore * 1.35)
    $estTokA = [math]::Round($wordsAfter * 1.35)
    $saved = $estTokB - $estTokA
    $pct = if ($estTokB -gt 0) { [math]::Round(($saved / $estTokB) * 100, 1) } else { 0 }
    
    Write-Host "Diretorio          : $dirPath" -ForegroundColor Cyan
    Write-Host "Skills Otimizadas  : $modified / $($dirs.Count) skills" -ForegroundColor White
    Write-Host "Palavras Originais : $wordsBefore (~$estTokB tokens)" -ForegroundColor DarkGray
    Write-Host "Palavras Apos Poda : $wordsAfter (~$estTokA tokens)" -ForegroundColor Green
    Write-Host "Tokens Poupados    : ~$saved tokens ($pct% de Reducao!)" -ForegroundColor Yellow
    Write-Host "---------------------------------------------------------"
}

$doApply = -not $DryRun
Optimize-TargetDirectory $SkillsDir $doApply
if ($doApply -and (Test-Path $SovereignSkillsDir)) {
    Optimize-TargetDirectory $SovereignSkillsDir $doApply
}

Write-Host "Otimizacao finalizada com sucesso!" -ForegroundColor Green
