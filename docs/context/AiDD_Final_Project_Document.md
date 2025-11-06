Campus Resource Hub — AiDD 2025 Capstone Project Brief
Module: AI Driven Development (AiDD / X501)
Project Title: Campus Resource Hub
Duration: 18 days (recommended schedule included)
Team Size: Core Teams
Instructor: Prof. Jay Newquist
Updated: Fall 2025
________________________________________
1. Executive Summary
The Campus Resource Hub is a full‑stack web application enabling university departments, student organizations, and individuals to list, share, and reserve campus resources (study rooms, AV equipment, lab instruments, event spaces, tutoring time, etc.). The system supports search, booking with calendar integration, role‑based access (student, staff, admin), ratings and reviews, and administrative workflows for approval and conflict resolution.
This project tests students’ ability to design, implement, validate, and present a production‑quality software product. Teams will demonstrate database modeling, server‑side validation, front‑end usability, deployment readiness, documentation, and a professional presentation.
________________________________________
2. Learning Objectives
By completing this project students will be able to:
•	Design and implement a relational schema supporting users, resources, bookings, messages, and reviews.
•	Build RESTful server endpoints with secure authentication and authorization.
•	Create responsive UI pages for browsing, booking, and managing resources using Flask + Jinja.
•	Implement server‑side validation, input sanitization, and basic security hardening (CSRF, XSS protection).
•	Demonstrate effective team collaboration, version control (Git branching + PRs), and documented AI usage in development (optional in later iterations). GitHub should be used for all major changes to the project.
•	Produce professional deliverables: PRD, wireframes, working app, technical documentation, and a live demo.
•	Students will apply AI-first development and context engineering practices, using prompt-driven collaboration and context-aware repositories to enhance design, implementation, and validation.
________________________________________
3. Team & Roles
Team Size: Cor Teams (~4 students)
Suggested Roles (rotate if needed):
•	Product Lead / PM: PRD, feature prioritization, demo script, stakeholder communication.
•	Backend Engineer: Database design, API routes, authentication, business logic, deployment pipelines.
•	Frontend Engineer / UX: Wireframes, templates/components, responsive layout, client validation.
•	Quality & DevOps / Security: Unit tests, integration tests, CI configuration, security checks, documentation.
Teams should commit to regular standups and use GitHub for source control. Peer evaluation will inform final grading adjustments.
________________________________________
4. Project Scope & Key Features
Teams must implement the following core features. Additional features are optional and may be used to differentiate high‑quality projects.
Core Features (required)
1.	User Management & Authentication
o	Sign up, sign in, sign out (email + password). Passwords must be stored hashed (bcrypt or similar).
o	Roles: Student, Staff, Admin. Role determines access to approval and management workflows.
2.	Resource Listings
o	CRUD operations for resources: title, description, images, category, location, availability rules, owner (user/team), capacity, and optional equipment lists.
o	Listing lifecycle: draft, published, archived.
3.	Search & Filter
o	Search by keyword, category, location, availability date/time, and capacity.
o	Sort options (recent, most booked, top rated).
4.	Booking & Scheduling
o	Calendar-based booking flow with start/end time, recurrence option (optional), and conflict detection.
o	Booking approval workflow: automatic approval for open resources, staff/admin approval for restricted resources.
o	Email notifications or simulated notifications for booking confirmations and changes.
5.	Messaging & Notifications
o	Basic message thread between requester and resource owner.
o	Students must decide: is it real-time? threaded? email-like?
6.	Reviews & Ratings
o	After completed bookings, users may rate and leave feedback for resources and hosts.
o	Aggregate rating calculation and top‑rated badges.
7.	Admin Panel
o	Admin dashboard to manage users, resources, bookings, and moderate reviews.
8.	Documentation & Local Runbook
o	README with setup + run instructions, requirements.txt, and database migration steps.
Optional Advanced Features (Top Projects)
•	Calendar sync with Google Calendar (OAuth) or iCal export.
•	Waitlist features for fully booked resources.
•	Role‑based analytics: usage reports by department or resource type.
•	Advanced search powered by simple embedding retrieval (if teams choose to extend later).
•	Accessibility improvements and WCAG conformance checks.
________________________________________
 
