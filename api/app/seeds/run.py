"""
Seed script: creates sample users, org, workspace, documents, prompts, eval datasets.
Run with: python -m app.seeds.run
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text


async def seed():
    from app.db.session import get_db_context
    from app.core.security import hash_password

    async with get_db_context() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT count(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print("Database already seeded, skipping.")
            return

        print("Seeding database...")

        # ── Users ───────────────────────────────────────
        admin_id = uuid.uuid4()
        user_id = uuid.uuid4()

        await db.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
                VALUES (:id, :email, :password, :name, true, true, now(), now())
            """),
            {
                "id": admin_id,
                "email": "admin@enterprise.ai",
                "password": hash_password("Admin123!"),
                "name": "Admin User",
            },
        )

        await db.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
                VALUES (:id, :email, :password, :name, true, false, now(), now())
            """),
            {
                "id": user_id,
                "email": "user@enterprise.ai",
                "password": hash_password("User1234!"),
                "name": "Regular User",
            },
        )

        # ── Organization ────────────────────────────────
        org_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO organizations (id, name, slug, description, is_active, created_at, updated_at)
                VALUES (:id, :name, :slug, :desc, true, now(), now())
            """),
            {
                "id": org_id,
                "name": "Enterprise Corp",
                "slug": "enterprise-corp",
                "desc": "Demo organization for Enterprise AI Knowledge Copilot",
            },
        )

        # Memberships
        await db.execute(
            text("""
                INSERT INTO organization_members (id, organization_id, user_id, role, created_at, updated_at)
                VALUES (:id, :org_id, :user_id, 'owner', now(), now())
            """),
            {"id": uuid.uuid4(), "org_id": org_id, "user_id": admin_id},
        )
        await db.execute(
            text("""
                INSERT INTO organization_members (id, organization_id, user_id, role, created_at, updated_at)
                VALUES (:id, :org_id, :user_id, 'member', now(), now())
            """),
            {"id": uuid.uuid4(), "org_id": org_id, "user_id": user_id},
        )

        # ── Workspace ──────────────────────────────────
        ws_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO workspaces (id, organization_id, name, slug, description, is_active, created_at, updated_at)
                VALUES (:id, :org_id, :name, :slug, :desc, true, now(), now())
            """),
            {
                "id": ws_id,
                "org_id": org_id,
                "name": "Engineering Knowledge Base",
                "slug": "engineering-kb",
                "desc": "Technical documentation and engineering knowledge",
            },
        )

        # ── Prompt Templates ───────────────────────────
        rag_template_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO prompt_templates (id, name, description, is_active, created_at, updated_at)
                VALUES (:id, :name, :desc, true, now(), now())
            """),
            {
                "id": rag_template_id,
                "name": "rag-qa",
                "desc": "RAG-based question answering prompt",
            },
        )

        rag_version_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO prompt_versions (id, template_id, version_number, content, system_prompt, label, created_by, created_at, updated_at)
                VALUES (:id, :tid, 1, :content, :system, 'production', :uid, now(), now())
            """),
            {
                "id": rag_version_id,
                "tid": rag_template_id,
                "content": (
                    "Given the following context from our knowledge base, answer the user's question.\n\n"
                    "Context:\n{context}\n\n"
                    "Question: {question}\n\n"
                    "Instructions:\n"
                    "- Answer based ONLY on the provided context\n"
                    "- If the context doesn't contain enough information, say so clearly\n"
                    "- Cite specific documents when possible\n"
                    "- Be concise and accurate"
                ),
                "system": (
                    "You are an Enterprise AI Knowledge Assistant. You help employees find "
                    "accurate information from the company knowledge base. Always cite sources "
                    "and never make up information that isn't in the provided context."
                ),
                "uid": admin_id,
            },
        )

        # Agent prompt
        agent_template_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO prompt_templates (id, name, description, is_active, created_at, updated_at)
                VALUES (:id, :name, :desc, true, now(), now())
            """),
            {
                "id": agent_template_id,
                "name": "agent-router",
                "desc": "Agent tool routing prompt",
            },
        )

        await db.execute(
            text("""
                INSERT INTO prompt_versions (id, template_id, version_number, content, system_prompt, label, created_by, created_at, updated_at)
                VALUES (:id, :tid, 1, :content, :system, 'production', :uid, now(), now())
            """),
            {
                "id": uuid.uuid4(),
                "tid": agent_template_id,
                "content": (
                    "Based on the user's query, determine which tools to use:\n\n"
                    "Available tools: {tools}\n\n"
                    "User query: {query}\n\n"
                    "Return a JSON array of tool names to invoke."
                ),
                "system": (
                    "You are an intelligent agent router. Analyze the user's intent and "
                    "select the most appropriate tools. Only select tools that are needed."
                ),
                "uid": admin_id,
            },
        )

        # ── Eval Dataset ───────────────────────────────
        dataset_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO eval_datasets (id, name, description, status, item_count, created_at, updated_at)
                VALUES (:id, :name, :desc, 'active', 3, now(), now())
            """),
            {
                "id": dataset_id,
                "name": "RAG Quality Baseline",
                "desc": "Baseline evaluation dataset for RAG pipeline quality",
            },
        )

        eval_questions = [
            {
                "question": "What is our company's vacation policy?",
                "ground_truth": "Employees receive 20 days of PTO per year, accruing monthly.",
            },
            {
                "question": "How do I set up the development environment?",
                "ground_truth": "Clone the repo, run docker compose up, and follow the README setup guide.",
            },
            {
                "question": "What are the security requirements for API endpoints?",
                "ground_truth": "All API endpoints require JWT authentication, RBAC authorization, and rate limiting.",
            },
        ]

        for q in eval_questions:
            await db.execute(
                text("""
                    INSERT INTO eval_dataset_items (id, dataset_id, question, ground_truth, created_at, updated_at)
                    VALUES (:id, :did, :question, :gt, now(), now())
                """),
                {
                    "id": uuid.uuid4(),
                    "did": dataset_id,
                    "question": q["question"],
                    "gt": q["ground_truth"],
                },
            )

        # ── Connectors ─────────────────────────────────
        await db.execute(
            text("""
                INSERT INTO connectors (id, name, connector_type, is_active, created_at, updated_at)
                VALUES (:id, 'File Upload', 'file_upload', true, now(), now())
            """),
            {"id": uuid.uuid4()},
        )
        await db.execute(
            text("""
                INSERT INTO connectors (id, name, connector_type, is_active, created_at, updated_at)
                VALUES (:id, 'Web Scraper', 'web_page', true, now(), now())
            """),
            {"id": uuid.uuid4()},
        )
        await db.execute(
            text("""
                INSERT INTO connectors (id, name, connector_type, config, is_active, created_at, updated_at)
                VALUES (:id, 'External API Connector', 'external_api', :config, true, now(), now())
            """),
            {"id": uuid.uuid4(), "config": '{"base_url": "https://api.example.com", "api_key_env": "EXTERNAL_API_KEY"}'},
        )

        print("Database seeded successfully!")
        print("  Admin: admin@enterprise.ai / Admin123!")
        print("  User:  user@enterprise.ai / User1234!")


def main():
    asyncio.run(seed())


if __name__ == "__main__":
    main()
