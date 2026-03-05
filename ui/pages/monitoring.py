import streamlit as st
import pandas as pd
from api_client import get_monitoring_alerts, ApiError

st.title("🛡️ Monitoring & Alerts")

# -----------------------
# Sidebar / paramètres
# -----------------------
with st.sidebar:
    st.header("Paramètres")

    window_days = st.slider("Fenêtre (jours)", 1, 30, 7, 1)
    spike_factor = st.slider("Spike factor", 1.0, 10.0, 2.0, 0.5)
    min_negative = st.number_input("Min négatifs pour alerte", min_value=1, max_value=50, value=3, step=1)
    top_k_popular = st.number_input("Top produits populaires", min_value=1, max_value=20, value=5, step=1)

    st.divider()
    st.subheader("Queue")

    page_size = st.selectbox("Taille page", [10, 20, 50, 100], index=1)

    if "queue_page" not in st.session_state:
        st.session_state.queue_page = 0

    colp1, colp2 = st.columns(2)
    with colp1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.queue_page = max(0, st.session_state.queue_page - 1)
    with colp2:
        if st.button("Suivant ➡️", use_container_width=True):
            st.session_state.queue_page += 1

    st.button("🔄 Rafraîchir", use_container_width=True)

queue_offset = st.session_state.queue_page * page_size

# -----------------------
# Chargement API
# -----------------------
params = {
    "window_days": window_days,
    "spike_factor": float(spike_factor),
    "min_negative": int(min_negative),
    "top_k_popular": int(top_k_popular),
    "max_queue": int(page_size),
    "queue_offset": int(queue_offset),
}

try:
    res = get_monitoring_alerts(params)
except ApiError as e:
    st.error(str(e))
    st.stop()

incidents = res.get("incidents", [])
queue = res.get("review_queue", [])
popular = res.get("popular_products", [])

# -----------------------
# Résumé
# -----------------------
c1, c2, c3 = st.columns(3)
c1.metric("Incidents", str(len(incidents)))
c2.metric("Queue (page)", str(len(queue)))
c3.metric("Produits populaires", str(len(popular)))

st.caption(
    f"Fenêtre: {res.get('window_days', window_days)} jours — "
    f"Généré à: {res.get('generated_at', '')} — "
    f"Page queue: {st.session_state.queue_page + 1}"
)

# -----------------------
# Onglets
# -----------------------
tab1, tab2, tab3 = st.tabs(["🚨 Incidents", "🧾 Review Queue", "⭐ Produits populaires"])