5. Technology Stack (required baseline)
The project will be developed using a modern AI-first repository structure that supports human AI collaboration. Students must configure their repos for AI assisted workflows using .prompt/ and /docs/context/ folders, enabling Copilot, Cursor, and other AI tools to reason about project context.
•	Backend: Python 3.10+ with Flask
•	Database: SQLite for local development (PostgreSQL optional for deployment)
•	Frontend: Jinja2 templates (Flask) + Bootstrap 5
•	Auth: Flask‑Login / Flask‑Security or equivalent; bcrypt for password hashing
•	Testing: pytest; simple unit tests for business logic
•	Version Control: GitHub (branching, PRs required)
•	Application Architecture:
The application must follow a Model–View–Controller (MVC) pattern separating presentation, business logic, and data access layers.
o	Model Layer: ORM or direct SQL classes managing all database operations.
o	View Layer: HTML / Jinja templates rendering the interface.
o	Controller Layer: Flask routes (or blueprints) coordinating requests and responses.
o	Data Access Layer (DAL): Encapsulate database interactions (CRUD methods) in dedicated Python modules/classes (e.g., data_access.py), ensuring controllers do not issue raw SQL.
o	Demonstrate this separation clearly in your repository structure and documentation.
o	Folder Structure Example:
	/src
	/controllers # Flask routes and blueprints
	/models # ORM classes or schema definitions\
	/views # HTML/Jinja templates
	/data_access # Encapsulated CRUD logic
	/static
	/tests
•	AI First Folder Structure (Required)
o	Your repository must include folders that support AI-assisted and context aware development. These structures help AI tools (such as Cursor and Copilot Agent Mode) understand your project’s architecture and generate accurate, contextually relevant code.
.prompt/
dev_notes.md ← log of all AI interactions and outcomes
golden_prompts.md ← high-impact prompts and responses

docs/
context/
APA/ ← artifacts from Agility, Processes & Automation module
DT/ ← Design Thinking artifacts (personas, journey maps)
PM/ ← Product Management materials (PRDs, OKRs)
shared/ ← common items (personas, glossary, OKRs)

tests/
ai_eval/ ← optional AI feature validation tests 
Note: This folder system collectively forms your Context Pack, a lightweight structure designed to help AI tools ground their reasoning in your project’s goals, data, and user context.

Expectation: Each repository should reflect this structure in its README and maintain consistent naming to support AI driven reasoning and safe automation.
Examples of useful cross-course artifacts:
•	APA: BPMN future-state process models, acceptance tests, backlog CSVs
•	DT: Personas, journey maps, or usability findings
•	PM: Product strategy briefs, OKRs, or stakeholder maps
Note: These items provide helpful context for AI tools and will not be graded directly, but their inclusion can improve how effectively AI understands project requirements, user needs, and business context.
•	Deployment (optional): Heroku, AWS Elastic Beanstalk, or similar
________________________________________
6. Non‑Functional Requirements & Security
•	Server‑Side Validation: All input fields must be validated on the server (types, lengths, date ranges).
•	XSS & Injection Protections: Use template escaping, parameterized SQL/ORM queries, and sanitize uploads.
•	Password Security: Store hashed + salted passwords (bcrypt). No plaintext passwords in repo.
•	CSRF Protection: Enable CSRF tokens for form submissions.
•	File Uploads: Restrict file types and sizes; store uploads in a safe folder; scan filenames for path traversal.
•	Privacy: Avoid storing unnecessary PII; keep minimal user info and allow admins to remove data if requested.
•	AI Testing & Verification
o	Projects that include AI features must provide at least one automated or manual test verifying that AI‑generated outputs behave predictably and align with factual project data. AI components must never return fabricated or unverifiable results.
o	AI feature outputs should be validated both functionally (correct data) and ethically (appropriate, non-biased responses).
________________________________________
 
