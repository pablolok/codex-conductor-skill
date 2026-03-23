# Agent Skills Catalog

This catalog mirrors the upstream Gemini Conductor skills contract so Codex can recommend and install comparable skills during `conductor:setup` and `conductor:newTrack`.

## Firebase Skills
Skills focused on setting up, managing, and using various Firebase services.

### firebase-ai-logic-basics
- **Description**: Official skill for integrating Firebase AI Logic (Gemini API) into web applications. Covers setup, multimodal inference, structured output, and security.
- **URL**: https://raw.githubusercontent.com/firebase/agent-skills/main/skills/firebase-ai-logic-basics/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `firebase`, `firebase-admin`
    - **Keywords**: `Firebase`, `AI Logic`, `Gemini API`, `GenAI`

### firebase-app-hosting-basics
- **Description**: Deploy and manage web apps with Firebase App Hosting. Use this skill when deploying Next.js/Angular apps with backends.
- **URL**: https://raw.githubusercontent.com/firebase/agent-skills/main/skills/firebase-app-hosting-basics/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `firebase`, `firebase-admin`
    - **Keywords**: `Firebase App Hosting`, `Next.js`, `Angular`

### firebase-auth-basics
- **Description**: Guide for setting up and using Firebase Authentication. Use this skill when the user's app requires user sign-in, user management, or secure data access using auth rules.
- **URL**: https://raw.githubusercontent.com/firebase/agent-skills/main/skills/firebase-auth-basics/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `firebase`, `firebase-admin`
    - **Keywords**: `Firebase Authentication`, `Auth`, `Sign-in`

### firebase-basics
- **Description**: Guide for setting up and using Firebase. Use this skill when the user is getting started with Firebase, setting up a local environment, or adding Firebase to an app.
- **URL**: https://raw.githubusercontent.com/firebase/agent-skills/main/skills/firebase-basics/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `firebase`, `firebase-admin`
    - **Keywords**: `Firebase`, `Setup`

### firebase-data-connect-basics
- **Description**: Build and deploy Firebase Data Connect backends with PostgreSQL. Use for schema design, GraphQL queries and mutations, authorization, and SDK generation.
- **URL**: https://raw.githubusercontent.com/firebase/agent-skills/main/skills/firebase-data-connect-basics/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `firebase`, `firebase-admin`
    - **Keywords**: `Firebase Data Connect`, `PostgreSQL`, `GraphQL`

### firebase-firestore-basics
- **Description**: Comprehensive guide for Firestore basics including provisioning, security rules, and SDK usage.
- **URL**: https://raw.githubusercontent.com/firebase/agent-skills/main/skills/firebase-firestore-basics/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `firebase`, `firebase-admin`
    - **Keywords**: `Firestore`, `Database`, `Security Rules`

### firebase-hosting-basics
- **Description**: Skill for working with Firebase Hosting (Classic). Use this for static web apps, SPAs, or simple microservices.
- **URL**: https://raw.githubusercontent.com/firebase/agent-skills/main/skills/firebase-hosting-basics/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `firebase`, `firebase-admin`
    - **Keywords**: `Firebase Hosting`, `Static Hosting`

## DevOps Skills
Skills for designing, building, and managing CI/CD pipelines and infrastructure on Google Cloud.

### cloud-deploy-pipelines
- **Description**: Manage the lifecycle of Google Cloud Deploy delivery pipelines and releases.
- **URL**: https://raw.githubusercontent.com/gemini-cli-extensions/devops/main/skills/cloud-deploy-pipelines/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `skaffold`
    - **Keywords**: `Cloud Deploy`, `delivery pipeline`, `skaffold.yaml`, `clouddeploy.yaml`

### gcp-cicd-deploy
- **Description**: Assistant for deploying applications to Google Cloud, supporting Static Sites, Cloud Run, and GKE.
- **URL**: https://raw.githubusercontent.com/gemini-cli-extensions/devops/main/skills/gcp-cicd-deploy/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `gcloud`
    - **Keywords**: `Cloud Run`, `GCS`, `Static Site`, `Deployment`, `Google Cloud`

### gcp-cicd-design
- **Description**: Assistant for designing and managing CI/CD pipelines on Google Cloud.
- **URL**: https://raw.githubusercontent.com/gemini-cli-extensions/devops/main/skills/gcp-cicd-design/
- **Party**: 1p
- **Detection Signals**:
    - **Keywords**: `CI/CD`, `Pipeline Design`, `Google Cloud`, `Architectural Design`

### gcp-cicd-terraform
- **Description**: Use Terraform to provision Google Cloud resources with standard GCS backend state management and IAM least privilege.
- **URL**: https://raw.githubusercontent.com/gemini-cli-extensions/devops/main/skills/gcp-cicd-terraform/
- **Party**: 1p
- **Detection Signals**:
    - **Dependencies**: `terraform`
    - **Keywords**: `Terraform`, `GCP`, `GCS Backend`, `Infrastructure as Code`, `IaC`