# ======================================================================
# TAB 1 : INCIDENTS
# ======================================================================
with tab1:
    if not incidents:
        st.info("Aucun incident détecté sur la période.")
    else:
        inc_rows = []
        for it in incidents:
            details = it.get("details", {}) or {}
            inc_rows.append({
                "produit": it.get("id_produit"),
                "populaire": details.get("is_popular"),
                "sévérité": it.get("severity"),
                "type": it.get("type"),
                "titre": it.get("title"),
                "neg_7j": details.get("neg_last_window"),
                "neg_prev_7j": details.get("neg_prev_window"),
                "delta": details.get("delta"),
                "ratio": details.get("ratio"),
                "count": details.get("count"),
            })



        df_inc = pd.DataFrame(inc_rows)

        # colonnes texte -> "-"
        text_cols = ["type", "titre", "sévérité"]
        for c in text_cols:
            if c in df_inc.columns:
                df_inc[c] = df_inc[c].fillna("-")

        # colonnes numériques -> restent NaN (Arrow OK)
        num_cols = ["produit", "neg_7j", "neg_prev_7j", "delta", "ratio", "count"]
        for c in num_cols:
            if c in df_inc.columns:
                df_inc[c] = pd.to_numeric(df_inc[c], errors="coerce")




        # Populaire en emoji
        df_inc["populaire"] = df_inc["populaire"].apply(
            lambda x: "🟢" if x is True else ("⚪" if x is False else "-")
        )

        # Tri P0 -> P1 -> P2 puis produit
        sev_order = {"P0": 0, "P1": 1, "P2": 2}
        df_inc["sev_rank"] = df_inc["sévérité"].map(lambda x: sev_order.get(x, 9))
        df_inc = df_inc.sort_values(["sev_rank", "produit"]).drop(columns=["sev_rank"])

        # Petite mise en forme : on peut masquer delta/ratio quand pas dispo, mais on garde "-"
        st.dataframe(
            df_inc[["produit", "populaire", "sévérité", "type", "titre", "neg_7j", "neg_prev_7j", "delta", "ratio", "count"]],
            width=None,
            hide_index=True
        )

        st.subheader("Détails & exemples")
        for it in incidents:
            details = it.get("details", {}) or {}
            typ = it.get("type")

            with st.expander(f"{it.get('severity')} — {it.get('title')}"):
                # Texte "lisible" au lieu du JSON brut
                if typ == "volume_spike":
                    st.markdown(
                        f"**Neg 7j:** {details.get('neg_last_window','-')} | "
                        f"**Prev:** {details.get('neg_prev_window','-')} | "
                        f"**Δ:** {details.get('delta','-')} | "
                        f"**Ratio:** {details.get('ratio','-')} | "
                        f"**Populaire:** {'Oui' if details.get('is_popular') else 'Non'}"
                    )
                elif typ == "keyword_severity":
                    kws = details.get("matched_keywords", [])
                    st.markdown(
                        f"**Occurrences:** {details.get('count','-')} | "
                        f"**Mots détectés:** {', '.join(kws) if kws else '-'} | "
                        f"**Populaire:** {'Oui' if details.get('is_popular') else 'Non'}"
                    )
                    examples = details.get("examples", [])
                    if examples:
                        st.write("Exemples :")
                        for ex in examples:
                            st.write(f"- {ex}")

                # Table des samples (si présent)
                samples = details.get("sample_predictions")
                if samples:
                    sdf = pd.DataFrame(samples)
                    st.dataframe(sdf, width=None, hide_index=True)

# ======================================================================
# TAB 2 : REVIEW QUEUE
# ======================================================================
with tab2:
    if not queue:
        st.info("Aucun élément dans la queue sur cette page.")
    else:
        priorities = sorted({q.get("priority", "P2") for q in queue})
        chosen = st.multiselect("Priorité", priorities, default=priorities)

        q_rows = []
        for q in queue:
            if q.get("priority") not in chosen:
                continue
            q_rows.append({
                "priorité": q.get("priority"),
                "score_prio": q.get("priority_score"),
                "id_prediction": q.get("id_prediction"),
                "produit": q.get("id_produit"),
                "label": q.get("label"),
                "confidence": q.get("confidence"),
                "model": q.get("model"),
                "time_stamp": q.get("time_stamp"),
                "avis": (q.get("avis") or "")[:180],
                "raisons": ", ".join(q.get("reasons") or []),
            })

        df_q = pd.DataFrame(q_rows)

        if df_q.empty:
            st.info("Aucun élément correspondant au filtre.")
        else:
            sev_order = {"P0": 0, "P1": 1, "P2": 2}
            df_q["prio_rank"] = df_q["priorité"].map(lambda x: sev_order.get(x, 9))
            df_q = df_q.sort_values(["prio_rank", "score_prio"], ascending=[True, False]).drop(columns=["prio_rank"])

            st.dataframe(df_q, width=None, hide_index=True)

        st.caption("Pagination : utilise la sidebar (Précédent / Suivant).")

# ======================================================================
# TAB 3 : PRODUITS POPULAIRES
# ======================================================================
with tab3:
    if not popular:
        st.info("Aucun produit populaire détecté sur la période.")
    else:
        df_pop = pd.DataFrame(popular).sort_values("total_reviews_7d", ascending=False)
        df_pop = df_pop.rename(columns={
            "id_produit": "produit",
            "total_reviews_7d": "total_7j",
            "positive_7d": "pos_7j",
            "negative_7d": "neg_7j",
            "neutral_7d": "neu_7j",
            "uncertain_7d": "unc_7j",
        })

        st.dataframe(df_pop, width=None, hide_index=True)

        st.subheader("Répartition des labels (Top produits)")
        chart_df = df_pop.set_index("produit")[["pos_7j", "neg_7j", "neu_7j", "unc_7j"]]
        st.bar_chart(chart_df)