7. Data Model / Database Schema 
(Suggested, may not be complete)
Below is a suggested relational schema; teams may extend as needed.
Tables
users
•	user_id INTEGER PRIMARY KEY AUTOINCREMENT
•	name TEXT NOT NULL
•	email TEXT NOT NULL UNIQUE
•	password_hash TEXT NOT NULL
•	role TEXT NOT NULL – (‘student’,‘staff’,‘admin’)
•	profile_image TEXT
•	department TEXT
•	created_at DATETIME
resources
•	resource_id INTEGER PRIMARY KEY AUTOINCREMENT
•	owner_id INTEGER REFERENCES users(user_id)
•	title TEXT NOT NULL
•	description TEXT
•	category TEXT
•	location TEXT
•	capacity INTEGER
•	images TEXT – comma separated paths or JSON array
•	availability_rules TEXT – JSON blob describing recurring availability
•	status TEXT – (‘draft’,‘published’,‘archived’)
•	created_at DATETIME
bookings
•	booking_id INTEGER PRIMARY KEY AUTOINCREMENT
•	resource_id INTEGER REFERENCES resources(resource_id)
•	requester_id INTEGER REFERENCES users(user_id)
•	start_datetime DATETIME
•	end_datetime DATETIME
•	status TEXT – (‘pending’,‘approved’,‘rejected’,‘cancelled’,‘completed’)
•	created_at DATETIME
•	updated_at DATETIME
messages
•	message_id INTEGER PRIMARY KEY AUTOINCREMENT
•	thread_id INTEGER
•	sender_id INTEGER REFERENCES users(user_id)
•	receiver_id INTEGER REFERENCES users(user_id)
•	content TEXT
•	timestamp DATETIME
reviews
•	review_id INTEGER PRIMARY KEY AUTOINCREMENT
•	resource_id INTEGER REFERENCES resources(resource_id)
•	reviewer_id INTEGER REFERENCES users(user_id)
•	rating INTEGER – 1..5
•	comment TEXT
•	timestamp DATETIME
admin_logs (optional)
•	log_id INTEGER PRIMARY KEY AUTOINCREMENT
•	admin_id INTEGER REFERENCES users(user_id)
•	action TEXT
•	target_table TEXT
•	details TEXT
•	timestamp DATETIME
Teams should provide an ER diagram as part of their documentation deliverable.
Model Context Protocol (MCP) Integration (Recommended): Teams may implement MCP to allow AI agents to query or inspect database content safely. MCP enables structured, read only interaction between the AI layer and the SQLite database for features such as summaries or intelligent search. MCP usage should be documented in .prompt/dev_notes.md and the README.
________________________________________
 
8. Server‑Side API Endpoints (Suggested)
•	POST /auth/register — create user
•	POST /auth/login — obtain session
•	GET /resources — list/search resources
•	GET /resources/<id> — resource detail
•	POST /resources — create a resource (auth required)
•	PUT /resources/<id> — update
•	DELETE /resources/<id> — delete
•	POST /bookings — request booking
•	GET /bookings/<id> — booking detail
•	PUT /bookings/<id>/approve — approve booking (staff/admin or owner)
•	POST /messages — send message
•	POST /reviews — submit review
•	GET /admin/stats — usage metrics (admin)
Document API request/response examples in the project README or an API.md file.
________________________________________
9. UX / Frontend Requirements
•	Homepage: Search box, categories, featured resources, and quick filters.
•	Listing Page: Grid or list view of resources with key metadata and availability preview.
•	Resource Detail: Image carousel, description, calendar availability, booking CTA, reviews.
•	Dashboard: For users to manage My Listings, My Bookings, Messages, and Profile.
•	Admin Dashboard: Approvals queue, user management, reports.
•	Forms: Client‑side validation to improve UX, but never replace server validation.
•	Context Grounding Requirement
o	Each team must include at least one example where AI‑generated code or documentation references materials from /docs/context/. For example, an AI‑powered Resource Concierge may reference acceptance tests in /docs/context/APA/ or persona data from /docs/context/DT/ to inform its responses.
Accessibility: Use semantic HTML, proper labels, keyboard navigation, and contrast ratios.
________________________________________
 
