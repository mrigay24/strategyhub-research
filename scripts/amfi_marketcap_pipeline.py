"""Parse AMFI 6-month average market-cap lists into one tidy parquet.

Source page: https://www.amfiindia.com/otherdata/categorisation-of-stocks
Raw files:   data_raw/amfi_mcap/YYYY-MM-DD.xlsx (period_end in the filename)
Output:      data_processed/amfi_avg_mcap.parquet
             (period_end, company, isin, nse_symbol, bse_code, avg_mcap_cr)

openpyxl is not installed in .venv, so a minimal stdlib reader (zipfile + XML)
is used; files are only ever read as data, never executed.
Run: .venv/bin/python scripts/amfi_marketcap_pipeline.py [--download]
"""
import re, sys, glob, os, zipfile, logging, urllib.request
import xml.etree.ElementTree as ET
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data_raw", "amfi_mcap")
OUT = os.path.join(ROOT, "data_processed", "amfi_avg_mcap.parquet")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("amfi")

B = "https://www.amfiindia.com/Themes/Theme1/downloads/"
URLS = {
 "2026-06-30": "https://portal.amfiindia.com/spages/AverageMarketCapitalization30Jun2026.xlsx",
 "2025-12-31": B + "AverageMarketCapitalization31Dec2025.xlsx",
 "2025-06-30": B + "AverageMarketCapitalization30Jun2025.xlsx",
 "2024-12-31": B + "AverageMarketCapitalizationoflistedcompaniesduringthesixmonthsended31Dec2024.xlsx",
 "2024-06-30": "https://www.amfiindia.com/uploads/Average_Market_Capitalization_30_Jun2024_2a1ab4c1d8.xlsx",
 "2023-12-31": B + "AverageMarketCapitalizationoflistedcompaniesduringthesixmonthsended31Dec2023.xlsx",
 "2023-06-30": B + "AverageMarketCapitalizationoflistedcompaniesduringthesixmonthsended30Jun2023.xlsx",
 "2022-12-31": B + "AverageMarketCapitalizationoflistedcompaniesduringthesixmonthsended31Dec2022.xlsx",
 "2022-06-30": B + "AverageMarketCapitalizationoflistedcompaniesduringthesixmonthsended30June2022.xlsx",
 "2021-12-31": B + "Average%20Market%20Capitalisation%20of%20Listed%20Companies%20during%20Jul%20-%20Dec%202021.xlsx",
 "2021-06-30": B + "Average%20Market%20Capitalization%20of%20List%20Companies%20during%20Jan-June%202021.xlsx",
 "2020-12-31": B + "Average%20Market%20Capitalization%20of%20Listed%20Companies%20during%20Jul%20-%20Dec%202020_Final.xlsx",
 "2020-06-30": B + "Average%20Market%20Capitalization%20of%20Listed%20Companies%20during%20Jan%20-%20Jun%202020_Final.xlsx",
 "2019-12-31": B + "Avg.%20Market%20Capitalization%20of%20listed%20companies%20during%20Jul-Dec%202019.xlsx",
 "2019-06-30": B + "Avg.%20Market%20Capitalization%20of%20listed%20companies%20during%20-Jan-June%202019.xlsx",
 "2018-12-31": B + "Avg.%20Market%20Capitalization%20of%20listed%20companies%20during%20Jul-Dec%202018.xlsx",
 "2018-06-30": B + "Avg.%20Market%20Capitalization%20of%20listed%20companies%20during%20-Jan-June%202018.xlsx",
 "2017-12-31": B + "Avg.%20Market%20Capitalization%20of%20listed%20companies%20during%20-Jul-Dec%202017.xlsx",
}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def download():
    os.makedirs(RAW, exist_ok=True)
    for p, u in URLS.items():
        dst = os.path.join(RAW, p + ".xlsx")
        if os.path.exists(dst):
            continue
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r, open(dst, "wb") as f:
                f.write(r.read())
            log.info("downloaded %s", p)
        except Exception as e:
            log.warning("FAILED %s %s: %s", p, u, e)


