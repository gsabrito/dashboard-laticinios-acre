# -*- coding: utf-8 -*-
"""
Dashboard GT Pecuária de Leite — Importação Interestadual de Laticínios pelo Acre
Dados: SEFAZ Acre (NF-e, 2023-2025)
Monolítico: app_render.py
"""
import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import re
from pathlib import Path
from functools import lru_cache
import locale

# ---------------------------------------------------------------------------
# Locale
# ---------------------------------------------------------------------------
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil')
    except:
        pass

# ---------------------------------------------------------------------------
# THEME
# ---------------------------------------------------------------------------
THEME = {
    "primary": "#015f4b",
    "secondary": "#2e86c1",
    "accent": "#f39c12",
    "success": "#1e8449",
    "danger": "#c0392b",
    "light": "#f0f4f8",
    "dark": "#1a252f",
    "text": "#2c3e50",
    "muted": "#7f8c8d",
    "card_bg": "#ffffff",
}

# ---------------------------------------------------------------------------
# Formatação BR
# ---------------------------------------------------------------------------
def format_br(value, decimals=2, prefix="R$ ", suffix=""):
    if value is None or (isinstance(value, float) and value != value):
        return ""
    try:
        v = value / 1e6 if abs(value) >= 1e6 else value
        s = f"{v:,.{decimals}f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return prefix + s + suffix
    except:
        return str(value)


def format_br_clean(value, decimals=2, suffix=""):
    return format_br(value, decimals=decimals, prefix="", suffix=suffix)


def format_br_number(value, decimals=0):
    if value is None or (isinstance(value, float) and value != value):
        return ""
    try:
        s = f"{value:,.{decimals}f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        if decimals == 0:
            s = s.replace(",00", "")
        return s
    except:
        return str(value)


# ---------------------------------------------------------------------------
# Data Loader
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent / "data"

ESPECIE_RULES = [
    (re.compile(r'\bMUSSARELA\b|\bMUSS\b', re.IGNORECASE), "QUEIJO MUSSARELA"),
    (re.compile(r'\bQUEIJO\b.*\bCOALHO\b|\bCOALHO\b', re.IGNORECASE), "QUEIJO COALHO"),
    (re.compile(r'\bQUEIJO\b.*\bRALAD|\bRALAD', re.IGNORECASE), "QUEIJO RALADO"),
    (re.compile(r'\bPARMESAO\b|\bPARMES\b|\bPROVOLONE\b', re.IGNORECASE), "QUEIJO PARMESAO/PROVOLONE"),
    (re.compile(r'\bCREAM\s*CHEESE\b', re.IGNORECASE), "CREAM CHEESE"),
    (re.compile(r'\bCATUPIRY\b', re.IGNORECASE), "CATUPIRY"),
    (re.compile(r'\bRICOTA\b', re.IGNORECASE), "RICOTA"),
    (re.compile(r'\bQUEIJO\b.*\bMINAS\b|\bFRESCAL\b', re.IGNORECASE), "QUEIJO MINAS FRESCAL"),
    (re.compile(r'\bREQUEIJAO\b', re.IGNORECASE), "REQUEIJAO"),
    (re.compile(r'\bIOGURTE\b|\bIOG\b', re.IGNORECASE), "IOGURTE"),
    (re.compile(r'\bBEBIDA\s*LACTEA\b', re.IGNORECASE), "BEBIDA LACTEA"),
    (re.compile(r'\bMANTEIGA\b.*\bGHEE\b|\bGHEE\b', re.IGNORECASE), "MANTEIGA GHEE"),
    (re.compile(r'\bMANTEIGA\b', re.IGNORECASE), "MANTEIGA"),
    (re.compile(r'\bCREME\s*DE\s*LEITE\b', re.IGNORECASE), "CREME DE LEITE"),
    (re.compile(r'\bLEITE\s*CONDENSADO\b|\bLEITE\s*COND\b', re.IGNORECASE), "LEITE CONDENSADO"),
    (re.compile(r'\bLEITE\s*EM\s*PO\b|\bLEITE\s*PO\b|\bLEPO\b|\bMOLICO\b|\bNINHO\b', re.IGNORECASE), "LEITE EM PO"),
    (re.compile(r'\bLEITE\s*UHT\b', re.IGNORECASE), "LEITE UHT"),
    (re.compile(r'\bLEITE\s*INTEGRAL\b|\bLEITE\s*DESNATADO\b|\bLEITE\s*SEMIDESNATADO\b|\bLEITE\s*ZERO\s*LACTOSE\b', re.IGNORECASE), "LEITE LIQUIDO"),
    (re.compile(r'\bSORO\s*DE\s*LEITE\b|\bSORO\b', re.IGNORECASE), "SORO DE LEITE"),
    (re.compile(r'\bCOMPOSTO\s*LACTEO\b', re.IGNORECASE), "COMPOSTO LACTEO"),
    (re.compile(r'\bDOCE\s*DE\s*LEITE\b', re.IGNORECASE), "DOCE DE LEITE"),
    (re.compile(r'\bQUEIJO\b.*\bAZUL\b', re.IGNORECASE), "QUEIJO AZUL"),
    (re.compile(r'\bQUEIJO\b.*\bBRIE\b', re.IGNORECASE), "QUEIJO BRIE"),
    (re.compile(r'\bQUEIJO\b', re.IGNORECASE), "QUEIJO OUTROS"),
    (re.compile(r'\bLEITE\b', re.IGNORECASE), "LEITE OUTROS"),
]


def extract_especie(text):
    if pd.isna(text):
        return "OUTROS"
    s = str(text).upper()
    for regex, label in ESPECIE_RULES:
        if regex.search(s):
            return label
    return "OUTROS"


@lru_cache(maxsize=1)
def load_enriched_data():
    csv_path = DATA_DIR / "dataset.csv"
    csv_gz_path = DATA_DIR / "dataset.csv.gz"
    xlsx_path = DATA_DIR / "dataset.xlsx"

    if csv_gz_path.exists():
        df = pd.read_csv(csv_gz_path, low_memory=False, compression='gzip')
    elif csv_path.exists():
        df = pd.read_csv(csv_path, low_memory=False)
    elif xlsx_path.exists():
        df = pd.read_excel(xlsx_path, sheet_name="DADOS_ENRIQUECIDOS")
    else:
        original = Path(r"D:\Gabriel\laticinios_acre_dataset_enriquecido.xlsx")
        df = pd.read_excel(original, sheet_name="DADOS_ENRIQUECIDOS")

    for c in ["VALOR_PRODUTO", "PESO_TOTAL_KG", "PRECO_POR_KG", "QUANT", "PESO_UNITARIO",
              "PARTICIPACAO_PRODUTO_%", "PARTICIPACAO_UF_%", "HHI_GERAL",
              "INDICE_CONCENTRACAO_CR3_%", "DEMANDA_MENSAL", "DEMANDA_ANUAL",
              "VOLUME_MENSAL_TON", "PESO_TOTAL_TON", "PRECO_POR_UNIDADE",
              "TICKET_MEDIO", "VALOR_POR_KG", "VALOR_POR_LITRO",
              "TAMANHO_EMBALAGEM", "QUANTIDADE_EMBALAGEM", "PARTICIPACAO_SEGMENTO_%"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["DATA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")
    df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce").astype("Int64")
    df["MES"] = pd.to_numeric(df["MES"], errors="coerce").astype("Int64")
    df["PESO_TON"] = df["PESO_TOTAL_KG"] / 1000

    if "PRODUTO" in df.columns:
        df["PRODUTO_ESPECIE"] = df["PRODUTO"].apply(extract_especie)

    for bc in ["PRODUTO_ALTO_VALOR_AGREGADO", "PRODUTO_ALTA_DEPENDENCIA", "TEM_INCONSISTENCIA"]:
        if bc in df.columns:
            df[bc] = df[bc].astype(bool)

    return df


def get_kpis(df):
    return {
        "valor_total_mi": df["VALOR_PRODUTO"].sum() / 1e6,
        "volume_total_ton": df["PESO_TOTAL_KG"].sum() / 1000,
        "ticket_medio": df["VALOR_PRODUTO"].mean(),
        "preco_medio_kg": df["VALOR_PRODUTO"].sum() / max(df["PESO_TOTAL_KG"].sum(), 1),
        "n_produtos": df["PRODUTO"].nunique(),
        "n_ufs": df["UF_EMITENTE"].nunique(),
        "n_transações": len(df),
        "inconsistencias": int(df["TEM_INCONSISTENCIA"].sum()),
        "período_ini": str(df["DATA"].min().strftime("%d/%m/%Y")),
        "período_fim": str(df["DATA"].max().strftime("%d/%m/%Y")),
    }


# ---------------------------------------------------------------------------
# Componentes
# ---------------------------------------------------------------------------
METRIC_LABELS = {"VALOR_PRODUTO": "Valor (R$)", "PESO_TOTAL_KG": "Volume (ton)"}


def kpi_card(title, value, subtitle=None, icon=None, color="primary", id=None):
    color_map = {
        "primary": THEME["primary"],
        "secondary": THEME["secondary"],
        "accent": THEME["accent"],
        "success": THEME["success"],
        "danger": THEME["danger"],
    }
    bar_color = color_map.get(color, THEME["primary"])
    card_kwargs = dict(
        className="h-100 shadow-sm",
        style={"border": "none", "borderRadius": "12px", "backgroundColor": THEME["card_bg"]},
    )
    if id is not None:
        card_kwargs["id"] = id
    return dbc.Card(
        dbc.CardBody([
            html.Div(html.H5(icon or "", className="mb-0", style={"color": bar_color}), className="float-end"),
            html.H6(title, className="card-subtitle mb-1 text-muted",
                    style={"fontSize": "0.8rem", "fontWeight": 600, "textTransform": "uppercase", "letterSpacing": "0.5px"}),
            html.H3(value, className="card-title mb-1",
                    style={"fontWeight": 700, "color": THEME["text"], "fontSize": "1.5rem"}),
            html.Small(subtitle, className="text-muted") if subtitle else None,
            html.Div(style={"height": "4px", "backgroundColor": bar_color, "borderRadius": "2px", "marginTop": "10px"}),
        ]),
        **card_kwargs
    )


def sidebar():
    return dbc.Nav([
        dbc.NavLink([html.I(className="fas fa-home me-2"), "Visão Geral"], href="#/home", active="exact"),
        dbc.NavLink([html.I(className="fas fa-chart-line me-2"), "Tendências"], href="#/tendencias", active="exact"),
        dbc.NavLink([html.I(className="fas fa-sitemap me-2"), "Fluxos"], href="#/fluxos", active="exact"),
        dbc.NavLink([html.I(className="fas fa-exchange-alt me-2"), "Substituição"], href="#/substituicao", active="exact"),
        dbc.NavLink([html.I(className="fas fa-dollar-sign me-2"), "Preços"], href="#/precos", active="exact"),
    ], vertical=True, pills=True, className="flex-column", style={"padding": "12px 6px"})


def filters_bar(df):
    anos = sorted(df["ANO"].dropna().unique().astype(int))
    ufs = sorted(df["UF_EMITENTE"].dropna().unique())
    segs = sorted(df["SEGMENTO_LACTEO"].dropna().unique())
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Select(
                id="filter-ano",
                options=[{"label": "Todos os Anos", "value": "all"}] + [{"label": str(a), "value": a} for a in anos],
                value="all", size="sm",
            ), width=2),
            dbc.Col(dbc.Select(
                id="filter-uf",
                options=[{"label": "Todas as UFs", "value": "all"}] + [{"label": u, "value": u} for u in ufs],
                value="all", size="sm",
            ), width=2),
            dbc.Col(dbc.Select(
                id="filter-seg",
                options=[{"label": "Todos os Segmentos", "value": "all"}] + [{"label": s, "value": s} for s in segs],
                value="all", size="sm",
            ), width=3),
            dbc.Col(dbc.Select(
                id="filter-metric",
                options=[{"label": "Valor (R$)", "value": "VALOR_PRODUTO"}, {"label": "Volume (ton)", "value": "PESO_TOTAL_KG"}],
                value="VALOR_PRODUTO", size="sm",
            ), width=3),
            dbc.Col(dbc.Button("Limpar Filtros", id="btn-clear-filters", color="outline-secondary", size="sm", className="w-100"), width=2),
        ], className="g-2 align-items-center"),
    ], style={
        "backgroundColor": "#fff", "padding": "12px 16px", "borderRadius": "10px",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.06)", "marginBottom": "20px"
    })


