import streamlit as st
import pandas as pd
from weasyprint import HTML

st.set_page_config(page_title="Gestione Report Eventi", layout="wide")

st.title("📊 Gestione & Report Eventi")

# 1. SIDEBAR: Parametri Generali del Mese
st.sidebar.header("⚙️ Parametri Mese")
mese_anno = st.sidebar.text_input("Mese e Anno di Riferimento", value="Gennaio 2026")
fatturato_totale = st.sidebar.number_input("Fatturato Totale Mensile (€)", value=47527.50, step=100.0)
cene_spettacolo = st.sidebar.number_input("Fatturato Cene Spettacolo (€)", value=19010.98, step=100.0)

# 2. SEZIONE INSERIMENTO EVENTI
st.subheader("🗓️ Inserimento Eventi Privati & Corporate")

# Tabella interattiva modificabile dall'utente
if "df_eventi" not in st.session_state:
    # Dati di esempio pre-compilati
    st.session_state.df_eventi = pd.DataFrame([
        {"Data": "04/01/2026", "Cliente": "SORRENTINO", "Tipologia": "Battesimo", "Fatturato": 2000.00, "Stato": "SALDATO"},
        {"Data": "04/01/2026", "Cliente": "CAPUTO", "Tipologia": "Festa di Laurea", "Fatturato": 2820.00, "Stato": "SALDATO"},
        {"Data": "08-09/01/2026", "Cliente": "FIN.RENT", "Tipologia": "Evento Aziendale / Coffee Break", "Fatturato": 160.00, "Stato": "SALDATO"},
        {"Data": "14/01/2026", "Cliente": "D'ALESSANDRO", "Tipologia": "Festa Privata (40° Compleanno)", "Fatturato": 1280.00, "Stato": "SALDATO"},
        {"Data": "18/01/2026", "Cliente": "ESPOSITO", "Tipologia": "Festa Privata (1° Compleanno)", "Fatturato": 1330.00, "Stato": "SALDATO"},
        {"Data": "19-20/01/2026", "Cliente": "MAXTRIS", "Tipologia": "Evento Aziendale / Coffee Break", "Fatturato": 850.00, "Stato": "SALDATO"},
        {"Data": "27/01/2026", "Cliente": "ESPOSITO", "Tipologia": "Festa Privata (80° Compleanno)", "Fatturato": 450.00, "Stato": "SALDATO"},
        {"Data": "31/01/2026", "Cliente": "ABBATE", "Tipologia": "Festa Privata (1° Compleanno)", "Fatturato": 2300.00, "Stato": "SALDATO"},
    ])

edited_df = st.data_editor(
    st.session_state.df_eventi, 
    num_rows="dynamic",
    use_container_width=True
)

# 3. CALCOLI AUTOMATICI
totale_eventi = edited_df["Fatturato"].sum() if not edited_df.empty else 0.0
num_eventi = len(edited_df)
spicciolata = max(0.0, fatturato_totale - cene_spettacolo - totale_eventi)

perc_cene = (cene_spettacolo / fatturato_totale * 100) if fatturato_totale > 0 else 0
perc_spicciolata = (spicciolata / fatturato_totale * 100) if fatturato_totale > 0 else 0
perc_eventi = (totale_eventi / fatturato_totale * 100) if fatturato_totale > 0 else 0

st.markdown("---")
st.subheader("📈 Anteprima Indicatori")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Fatturato Totale", f"€ {fatturato_totale:,.2f}")
col2.metric("Cene Spettacolo", f"€ {cene_spettacolo:,.2f}", f"{perc_cene:.2f}%")
col3.metric("Spicciolata / Ord.", f"€ {spicciolata:,.2f}", f"{perc_spicciolata:.2f}%")
col4.metric("Eventi Privati/Corp", f"€ {totale_eventi:,.2f}", f"{perc_eventi:.2f}% ({num_eventi} Eventi)")

# 4. GENERATORE PDF CON FUNZIONE DI CACHE
st.markdown("---")