10. Testing & Validation Requirements
Minimum required tests:
•	Unit tests for booking logic (conflict detection, status transitions).
•	Unit tests must include at least one test of the Data Access Layer verifying CRUD operations independently from the Flask route handlers.
•	Integration test for auth flow (register → login → access protected route).
•	One end‑to‑end scenario demonstrating booking a resource through the UI (can be manual script or automated with Selenium/playwright if feasible).
•	Security checks: test for SQL injection using parameterized queries and template escaping.
Include test instructions in the README and ensure tests run with pytest.
________________________________________
11. Documentation & Submission Requirements
Each team must submit a single ZIP or GitHub repo link containing:
1.	Product Requirements Document (PRD) — 1–2 pages: objective, stakeholders, non‑goals, core features, success metrics.
2.	Wireframes — PNG or PDF of main screens (homepage, detail, dashboard, admin). Hand sketches are acceptable if scanned.
3.	Codebase — fully working app with clear README, requirements.txt, and run instructions.
4.	Database schema & ER diagram.
5.	.prompt/dev_notes.md — document any AI assistance used during development (tools, prompts, and how AI influenced decisions). Note: this is part of academic integrity and should reflect honest AI usage.
6.	AI-First Folder Structure (Required)
Your repository must include folders that support AI-assisted and context-aware development. 
These help AI tools (e.g., Cursor, Copilot Agent) understand your project and generate accurate code.

.prompt/
  dev_notes.md        ← log of all AI interactions and outcomes
  golden_prompts.md   ← high-impact prompts and responses

/docs/
  context/
    APA/              ← artifacts from Agility, Processes & Automation module
    DT/               ← Design Thinking artifacts (personas, journey maps)
    PM/               ← Product Management materials (PRDs, OKRs)
  shared/             ← common items (personas, glossary, OKRs)

tests/
  ai_eval/            ← optional tests for AI-based components

README.md             ← must describe folder purpose and AI integration
7.	Test suite & results — pytest output logs or screenshots.
8.	Demo script & slide deck for a 10‑minute presentation (max 7 slides recommended).
9.	Optional: Deployment link if hosted.
Students are encouraged to include relevant artifacts from other MSIS Core modules (Agility, Processes & Automation; Design Thinking; Product Management) in their /docs/context/ folder. These materials will not be graded directly but will help AI tools better understand the business, design, and process context of your project—allowing for more accurate and meaningful code generation, documentation, and testing assistance.
Submit by pushing to the team GitHub repo and linking the repo to the Canvas assignment. Ensure at least one team member invites the instructor (or TA) as collaborator or shares repo link.
________________________________________
 
12. Grading & Evaluation Rubric
Dimension	Weight	Details
Functionality	30%	Core features implemented correctly; booking flows and conflict detection work
Code Quality & Architecture	15%	Clear structure, use of blueprints/modules, documentation, and readable code
User Experience & Accessibility	15%	Usability, layout, accessibility basics
Testing & Security	15%	Tests included, server validation, basic security protections
Documentation & Deliverables	10%	PRD, wireframes, runbook, ERD, README
Presentation & Team Reflection	15%	Demo quality, explanation of tradeoffs, team dynamics, and .prompt/dev_notes.md
Late policy: Follow AiDD module rules. Unexcused late submissions may lose up to 50% credit; no submissions accepted after final exam date.
________________________________________
13. Example Use Cases / Walkthroughs
Use Case 1 — Student reserves a study room
1.	Student searches “study room” with date/time filter.
2.	System shows available rooms and availability calendar.
3.	Student requests a one‑hour booking; system checks conflicts, creates booking with pending status.
4.	If the room is auto‑approved, booking moves to approved and the requester receives confirmation. Otherwise, the owner or admin approves and requester is notified.
Use Case 2 — Staff posts a high‑value lab instrument
1.	Staff creates a resource marked as requires_approval.
2.	Student requests booking; booking goes into staff approval queue.
3.	Staff approves after verifying prerequisite training (manual admin action captured in notes).
Use Case 3 — Admin moderates abuse
1.	Admin views flagged reviews or reported messages.
2.	Admin can hide reviews, suspend a user, or delete content; actions logged in admin_logs.
________________________________________
14. Timeline & Milestones (18 Days)
Day 1–3: Planning & Setup - Create GitHub repo, assign roles, write PRD, and create wireframes. - Setup virtualenv, requirements.txt, initial Flask app.
Day 4–6: Database & Auth - Finalize schema, implement user registration & login, begin resource model.
Day 7–9: Resource CRUD & Search - Implement resource listing, detail pages, and search filters.
Day 10–12: Booking Logic & Messaging - Implement booking flow, conflict detection, messaging.
Day 13–14: Frontend polish & Client Validation - UI improvements, responsive adjustments, accessibility fixes.
Day 15: Testing & Security Sweep - Write tests, run security checks, fix issues.
Day 16: Documentation - Finalize README, ERD, PRD, and prompt logs.
Day 17: Deployment Prep - Deploy to chosen cloud (optional) or prepare local demo instructions.
Day 18: Presentation Day - 10‑minute demo + 5‑minute Q&A and retrospective.
Students are encouraged to manage progress using agile sprints or milestone tracking. The use of AI tools such as Cursor’s context management and Copilot Agent workflows should be documented in .prompt/dev_notes.md throughout the project lifecycle.
________________________________________
 
