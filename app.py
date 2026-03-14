import streamlit as st
import asyncio
import os
import uuid
from typing import Any, Coroutine


def _load_streamlit_secrets_to_env():
    """Bridge Streamlit Cloud secrets into os.environ for all modules."""
    if hasattr(st, "secrets"):
        for key in st.secrets:
            if isinstance(st.secrets[key], str) and key not in os.environ:
                os.environ[key] = st.secrets[key]


_load_streamlit_secrets_to_env()

from connectors.apim_auth import (
    APIMTokenManager,
    APIMAuthError,
    SessionExpiredError,
    get_or_create_token_manager,
)
from connectors.collibra_auth import CollibraAuthenticator
from connectors.postgres import PostgresSessionManager
from core.collibra_client import CollibraClient
from core.utils import set_state, format_error
from agents.concierge import DataProductConcierge
from models.data_product import DataProductSpec, AssetResult
from components.styles import inject_styles
from components import search_bar, asset_cards, ingredient_label, chapter_form, handoff_summary


def run_async(coro: Coroutine) -> Any:
    """Execute async function in Streamlit sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def initialize_session_state():
    """Initialize all session state defaults."""
    defaults = {
        "step": "auth",
        "token_manager": None,
        "query": "",
        "intent": None,
        "results": [],
        "selected": None,
        "path": None,
        "spec": None,
        "chapter": 1,
        "concierge_msg": "",
        "session_id": str(uuid.uuid4()),
        "errors": [],
        "collibra_client": None,
        "concierge": None,
        "postgres": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def handle_auth():
    """Authenticate and initialize core services."""
    try:
        token_manager = get_or_create_token_manager()
        collibra_auth = CollibraAuthenticator(token_manager)
        collibra_client = CollibraClient(collibra_auth)
        concierge = DataProductConcierge(collibra_client)
        postgres = PostgresSessionManager()

        set_state({
            "token_manager": token_manager,
            "collibra_client": collibra_client,
            "concierge": concierge,
            "postgres": postgres,
            "step": "search",
        })
        st.rerun()
    except APIMAuthError as e:
        st.error("Authentication Failed")
        st.write(f"Unable to connect to data services: {format_error(str(e))}")
        st.info("Contact IT Support: dataplatform-support@company.com")
        if st.button("Retry Authentication"):
            st.rerun()
    except Exception as e:
        st.session_state.errors.append(format_error(str(e)))


def handle_search():
    """Render search interface and process queries."""
    search_bar.render_hero()

    if st.session_state.query:
        try:
            intent = run_async(st.session_state.concierge.interpret_query(st.session_state.query))
            results = run_async(st.session_state.collibra_client.search_assets(intent.search_terms))
            narration = run_async(st.session_state.concierge.narrate_results(results, st.session_state.query))

            set_state({
                "intent": intent,
                "results": results,
                "concierge_msg": narration,
                "step": "results",
            })
            st.rerun()
        except Exception as e:
            st.session_state.errors.append(format_error(str(e)))


def handle_results():
    """Render search results and process selection."""
    asset_cards.render_results(st.session_state.results, st.session_state.concierge_msg)

    if st.session_state.selected:
        try:
            if st.session_state.path == "reuse":
                spec = run_async(st.session_state.collibra_client.fetch_asset_detail(st.session_state.selected))
                set_state({"spec": spec, "step": "path_a"})
            elif st.session_state.path == "remix":
                spec = run_async(st.session_state.collibra_client.fetch_asset_detail(st.session_state.selected))
                set_state({"spec": spec, "step": "path_b", "chapter": 1})
            elif st.session_state.path == "create":
                spec = DataProductSpec(name="", description="", business_purpose="")
                set_state({"spec": spec, "step": "path_c", "chapter": 1})
            st.rerun()
        except Exception as e:
            st.session_state.errors.append(format_error(str(e)))


def handle_reuse():
    """Path A: Reuse asset."""
    try:
        recommendation = run_async(st.session_state.concierge.recommend_path(st.session_state.selected, st.session_state.query))
        ingredient_label.render(st.session_state.spec, recommendation.message)
    except Exception as e:
        st.session_state.errors.append(format_error(str(e)))


def handle_remix():
    """Path B: Remix asset."""
    try:
        chapter_intro = run_async(st.session_state.concierge.introduce_chapter(st.session_state.chapter, "remix", st.session_state.spec))
        chapter_form.render_chapter(st.session_state.chapter, st.session_state.spec, "remix", chapter_intro)

        if st.session_state.get("chapter_action") == "next":
            set_state({"chapter": st.session_state.chapter + 1})
            st.rerun()
        elif st.session_state.get("chapter_action") == "prev":
            set_state({"chapter": max(1, st.session_state.chapter - 1)})
            st.rerun()
        elif st.session_state.get("chapter_action") == "submit":
            set_state({"step": "handoff"})
            st.rerun()
    except Exception as e:
        st.session_state.errors.append(format_error(str(e)))


def handle_create():
    """Path C: Create new asset."""
    try:
        chapter_intro = run_async(st.session_state.concierge.introduce_chapter(st.session_state.chapter, "create", st.session_state.spec))
        chapter_form.render_chapter(st.session_state.chapter, st.session_state.spec, "create", chapter_intro)

        if st.session_state.get("chapter_action") == "next":
            set_state({"chapter": st.session_state.chapter + 1})
            st.rerun()
        elif st.session_state.get("chapter_action") == "prev":
            set_state({"chapter": max(1, st.session_state.chapter - 1)})
            st.rerun()
        elif st.session_state.get("chapter_action") == "submit":
            set_state({"step": "handoff"})
            st.rerun()
    except Exception as e:
        st.session_state.errors.append(format_error(str(e)))


def handle_handoff():
    """Final handoff before submission."""
    try:
        narrative = run_async(st.session_state.concierge.generate_handoff_narrative(st.session_state.spec))
        handoff_summary.render(st.session_state.spec, narrative)

        if st.session_state.get("handoff_action") == "submit":
            collibra_id = run_async(st.session_state.collibra_client.create_or_update_asset(st.session_state.spec))
            run_async(st.session_state.postgres.save_session(st.session_state.session_id, st.session_state.spec, collibra_id))
            set_state({"step": "complete"})
            st.rerun()
        elif st.session_state.get("handoff_action") == "edit":
            set_state({"step": "path_b", "chapter": 5})
            st.rerun()
    except Exception as e:
        st.session_state.errors.append(format_error(str(e)))


def handle_complete():
    """Display completion message."""
    try:
        completion_msg = run_async(st.session_state.concierge.generate_completion_message(st.session_state.spec))
        handoff_summary.render_completion(st.session_state.spec, completion_msg)

        if st.button("Start New Search"):
            for key in list(st.session_state.keys()):
                if key != "step":
                    del st.session_state[key]
            initialize_session_state()
            st.rerun()
    except Exception as e:
        st.session_state.errors.append(format_error(str(e)))


def main():
    """Main orchestrator."""
    st.set_page_config(
        page_title="Data Product Concierge",
        page_icon="✦",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_styles()
    initialize_session_state()

    if st.session_state.errors:
        with st.container():
            st.error(st.session_state.errors[-1])
            if st.button("Clear Error"):
                st.session_state.errors = []
                st.rerun()
        return

    step = st.session_state.step
    if step == "auth":
        handle_auth()
    elif step == "search":
        handle_search()
    elif step == "results":
        handle_results()
    elif step == "path_a":
        handle_reuse()
    elif step == "path_b":
        handle_remix()
    elif step == "path_c":
        handle_create()
    elif step == "handoff":
        handle_handoff()
    elif step == "complete":
        handle_complete()


if __name__ == "__main__":
    main()
