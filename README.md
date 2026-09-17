# E-Commerce Challenge

An enterprise-grade e-commerce application built for the technical challenge: product catalog management, CSV import, search, and a purchase flow with a simulated payment gateway.

**Example CSV file downloaded:** September 11th, 2026. The challenge was recevied on September 10th and started working in the design this same date in the evening. However the file was downloaded and used until the next day (11th).

## Tech Stack

- **Backend & UI:** Python, Streamlit
- **Data:** SQLAlchemy (ORM) + SQLite
- **CSV processing:** pandas
- **Containerization:** Docker

## Features

- Product CRUD (create, read, update, delete)
- CSV import with per-row validation and error reporting
- Product search
- Purchase flow with a simulated payment gateway (configurable decline rate)
- Structured logging (file + console)
- Admin/Shop navigation split reflecting the two real-world personas (catalog manager vs. customer)

## Architecture & Decisions

This README stays intentionally brief. For the full picture, see:

- **[`docs/Architecture.md`](docs/Architecture.md)** — layered architecture, diagrams (container view, sequence, class diagram), and 17 documented design decisions (why SQLite over PostgreSQL, why Streamlit, the exception hierarchy, the payment gateway design, logging setup, and more), plus what would change for a production deployment.
- **[`docs/Bugs.md`](docs/Bugs.md)** — bugs found during development, their root causes, and fixes — including a few genuinely non-obvious Streamlit behaviors worth knowing about if you extend this project.

## Project Structure

```
ecommerce-challenge/
├── app/
│   ├── core/          # Cross-cutting infrastructure: exceptions, logging config
│   ├── db/             # SQLAlchemy engine/session setup
│   ├── models/         # SQLAlchemy models
│   ├── repository/      # Data access layer
│   ├── services/        # Business logic (products, CSV import, purchases)
│   └── ui/              # Streamlit UI (Admin + Shop pages)
├── data/                # SQLite DB (generated) + example CSV
├── docs/                # Architecture.md, Bugs.md
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```

## Running Locally (Docker — recommended)

```bash
git clone <repo-url>
cd ecommerce-challenge
docker build -t ecommerce-challenge .
docker run -p 8501:8501 ecommerce-challenge
```

Open **http://localhost:8501** in your browser.

**Note:** the database and log file live inside the container only — they reset on every `docker run` (no volume is mounted). This is intentional for this challenge's scope; see `docs/Architecture.md` for what would change for persistent, production-grade storage.

## Running Locally (without Docker)

Requires Python 3.12+.

```bash
git clone <repo-url>
cd ecommerce-challenge
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # macOS/Linux

pip install -r requirements.txt
python -m streamlit run app/ui/streamlit_app.py
```

Open **http://localhost:8501** in your browser.

## Importing Products

An example CSV (`data/example_products.csv`) is included in the repo. From the app: **Admin → Manage Products → Import CSV** tab, upload the file, and click **Import**. A summary and any per-row errors are shown after import.

## A Note on AI Use and Code Comments

AI was used as part of building this project. Per the challenge instructions, the source code intentionally contains no inline comments explaining *what* the code does. Any non-obvious *why* behind a design or implementation choice is documented in `docs/Architecture.md` or `docs/Bugs.md`.
