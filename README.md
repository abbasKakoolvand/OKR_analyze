# OKR Analyze API

A FastAPI-based service that analyzes daily team tasks against OKRs (Objectives & Key Results) using OpenAI’s GPT models.

---

## Table of Contents

- [Project Overview](#project-overview)  
- [Features](#features)  
- [Getting Started](#getting-started)  
  - [Prerequisites](#prerequisites)  
  - [Installation](#installation)  
  - [Configure Environment Variables](#configure-environment-variables)  
  - [Running the Server](#running-the-server)  
- [API Usage](#api-usage)  
- [Project Structure](#project-structure)  
- [Extending for RAG & Agents](#extending-for-rag--agents)  
- [Testing](#testing)  
- [License](#license)  

---

## Project Overview

This service ingests:

1. A **daily task table** for each team member.  
2. A list of **OKRs** (Key Results).  

It then calls OpenAI’s Chat API to produce:

- **tasks_by_kr**: Which tasks each person completed for each KR.  
- **risks**: Potential risks per KR.  
- **deliverables**: Key deliverables per KR.  

---

## Features

- Modular, layered architecture  
- Clear separation of API, core logic, models, and external services  
- Environment-based configuration via `.env`  
- Easily extendable to RAG (Retrieval-Augmented Generation) or full conversational agents  

---

## Getting Started

### Prerequisites

- Python 3.8+  
- An OpenAI API key  

### Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/your-org/okr_analyze.git
   cd okr_analyze

 **Run in Terminal**  
   ```bash
    uvicorn okr_analyze:app --reload

 **List of APIs**  
   http://localhost:8000/docs