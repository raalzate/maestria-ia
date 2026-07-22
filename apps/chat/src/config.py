import os
from dotenv import load_dotenv
import logging
from dataclasses import dataclass
import engineio

# Cargar variables del archivo .env
load_dotenv()

# --- CONFIGURACIÓN CRÍTICA M1 ---
# Se ejecuta al importar este archivo
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Parche EngineIO
engineio.payload.Payload.max_decode_packets = 2000

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variables Globales
MODEL_PATH = os.getenv("MODEL_PATH", "")
APP_TITLE = os.getenv("APP_TITLE", "Emma AI")
MODEL_AUDIO_PATH = os.getenv("MODEL_AUDIO_PATH", "")

STATE_DEFAULT = {
        "current_level": "Intermediate", 
        "current_topic": "General Conversation",
        "completed_topics": [], 
        "conversation_history": [], 
        "user_memory": [],
        "student_name": "", 
        "student_interests": [], 
        "student_goals": [],
        "discovery_completed": False, 
        "audio_chunks": [], 
        "is_speaking": False,
        "networking_memory": [],
        "learning_progress": {}
}

CURRICULUM = {
  "Level 1 (The Intern - Daily Syncs & Basics)": [
    {
      "topic": "The Daily Stand-up: Status Updates (Present Continuous)",
      "example": "Manager asks 'What are you working on?', User answers: 'I am fixing the login bug and updating the CSS.'"
    },
    {
      "topic": "Clarifying Requirements: Asking 'What do you mean?' (Questions)",
      "example": "User asks: 'What do you mean by \"fast\"? Do we have a specific loading time target?'"
    },
    {
      "topic": "Reporting Bugs: Describing Expected vs. Actual Behavior (Past Simple)",
      "example": "User writes: 'I clicked the submit button, but the page did not refresh and no error appeared.'"
    },
    {
      "topic": "Environment Issues: 'It works on my machine' (Present Simple)",
      "example": "User says: 'It works fine on my local environment; I do not have that configuration error.'"
    },
    {
      "topic": "Asking for Help: Unblocking yourself politely (Can/Could)",
      "example": "User asks: 'Could you please help me debug this function when you have a minute? I am stuck.'"
    },
    {
      "topic": "Git Basics: Committing & Pushing (Verbs)",
      "example": "User says: 'I staged the files, committed the changes with a message, and pushed to the remote branch.'"
    },
    {
      "topic": "Code Comments: Explaining 'Why', not 'What' (Imperatives)",
      "example": "User comments: 'Check for null values here to prevent the application from crashing on startup.'"
    },
    {
      "topic": "Scheduling: Setting up a 1:1 (Prepositions of Time)",
      "example": "User writes: 'Are you free for a quick sync at 3 PM on Tuesday, or in the morning on Wednesday?'"
    },
    {
      "topic": "Hardware Requests: Asking for a new monitor (Polite Requests)",
      "example": "User writes: 'I would like to request a second monitor to improve my workflow, please.'"
    },
    {
      "topic": "The Onboarding Buddy: Asking where things are (Prepositions of Place)",
      "example": "User asks: 'Is the printer next to the kitchen or behind the main meeting room?'"
    }
  ],
  "Level 2 (The Junior - Pull Requests & Collaboration)": [
    {
      "topic": "Code Review 1: Explaining your logic (Because/So)",
      "example": "User comments: 'I used a HashMap here because lookup speed is critical for this feature.'"
    },
    {
      "topic": "Code Review 2: Responding to feedback politely (Agreeing/Disagreeing)",
      "example": "User replies: 'I agree with your point regarding readability, I will refactor that method.'"
    },
    {
      "topic": "The Demo: Showing a new feature (Demonstratives)",
      "example": "User presents: 'This is the new login screen, and those are the updated error messages we added.'"
    },
    {
      "topic": "Pair Programming: Navigating & Driving (Suggestions: Let's)",
      "example": "User suggests: 'Let's try refactoring this logic into a separate utility class.'"
    },
    {
      "topic": "Troubleshooting: Reading error logs out loud (Pronunciation)",
      "example": "User reads: 'It throws a NullPointerException on line forty-two in the main controller.'"
    },
    {
      "topic": "Time Estimation: 'It will take...' (Future with Will)",
      "example": "User estimates: 'I think it will take about three days to complete the backend integration.'"
    },
    {
      "topic": "Documentation: Writing a Readme (Passive Voice Basics)",
      "example": "User writes: 'The database is initialized by running the setup script provided in the root folder.'"
    },
    {
      "topic": "API Integration: Discussing endpoints (Nouns/Adjectives)",
      "example": "User discusses: 'The endpoint requires a valid authentication token in the header to return the data.'"
    },
    {
      "topic": "Deployments: 'The build failed' (Past Simple Irregular)",
      "example": "User updates: 'The build broke last night because I forgot to include the new dependency.'"
    },
    {
      "topic": "Retrospectives: 'What went well?' (Reflective Past)",
      "example": "User reflects: 'Communication was excellent this sprint, but the QA process took longer than expected.'"
    }
  ],
  "Level 3 (The Mid-Level - Architecture & Trade-offs)": [
    {
      "topic": "Design Patterns: Explaining Singleton/Factory (Definitions)",
      "example": "User explains: 'A Singleton is a design pattern that restricts the instantiation of a class to one single object.'"
    },
    {
      "topic": "Technical Debt: Explaining why we need to refactor (Necessity)",
      "example": "User argues: 'We need to refactor this module now, otherwise adding new features will be impossible later.'"
    },
    {
      "topic": "Trade-offs: Speed vs. Quality (Comparatives)",
      "example": "User compares: 'This solution is faster to implement, but the code is messier than the alternative approach.'"
    },
    {
      "topic": "Mentoring Juniors: Giving constructive feedback (Modals of Advice)",
      "example": "User advises: 'You should probably handle the error here instead of letting it crash the app.'"
    },
    {
      "topic": "System Design: Monoliths vs Microservices (Abstract Nouns)",
      "example": "User discusses: 'We need to consider scalability, maintainability, and complexity before splitting the monolith.'"
    },
    {
      "topic": "Database Choice: SQL vs NoSQL (Justification)",
      "example": "User justifies: 'We chose MongoDB due to the flexible schema requirements of our unstructured data.'"
    },
    {
      "topic": "Performance: 'It's too slow' (Too/Enough)",
      "example": "User analyzes: 'The database query is too slow; it is not efficient enough for high-traffic production.'"
    },
    {
      "topic": "Security: Discussing vulnerabilities (Passive Voice)",
      "example": "User notes: 'User passwords must be hashed and salted before being stored in the database.'"
    },
    {
      "topic": "The Incident: Post-mortem analysis (Third Conditional)",
      "example": "User analyzes: 'If we had set up proper alerts, we would have noticed the memory leak sooner.'"
    },
    {
      "topic": "Cross-functional: Talking to Designers (Adapting Register)",
      "example": "User explains: 'We cannot implement that animation because it would slow down the app significantly on older phones.'"
    }
  ],
  "Level 4 (The Senior - Leadership & Strategy)": [
    {
      "topic": "Architecture Reviews: Defending a decision (Persuasion)",
      "example": "User defends: 'This approach ensures long-term stability and minimizes external dependency risks.'"
    },
    {
      "topic": "Scaling: Discussing load balancers & caching (Cause/Effect)",
      "example": "User explains: 'The latency increased as a result of the cache miss rate spiking during peak hours.'"
    },
    {
      "topic": "Cloud Infrastructure: AWS vs Azure concepts (Technical Vocabulary)",
      "example": "User plans: 'We are migrating from EC2 instances to a serverless architecture using AWS Lambda functions.'"
    },
    {
      "topic": "Hiring: Interviewing candidates (Hypotheticals)",
      "example": "User evaluates: 'If we hired this candidate, they would bring strong DevOps skills that the team currently lacks.'"
    },
    {
      "topic": "Saying No: Managing Scope Creep (Diplomacy)",
      "example": "User negotiates: 'I understand the value of this feature; however, we cannot fit it into the current sprint without delaying the release.'"
    },
    {
      "topic": "Stakeholder Management: Explaining tech to non-tech (Simplification)",
      "example": "User simplifies: 'Think of the API like a waiter taking orders to the kitchen and bringing back the food you asked for.'"
    },
    {
      "topic": "Migration Plans: Moving Legacy Code (Future Perfect)",
      "example": "User projects: 'By the end of Q4, we will have migrated 80% of the legacy code to the new React stack.'"
    },
    {
      "topic": "Negotiating Deadlines: 'We can't make it' (Softening)",
      "example": "User warns: 'It might be difficult to deliver everything by Friday given the current blockers we found.'"
    },
    {
      "topic": "Release Planning: Versioning & Strategy (Future Continuous)",
      "example": "User plans: 'Next week, we will be rolling out the beta version to 10% of our user base.'"
    },
    {
      "topic": "Process Improvement: CI/CD Pipelines (Gerunds)",
      "example": "User suggests: 'Automating the testing process is crucial for reducing manual errors during deployment.'"
    }
  ],
  "Level 5 (The Lead - Vision & Culture)": [
    {
      "topic": "Vision Setting: The 1-Year Roadmap (Future Forms)",
      "example": "User presents: 'Next year, we are going to leverage AI to personalize the user experience across all platforms.'"
    },
    {
      "topic": "Crisis Management: Handling a Data Breach (Formal Tone)",
      "example": "User writes: 'We regret to inform you that an unauthorized party gained limited access to our user database.'"
    },
    {
      "topic": "Team Culture: Handling conflict (Advanced Modals)",
      "example": "User mediates: 'That code review comment could have been phrased more constructively to avoid friction.'"
    },
    {
      "topic": "Budgeting: Resource allocation (Financial English)",
      "example": "User proposes: 'We need to allocate more budget for cloud overhead and third-party licensing fees next quarter.'"
    },
    {
      "topic": "Public Speaking: presenting at a conf (Rhetoric)",
      "example": "User speaks: 'Not only does this architecture improve performance, but it also reduces our infrastructure costs significantly.'"
    },
    {
      "topic": "RFCs: Writing Request for Comments (Formal Writing)",
      "example": "User writes: 'The objective of this proposal is to standardize our logging infrastructure across all microservices.'"
    },
    {
      "topic": "Evaluation: Performance Reviews (Nuanced Adjectives)",
      "example": "User reviews: 'Your technical skills are exemplary, but your communication style is occasionally inconsistent.'"
    },
    {
      "topic": "Vendor Negotiations: Contracts & SLAs (Conditionals)",
      "example": "User negotiates: 'Unless you can guarantee 99.9% uptime, we won't be able to sign the renewal contract.'"
    },
    {
      "topic": "Buy vs Build: Strategic Decisions (weighted pros/cons)",
      "example": "User analyzes: 'While building in-house offers more control, buying a SaaS solution accelerates our time-to-market substantially.'"
    }
  ]
}




@dataclass
class AppConfig:
    SILENCE_THRESHOLD: int = 3500
    SILENCE_TIMEOUT: float = 1300.0  # ms
    SAMPLE_RATE: int = 24000
    CHANNELS: int = 1
    SAMPLE_WIDTH: int = 2
    MIN_AUDIO_DURATION: float = 0.8

CONFIG = AppConfig()

HUMAN_STATUS = {
    "grammar": ["Checking your grammar...", "Reviewing sentence structure..."],
    "assessor": ["Checking your level...", "Assessing your response..."],
    "memory": ["Recalling our history...", "Connecting the dots..."],
    "curriculum": ["Thinking about the next step...", "Planning our lesson..."],
    "tutor": ["Emma is typing..."]
}