def col_idx(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path):
    """Return {sheet_name: list of rows (lists of str/None)} using stdlib only."""
    z = zipfile.ZipFile(path)
    sst = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            sst.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    out = {}
    for sh in wb.find("m:sheets", NS):
        rid = sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        tgt = rmap[rid].lstrip("/")
        tgt = tgt if tgt.startswith("xl/") else "xl/" + tgt
        rows = []
        for row in ET.fromstring(z.read(tgt)).iter("{%s}row" % NS["m"]):
            vals = {}
            for c in row.findall("m:c", NS):
                t = c.get("t")
                if t == "inlineStr":
                    v = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                else:
                    ve = c.find("m:v", NS)
                    v = None if ve is None else ve.text
                    if v is not None and t == "s":
                        v = sst[int(v)]
                if v is not None:
                    vals[col_idx(c.get("r"))] = v
            if vals:
                r = [None] * (max(vals) + 1)
                for k, v in vals.items():
                    r[k] = v
                rows.append(r)
        out[sh.get("name")] = rows
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def classify(h):
    n = norm(h)
    if n.startswith(("sr", "s no", "serial")):
        return "sr"
    if "isin" in n:
        return "isin"
    if "company" in n or n in ("name", "name of the company"):
        return "company"
    if "bse" in n and ("symbol" in n or "code" in n) and "cap" not in n:
        return "bse_code"
    if "nse" in n and "symbol" in n:
        return "nse_symbol"
    if "msei" in n and "symbol" in n:
        return "msei_symbol"
    if "cap" in n and "bse" in n:
        return "mcap_bse"
    if "cap" in n and "nse" in n:
        return "mcap_nse"
    if "cap" in n and "msei" in n:
        return "mcap_msei"
    if "cap" in n:
        return "mcap_other"
    return None


def parse_sheet(rows, period):
    hi = None
    for i, r in enumerate(rows[:40]):
        kinds = [classify(x) for x in r if x]
        if "isin" in kinds and "company" in kinds:
            hi = i
            break
    if hi is None:
        return None
    # header may span two rows (merged "Average Market Cap" over exchange columns)
    hdr = list(rows[hi]) + [None] * 20
    above = list(rows[hi - 1]) + [None] * 20 if hi > 0 else [None] * 20
    below = list(rows[hi + 1]) + [None] * 20 if hi + 1 < len(rows) else [None] * 20
    kinds = {}
    for j in range(len(rows[hi])):
        for cand in (hdr[j], (f"{above[j]} {hdr[j]}" if above[j] else None), (f"{hdr[j]} {below[j]}" if below[j] else None)):
            k = classify(cand) if cand else None
            if k and k not in kinds.values():
                kinds[j] = k
                break
    data_start = hi + 1
    if any(kinds.get(j, "").startswith("mcap") for j in kinds) is False:
        pass
    recs = []
    for r in rows[data_start:]:
        r = r + [None] * 20
        d = {k: r[j] for j, k in kinds.items()}
        isin = str(d.get("isin") or "").strip()
        if not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", isin):
            continue
        def num(x):
            try:
                return float(str(x).replace(",", ""))
            except Exception:
                return float("nan")
        nse, bse = num(d.get("mcap_nse")), num(d.get("mcap_bse"))
        mc = nse if nse == nse else (bse if bse == bse else num(d.get("mcap_msei")))
        if mc != mc and "mcap_other" in d:
            mc = num(d["mcap_other"])
        sym = d.get("nse_symbol")
        sym = str(sym).strip() if sym and str(sym).strip() not in ("", "-", "NA", "nan") else None
        bc = d.get("bse_code")
        bc = str(bc).strip().replace(".0", "") if bc else None
        recs.append(dict(period_end=period, company=str(d.get("company") or "").strip(), isin=isin,
                         nse_symbol=sym, bse_code=bc, avg_mcap_cr=mc))
    return pd.DataFrame(recs)


def main():
    if "--download" in sys.argv:
        download()
    frames = []
    for f in sorted(glob.glob(os.path.join(RAW, "*.xlsx"))):
        period = os.path.basename(f)[:-5]
        try:
            best = None
            for name, rows in read_xlsx(f).items():
                df = parse_sheet(rows, period)
                if df is not None and (best is None or len(df) > len(best)):
                    best = df
            if best is None or best.empty:
                log.warning("UNPARSED %s", f)
                continue
            log.info("%s rows=%d nse_sym=%d mcap_ok=%d", period, len(best), best.nse_symbol.notna().sum(), best.avg_mcap_cr.notna().sum())
            frames.append(best)
        except Exception as e:
            log.warning("UNPARSED %s: %r", f, e)
    df = pd.concat(frames, ignore_index=True)
    df["period_end"] = pd.to_datetime(df["period_end"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_parquet(OUT, index=False)
    log.info("saved %s rows=%d periods=%d", OUT, len(df), df.period_end.nunique())


if __name__ == "__main__":
    main()
