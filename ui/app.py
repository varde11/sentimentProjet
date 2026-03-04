import streamlit as st
import pandas as pd

from api_client import (
    get_all_produits,
    get_produit,
    get_all_clients,
    
    get_predictions_by_produit,
    get_predictions_by_client,
    predict,
    PredictPublic,
    get_uncertain_predictions,
    update_label
    
)

st.set_page_config(page_title="Sentiment E-commerce", page_icon="🛒", layout="wide")


# -Session state init 
if "nav" not in st.session_state:
    st.session_state.nav = "Catalogue"

if "selected_product_id" not in st.session_state:
    st.session_state.selected_product_id = None

if "nav_request" not in st.session_state:
    st.session_state.nav_request = None


def goto(page: str):
    """Navigation safe: on demande un changement de page, appliqué au prochain rerun."""
    st.session_state.nav_request = page
    st.rerun()



if st.session_state.nav_request is not None:
    st.session_state.nav = st.session_state.nav_request
    st.session_state.nav_request = None


# --------------------- Sidebar ---
st.sidebar.title("🛒 Sentiment E-commerce")


st.sidebar.radio(
    "Navigation",
    ["Catalogue", "Produit", "Review Queue"],
    key="nav",
)

page = st.session_state.nav


# --------------------- Helpers -----
def label_badge(label: str) -> str:
    colors = {
        "negative": "#ef4444",
        "neutral": "#6b7280",
        "positive": "#22c55e",
        "uncertain": "#f59e0b",
    }
    c = colors.get(label, "#3b82f6")
    return (
        f"<span style='background:{c};color:white;padding:4px 10px;"
        f"border-radius:999px;font-size:13px'>{label}</span>"
    )


def show_predictions_table(preds):
    if not preds:
        st.info("Aucune prédiction.")
        return

    df = pd.DataFrame(preds)

    cols_pref = [
        "time_stamp",
        "id_prediction",
        "id_produit",
        "label",
        "confidence",
        "model",
        "avis",
    ]
    cols = [c for c in cols_pref if c in df.columns] + [c for c in df.columns if c not in cols_pref]
    st.dataframe(df[cols], use_container_width=True)


# --------------------- Page: Catalogue ---------------------
if page == "Catalogue":
    st.markdown("## 🛍️ Catalogue produits")
    st.caption("Choisis un produit, laisse un avis, et suis l’historique des prédictions.")

    try:
        produits = get_all_produits()
    except Exception as e:
        st.error(f"Impossible de charger les produits : {e}")
        st.stop()

    dfp = pd.DataFrame(produits)
    if dfp.empty:
        st.warning("Aucun produit en base.")
        st.stop()

    q = st.text_input("Rechercher dans les descriptions", "")
    if q.strip():
        dfp = dfp[dfp["detail"].str.contains(q, case=False, na=False)]

    cols = st.columns(3, gap="large")
    for i, row in dfp.reset_index(drop=True).iterrows():
        with cols[i % 3]:
            with st.container(border=True):
                if "lien" in row and isinstance(row["lien"], str) and row["lien"]:
                    st.image(row["lien"], use_container_width=True)

                st.write(f"**Produit #{int(row['id_produit'])}**")
                st.write(row.get("detail", ""))

                if st.button("Voir produit", key=f"view_{int(row['id_produit'])}"):
                    st.session_state.selected_product_id = int(row["id_produit"])
                    goto("Produit")


