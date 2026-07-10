# AgentTutor

## Overall Goal

The goal of AgentTutor is to create a modern tutoring platform where requests submitted through an integrated chat interface are delegated to an AI agent.

Instead of simply answering questions, the AI should be able to:

* Understand user requests
* Reason through multi-step tasks
* Retrieve relevant information
* Select the appropriate system capabilities
* Perform actions within the platform

The AI agent should have a predetermined, finite set of actions. However, the internal tool selection and execution process should be encapsulated so that users interact with a simple conversational interface rather than directly interacting with individual tools.

The AI should serve as a true platform assistant rather than a standalone chatbot connected to LangChain.

---

## User Roles

### Students

Students should be able to:

* Create an account
* Manage their profile
* Browse tutors
* Search tutors by:

  * Subject
  * Availability
  * Expertise
* Request tutoring sessions
* Schedule appointments
* Reschedule appointments
* Cancel appointments
* View upcoming sessions
* View session history
* Ask questions about the platform through the AI chat
* Ask the AI to perform tasks on their behalf
* Receive personalized tutor recommendations

### Tutors

Tutors should be able to:

* Create professional profiles
* List the subjects they teach
* Configure weekly availability
* Accept tutoring requests
* Reject tutoring requests
* Manage their calendars
* Track completed sessions
* Receive AI assistance for scheduling and organization

### Administrators

Administrators should be able to:

* Manage users
* Manage tutors
* Review reports
* Moderate content
* View analytics dashboards
* Handle disputes
* Manage platform settings
* Access system logs
* Monitor AI actions
* Configure permissions

---

## AI Agent

The platform should include an integrated AI agent that accesses application functionality through tools rather than relying only on text generation.

The agent should be capable of:

* Looking up tutors
* Checking schedules
* Booking sessions
* Rescheduling sessions
* Cancelling appointments
* Recommending tutors
* Answering platform-related questions
* Summarizing conversations
* Searching the database
* Updating user information
* Creating reminders
* Sending notifications
* Performing multi-step reasoning before taking action

The AI should determine which tools to call based on the user's request rather than relying on hardcoded workflows.

The available tools should remain encapsulated behind the AI agent. Users should only need to describe what they want through the chat interface.

### Example Requests

Users should be able to submit requests such as:

> Find me a calculus tutor available tomorrow after 5 PM.

> Book the highest-rated physics tutor.

> Move my session from Friday to Saturday.

> Summarize my conversations with my algebra tutor.

> Recommend a tutor based on my previous sessions.

> Which tutor specializes in machine learning?

> Cancel my appointment next week.

> What homework did I upload last month?

---

## Agent Architecture

The AI agent should be built using an agent framework such as:

* LangGraph
* LangChain

The agent should support:

* Tool calling
* Retrieval-Augmented Generation
* Conversation memory
* Multi-step planning
* Long-term memory
* Structured outputs
* Streaming responses
* Human-in-the-loop approval for sensitive actions
* Error recovery
* Logging
* Observability

### Agent Tools

The AI agent should have tools for interacting with:

* User database
* Tutor database
* Session database
* Calendar system
* Authentication system
* Messaging system
* Notification service
* Search engine
* Analytics system

Each tool should expose a limited and clearly defined capability.

The agent should not have unrestricted access to the entire application. Instead, it should interact with the system through secure, validated, and permission-aware tool interfaces.

---

## Core Features

### Authentication

* Sign up
* Login
* OAuth
* Password reset
* Email verification
* Multi-factor authentication
* Role-based permissions

### Scheduling

* Calendar interface
* Availability management
* Time-zone support
* Automatic conflict detection
* Recurring sessions
* Session reminders
* Session rescheduling
* Session cancellation

---

## Dashboards

### Student Dashboard

The student dashboard should include:

* Upcoming sessions
* Homework
* Messages
* AI recommendations
* Session history
* Personalized tutor recommendations

### Tutor Dashboard

The tutor dashboard should include:

* Schedule
* Student requests
* Completed sessions
* Availability
* Performance metrics

### Administrator Dashboard

The administrator dashboard should include:

* Platform statistics
* User growth
* Revenue
* AI usage
* Reports
* System logs
* AI action logs

---

## Suggested Agent Workflow

A user submits the following request through the chat:

> Find me a calculus tutor available tomorrow after 5 PM.

The agent should:

1. Identify the authenticated user.
2. Determine the user's time zone.
3. Extract the requested subject, date, and time.
4. Search the tutor database.
5. Check the availability of matching tutors.
6. Rank the available tutors.
7. Present the strongest options to the user.
8. Ask for confirmation before booking.
9. Book the selected session.
10. Update the relevant calendars.
11. Send notifications to the student and tutor.
12. Record the action in the system logs.

The user should not need to know which tools were called internally.

---

## Safety and Permissions

The AI agent should operate within strict security and permission boundaries.

The system should include:

* Role-based access control
* Tool-level authorization
* User confirmation for sensitive actions
* Audit logs for AI actions
* Input validation
* Structured output validation
* Rate limiting
* Secure credential management
* Protection against prompt injection
* Protection against unauthorized data access
* Separation between read-only and write actions

Sensitive actions may include:

* Booking sessions
* Cancelling sessions
* Rescheduling sessions
* Updating account information
* Sending messages on behalf of users
* Changing platform settings
* Accessing private conversations

The system should request confirmation before performing consequential or irreversible actions.

---

## Technology Stack

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS

### Backend

* FastAPI

### Database and Caching

* PostgreSQL
* Redis

### Authentication

* JWT
* OAuth

### AI

* LangGraph or LangChain
* Free or open-access LLM providers
* Embedding model
* Retrieval-Augmented Generation pipeline
* Structured tool calling

### Vector Database

Possible options include:

* Pinecone
* Weaviate
* Chroma
* pgvector

### Infrastructure

* Docker
* CI/CD
* Cloud deployment
* Monitoring
* Logging

---

## Suggested System Architecture

```text
Next.js Frontend
        |
        v
FastAPI Backend
        |
        +----------------------+
        |                      |
        v                      v
Application Services      AI Agent Service
        |                      |
        v                      v
PostgreSQL                LangGraph/LangChain
Redis                     LLM Provider
Authentication            Agent Tools
Calendar                  RAG Pipeline
Messaging                 Vector Database
Notifications
Analytics
```

---

## Application Modules

The backend can be divided into the following modules:

* Authentication
* Users
* Tutors
* Sessions
* Scheduling
* Messaging
* Notifications
* Analytics
* AI agent
* Agent tools
* Audit logging

Each module should expose clearly defined services that can be used by both the traditional application interface and the AI agent.

---

## Design Principles

The platform should follow these principles:

* Modular architecture
* Encapsulated AI tools
* Secure tool execution
* Clear permission boundaries
* Human approval for sensitive actions
* Reliable error handling
* Strong observability
* Scalable infrastructure
* Testable components
* Provider-independent AI interfaces
* Easy integration of new agent tools

New tools and capabilities should be addable without requiring major changes to the agent or the rest of the platform.

---

## Overall Vision

The final product should feel like a fully autonomous tutoring platform where users can either navigate the application traditionally or ask the AI to accomplish tasks on their behalf through the chat interface.

The AI should understand natural language, access the platform's data and services through secure tools, reason across multiple steps when necessary, and execute actions while respecting user permissions.

The finite set of agent actions should remain encapsulated behind the conversational interface so that users do not need to understand the underlying tools or workflows.

The system should be modular, production-ready, scalable, and designed so that new tools and capabilities can be added to the AI agent over time without requiring major architectural changes.
