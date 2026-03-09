import os
import requests
import streamlit as st
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


def _get(path: str, params: dict | None = None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def _post(path: str, json: dict):
    r = requests.post(f"{API_URL}{path}", json=json, timeout=60)
    r.raise_for_status()
    return r.json()

def get_all_produits():
    return _get("/GetAllProduit")

def get_produit(id_produit: int):
    return _get(f"/GetProduit/{id_produit}")

def predict_public(payload: dict):
    return _post("/PredictPublic", json=payload)

if "view" not in st.session_state:
    st.session_state.view = "catalogue"
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "toast" not in st.session_state:
    st.session_state.toast = None

def goto(view: str, pid: int | None = None):
    st.session_state.view = view
    st.session_state.selected_id = pid
    st.rerun()


st.set_page_config(page_title="Vannel Shop", page_icon="🛍️", layout="wide")

st.markdown(
    """
<style>
/* background */
.stApp {
  background: radial-gradient(1200px 600px at 20% 10%, rgba(59,130,246,0.16), transparent 60%),
              radial-gradient(900px 500px at 85% 30%, rgba(168,85,247,0.14), transparent 55%),
              linear-gradient(180deg, rgba(15,23,42,0.03), rgba(255,255,255,1));
}

/* typography */
h1, h2, h3 { letter-spacing: -0.02em; }
.small-muted { color: rgba(15,23,42,0.6); font-size: 0.95rem; }

/* topbar */
.topbar {
  display:flex; align-items:center; justify-content:space-between;
  padding: 18px 22px;
  border: 1px solid rgba(15,23,42,0.08);
  border-radius: 18px;
  background: rgba(255,255,255,0.65);
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 25px rgba(15,23,42,0.06);
  margin-bottom: 18px;
}
.brand { font-weight: 800; font-size: 1.2rem; display:flex; gap:10px; align-items:center; }
.badge {
  font-size: 0.78rem; padding: 4px 10px; border-radius: 999px;
  border: 1px solid rgba(15,23,42,0.12);
  background: rgba(255,255,255,0.7);
}

/* product card */
.card {
  border: 1px solid rgba(15,23,42,0.08);
  border-radius: 18px;
  background: rgba(255,255,255,0.8);
  box-shadow: 0 14px 30px rgba(15,23,42,0.06);
  overflow: hidden;
  transition: transform .18s ease, box-shadow .18s ease;
}
.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 22px 40px rgba(15,23,42,0.10);
}
.card-img {
  padding: 14px;
  background: linear-gradient(180deg, rgba(15,23,42,0.03), rgba(255,255,255,0));
}
.card-title { font-weight: 800; font-size: 1.05rem; margin-top: 6px; }
.card-desc { color: rgba(15,23,42,0.68); font-size: 0.92rem; line-height: 1.35; }
.price { font-weight: 800; font-size: 1.05rem; }
.kpis { display:flex; gap:10px; flex-wrap:wrap; margin-top: 8px; }
.kpi {
  font-size: 0.80rem; padding: 6px 10px; border-radius: 999px;
  border: 1px solid rgba(15,23,42,0.10);
  background: rgba(255,255,255,0.75);
}

/* buttons */
.stButton > button {
  border-radius: 14px !important;
  padding: 0.55rem 0.85rem !important;
  font-weight: 700 !important;
}

/* hero section */
.hero {
  display:flex; gap:16px; align-items:stretch; justify-content:space-between;
  padding: 18px 18px;
  border: 1px solid rgba(15,23,42,0.08);
  border-radius: 22px;
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(12px);
  box-shadow: 0 18px 45px rgba(15,23,42,0.08);
  margin-bottom: 14px;
}
.hero-left { flex: 1.4; padding: 6px; }
.hero-right { flex: 1; display:flex; }
.hero-kicker {
  display:inline-block; font-weight:700; font-size:0.85rem; padding: 6px 10px;
  border-radius: 999px; background: rgba(59,130,246,0.10);
  border: 1px solid rgba(59,130,246,0.18); color: rgba(30,64,175,0.95);
}
.hero-title { font-size: 2.0rem; font-weight: 900; margin-top: 10px; line-height: 1.1; }
.hero-sub { color: rgba(15,23,42,0.72); margin-top: 10px; font-size: 1.02rem; line-height: 1.35; }
.hero-card {
  flex:1; border-radius: 18px; border: 1px solid rgba(15,23,42,0.10);
  background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(168,85,247,0.10));
  padding: 16px; display:flex; flex-direction:column; justify-content:center;
}
.hero-card-title { font-weight: 900; font-size: 1.1rem; }
.hero-card-sub { color: rgba(15,23,42,0.70); margin-top: 6px; }
.hero-pillrow { display:flex; gap:8px; flex-wrap:wrap; margin-top: 10px; }
.hero-pill {
  padding: 6px 10px; border-radius: 999px; background: rgba(255,255,255,0.70);
  border: 1px solid rgba(15,23,42,0.10); font-weight: 700; font-size: 0.85rem;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.reveal { animation: fadeUp .35s ease both; }
</style>
""",
    unsafe_allow_html=True,
)


left, right = st.columns([1.2, 1.0])
with left:
    st.markdown(
        """
<div class="topbar">
  <div class="brand">🛍️ Vannel Shop <span class="badge">Contactez moi</span></div>
  <div class="small-muted">Avis clients → analyse automatique → monitoring côté ops</div>
</div>
""",
        unsafe_allow_html=True,
    )


if st.session_state.toast:
    st.toast(st.session_state.toast, icon="✅")
    st.session_state.toast = None


try:
    produits = get_all_produits()
except Exception as e:
    st.error(f"Impossible de charger les produits : {e}")
    st.stop()

dfp = pd.DataFrame(produits)
popular_set = {1,2,4,5,7}

if dfp.empty:
    st.warning("Aucun produit en base.")
    st.stop()

PRICES = [200,50,0,50,150,899.99,599,8000,30,50,15,15,10]
#costume,baryon,bonheur,ssj3,gtavi,pcgamer,ps5,voiture,imposteur,halter,basket,lego,cable

def price_of(pid: int) -> float:
    i = pid - 1
    if 0 <= i < len(PRICES):
        return float(PRICES[i])
    return 19.99


if st.session_state.view == "catalogue":

    st.markdown(
        """
    <div class="hero">
    <div class="hero-left">
        <div class="hero-kicker">Nouveautés • Sélection du moment</div>
        <div class="hero-title">Trouvez votre prochain produit coup de cœur ✨</div>
        <div class="hero-sub">
        Parcourez le catalogue, ouvrez une fiche produit, laissez un avis.
        <b>Livraison rapide</b> • <b>Retour 14 jours</b>.
        </div>
    </div>
    <div class="hero-right">
        <div class="hero-card">
        <div class="hero-card-title">🔥 Produits tendances</div>
        <div class="hero-card-sub">Découvrez ce que les clients adorent cette semaine.</div>
        <div class="hero-pillrow">
            <span class="hero-pill">Jeux</span>
            <span class="hero-pill">Accessoires</span>
            <span class="hero-pill">Jouets</span>
        </div>
        </div>
    </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("## Catalogue produits")
    q = st.text_input("Rechercher dans les descriptions", "")

    df_show = dfp.copy()
    if q.strip():
        df_show = df_show[df_show["detail"].str.contains(q, case=False, na=False)]

    st.caption(f"{len(df_show)} produit(s)")

    cols = st.columns(3, gap="large")
    for i, row in df_show.reset_index(drop=True).iterrows():
        pid = int(row["id_produit"])
        lien = row.get("lien", "")
        detail = str(row.get("detail", "") or "")
        desc = detail[:140] + ("…" if len(detail) > 140 else "")

        badge_html = '<div class="badge">🔥 Populaire</div>' if pid in popular_set else '<div></div>'

        with cols[i % 3]:
            st.markdown('<div class="card reveal">', unsafe_allow_html=True)

            st.markdown('<div class="card-img">', unsafe_allow_html=True)
            if isinstance(lien, str) and lien:
                st.image(lien, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div style="padding: 14px 16px 16px;">', unsafe_allow_html=True)
            st.markdown(f'<div class="card-title">Produit #{pid}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-desc">{desc}</div>', unsafe_allow_html=True)
            
            st.markdown(
                f"""
<div style="display:flex; align-items:center; justify-content:space-between; margin-top:10px;">
  <div class="price">{price_of(pid):.2f} €</div>
  {badge_html}
</div>
""",
                unsafe_allow_html=True,
            )

            st.markdown(
                """
<div class="kpis">
  <div class="kpi">🔒 Paiement sécurisé</div>
  <div class="kpi">↩️ Retour 14j</div>
  <div class="kpi">🚚 Livraison 48h</div>
</div>
""",
                unsafe_allow_html=True,
            )

            if st.button("Voir détails", key=f"see_{pid}", type="primary", use_container_width=True):
                goto("detail", pid)

            st.markdown("</div></div>", unsafe_allow_html=True)


else:
    pid = st.session_state.selected_id
    if pid is None:
        goto("catalogue")

    colA, colB = st.columns([0.25, 0.75])
    with colA:
        if st.button("⬅️ Retour", use_container_width=True):
            goto("catalogue")

    try:
        produit = get_produit(int(pid))
    except Exception as e:
        st.error(f"Impossible de charger le produit #{pid} : {e}")
        st.stop()

    lien = produit.get("lien", "")
    detail = str(produit.get("detail", "") or "")

    st.markdown(f"## Produit #{pid}")
    st.caption("Laisse un avis anonyme : le système analyse automatiquement le sentiment.")

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        with st.container(border=True):
            if isinstance(lien, str) and lien:
                st.image(lien, use_container_width=True)
            st.markdown("**Description**")
            st.write(detail)
            st.markdown(f"**Prix** : {price_of(int(pid)):.2f} €")
            st.markdown("**Badges** : 🔒 sécurisé • ↩️ retour 14j • 🚚 48h")

    with right:
        with st.container(border=True):
            st.subheader("✍️ Laisser un avis")
            avis = st.text_area("Votre avis", height=140, placeholder="Ex: Super qualité, livraison rapide…")

            if st.button("Envoyer", type="primary", disabled=not avis.strip(), use_container_width=True):
                try:
                    predict_public({"id_produit": int(pid), "avis": avis.strip()})
                    st.session_state.toast = "Merci ! Votre avis a bien été enregistré"
                    goto("catalogue") 
                except Exception as e:
                    st.error(f"Erreur lors de l'envoi : {e}")

        st.info("ℹ️ Pour le monitoring/alerting (incidents, queue), voir le backoffice.")

    st.divider()
    if st.button("⬅️ Retour au catalogue", use_container_width=True):
        goto("catalogue")