15. Appendix A — Suggested Acceptance Criteria (Sample)
•	A user can register and log in using a verified email address.
•	An authenticated user can create a resource and set its availability.
•	The search page returns accurate results for a given date/time filter.
•	Booking conflicts are detected and prevented.
•	Admin can view and modify bookings and moderate content.
________________________________________
16. Appendix B — Submission Checklist (Team)
☐	PRD (1–2 pages)
☐	Wireframes (PNG/PDF)
☐	Running Flask app (requirements.txt + README)
☐	ER Diagram and schema
☐	.prompt/dev_notes.md (AI usage log)
☐	Tests & pytest results
☐	Demo slides + script
☐	GitHub repo shared with instructor
________________________________________
 
17. Appendix C — AI-First Development Enhancements
________________________________________
Overview
This appendix integrates AI-First Development practices directly into the Campus Resource Hub project using Cursor AI, GitHub Copilot Agent Mode, and Model Context Protocol (MCP). These practices are required for the AiDD 2025 Capstone. Students will use AI responsibly and transparently throughout design, coding, testing, and documentation, reflecting modern professional development environments.
Refer to Section 5.1 and the Context Pack folder requirements when implementing AI First Development. Appendix C elaborates on prompt logging, ethical guidelines, and required AI integration deliverables.
________________________________________
C.1 Learning Goals
By completing this AI-First project, teams will:
1.	Collaborate effectively with AI-powered coding tools (Copilot, Cursor) while maintaining human oversight and accountability.
2.	Practice prompt engineering and context grounding using .prompt/ and /docs/context/ artifacts.
3.	Integrate context-aware or agentic features into their Campus Resource Hub application (e.g., scheduling assistant, auto-summary, or retrieval-based help component).
4.	Reflect on ethical, managerial, and technical considerations of AI-assisted development in professional environments.
________________________________________
C.2 Implementation Requirements
Each team must incorporate AI into both their development workflow and the functionality of their Campus Resource Hub system.
1. AI-Assisted Development Workflow
Requirements: - Maintain a .prompt/dev_notes.md file with representative prompts and AI interactions used throughout development. - Mark AI-authored or AI-suggested code with attribution comments such as:
# AI Contribution: Copilot suggested initial CRUD logic; reviewed and modified by team. - Include at least one Golden Prompt in .prompt/golden_prompts.md — a prompt that was especially effective in improving design, debugging, or documentation. - Summarize AI collaboration insights in the README file (approximately 150–200 words).
2. Context-Aware Application Feature
Teams must extend their Campus Resource Hub application with one AI-powered feature that leverages context or data from the project itself.
Examples: 
1. Resource Concierge:
A retrieval-based assistant that answers natural-language questions about available campus resources using /docs/context/*.md and database content. 
2. AI Scheduler:
Suggests optimal booking times or conflict resolutions based on previous usage data. 
3. Auto-Summary Reporter:
Generates weekly summaries (e.g., “Top 5 Most Reserved Resources”) or system insights.
Implementation Notes: - AI reasoning should reference existing project data and never generate fabricated content. - MCP may be used to safely connect AI agents with the local SQLite database. - Teams may use local LLMs (e.g., Ollama, LM Studio) or institution-provided API access if available.
3. AI-Enhanced Documentation
•	Use AI tools to assist in refining one or more of the following:
o	Product Requirements Document (PRD)
o	Wireframe or UI flow descriptions
o	Database schema or ERD commentary
o	API documentation (Markdown or auto-generated OpenAPI spec)
•	All AI-assisted text must be reviewed, verified, and clearly attributed.
________________________________________
C.3 Ethics, Attribution, and Academic Integrity
AI-assisted development is integral to this project and must be conducted transparently and ethically. Each team must:
•	Disclose all AI tools used in .prompt/dev_notes.md.
•	Validate all AI-generated code and text before submission.
•	Avoid submitting unreviewed AI outputs as final work.
•	Discuss the ethical implications of AI collaboration in the written reflection.
Unacknowledged or unverified AI-generated material will be treated as academic misconduct under Kelley School of Business policies.
________________________________________
C.4 Project Timeline
The AI-First development requirements apply throughout the duration of the Campus Resource Hub project. Teams are expected to integrate AI tools from the planning phase through final submission.
Project Due Date: Friday, November 15, 2025 (11:59 PM)
Suggested pacing milestones:
Phase	Focus	Expected AI Integration
Planning	Define scope, create PRD, and design wireframes	Use Copilot or Cursor to generate PRD drafts and diagram descriptions
Backend Development	Database, models, and Flask routes	Use AI to scaffold models and CRUD logic; document key prompts
Frontend & Validation	Templates, forms, and input validation	Use AI to propose Jinja layout patterns and validation logic
AI Feature Integration	Context-aware or agentic functionality	Implement and test AI component (e.g., scheduler or summary bot)
Testing & Documentation	Unit tests, reflections, and final polish	Generate test cases with Copilot; finalize README and reflection
________________________________________
C.5 Required Deliverables
In addition to all standard project deliverables, the following AI-related artifacts are required:
5.	.prompt/dev_notes.md — document AI prompts, context usage, and reflections.
6.	.prompt/golden_prompts.md — highlight the most impactful prompts and results.
7.	AI-enhanced application feature integrated into Flask app (concierge, scheduler, or summary bot).
8.	README section describing AI integration, ethical considerations, and technical overview.
9.	Written reflection summarizing AI collaboration and lessons learned.
________________________________________
C.6 Evaluation Criteria (Integrated)
The table below explains how AI-first development elements will be evaluated as part of the overall grading rubric in Section 12. These are not additional weights but illustrate how AI integration maps to the existing categories.
Dimension	Weight	Description
Functionality	25%	Core Campus Resource Hub features implemented and working correctly
AI Integration & Collaboration	20%	AI-assisted workflow, prompts, documentation, and integrated AI feature
Architecture & Code Quality	15%	Modular, documented, and maintainable code
UX & Accessibility	15%	Usability and clarity of design
Testing & Security	15%	Proper validation and test coverage, including AI-assisted testing
Reflection & Professionalism	10%	Clear written reflection and ethical handling of AI and human contributions
________________________________________
C.7 Reflection Prompts
Each team must address the following reflection questions within their .prompt/dev_notes.md or as a separate document:
10.	How did AI tools shape your design or coding decisions?

11.	What did you learn about verifying and improving AI-generated outputs?

12.	What ethical or managerial considerations emerged from using AI in your project?

13.	How might these tools change the role of a business technologist or product manager in the next five years?
________________________________________
End of Appendix C — AI-First Development Enhancements (Integrated Requirements)

End of Project Brief — Campus Resource Hub