def apply_filters(df, ano, uf, seg, metric):
    if ano and str(ano) != "all":
        df = df[df["ANO"] == int(ano)]
    if uf and str(uf) != "all":
        df = df[df["UF_EMITENTE"] == uf]
    if seg and str(seg) != "all":
        df = df[df["SEGMENTO_LACTEO"] == seg]
    return df


def methodology_box(items):
    return dbc.Accordion([
        dbc.AccordionItem([
            html.Ul([
                html.Li([
                    html.Strong(it["termo"] + ": "),
                    it["definição"]
                ], style={"fontSize": "0.82rem", "marginBottom": "6px"})
                for it in items
            ])
        ], title="Conceitos e Metodologia"),
    ], start_collapsed=True, className="mb-3 mt-3", style={"fontSize": "0.85rem"})


# ---------------------------------------------------------------------------
# Premium Charts
# ---------------------------------------------------------------------------
C = {
    "primary": "#015f4b", "secondary": "#2e86c1", "accent": "#f39c12",
    "success": "#1e8449", "danger": "#c0392b", "purple": "#8e44ad",
    "gray": "#7f8c8d", "light": "#ecf0f1", "dark": "#2c3e50", "white": "#ffffff",
}

SEGMENT_COLORS = {
    "LEITES": "#015f4b", "QUEIJOS": "#f39c12", "GORDURAS": "#e74c3c",
    "IOGURTES": "#2e86c1", "CREMES": "#1e8449", "DERIVADOS": "#8e44ad",
    "DOCES_LACTEOS": "#e67e22", "OUTROS": "#95a5a6",
}

POTENTIAL_COLORS = {"ALTO": "#1e8449", "MEDIO": "#f39c12", "BAIXO": "#7f8c8d"}

LAYOUT_BASE = dict(
    template="plotly_white",
    font=dict(family="Inter, -apple-system, sans-serif", size=12, color=C["dark"]),
    plot_bgcolor=C["white"], paper_bgcolor=C["white"],
    margin=dict(l=50, r=30, t=60, b=50), hovermode="closest",
    hoverlabel=dict(bgcolor=C["dark"], font_size=12),
    title=dict(font=dict(size=15, color=C["primary"]), x=0.02),
    legend=dict(font=dict(size=10), orientation="h", y=1.10, x=0.02, bgcolor="rgba(255,255,255,0.8)"),
)


def _apply_base(fig, **kwargs):
    layout = LAYOUT_BASE.copy()
    layout.update(kwargs)
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=C["light"], zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=C["light"], zeroline=False)
    return fig


def choropleth_brasil(df, metric="VALOR_PRODUTO"):
    is_volume = metric == "PESO_TOTAL_KG"
    z_col = "VOLUME_TON" if is_volume else "VALOR_MI"
    z_title = "Volume (ton)" if is_volume else "Share %"
    z_suffix = " ton" if is_volume else "%"

    uf_data = df.groupby("UF_EMITENTE").agg(
        VALOR_MI=("VALOR_PRODUTO", lambda x: x.sum() / 1e6),
        VOLUME_TON=("PESO_TOTAL_KG", lambda x: x.sum() / 1000),
        N_PRODS=("PRODUTO", "nunique"),
    ).reset_index()

    if is_volume:
        total = uf_data["VOLUME_TON"].sum()
        uf_data["SHARE_%"] = (uf_data["VOLUME_TON"] / total * 100).round(1) if total > 0 else 0
    else:
        uf_data["SHARE_%"] = (uf_data["VALOR_MI"] / uf_data["VALOR_MI"].sum() * 100).round(1)

    all_ufs = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
    for uf in all_ufs:
        if uf not in uf_data["UF_EMITENTE"].values:
            uf_data = pd.concat([uf_data, pd.DataFrame([{"UF_EMITENTE": uf, "VALOR_MI": 0, "VOLUME_TON": 0, "N_PRODS": 0, "SHARE_%": 0}])], ignore_index=True)

    fig = go.Figure(data=go.Choropleth(
        geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
        featureidkey="properties.sigla",
        locations=uf_data["UF_EMITENTE"],
        z=uf_data["SHARE_%"],
        colorscale=[[0, "#f0f8ff"], [0.2, "#bdd7e7"], [0.5, "#6baed6"], [0.8, "#3182bd"], [1, "#08519c"]],
        zmin=0, zmax=max(uf_data["SHARE_%"].max(), 1),
        marker_line=dict(color="#34495e", width=0.6),
        colorbar=dict(title=dict(text=z_title, font=dict(size=11)), thickness=12, len=0.6, x=0.93),
        hovertemplate="<b>%{location}</b><br>Share: %{z:.1f}" + z_suffix + "<br>Valor: R$ %{customdata[0]:,.1f} Mi<br>Volume: %{customdata[1]:,.0f} ton<br>Produtos: %{customdata[2]:,}<extra></extra>",
        customdata=uf_data[["VALOR_MI", "VOLUME_TON", "N_PRODS"]].values,
    ))
    fig.update_geos(fitbounds="locations", visible=False, resolution=50,
                    showcoastlines=True, coastlinecolor="#7f8c8d",
                    showcountries=True, countrycolor="#7f8c8d",
                    showsubunits=True, subunitcolor="#bdc3c7")
    fig.add_scattergeo(
        geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
        featureidkey="properties.sigla",
        locations=["AC"], mode="markers",
        marker=dict(size=14, color=C["accent"], symbol="star", line=dict(color="white", width=2)),
        name="Acre (destino)", showlegend=True,
        hovertemplate="<b>Acre</b> — Destino das importações<extra></extra>",
    )
    return _apply_base(fig, height=460, title="Origem das Importações por UF")