# Memorizziamo in cache la generazione per evitare ricalcoli inutili
# Se i parametri in input non cambiano, restituisce istantaneamente il PDF precedente.
@st.cache_data
def genera_pdf_cached(edited_df_dict, mese_anno, fatturato_totale, cene_spettacolo, totale_eventi, num_eventi, spicciolata, perc_cene, perc_spicciolata, perc_eventi):
    # Ripristiniamo il DataFrame dal dizionario della cache
    df = pd.DataFrame(edited_df_dict)
    
    rows_html = ""
    for _, row in df.iterrows():
        rows_html += f"""
        <tr>
            <td>{row['Data']}</td>
            <td><strong>{row['Cliente']}</strong></td>
            <td>{row['Tipologia']}</td>
            <td class="text-right">€ {row['Fatturato']:,.2f}</td>
            <td class="text-center"><span class="status-badge">{row['Stato']}</span></td>
        </tr>
        """

    html_template = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
    <meta charset="UTF-8">
    <style>
      @page {{ size: A4 portrait; margin: 8mm 10mm; background-color: #f8fafc; }}
      *, *::before, *::after {{ box-sizing: border-box; }}
      body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; margin: 0; font-size: 8.5pt; line-height: 1.35; }}
      .header-card {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 12px 18px; border-radius: 6px; margin-bottom: 12px; }}
      .header-table {{ width: 100%; border-collapse: collapse; }}
      .title-main {{ font-size: 16pt; font-weight: 700; margin: 0; color: #ffffff; }}
      .subtitle {{ font-size: 8.5pt; color: #94a3b8; margin: 0; text-transform: uppercase; }}
      .header-right {{ text-align: right; }}
      .badge-period {{ background-color: #38bdf8; color: #0f172a; font-weight: 700; font-size: 8.5pt; padding: 4px 10px; border-radius: 14px; text-transform: uppercase; }}
      
      .kpi-table {{ width: 100%; border-collapse: separate; border-spacing: 8px 0; margin-left: -8px; margin-right: -8px; margin-bottom: 12px; }}
      .kpi-card {{ background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; width: 25%; }}
      .kpi-card-highlight {{ background-color: #f0f9ff; border: 1px solid #7dd3fc; }}
      .kpi-label {{ font-size: 7.5pt; color: #64748b; text-transform: uppercase; font-weight: 700; }}
      .kpi-value {{ font-size: 12.5pt; font-weight: 800; color: #0f172a; }}
      .kpi-subtext {{ font-size: 7.5pt; font-weight: 600; }}
      
      .section-title {{ font-size: 10.5pt; font-weight: 700; color: #0f172a; margin: 0 0 8px 0; padding-left: 8px; border-left: 3.5px solid #0284c7; }}
      
      .data-table {{ width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 6px; overflow: hidden; border: 1px solid #cbd5e1; margin-bottom: 12px; }}
      .data-table th {{ background-color: #f1f5f9; color: #334155; font-weight: 700; font-size: 7.5pt; text-transform: uppercase; padding: 6px 8px; border-bottom: 1px solid #cbd5e1; text-align: left; }}
      .data-table td {{ padding: 5.5px 8px; font-size: 8.5pt; color: #334155; border-bottom: 1px solid #e2e8f0; }}
      .data-table tr:nth-child(even) td {{ background-color: #f8fafc; }}
      .text-right {{ text-align: right !important; }}
      .text-center {{ text-align: center !important; }}
      .status-badge {{ padding: 2px 6px; font-size: 7pt; font-weight: 700; border-radius: 3px; background-color: #dcfce7; color: #166534; }}
      
      .total-row-accent td {{ background-color: #f0f9ff !important; color: #0369a1 !important; font-weight: 700 !important; font-size: 8.5pt !important; border-top: 1.5px solid #0284c7; }}
      .total-row td {{ background-color: #0f172a !important; color: #ffffff !important; font-weight: 700 !important; font-size: 8.5pt !important; }}
      
      .progress-bg {{ background-color: #e2e8f0; border-radius: 3px; height: 6px; width: 100%; overflow: hidden; margin-top: 3px; }}
      .progress-fill {{ background-color: #0284c7; height: 100%; }}
      
      .layout-table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
      .layout-table td {{ vertical-align: top; padding: 0; }}
      .layout-left {{ width: 55%; padding-right: 8px; }}
      .layout-right {{ width: 45%; padding-left: 8px; }}
      
      .insight-box {{ background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; }}
      .insight-title {{ font-weight: 700; font-size: 8pt; color: #0f172a; }}
      .insight-desc {{ font-size: 7.5pt; color: #64748b; line-height: 1.25; }}
      .footer {{ margin-top: 6px; padding-top: 6px; border-top: 1px solid #e2e8f0; font-size: 7pt; color: #94a3b8; text-align: center; }}
    </style>
    </head>
    <body>

      <div class="header-card">
        <table class="header-table">
          <tr>
            <td>
              <div class="subtitle">Report Gestionale & Performance</div>
              <h1 class="title-main">Analisi Fatturato & Eventi</h1>
            </td>
            <td class="header-right">
              <span class="badge-period">{mese_anno}</span>
            </td>
          </tr>
        </table>
      </div>

      <table class="kpi-table">
        <tr>
          <td class="kpi-card kpi-card-highlight">
            <div class="kpi-label">Fatturato Totale</div>
            <div class="kpi-value">€ {fatturato_totale:,.2f}</div>
            <div class="kpi-subtext" style="color: #059669;">100% Incassato</div>
          </td>
          <td class="kpi-card">
            <div class="kpi-label">Cene Spettacolo</div>
            <div class="kpi-value">€ {cene_spettacolo:,.2f}</div>
            <div class="kpi-subtext" style="color: #7c3aed;">{perc_cene:.2f}% del Totale</div>
          </td>
          <td class="kpi-card">
            <div class="kpi-label">Spicciolata / Ord.</div>
            <div class="kpi-value">€ {spicciolata:,.2f}</div>
            <div class="kpi-subtext" style="color: #059669;">{perc_spicciolata:.2f}% del Totale</div>
          </td>
          <td class="kpi-card">
            <div class="kpi-label">Eventi Privati/Corp</div>
            <div class="kpi-value">€ {totale_eventi:,.2f}</div>
            <div class="kpi-subtext" style="color: #0284c7;">{num_eventi} Eventi Gestiti</div>
          </td>
        </tr>
      </table>

      <h2 class="section-title">Dettaglio Eventi Privati & Corporate ({mese_anno})</h2>
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 15%;">Data</th>
            <th style="width: 25%;">Cliente / Evento</th>
            <th style="width: 32%;">Tipologia</th>
            <th class="text-right" style="width: 16%;">Fatturato (€)</th>
            <th class="text-center" style="width: 12%;">Stato</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
          <tr class="total-row-accent">
            <td colspan="3"><strong>TOTALE EVENTI PRIVATI & CORPORATE ({num_eventi} Eventi)</strong></td>
            <td class="text-right"><strong>€ {totale_eventi:,.2f}</strong></td>
            <td class="text-center"><strong>100%</strong></td>
          </tr>
        </tbody>
      </table>

      <table class="layout-table">
        <tr>
          <td class="layout-left">
            <h2 class="section-title">Ripartizione Macro-Categorie</h2>
            <table class="data-table" style="margin-bottom: 0;">
              <thead>
                <tr>
                  <th>Categoria</th>
                  <th class="text-right">Fatturato (€)</th>
                  <th class="text-right">Incidenza</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <strong>Cene Spettacolo</strong>
                    <div class="progress-bg"><div class="progress-fill" style="width: {perc_cene}%; background-color: #8b5cf6;"></div></div>
                  </td>
                  <td class="text-right">€ {cene_spettacolo:,.2f}</td>
                  <td class="text-right"><strong>{perc_cene:.2f}%</strong></td>
                </tr>
                <tr>
                  <td>
                    <strong>Spicciolata / Entrate Ord.</strong>
                    <div class="progress-bg"><div class="progress-fill" style="width: {perc_spicciolata}%; background-color: #10b981;"></div></div>
                  </td>
                  <td class="text-right">€ {spicciolata:,.2f}</td>
                  <td class="text-right"><strong>{perc_spicciolata:.2f}%</strong></td>
                </tr>
                <tr>
                  <td>
                    <strong>Eventi Privati & Corporate</strong>
                    <div class="progress-bg"><div class="progress-fill" style="width: {perc_eventi}%; background-color: #0284c7;"></div></div>
                  </td>
                  <td class="text-right">€ {totale_eventi:,.2f}</td>
                  <td class="text-right"><strong>{perc_eventi:.2f}%</strong></td>
                </tr>
                <tr class="total-row">
                  <td><strong>TOTALE GENERALE</strong></td>
                  <td class="text-right"><strong>€ {fatturato_totale:,.2f}</strong></td>
                  <td class="text-right"><strong>100,00%</strong></td>
                </tr>
              </tbody>
            </table>
          </td>

          <td class="layout-right">
            <h2 class="section-title">Analisi & Insight Strategici</h2>
            <div class="insight-box">
              <div style="margin-bottom: 6px;">
                <div class="insight-title" style="color: #7c3aed;">🎯 Cene Spettacolo</div>
                <div class="insight-desc">Rappresentano il <strong>{perc_cene:.2f}%</strong> del fatturato (€ {cene_spettacolo:,.2f}).</div>
              </div>
              <div style="margin-bottom: 6px;">
                <div class="insight-title" style="color: #059669;">⚖️ Spicciolata</div>
                <div class="insight-desc">Con il <strong>{perc_spicciolata:.2f}%</strong> (€ {spicciolata:,.2f}), copre i costi fissi quotidiani.</div>
              </div>
              <div>
                <div class="insight-title" style="color: #0284c7;">💎 Eventi Privati</div>
                <div class="insight-desc">{num_eventi} eventi gestiti per il <strong>{perc_eventi:.2f}%</strong> del totale mensile.</div>
              </div>
            </div>
          </td>
        </tr>
      </table>

      <div class="footer">
        Report generato per uso interno e gestionale • Periodo: {mese_anno}
      </div>

    </body>
    </html>"""

    return HTML(string=html_template).write_pdf()

# Generiamo il dizionario dai dati per la firma della cache
df_dict = edited_df.to_dict(orient="records")

# Richiamiamo la versione con la cache
pdf_data = genera_pdf_cached(
    df_dict, 
    mese_anno, 
    fatturato_totale, 
    cene_spettacolo, 
    totale_eventi, 
    num_eventi, 
    spicciolata, 
    perc_cene, 
    perc_spicciolata, 
    perc_eventi
)

# Tasto di download del PDF (restituisce istantaneamente il file memorizzato in cache)
st.download_button(
    label="📄 Scarica Report PDF A4 (Pagina Singola)",
    data=pdf_data,
    file_name=f"Report_Eventi_{mese_anno.replace(' ', '_')}.pdf",
    mime="application/pdf"
)
