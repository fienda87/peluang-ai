# Graph Report - peluang-ai  (2026-08-25)

## Corpus Check
- Corpus is ~46,363 words - fits in a single context window. You may not need a graph.

## Summary
- 986 nodes · 1584 edges · 102 communities (91 shown, 11 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 146 edges (avg confidence: 0.87)
- Token cost: 29,400 input · 24,900 output

## Community Hubs (Navigation)
- AI Provider Adapters
- Deterministic Extraction
- Extraction Agent Graph
- Auth Routes JWT
- Local File Storage
- Recommendation Routes
- Behavior Tracking Routes
- Admin Crawl Pipeline
- Streaming Agent Status
- Agent Budgets Principles
- TypeScript Config
- Frontend Dependencies
- Applied Login Pages
- Application Services
- Admin Metrics Routes
- Profile Routes
- BRIN Fellowships Trainings
- LLM Provider Setup
- Storage Lifecycle
- Architecture Layers
- Dedup Matching Concepts
- Scholarship Programs
- Embedding Service
- Deterministic Extractors
- Document Processing
- CI Migrations
- Base Repository Pattern
- Scholarship Providers
- Deduplication Service
- Discovery Agent Graph
- Recommendation Agent Graph
- Opportunities Service
- Dashboard Page
- Feedback Agent Graph
- Recovery Agent Graph
- Notification Service
- Student Competitions
- Playwright Dependencies
- Testing Milestones
- Research Volunteer Programs
- Opportunity Actions
- Home Page
- Retention Service
- Alembic Environment
- Fixture Generator
- Academic Conferences
- Program Posters
- Conference Fixtures
- Essay Bizplan Contests
- Data Science Hackathons
- Demo Data
- Explore Page
- Business Training Posters
- Creative Contest Posters
- Internship Seminar Posters
- Root Layout
- International Scholarships
- Robotics Photo Posters
- Medical Research Program
- Next Config
- Next Env Types
- Journalist Fellowship Poster
- Startup Internship Poster
- Education Volunteer Poster

## God Nodes (most connected - your core abstractions)
1. `get_logger()` - 47 edges
2. `get_settings()` - 21 edges
3. `Peluang.ai` - 21 edges
4. `get_ai()` - 20 edges
5. `ExtractionSchema` - 20 edges
6. `process_document()` - 20 edges
7. `ExtractionState` - 19 edges
8. `CrawlPipeline` - 19 edges
9. `StorageBackend` - 16 edges
10. `AIPort` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Bounded Agent Runs Rule` --semantically_similar_to--> `Bounded Agent Budgets`  [INFERRED] [semantically similar]
  CONTRIBUTING.md → ARCHITECTURE.md
- `Deterministic Logic First Rule` --semantically_similar_to--> `Deterministic-First Principle`  [INFERRED] [semantically similar]
  CONTRIBUTING.md → ARCHITECTURE.md
- `Validation Service` --semantically_similar_to--> `3-State Eligibility`  [INFERRED] [semantically similar]
  IMPLEMENTATION_CHECKLIST.md → ARCHITECTURE.md
- `backend CI Job` --semantically_similar_to--> `Contributing Guide`  [INFERRED] [semantically similar]
  .github/workflows/ci.yml → CONTRIBUTING.md
- `Beasiswa Unggulan Kemendikbud 2026` --semantically_similar_to--> `Beasiswa Tanoto Foundation 2026`  [INFERRED] [semantically similar]
  backend/scripts/fixtures/html/beasiswa_unggulan.html → backend/scripts/fixtures/pdf/beasiswa_tanoto.pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Bounded LangGraph Agent System** — architecture_langgraph_agents, architecture_discovery_agent, architecture_extraction_agent, architecture_recovery_agent, architecture_recommendation_agent, architecture_feedback_agent, architecture_bounded_budgets, config_agents_agent_budgets [EXTRACTED 1.00]
- **Local Development Stack (Docker Compose)** — docker_compose_postgres, docker_compose_redis, docker_compose_api, docker_compose_worker [EXTRACTED 1.00]
- **Extraction Strategy Ladder (deterministic, LLM, vision, recovery)** — architecture_extraction_agent, architecture_deterministic_first, implementation_checklist_llm_extraction_service, implementation_checklist_vision_llm_fallback, implementation_checklist_validation_service, config_app_ocr_config, docs_setup_guide_gemini_flash_15 [EXTRACTED 1.00]
- **Program Beasiswa 2026** — backend_scripts_fixtures_html_beasiswa_lpdp_2026_beasiswa_lpdp_2026_tahap_1, backend_scripts_fixtures_html_beasiswa_unggulan_beasiswa_unggulan_kemdikbud_2026, backend_scripts_fixtures_pdf_beasiswa_djarum_beasiswa_djarum_plus_2026, backend_scripts_fixtures_pdf_beasiswa_tanoto_beasiswa_tanoto_foundation_2026, backend_scripts_fixtures_html_beasiswa_lpdp_2026_category_beasiswa [INFERRED]
- **Kompetisi Mahasiswa Nasional 2026** — backend_scripts_fixtures_html_lomba_business_plan_lomba_business_plan_nasional, backend_scripts_fixtures_html_lomba_data_science_kompetisi_data_science_nasional_2026, backend_scripts_fixtures_pdf_lomba_esai_lomba_esai_nasional_2026, backend_scripts_fixtures_pdf_lomba_hackathon_hackathon_nasional_2026, backend_scripts_fixtures_html_lomba_business_plan_category_kompetisi [INFERRED]
- **Program Daring (Online)** — backend_scripts_fixtures_html_pelatihan_cloud_pelatihan_cloud_computing_gratis, backend_scripts_fixtures_pdf_pelatihan_ai_pelatihan_ai_dan_machine_learning, backend_scripts_fixtures_pdf_fellowship_kominfo_fellowship_digital_talent_kominfo [INFERRED]

## Communities (102 total, 11 thin omitted)

### Community 0 - "AI Provider Adapters"
Cohesion: 0.07
Nodes (30): get_ai(), OllamaAdapter, Any, OpenRouterAdapter, Any, AIPort, AIProviderError, AIResponse (+22 more)

### Community 1 - "Deterministic Extraction"
Cohesion: 0.05
Nodes (27): DeterministicExtractor, detect_doc_type(), FetchResult, HTMLFetcher, AsyncClient, PDFAdapter, PDFResult, _asset_filter() (+19 more)

### Community 2 - "Extraction Agent Graph"
Cohesion: 0.09
Nodes (31): asyncio, build_extraction_graph(), _conf_of(), _det_to_schema(), ExtractionState, node_detect(), node_finalize(), node_try_deterministic() (+23 more)

### Community 3 - "Auth Routes JWT"
Cohesion: 0.08
Nodes (21): login(), AsyncSession, post, refresh(), register(), get_current_user_id(), UUID, AuthAPI (+13 more)

### Community 4 - "Local File Storage"
Cohesion: 0.08
Nodes (11): LocalFileStorage, ABC, StorageBackend, AsyncSession, UUID, SourceHealthService, AsyncSession, IngestionService (+3 more)

### Community 5 - "Recommendation Routes"
Cohesion: 0.09
Nodes (19): generate(), get_feed(), AsyncSession, get, post, UUID, CandidateService, AsyncSession (+11 more)

### Community 6 - "Behavior Tracking Routes"
Cohesion: 0.08
Nodes (21): behavior_profile(), EventRequest, AsyncSession, BaseModel, get, post, UUID, record_event() (+13 more)

### Community 7 - "Admin Crawl Pipeline"
Cohesion: 0.07
Nodes (24): get_schedule(), get, post, Trigger crawl + extract sebagai background process terpisah., run_now(), set_schedule(), Request, RateLimitMiddleware (+16 more)

### Community 8 - "Streaming Agent Status"
Cohesion: 0.10
Nodes (22): agents_status(), AsyncSession, get, post, stream(), test_event(), OCRAdapter, OCRResult (+14 more)

### Community 9 - "Agent Budgets Principles"
Cohesion: 0.11
Nodes (28): agent_run_events, agent_runs, Bounded Agent Budgets, Opportunity Data Flow, Deterministic-First Principle, Discovery Agent, Extraction Agent, Feedback Agent (+20 more)

### Community 10 - "TypeScript Config"
Cohesion: 0.07
Nodes (26): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+18 more)

### Community 11 - "Frontend Dependencies"
Cohesion: 0.08
Nodes (24): dependencies, next, react, react-dom, devDependencies, @types/node, @types/react, @types/react-dom (+16 more)

### Community 12 - "Applied Login Pages"
Cohesion: 0.16
Nodes (15): AppliedPage(), Item, LoginPage(), submit(), FIELDS, Profile, ProfilePage(), save() (+7 more)

### Community 13 - "Application Services"
Cohesion: 0.10
Nodes (21): ADR-001, AnalyticsService, Application Services, arq over Celery, BehaviorService, FeedbackService, Infrastructure Layer, IngestionService (+13 more)

### Community 14 - "Admin Metrics Routes"
Cohesion: 0.19
Nodes (14): agent_metrics(), beta_metrics(), extraction_metrics(), list_agent_runs(), list_sources(), pause_source(), AsyncSession, get (+6 more)

### Community 15 - "Profile Routes"
Cohesion: 0.21
Nodes (14): applied_list(), get_profile(), _list_by_event(), ProfileUpdate, AsyncSession, BaseModel, get, UUID (+6 more)

### Community 16 - "BRIN Fellowships Trainings"
Cohesion: 0.12
Nodes (18): BRIN, Fellowship, Fellowship Riset AI Indonesia, Pelatihan (Training), Google Developer Student Club, Pelatihan Cloud Computing Gratis, Pendanaan Riset (Research Funding), Program Riset Mahasiswa BRIN (+10 more)

### Community 17 - "LLM Provider Setup"
Cohesion: 0.16
Nodes (17): Provider-Neutral AI, Embedding Configuration, @BotFather, Gemini Flash 1.5 (vision fallback), Llama 3.1 8B Instruct (free), Ollama, OpenRouter, Setup Guide (+9 more)

### Community 18 - "Storage Lifecycle"
Cohesion: 0.18
Nodes (10): get_storage(), LifecycleService, AsyncSession, WorkerSettings, crawl_source_task(), expire_opportunities_task(), extract_document_task(), feedback_agent_task() (+2 more)

### Community 19 - "Architecture Layers"
Cohesion: 0.16
Nodes (15): API / Transport Layer, Experience Layer, FastAPI, JWT Authentication, Next.js Dashboard, Pydantic v2, Telegram Bot (aiogram), Environment Variables Reference (+7 more)

### Community 20 - "Dedup Matching Concepts"
Cohesion: 0.17
Nodes (15): Deduplication, Domain Services, Eligibility, Matching, pg_trgm, pgvector, pgvector Exact Search, PostgreSQL (+7 more)

### Community 21 - "Scholarship Programs"
Cohesion: 0.13
Nodes (15): Beasiswa LPDP 2026 Tahap 1, Beasiswa Unggulan Kemendikbud 2026, Magang Bersertifikat Kampus Merdeka Batch 8, Pelatihan Cloud Computing Gratis, Beasiswa Djarum Plus 2026, Beasiswa Tanoto Foundation 2026, Magang BUMN 2026, Pelatihan AI dan Machine Learning (+7 more)

### Community 22 - "Embedding Service"
Cohesion: 0.24
Nodes (7): embed_texts_local(), EmbeddingService, _get_local_model(), AsyncSession, UUID, main(), Backfill embeddings untuk semua opportunity + user profile test.

### Community 23 - "Deterministic Extractors"
Cohesion: 0.33
Nodes (10): DeterministicResult, extract_category(), extract_deadline(), extract_location(), extract_organizer(), extract_prize(), extract_title_from_html(), parse_indonesian_date() (+2 more)

### Community 24 - "Document Processing"
Cohesion: 0.20
Nodes (11): clean_title(), Bersihkan judul dari nav junk, HTML entities, dan suffix situs., process_document(), AsyncSession, UUID, Document processing: load → Extraction Agent graph → persist → upsert → dedup →…, setup_logging(), Run one full crawl cycle synchronously: crawl sources → extract → persist.… (+3 more)

### Community 25 - "CI Migrations"
Cohesion: 0.29
Nodes (13): backend CI Job, CI Workflow, Architecture Overview, pytest, ruff, Alembic Migrations, Contributing Guide, Local Development Workflow (+5 more)

### Community 26 - "Base Repository Pattern"
Cohesion: 0.23
Nodes (5): BaseRepository, Any, AsyncSession, UUID, T

### Community 27 - "Scholarship Providers"
Cohesion: 0.18
Nodes (13): Beasiswa LPDP 2026 Tahap 1, Beasiswa (Scholarship), Kementerian Keuangan RI, Beasiswa Unggulan Kemendikbud 2026, Kemdikbudristek, Magang (Internship), Magang Bersertifikat Kampus Merdeka Batch 8, Beasiswa Djarum Plus 2026 (+5 more)

### Community 28 - "Deduplication Service"
Cohesion: 0.20
Nodes (5): DeduplicationService, AsyncSession, deduplicate_opportunity_task(), main(), Backfill dedup decisions + embeddings for opportunities missing them.

### Community 29 - "Discovery Agent Graph"
Cohesion: 0.47
Nodes (9): build_discovery_graph(), DiscoveryState, node_evaluate(), node_inspect(), node_plan_search(), node_register(), node_search(), BaseModel (+1 more)

### Community 30 - "Recommendation Agent Graph"
Cohesion: 0.47
Nodes (9): build_recommendation_graph(), node_contextual_reorder(), node_explain(), node_get_candidates(), node_persist(), node_rank(), node_user_context(), BaseModel (+1 more)

### Community 31 - "Opportunities Service"
Cohesion: 0.29
Nodes (5): OpportunitiesService, AsyncSession, date, UUID, slugify()

### Community 32 - "Dashboard Page"
Cohesion: 0.27
Nodes (7): Agent, DashboardPage(), Ev, FILTERS, matchFilter(), relTime(), wibClock()

### Community 33 - "Feedback Agent Graph"
Cohesion: 0.50
Nodes (8): build_feedback_graph(), FeedbackState, node_check_signal_quality(), node_load_behavior(), node_propose_update(), node_summarize_patterns(), node_validate(), BaseModel

### Community 34 - "Recovery Agent Graph"
Cohesion: 0.50
Nodes (8): build_recovery_graph(), node_diagnose(), node_execute(), node_select_strategy(), node_validate(), BaseModel, RecoveryState, route_after_validate()

### Community 35 - "Notification Service"
Cohesion: 0.25
Nodes (4): NotificationService, AsyncSession, UUID, dispatch_notifications_task()

### Community 36 - "Student Competitions"
Cohesion: 0.22
Nodes (9): Kompetisi Mahasiswa (Competition), Lomba Business Plan Nasional, Universitas Gadjah Mada, Kompetisi Data Science Nasional 2026, Universitas Indonesia, Lomba Esai Nasional 2026, Universitas Diponegoro, Dicoding (+1 more)

### Community 37 - "Playwright Dependencies"
Cohesion: 0.22
Nodes (8): devDependencies, @playwright/test, name, private, scripts, test, test:headed, @playwright/test

### Community 38 - "Testing Milestones"
Cohesion: 0.25
Nodes (8): Playwright, Milestone Commit Convention, Discovery Agent Graph, Implementation Checklist M0-M6, M5 Discovery & Recovery, M6 Beta Hardening, Observability & Security Hardening, Recovery Agent Graph

### Community 39 - "Research Volunteer Programs"
Cohesion: 0.29
Nodes (8): Fellowship Riset AI Indonesia, Program Riset Mahasiswa BRIN, Volunteer Mengajar Desa Digital, Fellowship Digital Talent Kominfo, Volunteer Lingkungan Hidup, BRIN, Kominfo, WALHI

### Community 40 - "Opportunity Actions"
Cohesion: 0.38
Nodes (4): OpportunityActions(), getOpportunity(), Opportunity, OpportunityPage()

### Community 41 - "Home Page"
Cohesion: 0.43
Nodes (6): categoryLabels, daysLeft(), formatShort(), getOpportunities(), HomePage(), Opportunity

### Community 42 - "Retention Service"
Cohesion: 0.33
Nodes (3): AsyncSession, RetentionService, retention_purge_task()

### Community 43 - "Alembic Environment"
Cohesion: 0.47
Nodes (4): do_run_migrations(), run_async_migrations(), run_migrations_online(), Connection

### Community 45 - "Academic Conferences"
Cohesion: 0.40
Nodes (5): Konferensi Akademik (Conference), ITB, Konferensi Teknologi Mahasiswa Nasional, Konferensi Ilmiah Mahasiswa Nasional, Universitas Airlangga

### Community 46 - "Program Posters"
Cohesion: 0.40
Nodes (5): Poster Beasiswa Chevening, Poster Beasiswa Fulbright, Poster Fellowship Jurnalis, Poster Volunteer Pendidikan, Peluang AI App Icon (P Letter Mark)

### Community 47 - "Conference Fixtures"
Cohesion: 0.50
Nodes (4): Konferensi Teknologi Mahasiswa Nasional, Konferensi Ilmiah Mahasiswa Nasional, ITB, Universitas Airlangga

### Community 48 - "Essay Bizplan Contests"
Cohesion: 0.50
Nodes (4): Lomba Business Plan Nasional, Lomba Esai Nasional 2026, Universitas Diponegoro, Universitas Gadjah Mada

### Community 49 - "Data Science Hackathons"
Cohesion: 0.50
Nodes (4): Kompetisi Data Science Nasional 2026, Hackathon Nasional 2026, Dicoding, Universitas Indonesia

### Community 51 - "Explore Page"
Cohesion: 0.67
Nodes (3): ExplorePage(), Opportunity, searchOpportunities()

### Community 63 - "Business Training Posters"
Cohesion: 0.67
Nodes (3): Pelatihan Bisnis, Seminar Ekonomi, Workshop Design

### Community 64 - "Creative Contest Posters"
Cohesion: 0.67
Nodes (3): Poster Kompetisi Robotik, Poster Lomba Foto, Poster Workshop Design

### Community 65 - "Internship Seminar Posters"
Cohesion: 0.67
Nodes (3): Poster Magang Startup, Poster Pelatihan Bisnis, Poster Seminar Ekonomi

## Ambiguous Edges - Review These
- `Pelatihan AI dan Machine Learning` → `Kemdikbudristek`  [AMBIGUOUS]
  backend/tests/fixtures/pdf/pelatihan_ai.pdf · relation: conceptually_related_to

## Knowledge Gaps
- **103 isolated node(s):** `WorkerSettings`, `Item`, `Ev`, `Agent`, `FILTERS` (+98 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Pelatihan AI dan Machine Learning` and `Kemdikbudristek`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `get_logger()` connect `AI Provider Adapters` to `Deterministic Extraction`, `Extraction Agent Graph`, `Auth Routes JWT`, `Local File Storage`, `Recommendation Routes`, `Behavior Tracking Routes`, `Admin Crawl Pipeline`, `Streaming Agent Status`, `Admin Metrics Routes`, `Profile Routes`, `Storage Lifecycle`, `Embedding Service`, `Deterministic Extractors`, `Document Processing`, `Deduplication Service`, `Discovery Agent Graph`, `Recommendation Agent Graph`, `Opportunities Service`, `Feedback Agent Graph`, `Recovery Agent Graph`, `Notification Service`, `Retention Service`?**
  _High betweenness centrality (0.175) - this node is a cross-community bridge._
- **Why does `get_ai()` connect `AI Provider Adapters` to `Deterministic Extraction`, `Extraction Agent Graph`, `Storage Lifecycle`, `Document Processing`, `Deduplication Service`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `DeterministicExtractor` connect `Deterministic Extraction` to `Extraction Agent Graph`, `Deterministic Extractors`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `get_ai()` (e.g. with `OllamaAdapter` and `OpenRouterAdapter`) actually correct?**
  _`get_ai()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ExtractionSchema` (e.g. with `_conf_of()` and `ExtractionState`) actually correct?**
  _`ExtractionSchema` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `WorkerSettings`, `Item`, `Ev` to the rest of the system?**
  _103 weakly-connected nodes found - possible documentation gaps or missing edges._