def heatmap_sazonal(df, metric="VALOR_PRODUTO"):
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    heat = df.groupby(["ANO", "MES"])[metric].sum().reset_index()
    is_ton = metric == "PESO_TOTAL_KG"
    if is_ton:
        heat["VALOR_MI"] = heat[metric] / 1000
        unidade = "ton"
        cb_title = "Toneladas"
        hovert = "Ano: %{y}<br>Mes: %{x}<br>Volume: %{z:,.0f} ton<extra></extra>"
        title = "Calendário de Demanda (Toneladas) — Ano x Mes"
    else:
        heat["VALOR_MI"] = heat[metric] / 1e6
        unidade = "Mi R$"
        cb_title = "R$ Milhoes"
        hovert = "Ano: %{y}<br>Mes: %{x}<br>Valor: R$ %{z:.1f} Mi<extra></extra>"
        title = "Calendário de Demanda (R$ Milhoes) — Ano x Mes"
    pivot = heat.pivot(index="ANO", columns="MES", values="VALOR_MI").fillna(0)
    pivot.columns = meses[:pivot.shape[1]]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0, "#f7fbff"], [0.33, "#bdd7e7"], [0.66, "#6baed6"], [1, "#08519c"]],
        text=[[f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") for v in row] for row in pivot.values],
        texttemplate="%{text}", textfont=dict(size=11),
        hovertemplate=hovert,
        xgap=2, ygap=2,
        colorbar=dict(title=cb_title, thickness=12, len=0.6),
    ))
    col_avg = pivot.mean(axis=0)
    peak_m = col_avg.idxmax()
    valley_m = col_avg.idxmin()
    fig.add_annotation(x=peak_m, y=pivot.index[-1] + 0.3, text="Pico", showarrow=True,
                       arrowhead=1, arrowcolor=C["accent"], font=dict(size=9, color=C["accent"]), ax=0, ay=-28)
    fig.add_annotation(x=valley_m, y=pivot.index[-1] + 0.3, text="Vale", showarrow=True,
                       arrowhead=1, arrowcolor=C["danger"], font=dict(size=9, color=C["danger"]), ax=0, ay=-28)
    fig.update_xaxes(side="top", title="")
    fig.update_yaxes(title="", dtick=1)
    return _apply_base(fig, height=280, title=title, margin=dict(l=50, r=60, t=60, b=40))


def waterfall_variacao_anual(df, metric="VALOR_PRODUTO"):
    anual = df.groupby("ANO")[metric].sum().reset_index()
    anual["VAR"] = anual[metric].diff()
    anual["VAR_PCT"] = ((anual[metric].pct_change()) * 100).round(1)
    is_ton = metric == "PESO_TOTAL_KG"
    divisor = 1000 if is_ton else 1e6
    unidade = "ton" if is_ton else "R$ Mi"
    fmt_val = lambda v: f"{v/divisor:,.1f}" if is_ton else f"R$ {v/divisor:,.1f}M"

    measures = ["absolute"]
    xs, ys, texts = [f"2023\nBaseline"], [anual[metric].iloc[0]], [fmt_val(anual[metric].iloc[0])]

    for i in range(1, len(anual)):
        measures.append("relative")
        ano_label = str(int(anual["ANO"].iloc[i]))
        var_val = anual["VAR"].iloc[i] / divisor
        sinal = "+" if var_val > 0 else ""
        xs.append(ano_label)
        ys.append(anual["VAR"].iloc[i])
        texts.append(f"{sinal}{var_val:,.1f} " + ("ton" if is_ton else "Mi R$") + f"<br>({anual['VAR_PCT'].iloc[i]:+.1f}%)")

    measures.append("total")
    ano_final = str(int(anual["ANO"].iloc[-1]))
    xs.append(f"{ano_final}\nTotal")
    ys.append(anual[metric].iloc[-1])
    texts.append(fmt_val(anual[metric].iloc[-1]))

    fig = go.Figure(data=go.Waterfall(
        measure=measures, x=xs, y=[y / divisor for y in ys], text=texts, textposition="outside",
        connector=dict(line=dict(color=C["gray"], width=1, dash="dot")),
        increasing=dict(marker=dict(color=C["success"])),
        decreasing=dict(marker=dict(color=C["danger"])),
        totals=dict(marker=dict(color=C["primary"])),
    ))
    title = f"Waterfall: Evolução Anual — {'Volume (ton)' if is_ton else 'Valor (R$ Mi)'}"
    return _apply_base(fig, height=360, title=title,
                       yaxis=dict(title=unidade), showlegend=False)


def evolucao_mensal_premium(df):
    mensal = df.groupby("ANO_MES").agg(
        VALOR_MI=("VALOR_PRODUTO", lambda x: x.sum() / 1e6),
        VOLUME_TON=("PESO_TOTAL_KG", lambda x: x.sum() / 1000),
    ).reset_index()
    mensal["MA3"] = mensal["VALOR_MI"].rolling(3, center=True).mean()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=mensal["ANO_MES"], y=mensal["VOLUME_TON"],
                             mode="none", fill="tozeroy", fillcolor="rgba(243,156,18,0.25)",
                             name="Volume (ton)", yaxis="y2",
                             hovertemplate="Volume: %{y:,.0f} ton<extra></extra>"), secondary_y=True)
    fig.add_trace(go.Scatter(x=mensal["ANO_MES"], y=mensal["MA3"],
                             mode="lines", line=dict(color=C["primary"], width=3),
                             name="Tendencia (MM3)",
                             hovertemplate="Tendencia: R$ %{y:.1f}M<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Bar(x=mensal["ANO_MES"], y=mensal["VALOR_MI"],
                          name="Valor Mensal", marker=dict(color=C["secondary"], opacity=0.7),
                          hovertemplate="Valor: R$ %{y:.1f}M<extra></extra>"), secondary_y=False)

    fig.update_layout(
        yaxis=dict(title=dict(text="R$ Milhoes", font=dict(color=C["primary"]))),
        yaxis2=dict(title=dict(text="Toneladas", font=dict(color=C["secondary"])),
                    overlaying="y", side="right"),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0.02),
    )
    return _apply_base(fig, height=380, title="Evolução Mensal: Valor, Volume e Tendencia")


def scatter_bolhas(df):
    cat_agg = df.groupby("SUBCATEGORIA_PRODUTO").agg(
        VOLUME_TON=("PESO_TOTAL_KG", lambda x: x.sum() / 1000),
        PRECO_MEDIANO=("PRECO_POR_KG", "median"),
        VALOR_MI=("VALOR_PRODUTO", lambda x: x.sum() / 1e6),
        N_UFS=("UF_EMITENTE", "nunique"),
        SEGMENTO=("SEGMENTO_LACTEO", "first"),
    ).reset_index()
    cat_agg = cat_agg[cat_agg["VOLUME_TON"] > 5]

    fig = go.Figure()
    for seg in cat_agg["SEGMENTO"].dropna().unique():
        d = cat_agg[cat_agg["SEGMENTO"] == seg]
        fig.add_trace(go.Scatter(
            x=d["VOLUME_TON"], y=d["PRECO_MEDIANO"],
            mode="markers",
            marker=dict(size=np.sqrt(d["VALOR_MI"].clip(lower=0.5)) * 5,
                        color=SEGMENT_COLORS.get(seg, C["gray"]),
                        opacity=0.7, line=dict(width=1, color="white")),
            text=[n[:30] for n in d["SUBCATEGORIA_PRODUTO"]],
            name=seg,
            hovertemplate="<b>%{text}</b><br>Preco: R$ %{y:.2f}/kg<br>Volume: %{x:,.0f} ton<br>Valor: %{marker.size:.0f} R$ Mi<br>Segmento: " + seg + "<extra></extra>",
        ))

    x_max = cat_agg["VOLUME_TON"].max() * 1.2
    x_min = -max(cat_agg["VOLUME_TON"].max() * 0.05, 10)
    fig.add_hline(y=df["PRECO_POR_KG"].median(), line_dash="dash", line_color=C["gray"],
                  annotation_text=f"Mediana: R$ {df['PRECO_POR_KG'].median():.1f}/kg",
                  annotation_position="top left", annotation_font=dict(size=9, color=C["gray"]))
    return _apply_base(fig, height=460,
                       title="Matriz Volume x Preco Mediano<br><sup style='font-size:10px;color:gray'>(tamanho da bolha = valor total)</sup>",
                       xaxis=dict(title="Volume (toneladas)", range=[x_min, x_max]),
                       yaxis=dict(title="Preco Mediano (R$/kg)"), legend=dict(y=1.05))


def doughnut_top5_ufs(df, periodo="all"):
    if periodo and str(periodo) != "all":
        df = df[df["ANO"] == int(periodo)]

    uf_agg = df.groupby("UF_EMITENTE")["VALOR_PRODUTO"].sum().reset_index()
    uf_agg = uf_agg.sort_values("VALOR_PRODUTO", ascending=False)
    top5 = uf_agg.head(5)
    outros_val = uf_agg.iloc[5:]["VALOR_PRODUTO"].sum()

    labels = top5["UF_EMITENTE"].tolist() + ["Demais"]
    values = top5["VALOR_PRODUTO"].tolist() + [outros_val]
    pcts = [v / sum(values) * 100 for v in values]
    vals_mi = [v / 1e6 for v in values]

    text_display = [f"{p:.1f}%" for p in pcts]

    fig = go.Figure(data=go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=[C["primary"], C["secondary"], C["accent"], C["success"], C["purple"], C["gray"]]),
        text=text_display,
        textfont=dict(size=11), textposition="outside",
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Participacao: %{percent}<extra></extra>",
        sort=False,
    ))
    fig.add_annotation(text=f"Total<br>R$ {sum(values) / 1e6:,.0f}M", x=0.5, y=0.5,
                        font=dict(size=13, color=C["dark"]), showarrow=False)
    periodo_label = str(periodo) if str(periodo) != "all" else "2023-2025"
    return _apply_base(fig, height=420, title=f"Top 5 Estados Fornecedores — {periodo_label}")


