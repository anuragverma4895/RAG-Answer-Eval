# RAG Pipeline with Automated Answer Evaluation

A polished, portfolio-ready React/Vite interface for demonstrating a Retrieval-Augmented Generation workflow and automated answer-quality evaluation.

## Product experience
- Clean black-and-white visual system with visible borders and high-contrast text
- RAG playground with a question, retrieval settings, generated answer, and retrieved context
- Evaluation snapshot with relevance, context precision, faithfulness, completeness, and overall score
- Knowledge-base inventory with indexed document and chunk metadata
- Recent evaluation examples with human-readable verdicts
- Responsive layout for desktop, tablet, and mobile

## Tech stack
React, Vite, JavaScript, Lucide React, CSS.

## Run locally
```bash
npm install
npm run dev
```

Open the local URL printed by Vite.

## Architecture
The UI is structured into product surfaces so a real retrieval/generation backend can be connected later. The current repository provides a front-end demo experience with realistic state changes and evaluation visuals.