# --------------------- Page: Produit ---------------------
elif page == "Produit":
    st.markdown("## 📦 Produit")

    
    try:
        produits = get_all_produits()
    except Exception as e:
        st.error(f"Impossible de charger les produits : {e}")
        st.stop()

    dfp = pd.DataFrame(produits)
    if dfp.empty:
        st.warning("Aucun produit en base.")
        st.stop()

    
    default_index = 0
    if st.session_state.selected_product_id is not None:
        matches = dfp.index[dfp["id_produit"] == st.session_state.selected_product_id].tolist()
        if matches:
            default_index = matches[0]

    product_labels = dfp.apply(
        lambda r: f"{int(r['id_produit'])} — {str(r.get('detail', ''))[:55]}",
        axis=1,
    ).tolist()

    chosen = st.selectbox(
        "Choisir un produit",
        options=list(range(len(dfp))),
        format_func=lambda idx: product_labels[idx],
        index=default_index,
    )

    id_produit = int(dfp.iloc[chosen]["id_produit"])
    st.session_state.selected_product_id = id_produit

    
    produit = get_produit(id_produit)

    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        with st.container(border=True):
            st.subheader(f"Produit #{id_produit}")
            lien = produit.get("lien") or dfp.iloc[chosen].get("lien")
            if lien:
                st.image(lien, use_container_width=True)
            st.write(produit.get("detail", ""))

        

        # clients = get_all_clients()
        # dfc = pd.DataFrame(clients)
        # if dfc.empty:
        #     st.warning("Aucun client en base.")
        #     st.stop()

        # dfc["label_ui"] = dfc.apply(
        #     lambda r: f"{int(r['id_client'])} — {r.get('nom','')} ({r.get('langue','')})",
        #     axis=1,
        # )

        # client_idx = st.selectbox(
        #     "Client",
        #     options=list(range(len(dfc))),
        #     format_func=lambda i: dfc.iloc[i]["label_ui"],
        # )
        # id_client = int(dfc.iloc[client_idx]["id_client"])



        st.markdown("### ✍️ Laisser un avis")
        avis = st.text_area("Avis", height=120, placeholder="Écris un avis sur le produit…")
        st.caption("Le backend utilise TF-IDF (rapide) et bascule sur XLM-R si besoin.")

        if st.button("Analyser & enregistrer", type="primary", disabled=not avis.strip()):
            try:
                res = PredictPublic({"id_produit": id_produit, "avis": avis})
                st.success("Prédiction enregistrée ✅")

                st.markdown("### Résultat")
                st.markdown(label_badge(res.get("label", "")), unsafe_allow_html=True)

                conf = float(res.get("confidence", 0.0) or 0.0)
                st.progress(min(max(conf, 0.0), 1.0))
                st.write(f"**Confiance :** {conf:.2f}")
                st.write(f"**Modèle :** {res.get('model')}")

                raw = res.get("raw_probs")
                if isinstance(raw, dict):
                    st.bar_chart(pd.DataFrame({"proba": raw}))
            except Exception as e:
                st.error(f"Erreur pendant la prédiction : {e}")

    with right:
        with st.container(border=True):
            st.subheader("📚 Historique du produit")

            label_filter = st.selectbox(
                "Filtrer l'historique",
                ["all", "negative", "neutral", "positive", "uncertain"],
                index=0,
            )

            preds = get_predictions_by_produit(id_produit)
            if label_filter != "all":
                preds = [p for p in preds if p.get("label") == label_filter]

            show_predictions_table(preds)


# --------------------- Page: Clients ---------------------
# elif page == "Clients":
#     st.markdown("## 👤 Clients")

#     clients = get_all_clients()
#     dfc = pd.DataFrame(clients)
#     if dfc.empty:
#         st.info("Aucun client.")
#         st.stop()

#     dfc["label_ui"] = dfc.apply(
#         lambda r: f"{int(r['id_client'])} — {r.get('nom','')} ({r.get('langue','')})",
#         axis=1,
#     )

#     idx = st.selectbox(
#         "Choisir un client",
#         options=list(range(len(dfc))),
#         format_func=lambda i: dfc.iloc[i]["label_ui"],
#     )
#     id_client = int(dfc.iloc[idx]["id_client"])

#     st.subheader("Historique des prédictions")
#     preds = get_predictions_by_client(id_client)
#     show_predictions_table(preds)




#-----Page: Review Queue ---
elif page == "Review Queue":
    st.markdown("## 🧑‍⚖️ Review Queue — Incertains: La page est toujours en cours de développemnt")

    preds = get_uncertain_predictions()
    if not preds:
        st.success("Aucune prédiction uncertain 🎉")
        st.stop()
    
    
    st.caption("Valide une prédiction uncertain en choisissant un label final.")
    df = pd.DataFrame(preds)
    st.dataframe(df, use_container_width=True)

    st.markdown("### ✅ Valider une prédiction")
    id_prediction = st.number_input("id_prediction", min_value=1, step=1)
    label = st.selectbox("Label final", ["negative", "neutral", "positive"])

    if st.button("Valider", type="primary"):
        try:
            update_label(int(id_prediction), label)
            st.success(f"Prédiction #{id_prediction} mise à jour → {label}")
            st.info("Recharge de la file…")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")