def radar_comparacao(df, cat1=None, cat2=None):
    top_cats = df.groupby("SUBCATEGORIA_PRODUTO")["VALOR_PRODUTO"].sum().nlargest(20).index.tolist()
    if cat1 is None:
        cat1 = top_cats[0] if top_cats else None
    if cat2 is None:
        cat2 = top_cats[1] if len(top_cats) > 1 else top_cats[0]

    categories = ["Volume (ton)", "Preco Mediano", "No UFs", "Ticket Medio", "Valor Total (R$ Mi)"]
    metrics = {
        "Volume (ton)": ("PESO_TOTAL_KG", "sum", 1000, ".0f", " ton"),
        "Preco Mediano": ("PRECO_POR_KG", "median", 1, ".2f", " R$/kg"),
        "No UFs": ("UF_EMITENTE", "nunique", 1, ".0f", " UFs"),
        "Ticket Medio": ("VALOR_PRODUTO", "mean", 1, ".2f", " R$"),
        "Valor Total (R$ Mi)": ("VALOR_PRODUTO", "sum", 1e6, ".2f", " Mi R$"),
    }

    fig = go.Figure()
    colors_map = [C["primary"], C["accent"]]
    max_vals = {}
    for cat in [cat1, cat2]:
        if cat is None:
            continue
        g = df[df["SUBCATEGORIA_PRODUTO"] == cat]
        for name, (col, agg, scale, _fmt, _unit) in metrics.items():
            try:
                v = abs(getattr(g[col], agg)() / scale) if len(g) > 0 else 0
            except Exception:
                v = 0
            max_vals[name] = max(max_vals.get(name, 0), v)

    for i, cat in enumerate([cat1, cat2]):
        if cat is None:
            continue
        g = df[df["SUBCATEGORIA_PRODUTO"] == cat]
        values = []
        hover_texts = []
        for name, (col, agg, scale, fmt, unit) in metrics.items():
            try:
                raw = getattr(g[col], agg)() if len(g) > 0 else 0
            except Exception:
                raw = 0
            v = raw / scale
            max_v = max_vals.get(name, 1)
            values.append(abs(v) / max(max_v, 1) if max_v > 0 else 0)
            hover_texts.append(f"{name}: {v:{fmt}}{unit}")

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            name=cat[:35],
            fill="toself",
            line=dict(color=colors_map[i % 2], width=2),
            opacity=0.4,
            meta=hover_texts + [hover_texts[0]],
            hovertemplate="<b>" + cat[:25] + "</b><br>%{meta}<br><i>Eixo normalizado (0-1)</i><extra></extra>",
        ))

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1.05], showticklabels=False)))
    return _apply_base(fig, height=440,
                       title=f"Comparacao (normalizada 0-1): {cat1[:25] if cat1 else ''} vs {cat2[:25] if cat2 else ''}",
                       legend=dict(y=1.02, font=dict(size=10)))


def sankey_flow(df, max_nodes=60, metric="VALOR_PRODUTO"):
    flow = df.groupby(["UF_EMITENTE", "SEGMENTO_LACTEO", "SUBCATEGORIA_PRODUTO"]).agg(
        VALOR=(metric, "sum")).reset_index()
    flow = flow.nlargest(max_nodes, "VALOR")

    is_ton = metric == "PESO_TOTAL_KG"
    unidade = "ton" if is_ton else "R$"
    divisor = 1000 if is_ton else 1e6

    # Ordena cada nivel do maior para o menor (valor total decrescente)
    uf_total = flow.groupby("UF_EMITENTE")["VALOR"].sum()
    ufs = sorted(uf_total.index, key=lambda x: uf_total[x], reverse=True)

    seg_total = flow.groupby("SEGMENTO_LACTEO")["VALOR"].sum()
    segs = sorted(seg_total.index, key=lambda x: seg_total[x], reverse=True)

    cat_total = flow.groupby("SUBCATEGORIA_PRODUTO")["VALOR"].sum()
    cats = sorted(cat_total.index, key=lambda x: cat_total[x], reverse=True)

    labels = ufs + segs + cats
    n_ufs = len(ufs)

    node_colors = []
    for i, lbl in enumerate(labels):
        if i < n_ufs:
            node_colors.append(C["primary"])
        elif i < n_ufs + len(segs):
            node_colors.append(SEGMENT_COLORS.get(lbl, C["gray"]))
        else:
            seg_match = flow[flow["SUBCATEGORIA_PRODUTO"] == lbl]["SEGMENTO_LACTEO"].iloc[0] if lbl in flow["SUBCATEGORIA_PRODUTO"].values else "OUTROS"
            node_colors.append(SEGMENT_COLORS.get(seg_match, C["gray"]))

    source, target, value, link_c = [], [], [], []
    for _, r in flow.iterrows():
        si, ti = labels.index(r["UF_EMITENTE"]), labels.index(r["SEGMENTO_LACTEO"])
        source.append(si)
        target.append(ti)
        value.append(r["VALOR"])
        seg_hex = SEGMENT_COLORS.get(r["SEGMENTO_LACTEO"], C["gray"])
        link_c.append(f"rgba({int(seg_hex[1:3], 16)},{int(seg_hex[3:5], 16)},{int(seg_hex[5:7], 16)},0.2)")

    for _, r in flow.iterrows():
        si, ti = labels.index(r["SEGMENTO_LACTEO"]), labels.index(r["SUBCATEGORIA_PRODUTO"])
        source.append(si)
        target.append(ti)
        value.append(r["VALOR"])
        seg_hex = SEGMENT_COLORS.get(r["SEGMENTO_LACTEO"], C["gray"])
        link_c.append(f"rgba({int(seg_hex[1:3], 16)},{int(seg_hex[3:5], 16)},{int(seg_hex[5:7], 16)},0.5)")

    hover_link = "%{source.label} → %{target.label}<br>" + unidade + " %{value:,.0f}<extra></extra>"

    fig = go.Figure(data=go.Sankey(
        node=dict(pad=18, thickness=18, line=dict(color="rgba(0,0,0,0.15)", width=0.8),
                  label=labels, color=node_colors,
                  hovertemplate="%{label}<br>Fluxo: " + unidade + " %{value:,.0f}<extra></extra>"),
        link=dict(source=source, target=target, value=value, color=link_c,
                  hovertemplate=hover_link),
    ))
    titulo = f"Fluxo Interestadual ({'Volume (ton)' if is_ton else 'Valor (R$)'}): Origem → Segmento → Categoria"
    return _apply_base(fig, height=520, title=titulo)


def gauge_dependencia(df):
    pot_data = df.groupby("POTENCIAL_SUBSTITUICAO")["VALOR_PRODUTO"].sum()
    substituivel = pot_data.get("ALTO", 0) + pot_data.get("MEDIO", 0)
    total = pot_data.sum()
    pct = (substituivel / total * 100) if total > 0 else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        title={"text": "Índice de Substituibilidade (%)"},
        delta={"reference": 60},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": C["success"] if pct > 50 else C["accent"] if pct > 30 else C["danger"]},
            "steps": [
                {"range": [0, 30], "color": "rgba(192,57,43,0.15)"},
                {"range": [30, 60], "color": "rgba(243,156,18,0.15)"},
                {"range": [60, 100], "color": "rgba(30,132,73,0.15)"},
            ],
            "threshold": {"line": {"color": C["accent"], "width": 3}, "thickness": 0.75, "value": 60},
        },
        number={"suffix": "%", "font": {"size": 22, "color": C["primary"]}},
    ))
    return _apply_base(fig, height=300, title="Potencial de Substituição de Importações")


def bump_chart_ufs(df, top_n=8):
    ranking = df.groupby(["ANO_MES", "UF_EMITENTE"])["VALOR_PRODUTO"].sum().reset_index()
    ranking["RANK"] = ranking.groupby("ANO_MES")["VALOR_PRODUTO"].rank(ascending=False, method="first")
    top_ufs = ranking[ranking["RANK"] <= top_n]
    uf_colors = {u: px.colors.qualitative.Set2[i % 8] for i, u in enumerate(top_ufs["UF_EMITENTE"].unique())}

    fig = go.Figure()
    for uf in top_ufs["UF_EMITENTE"].unique():
        d = top_ufs[top_ufs["UF_EMITENTE"] == uf].sort_values("ANO_MES")
        fig.add_trace(go.Scatter(
            x=d["ANO_MES"], y=d["RANK"], mode="lines+markers", name=uf,
            line=dict(color=uf_colors.get(uf, C["gray"]), width=2.5, shape="spline"),
            marker=dict(size=8, symbol="circle"),
            hovertemplate=f"<b>{uf}</b><br>Rank: %{{y:.0f}}<br>Mes: %{{x}}<extra></extra>",
        ))
    fig.update_yaxes(autorange="reversed", tickmode="linear", dtick=1, title="Ranking")
    return _apply_base(fig, height=400, title="Ranking Evolutivo: Top 8 UFs ao Longo do Tempo",
                       legend=dict(orientation="v", y=0.5, x=1.01))


