# -*- coding: utf-8 -*-
"""
Medical Equipment Maintenance Management System - Teaching Hospital Peradeniya
Print Helper Utility
Generates clean, professional A4 printable views and triggers browser / system print dialog.
"""

import os
import tempfile
import webbrowser
import html

def print_document(title, content_html, is_landscape=False, doc_type="report"):
    """
    Creates a styled HTML print page and opens it in the default browser with window.print() triggered.
    """
    orientation = "landscape" if is_landscape else "portrait"
    
    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>
  @page {{
    size: A4 {orientation};
    margin: 12mm 10mm 12mm 10mm;
  }}
  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    color: #1e293b;
    background-color: #f8fafc;
    margin: 0;
    padding: 15px;
    font-size: 11px;
    line-height: 1.4;
  }}
  .print-container {{
    max-width: 100%;
    margin: 0 auto;
    background: #ffffff;
    padding: 20px 24px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }}
  .no-print-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0f172a;
    color: #f8fafc;
    padding: 10px 18px;
    border-radius: 6px;
    margin-bottom: 18px;
  }}
  .btn-print {{
    background: #2563eb;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 5px;
    font-weight: 600;
    cursor: pointer;
    font-size: 12px;
  }}
  .btn-print:hover {{
    background: #1d4ed8;
  }}
  .doc-header {{
    border-bottom: 2px solid #0f172a;
    padding-bottom: 10px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .doc-title {{
    font-size: 16px;
    font-weight: 800;
    color: #0f172a;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0;
  }}
  .doc-date {{
    font-size: 10px;
    color: #64748b;
    font-family: monospace;
  }}
  /* Tables */
  table.print-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-size: 10px;
  }}
  table.print-table th {{
    background-color: #1e293b !important;
    color: #ffffff !important;
    text-align: left;
    padding: 6px 8px;
    font-weight: 700;
    border: 1px solid #0f172a;
    white-space: nowrap;
  }}
  table.print-table td {{
    padding: 6px 8px;
    border: 1px solid #cbd5e1;
    color: #334155;
    vertical-align: top;
  }}
  table.print-table tr:nth-child(even) td {{
    background-color: #f8fafc;
  }}
  /* Dossier Card layout for 360 profile */
  .profile-section {{
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    margin-bottom: 14px;
    overflow: hidden;
  }}
  .profile-section-hdr {{
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    font-size: 11px;
    padding: 6px 12px;
    border-bottom: 1px solid #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }}
  .profile-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 8px 16px;
    padding: 10px 12px;
  }}
  .profile-item {{
    display: flex;
    flex-direction: column;
  }}
  .profile-lbl {{
    font-size: 9px;
    color: #64748b;
    text-transform: uppercase;
    font-weight: 600;
  }}
  .profile-val {{
    font-size: 11px;
    color: #0f172a;
    font-weight: 600;
    margin-top: 2px;
  }}
  @media print {{
    body {{
      background: #ffffff !important;
      padding: 0 !important;
    }}
    .no-print, .no-print-bar {{
      display: none !important;
    }}
    .print-container {{
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
    }}
  }}
</style>
</head>
<body>
  <div class="print-container">
    <div class="no-print-bar">
      <span>🖨️ <strong>Print Preview</strong> - Press the button or use Ctrl+P to Print / Save as PDF</span>
      <button class="btn-print" onclick="window.print()">🖨️ Print / Save PDF</button>
    </div>
    
    <div class="doc-header">
      <div>
        <h1 class="doc-title">{html.escape(title)}</h1>
      </div>
      <div class="doc-date">
        Generated: <span id="gen-time"></span>
      </div>
    </div>
    
    <div class="doc-body">
      {content_html}
    </div>
  </div>

  <script>
    document.getElementById('gen-time').innerText = new Date().toLocaleString();
    window.onload = function() {{
      setTimeout(function() {{
        window.print();
      }}, 300);
    }};
  </script>
</body>
</html>
"""
    try:
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"thp_print_{os.getpid()}.html")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html_page)
        webbrowser.open(f"file://{temp_file}")
    except Exception as e:
        print(f"Error launching print: {e}")