def parallel_coordinates(df, top_n=5):
    cat_agg = df.groupby(["SUBCATEGORIA_PRODUTO", "SEGMENTO_LACTEO"]).agg(
        VOLUME_TON=("PESO_TOTAL_KG", lambda x: x.sum() / 1000),
        PRECO_MEDIANO=("PRECO_POR_KG", "median"),
        VALOR_MI=("VALOR_PRODUTO", lambda x: x.sum() / 1e6),
        N_UFS=("UF_EMITENTE", "nunique"),
        N_PRODS=("PRODUTO", "nunique"),
        SHARE=("PARTICIPACAO_SEGMENTO_%", "mean"),
    ).reset_index()
    cat_agg = cat_agg.nlargest(top_n, "VALOR_MI").reset_index(drop=True)

    seg_list = sorted(cat_agg["SEGMENTO_LACTEO"].unique())
    distinct_colors = ["#015f4b", "#f39c12", "#e74c3c", "#2e86c1", "#8e44ad", "#1e8449", "#e67e22"]
    seg_map_color = {s: distinct_colors[i % len(distinct_colors)] for i, s in enumerate(seg_list)}
    cat_agg["COLOR_HEX"] = cat_agg["SEGMENTO_LACTEO"].map(seg_map_color)

    dims = ["Categoria", "Volume", "Preco/kg", "No UFs", "No Produtos", "Share %"]
    raw_cols = ["VOLUME_TON", "PRECO_MEDIANO", "N_UFS", "N_PRODS", "SHARE"]

    for d in raw_cols:
        minv, maxv = cat_agg[d].min(), cat_agg[d].max()
        if maxv > minv:
            cat_agg[d + "_norm"] = ((cat_agg[d] - minv) / (maxv - minv) * 10).round(1)
        else:
            cat_agg[d + "_norm"] = 0

    cat_idx = {c: i for i, c in enumerate(cat_agg["SUBCATEGORIA_PRODUTO"])}
    cat_agg["CAT_IDX"] = cat_agg["SUBCATEGORIA_PRODUTO"].map(cat_idx)

    fig = go.Figure(data=go.Parcoords(
        line=dict(color=cat_agg["COLOR_HEX"].tolist(),
                  showscale=True,
                  colorbar=dict(title="Segmento", thickness=12, x=1.05,
                                tickvals=list(range(len(seg_list))),
                                ticktext=seg_list)),
        dimensions=[
            dict(label=dims[0], values=cat_agg["CAT_IDX"], range=[0, len(cat_agg) - 1],
                 tickvals=list(cat_idx.values()), ticktext=[c[:20] for c in cat_idx.keys()]),
            dict(label=dims[1], values=cat_agg["VOLUME_TON_norm"], range=[0, 10],
                 tickvals=[0, 5, 10], ticktext=["Baixo", "Medio", "Alto"]),
            dict(label=dims[2], values=cat_agg["PRECO_MEDIANO_norm"], range=[0, 10],
                 tickvals=[0, 5, 10], ticktext=["Baixo", "Medio", "Alto"]),
            dict(label=dims[3], values=cat_agg["N_UFS_norm"], range=[0, 10],
                 tickvals=[0, 5, 10], ticktext=["Poucos", "Medio", "Muitos"]),
            dict(label=dims[4], values=cat_agg["N_PRODS_norm"], range=[0, 10],
                 tickvals=[0, 5, 10], ticktext=["Poucos", "Medio", "Muitos"]),
            dict(label=dims[5], values=cat_agg["SHARE_norm"], range=[0, 10],
                 tickvals=[0, 5, 10], ticktext=["Baixo", "Medio", "Alto"]),
        ],
        labelfont=dict(size=10, color=C["dark"]),
    ))
    return _apply_base(fig, height=460,
                       title="Perfil Multi-dimensional: Top 5 Categorias (cor = segmento)",
                       margin=dict(l=80, r=120, t=80, b=60))


def _make_top10_table(df, agrupar_por="Produto"):
    if agrupar_por == "Segmento":
        col = "SEGMENTO_LACTEO"
    elif agrupar_por == "Categoria":
        col = "SUBCATEGORIA_PRODUTO"
    elif agrupar_por == "Subcategoria":
        col = "SUBCATEGORIA_PRODUTO"
    else:
        col = "PRODUTO"

    agg = df.groupby(col).agg(
        VALOR_MI=("VALOR_PRODUTO", lambda x: x.sum() / 1e6),
        VOLUME_TON=("PESO_TOTAL_KG", lambda x: x.sum() / 1000),
    ).reset_index()
    agg["PRECO_MEDIO"] = agg["VALOR_MI"] * 1e6 / (agg["VOLUME_TON"] * 1000).clip(lower=0.01)
    agg = agg.nlargest(10, "VALOR_MI").reset_index(drop=True)

    rows = []
    for i, r in agg.iterrows():
        rows.append(html.Tr([
            html.Td(str(i + 1), style={"fontSize": "0.82rem", "fontWeight": 600, "textAlign": "center"}),
            html.Td(str(r[col])[:55], style={"fontSize": "0.82rem"}),
            html.Td(format_br_clean(r["VALOR_MI"], 1), style={"fontSize": "0.82rem", "textAlign": "right"}),
            html.Td(format_br_clean(r["VOLUME_TON"], 0), style={"fontSize": "0.82rem", "textAlign": "right"}),
            html.Td(format_br_clean(r["PRECO_MEDIO"], 2), style={"fontSize": "0.82rem", "textAlign": "right"}),
        ]))

    return dbc.Table([
        html.Thead(html.Tr([
            html.Th("Rank", style={"fontSize": "0.78rem"}),
            html.Th(agrupar_por, style={"fontSize": "0.78rem"}),
            html.Th("Valor (Mi R$)", style={"fontSize": "0.78rem", "textAlign": "right"}),
            html.Th("Volume (t)", style={"fontSize": "0.78rem", "textAlign": "right"}),
            html.Th("Preco (R$/kg)", style={"fontSize": "0.78rem", "textAlign": "right"}),
        ])),
        html.Tbody(rows)
    ], striped=True, hover=True, size="sm", style={"backgroundColor": "#fff", "borderRadius": "10px"})


def _tabela_parcoords(df, top_n=5):
    cat_agg = df.groupby(["SUBCATEGORIA_PRODUTO", "SEGMENTO_LACTEO"]).agg(
        VALOR_MI=("VALOR_PRODUTO", lambda x: x.sum() / 1e6),
        VOLUME_TON=("PESO_TOTAL_KG", lambda x: x.sum() / 1000),
        PRECO_MEDIANO=("PRECO_POR_KG", "median"),
        N_UFS=("UF_EMITENTE", "nunique"),
    ).reset_index().nlargest(top_n, "VALOR_MI")
    rows = []
    for _, r in cat_agg.iterrows():
        rows.append(html.Tr([
            html.Td(str(r["SUBCATEGORIA_PRODUTO"])[:30], style={"fontSize": "0.75rem"}),
            html.Td(format_br_clean(r["VALOR_MI"], 1), style={"fontSize": "0.75rem", "textAlign": "right"}),
            html.Td(format_br_clean(r["VOLUME_TON"], 0), style={"fontSize": "0.75rem", "textAlign": "right"}),
            html.Td(format_br_clean(r["PRECO_MEDIANO"], 1), style={"fontSize": "0.75rem", "textAlign": "right"}),
            html.Td(f"{int(r['N_UFS'])}", style={"fontSize": "0.75rem", "textAlign": "center"}),
        ]))
    return dbc.Table([
        html.Thead(html.Tr([
            html.Th("Categoria", style={"fontSize": "0.75rem"}),
            html.Th("Valor (Mi R$)", style={"fontSize": "0.75rem", "textAlign": "right"}),
            html.Th("Volume (t)", style={"fontSize": "0.75rem", "textAlign": "right"}),
            html.Th("Preco (R$/kg)", style={"fontSize": "0.75rem", "textAlign": "right"}),
            html.Th("UFs", style={"fontSize": "0.75rem", "textAlign": "center"}),
        ])),
        html.Tbody(rows)
    ], striped=True, hover=True, size="sm", style={"backgroundColor": "#fff", "borderRadius": "10px"})


# ---------------------------------------------------------------------------
# Paginas — Funcoes de layout
# ---------------------------------------------------------------------------
def _render_home(df, metric="VALOR_PRODUTO"):
    kpis = get_kpis(df)
    return [
        dbc.Row([
            dbc.Col(kpi_card("Valor Total Importado (R$ Mi)", format_br_clean(kpis['valor_total_mi'], 1),
                               f"{format_br_number(kpis['n_transações'], 0)} transações",
                               icon=html.I(className="fas fa-sack-dollar"), color="primary"), width=3),
            dbc.Col(kpi_card("Volume Total (ton)", format_br_clean(kpis['volume_total_ton'], 0),
                               "Peso total em toneladas",
                               icon=html.I(className="fas fa-weight-hanging"), color="secondary"), width=3),
            dbc.Col(kpi_card("Ticket Medio (R$)", format_br_clean(kpis['ticket_medio'], 0),
                               "Por transação NF-e",
                               icon=html.I(className="fas fa-receipt"), color="accent"), width=3),
            dbc.Col(kpi_card("Preco Medio (R$/kg)", format_br_clean(kpis['preco_medio_kg'], 2),
                               "Ponderado por volume",
                               icon=html.I(className="fas fa-tag"), color="success"), width=3),
        ], className="g-3 mb-4"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=choropleth_brasil(df, metric), config={"displayModeBar": False}), width=12),
        ], className="g-3 mb-4"),
        dbc.Row([
            dbc.Col([
                html.Label("Agrupar por:", style={"fontWeight": 600, "fontSize": "0.85rem"}),
                dcc.Dropdown(
                    id="home-top10-agrup",
                    options=[
                        {"label": "Segmento", "value": "Segmento"},
                        {"label": "Categoria", "value": "Categoria"},
                        {"label": "Subcategoria", "value": "Subcategoria"},
                        {"label": "Produto", "value": "Produto"},
                    ],
                    value="Produto",
                    clearable=False,
                    style={"maxWidth": "280px", "marginBottom": "12px"},
                ),
                html.H5("Top 10 Produtos Mais Importados", className="mb-2",
                        style={"fontWeight": 600, "color": "#015f4b"}),
                html.Div(id="home-top10-table", children=_make_top10_table(df, "Produto")),
            ], width=12),
        ], className="g-3 mb-4"),
    ]


def render_home(df):
    return html.Div([
        html.H2("Visão Geral", className="mb-1", style={"fontWeight": 700, "color": "#015f4b"}),
        html.P(f"{df['DATA'].min().strftime('%d/%m/%Y')} a {df['DATA'].max().strftime('%d/%m/%Y')}"
               f" | {format_br_number(len(df), 0)} registros | {format_br_number(df['PRODUTO'].nunique(), 0)} produtos",
               className="text-muted mb-4", style={"fontSize": "0.85rem"}),
        filters_bar(df),
        html.Div(id="home-content", children=_render_home(df)),
        methodology_box([
            {"termo": "Ticket Medio", "definição": "Valor medio por transação (NF-e). Indica o poder aquisitivo típico de cada operação e ajuda a dimensionar o mercado."},
            {"termo": "Preco Medio Ponderado", "definição": "Calculado dividindo o valor total importado pelo volume total (kg). Reflete o preço real médio pago, considerando todos os lotes."},
            {"termo": "Share (Participacao)", "definição": "Percentual que cada UF fornecedora representa no valor total importado pelo Acre. Calculado como o valor da UF dividido pelo valor total."},
            {"termo": "NF-e", "definição": "Nota Fiscal Eletrônica de Entrada. Documento fiscal digital obrigatório para movimentação interestadual de mercadorias. Fonte: SEFAZ/AC."},
            {"termo": "Mapa Coropletico", "definição": "Mapa do Brasil onde cada estado é colorido proporcionalmente à sua participação (share) nas importações do Acre. Tons mais escuros indicam maior share. A estrela laranja marca o Acre como destino."},
            {"termo": "Top 10 Produtos", "definição": "Ranking dos 10 produtos/categorias/segmentos mais importados por valor total. O agrupamento pode ser alterado para diferentes níveis de agregação: Segmento (família ampla), Categoria/Subcategoria (agrupamento técnico-comercial) ou Produto (nível NF-e)."},
        ]),
    ])


def _render_tendencias(df, metric="VALOR_PRODUTO"):
    return [
        dbc.Row([
            dbc.Col(dcc.Graph(figure=waterfall_variacao_anual(df, metric), config={"displayModeBar": False}), width=6),
            dbc.Col(dcc.Graph(figure=heatmap_sazonal(df, metric), config={"displayModeBar": False}), width=6),
        ], className="g-3 mb-4"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=evolucao_mensal_premium(df), config={"displayModeBar": False}), width=12),
        ], className="g-3 mb-4"),
    ]


def render_tendencias(df):
    return html.Div([
        html.H2("Tendências e Sazonalidade", className="mb-4", style={"fontWeight": 700, "color": "#015f4b"}),
        filters_bar(df),
        html.Div(id="tendencias-content", children=_render_tendencias(df)),
        methodology_box([
            {"termo": "Média Móvell (MM)", "definição": "Técnica que suaviza picos e vales calculando a média de um período deslizante. Reduz o ruído e revela a direção da tendência. A linha verde (MM3) mostra a tendência dos últimos 3 meses."},
            {"termo": "Waterfall (Cascata)", "definição": "Gráfico que mostra o efeito cumulativo de variações positivas (verde) e negativas (vermelho) sobre um valor-base (baseline). A barra inicial é o valor de 2023, e cada barra seguinte mostra a variação (aumento ou queda) em relação ao ano anterior."},
            {"termo": "Baseline", "definição": "Valor de referência inicial (2023) contra o qual as variações dos anos seguintes são comparadas. Serve como ponto de partida para medir o crescimento ou retração."},
            {"termo": "Sazonalidade", "definição": "Padroes de demanda que se repetem em períodos especificos do ano. O heatmap (calendário de demanda) identifica meses de pico e vale nas importações de laticinios, permitindo antecipar necessidades de estoque e logistica."},
            {"termo": "Evolução Mensal", "definição": "Gráfico combinado que mostra barras (valor mensal em R$), linha verde (tendência MM3) e área sombreada laranja (volume em toneladas). Permite visualizar simultaneamente a evolução do valor e do volume ao longo do tempo, identificando se o crescimento é puxado por preço ou quantidade."},
            {"termo": "Heatmap / Calendário de Demanda", "definição": "Matriz Ano x Mês onde cada célula mostra o valor importado em R$ milhões. Quanto mais escura a cor, maior o valor. Permite identificar padrões sazonais (ex: meses de festas juninas, final de ano) e comparar o mesmo mês entre diferentes anos."},
        ]),
    ])


def _render_fluxos(df, metric="VALOR_PRODUTO"):
    anos_opts = [{"label": "Todos (2023-2025)", "value": "all"}] + [
        {"label": str(int(a)), "value": int(a)} for a in sorted(df["ANO"].dropna().unique().astype(int))
    ]
    try:
        fig_sankey = sankey_flow(df, metric=metric)
    except Exception as e:
        fig_sankey = go.Figure().add_annotation(text=f"ERRO SANKY: {e}", showarrow=False)
    try:
        fig_donut = doughnut_top5_ufs(df, "all")
    except Exception as e:
        fig_donut = go.Figure().add_annotation(text=f"ERRO DONUT: {e}", showarrow=False)
    try:
        fig_bump = bump_chart_ufs(df)
    except Exception as e:
        fig_bump = go.Figure().add_annotation(text=f"ERRO BUMP: {e}", showarrow=False)
    return [
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_sankey, config={"displayModeBar": False}), width=12),
        ], className="g-3 mb-4"),
        dbc.Row([
            dbc.Col([
                html.Label("Selecione o período:", style={"fontWeight": 600, "fontSize": "0.85rem", "marginBottom": "6px"}),
                dcc.Dropdown(id="donut-periodo", options=anos_opts, value="all",
                             clearable=False, style={"marginBottom": "10px", "maxWidth": "250px"}),
                dcc.Graph(id="donut-graph", figure=fig_donut, config={"displayModeBar": False}),
            ], width=5),
            dbc.Col(dcc.Graph(figure=fig_bump, config={"displayModeBar": False}), width=7),
        ], className="g-3 mb-4"),
    ]


def render_fluxos(df):
    return html.Div([
        html.H2("Fluxos Interestaduais", className="mb-4", style={"fontWeight": 700, "color": "#015f4b"}),
        filters_bar(df),
        html.Div(id="fluxos-content", children=_render_fluxos(df)),
        methodology_box([
            {"termo": "Sankey Diagram", "definição": "Visualização de fluxos onde a largura das faixas é proporcional ao valor movimentado. Mostra a cadeia completa: UF de origem (estado fornecedor) -> Segmento (família ampla do produto) -> Categoria (tipo especifico). As cores dos nos indicam o segmento do produto."},
            {"termo": "Donut (Rosca)", "definição": "Gráfico de pizza com centro vazio mostrando a participação percentual dos 5 maiores estados fornecedores. O valor no centro e o total importado no período. A categoria 'Demais' agrupa todos os outros estados para simplificar a visualização."},
            {"termo": "Bump Chart", "definição": "Gráfico de evolução do ranking ao longo do tempo. Cada linha colorida representa um estado. Linhas mais baixas (ranking 1, 2, 3...) indicam melhores posições. O gráfico usa spline para suavizar as transições entre posições, permitindo identificar tendências de ganho ou perda de mercado."},
            {"termo": "Ranking", "definição": "Ordenação dos estados fornecedores pelo valor importado em cada mês. Permite identificar quais estados estão ganhando ou perdendo participação no mercado acreano ao longo do tempo. Um estado que sobe no ranking está aumentando sua importância relativa como fornecedor."},
        ]),
    ])


def _render_substituicao(df, metric="VALOR_PRODUTO"):
    pot = df.groupby("POTENCIAL_SUBSTITUICAO")["VALOR_PRODUTO"].sum()
    total = max(pot.sum(), 1)
    pcts = {k: v / total * 100 for k, v in pot.items()}

    alto = df[df["POTENCIAL_SUBSTITUICAO"] == "ALTO"].groupby("SUBCATEGORIA_PRODUTO").agg(
        VALOR_MI=("VALOR_PRODUTO", lambda x: x.sum() / 1e6),
        VOLUME_TON=("PESO_TOTAL_KG", lambda x: x.sum() / 1000),
        PRECO_MEDIO=("PRECO_POR_KG", "median"),
        N_UFS=("UF_EMITENTE", "nunique"),
    ).reset_index().nlargest(10, "VALOR_MI")

    rows = []
    for _, r in alto.iterrows():
        rows.append(html.Tr([
            html.Td(str(r["SUBCATEGORIA_PRODUTO"])[:40], style={"fontSize": "0.82rem"}),
            html.Td(format_br_clean(r["VALOR_MI"], 1), style={"fontSize": "0.82rem", "textAlign": "right"}),
            html.Td(format_br_clean(r["VOLUME_TON"], 0), style={"fontSize": "0.82rem", "textAlign": "right"}),
            html.Td(format_br_clean(r["PRECO_MEDIO"], 1), style={"fontSize": "0.82rem", "textAlign": "right"}),
            html.Td(f"{int(r['N_UFS'])}", style={"fontSize": "0.82rem", "textAlign": "center"}),
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Categoria"),
            html.Th("Valor (Mi R$)", style={"textAlign": "right"}),
            html.Th("Volume (t)", style={"textAlign": "right"}),
            html.Th("Preco (R$/kg)", style={"textAlign": "right"}),
            html.Th("UFs", style={"textAlign": "center"}),
        ])),
        html.Tbody(rows)
    ], striped=True, hover=True, size="sm", style={"backgroundColor": "#fff", "borderRadius": "10px"})

    return [
        dbc.Row([
            dbc.Col(kpi_card("ALTO Potencial (R$ Mi)", format_br_clean(pot.get('ALTO', 0) / 1e6, 1),
                               f"{(pcts.get('ALTO', 0)):.1f}% do total".replace(".", ","), color="success"), width=4),
            dbc.Col(kpi_card("MEDIO Potencial (R$ Mi)", format_br_clean(pot.get('MEDIO', 0) / 1e6, 1),
                               f"{(pcts.get('MEDIO', 0)):.1f}% do total".replace(".", ","), color="accent"), width=4),
            dbc.Col(kpi_card("BAIXO Potencial (R$ Mi)", format_br_clean(pot.get('BAIXO', 0) / 1e6, 1),
                               f"{(pcts.get('BAIXO', 0)):.1f}% do total".replace(".", ","), color="secondary"), width=4),
        ], className="g-3 mb-4"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=gauge_dependencia(df), config={"displayModeBar": False}), width=4),
            dbc.Col(html.Div([
                html.H5("Top 10 Categorias com ALTO Potencial", className="mb-2",
                        style={"color": "#015f4b", "fontWeight": 600}),
                table,
            ]), width=8),
        ], className="g-3 mb-4"),
    ]


def render_substituicao(df):
    return html.Div([
        html.H2("Potencial de Substituição de Importações", className="mb-4",
                style={"fontWeight": 700, "color": "#015f4b"}),
        filters_bar(df),
        html.Div(id="substituicao-content", children=_render_substituicao(df)),
        methodology_box([
            {"termo": "Potencial de Substituição", "definição": "Classificação baseada na logística e volume de cada produto. Mede o percentual do volume importado que vem de estados considerados 'distantes' (SP, RJ, MG, RS, SC, PR, ES, BA, PE, GO). ALTO: >50% do volume de estados distantes E volume total acima da mediana. MEDIO: >30% de estados distantes. BAIXO: restante. IMPORTANTE: esta métrica não mede capacidade produtiva local — apenas o potencial logístico-econômico de substituição. Produtos com ALTO potencial sao candidatos prioritários para substituição por produção local."},
            {"termo": "Índice de Substituibilidade (Gauge)", "definição": "Indicador principal desta aba. Mostra o percentual do valor total importado classificado como ALTO ou MÉDIO potencial de substituição. Quanto maior o percentual, maior a parcela das importações que teoricamente poderia ser substituída por produção local. O gauge (velocímetro) tem três zonas: verde (acima de 60%, alta substituibilidade), amarelo (30-60%, moderada) e vermelho (abaixo de 30%, baixa). A linha de referência em 60% é uma meta sugerida. O valor numérico no centro do gauge mostra o percentual atual."},
            {"termo": "Alto Valor Agregado", "definição": "Produtos cujo preço/kg está acima do percentil 80 (top 20% mais caros) de toda a base. Sua substituição gera maior retenção de renda no estado, pois são produtos de maior valor unitário."},
            {"termo": "Alta Dependencia", "definição": "Produtos onde mais de 75% do valor importado provém dos estados distantes listados acima. Indica vulnerabilidade da cadeia de abastecimento — se houver interrupção no fornecimento desses estados, o Acre teria dificuldade em obter esses produtos de fontes alternativas."},
            {"termo": "Top 10 ALTO Potencial", "definição": "Tabela que lista as 10 categorias de produtos com maior potencial de substituicao (classificação ALTO), ordenadas por valor total importado. Para cada categoria, mostra o valor em milhoes de reais, o volume em toneladas, o preco medio por kg e o número de estados fornecedores. Quanto menos UFs fornecedoras, maior a dependencia e mais urgente a substituicao."},
            {"termo": "Segmento vs Categoria", "definição": "Segmento e a família ampla do produto (ex: QUEIJOS, LEITES, GORDURAS). Categoria e o agrupamento técnico-comercial mais especifico (ex: QUEIJO MUSSARELA, LEITE UHT). A análise de substituicao e feita no nivel de categoria, pois diferentes categorias têm diferentes dinâmicas de produção e logística."},
        ]),
    ])


def _render_precos(df, metric="VALOR_PRODUTO", cat_opts=None, c1=None, c2=None):
    try:
        fig_scatter = scatter_bolhas(df)
    except Exception as e:
        fig_scatter = go.Figure().add_annotation(text=f"ERRO SCATTER: {e}", showarrow=False)
    try:
        fig_radar = radar_comparacao(df, c1, c2) if c1 and c2 else go.Figure().add_annotation(text="Selecione 2 categorias", showarrow=False)
    except Exception as e:
        fig_radar = go.Figure().add_annotation(text=f"ERRO RADAR: {e}", showarrow=False)
    return [
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_scatter, config={"displayModeBar": False}), width=7),
            dbc.Col([
                html.Label("Comparar categorias:", style={"fontWeight": 600, "fontSize": "0.82rem", "marginBottom": "4px"}),
                dcc.Dropdown(id="radar-cat1", options=cat_opts or [], value=c1,
                             clearable=False, style={"marginBottom": "6px", "fontSize": "0.8rem"}),
                dcc.Dropdown(id="radar-cat2", options=cat_opts or [], value=c2,
                             clearable=False, style={"marginBottom": "6px", "fontSize": "0.8rem"}),
                dcc.Graph(id="radar-graph", figure=fig_radar, config={"displayModeBar": False}),
            ], width=5),
        ], className="g-3 mb-4"),
    ]


def render_precos(df):
    top20 = df.groupby("SUBCATEGORIA_PRODUTO")["VALOR_PRODUTO"].sum().nlargest(20).index.tolist()
    cat_opts = [{"label": c[:45], "value": c} for c in top20]
    c1 = top20[0] if top20 else None
    c2 = top20[1] if len(top20) > 1 else c1
    return html.Div([
        html.H2("Inteligência de Preços e Valor Agregado", className="mb-4",
                style={"fontWeight": 700, "color": "#015f4b"}),
        filters_bar(df),
        html.Div(id="precos-content", children=_render_precos(df, "VALOR_PRODUTO", cat_opts, c1, c2)),
        methodology_box([
            {"termo": "Preco Mediano", "definição": "Valor central dos preços observados (divide a amostra ao meio). Menos sensível a outliers (valores extremos) do que a média aritmética. Utilizado no eixo vertical do gráfico de bolhas e na tabela de valores reais."},
            {"termo": "Matriz Volume x Preco (Bolhas)", "definição": "Cada bolha representa uma categoria de produto. Eixo horizontal (X): volume total importado em toneladas. Eixo vertical (Y): preço mediano em R$/kg. Tamanho da bolha: valor total importado (R$). A cor indica o segmento do produto. Produtos no canto superior direito tem alto volume e alto preço (grandes e valiosos). Produtos no canto inferior esquerdo tem baixo volume e baixo preço (pequenos e baratos). A linha tracejada horizontal mostra a mediana geral de preços."},
            {"termo": "Subtitle explicativo", "definição": "O subtítulo '(tamanho da bolha = valor total)' abaixo do titulo do gráfico de bolhas explica que bolhas maiores representam categorias com maior valor total importado, independentemente da posição nos eixos."},
            {"termo": "Radar / Spider Chart", "definição": "Comparação multivariada entre duas categorias selecionadas nos dropdowns. Os eixos são: Volume (ton), Preço Mediano (R$/kg), Número de UFs fornecedoras, Ticket Medio (R$) e Valor Total (R$ Mi). Cada eixo é normalizado para escala 0-1 para permitir comparação justa entre métricas de unidades diferentes. Passe o mouse sobre os pontos para ver os valores reais. A categoria com área maior tem desempenho superior na maioria das métricas."},
            {"termo": "Normalizado (norm)", "definição": "Valor ajustado para escala 0-1 dentro de cada dimensão. O valor 0 representa o menor valor entre as duas categorias comparadas e 1 o maior. Serve apenas para visualização comparativa — os valores reais aparecem no hover (ao passar o mouse)."},
            {"termo": "Share %", "definição": "Participação percentual média da categoria no seu segmento. Indica o peso relativo da categoria dentro da sua família de produtos. Um share alto significa que a categoria domina seu segmento."},
            {"termo": "QUEIJO FRESCO — composição", "definição": "Inclui: REQUEIJÃO (cremoso, light, bisnaga, copo), RICOTA (fresca, defumada, temperada), CREAM CHEESE (Catupiry, Philadelphia, cream cheese tradicional), PETIT SUISSE (Chambinho, Polenguinho, Frutapinho, Danoninho, Nuvolat, Batavinho) e QUEIJO FRESCO genérico (Burrata, Queijo de Búfala, Creme Quark). São produtos de alta umidade, não maturados, consumo rápido."},
            {"termo": "QUEIJO OUTROS — composição", "definição": "Categoria residual que agrupa queijos que não se enquadram nas classificações mais específicas (Mussarela, Parmesão, Coalho, Minas, Prato, Brie, Gouda, Reino, Estepe, Cottage, Provolone, Azul, Ralado, Processado). Inclui queijos artesanais regionais, misturas lácteas com queijo, e produtos com descrição genérica de 'queijo' sem identificação precisa do tipo."},
        ]),
    ])


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
print("[INIT] Carregando dataset...")
df_global = load_enriched_data()
print(f"[INIT] Dataset carregado: {len(df_global):,} linhas")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
                suppress_callback_exceptions=True)
app.title = "GT Pecuaria de Leite — Importacao de Laticinios | Acre"
server = app.server

app.layout = dbc.Container([
    dcc.Store(id="theme-store", data="light"),
    dcc.Location(id="url", refresh=False),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Img(src="/assets/faeac-branco.png",
                         style={"width": "42%", "margin": "8px auto", "display": "block"}),
                html.H4("Laticinios Acre", className="text-white text-center py-1 mb-0",
                        style={"fontWeight": 700, "fontSize": "1.1rem"}),
                html.P("GT Pecuaria de Leite",
                       className="text-white-50 text-center mb-0",
                       style={"fontSize": "0.65rem", "letterSpacing": "1px"}),
                html.Hr(style={"borderColor": "rgba(255,255,255,0.2)", "margin": "8px 16px"}),
                sidebar(),
                html.Hr(style={"borderColor": "rgba(255,255,255,0.2)", "margin": "8px 16px"}),
                html.Div([
                    html.Small("Importacao Interestadual", className="text-white-50 d-block text-center"),
                    html.Small("de Laticinios pelo Acre", className="text-white-50 d-block text-center"),
                    html.Small("2023-2025", className="text-white-50 d-block text-center"),
                    html.Small("Fonte: SEFAZ/AC (NF-e)", className="text-white-50 d-block text-center mt-1",
                               style={"fontSize": "0.6rem", "opacity": "0.5"}),
                ], className="mt-auto pb-3 text-center"),
            ], style={"height": "100vh", "backgroundColor": THEME["primary"],
                      "position": "sticky", "top": 0, "display": "flex", "flexDirection": "column"}),
        ], width=2, className="p-0"),

        dbc.Col([
            html.Div([
                html.Div(id="page-content"),
                html.Footer(
                    html.Div([
                        html.Hr(style={"margin": "8px 0"}),
                        html.Small(
                            "Dados: Secretaria de Estado da Fazenda do Acre (SEFAZ/AC) — "
                            "Notas Fiscais Eletronicas de Entrada | Período: 2023-2025 | "
                            "Desenvolvido no ambito do GT Pecuaria de Leite",
                            className="text-muted d-block text-center",
                            style={"padding": "8px", "fontSize": "0.68rem"}),
                    ]),
                ),
            ], style={"padding": "24px 24px 0 24px", "backgroundColor": "#f4f6f9", "minHeight": "100vh"})
        ], width=10, className="p-0"),
    ], className="g-0"),
], fluid=True, className="p-0")


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
@app.callback(
    Output("page-content", "children"),
    Input("url", "hash"),
)
def display_page(hash_):
    if not hash_:
        hash_ = "#/home"
    df = load_enriched_data()
    if hash_ == "#/home" or hash_ == "#/" or hash_ == "":
        return render_home(df)
    elif hash_ == "#/tendencias":
        return render_tendencias(df)
    elif hash_ == "#/fluxos":
        return render_fluxos(df)
    elif hash_ == "#/substituicao":
        return render_substituicao(df)
    elif hash_ == "#/precos":
        return render_precos(df)
    return render_home(df)


@app.callback(
    Output("home-content", "children"),
    Input("filter-ano", "value"), Input("filter-uf", "value"),
    Input("filter-seg", "value"), Input("filter-metric", "value"),
)
def update_home(ano, uf, seg, metric):
    if None in (ano, uf, seg, metric):
        return dash.no_update
    df = load_enriched_data()
    return _render_home(apply_filters(df, ano, uf, seg, metric), metric)


@app.callback(
    Output("home-top10-table", "children"),
    Input("home-top10-agrup", "value"),
    Input("filter-ano", "value"), Input("filter-uf", "value"),
    Input("filter-seg", "value"), Input("filter-metric", "value"),
)
def update_home_top10(agrup, ano, uf, seg, metric):
    if None in (ano, uf, seg, metric, agrup):
        return dash.no_update
    df = load_enriched_data()
    df_f = apply_filters(df, ano, uf, seg, metric)
    return _make_top10_table(df_f, agrup)


@app.callback(
    Output("tendencias-content", "children"),
    Input("filter-ano", "value"), Input("filter-uf", "value"),
    Input("filter-seg", "value"), Input("filter-metric", "value"),
)
def update_tendencias(ano, uf, seg, metric):
    if None in (ano, uf, seg, metric):
        return dash.no_update
    df = load_enriched_data()
    return _render_tendencias(apply_filters(df, ano, uf, seg, metric), metric)


@app.callback(
    Output("fluxos-content", "children"),
    Input("filter-ano", "value"), Input("filter-uf", "value"),
    Input("filter-seg", "value"), Input("filter-metric", "value"),
)
def update_fluxos(ano, uf, seg, metric):
    if None in (ano, uf, seg, metric):
        return dash.no_update
    df = load_enriched_data()
    return _render_fluxos(apply_filters(df, ano, uf, seg, metric), metric)


@app.callback(
    Output("donut-graph", "figure"),
    Input("donut-periodo", "value"),
    Input("filter-ano", "value"), Input("filter-uf", "value"),
    Input("filter-seg", "value"), Input("filter-metric", "value"),
    prevent_initial_call=False,
)
def update_donut(periodo, ano, uf, seg, metric):
    if None in (periodo, ano, uf, seg, metric):
        return dash.no_update
    df = load_enriched_data()
    df_f = apply_filters(df, ano, uf, seg, metric)
    return doughnut_top5_ufs(df_f, periodo)


@app.callback(
    Output("substituicao-content", "children"),
    Input("filter-ano", "value"), Input("filter-uf", "value"),
    Input("filter-seg", "value"), Input("filter-metric", "value"),
)
def update_substituicao(ano, uf, seg, metric):
    if None in (ano, uf, seg, metric):
        return dash.no_update
    df = load_enriched_data()
    return _render_substituicao(apply_filters(df, ano, uf, seg, metric), metric)


@app.callback(
    Output("precos-content", "children"),
    Input("filter-ano", "value"), Input("filter-uf", "value"),
    Input("filter-seg", "value"), Input("filter-metric", "value"),
)
def update_precos(ano, uf, seg, metric):
    if None in (ano, uf, seg, metric):
        return dash.no_update
    df = load_enriched_data()
    df_f = apply_filters(df, ano, uf, seg, metric)
    top20 = df_f.groupby("SUBCATEGORIA_PRODUTO")["VALOR_PRODUTO"].sum().nlargest(20).index.tolist()
    cat_opts = [{"label": c[:45], "value": c} for c in top20]
    c1 = top20[0] if top20 else None
    c2 = top20[1] if len(top20) > 1 else c1
    return _render_precos(df_f, metric, cat_opts, c1, c2)


@app.callback(
    Output("radar-graph", "figure"),
    Input("radar-cat1", "value"), Input("radar-cat2", "value"),
    Input("filter-ano", "value"), Input("filter-uf", "value"),
    Input("filter-seg", "value"), Input("filter-metric", "value"),
    prevent_initial_call=False,
)
def update_radar(cat1, cat2, ano, uf, seg, metric):
    if not cat1 or not cat2:
        return dash.no_update
    df = load_enriched_data()
    df_f = apply_filters(df, ano, uf, seg, metric)
    return radar_comparacao(df_f, cat1, cat2)


# ---------------------------------------------------------------------------
# Clientside callback — limpar filtros
# ---------------------------------------------------------------------------
app.clientside_callback(
    """
    function(n) {
        if (!n) return window.dash_clientside.no_update;
        return ["all", "all", "all", "VALOR_PRODUTO"];
    }
    """,
    [
        Output("filter-ano", "value"),
        Output("filter-uf", "value"),
        Output("filter-seg", "value"),
        Output("filter-metric", "value"),
    ],
    Input("btn-clear-filters", "n_clicks"),
    prevent_initial_call=True,
)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False, port=8050)
