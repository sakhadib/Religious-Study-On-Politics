"""
Prereqs (one-time):
    pip install selenium webdriver-manager pandas

Run:
    python validator.py

Notes:
- Adjust CSV_PATH if needed.
- Keeps a 0.3s delay between responders (columns).
- Adds detailed logs for each step and resilient clicking.
"""

import json
import logging
import re
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ===================== CONFIG =====================
URL = "https://politicalcompass.github.io/"
CSV_PATH = r"D:\Research\islamic_political_compass\_merged_predictions.csv"
RESULTS_JSON_PATH = "_pc_scores.json"

KEYS = ["question_id", "question_text"]  # columns to keep as identifiers
VALID_ANS = {"sa", "a", "d", "sd"}       # value attributes on inputs
WAIT_BETWEEN_RESPONDERS_SEC = 0.1        # reduced from 0.3s to 0.1s
ANSWER_CLICK_PAUSE_SEC = 0.005           # reduced from 0.02s to 0.005s (5ms)
PAGE_LOAD_TIMEOUT = 15                   # reduced from 20s to 15s
FIND_TIMEOUT = 5                         # reduced from 10s to 5s
HEADLESS = False                         # set True if you want headless runs

# ===================== LOGGING =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pc-scraper")


# ===================== SELENIUM SETUP =====================
def make_driver(headless=HEADLESS):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    # Performance optimizations
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-plugins")
    opts.add_argument("--disable-images")  # Skip loading images for speed
    opts.add_argument("--disable-javascript-harmony-shipping")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


def open_form(driver):
    log.info("Loading page: %s", URL)
    driver.get(URL)
    wait = WebDriverWait(driver, FIND_TIMEOUT)
    # Ensure form and score spans exist
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form")))
    wait.until(EC.presence_of_element_located((By.ID, "displayEcon")))
    wait.until(EC.presence_of_element_located((By.ID, "displaySoc")))
    log.info("Page loaded and essential elements present.")


# ===================== UTILITIES =====================
_qnum_re = re.compile(r"^q(\d+)$")

def numeric_qid(qid: str) -> int:
    """
    Turn 'q1' -> 1 for stable sorting. If pattern fails, return a large number to push it last.
    """
    m = _qnum_re.match(qid.strip().lower())
    return int(m.group(1)) if m else 10_000


def click_answer(driver, qid: str, ans_val: str):
    """
    Click the radio with name={qid} and value={ans_val}. Optimized for speed with JS click first.
    """
    sel = f"input.form-check-input[name='{qid}'][value='{ans_val}']"
    wait = WebDriverWait(driver, FIND_TIMEOUT)
    try:
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
    except TimeoutException:
        raise NoSuchElementException(f"Could not find element for {qid} -> {ans_val} with selector {sel}")

    # Use JS click directly for speed (more reliable and faster)
    driver.execute_script("arguments[0].click();", el)
    time.sleep(ANSWER_CLICK_PAUSE_SEC)


def read_scores(driver):
    """
    Read the econ and soc scores (text), convert to float if possible.
    """
    econ = driver.find_element(By.ID, "displayEcon").text.strip()
    soc = driver.find_element(By.ID, "displaySoc").text.strip()
    try:
        econ_f = float(econ)
    except ValueError:
        econ_f = None
        log.warning("Econ score not a float: %r", econ)
    try:
        soc_f = float(soc)
    except ValueError:
        soc_f = None
        log.warning("Soc score not a float: %r", soc)
    return econ_f, soc_f


# ===================== CORE WORKFLOW =====================
def load_dataframe(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    missing = [c for c in KEYS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    # Ensure rows are in q1..q62 order
    df = df.copy()
    df["__qnum__"] = df["question_id"].apply(numeric_qid)
    df = df.sort_values("__qnum__", kind="mergesort").drop(columns="__qnum__").reset_index(drop=True)

    # Basic validation
    if len(df) < 62:
        log.warning("CSV has %d rows; expected 62. Proceeding anyway.", len(df))
    elif len(df) > 62:
        log.info("CSV has %d rows (>=62). Will still answer per available questions.", len(df))

    return df


def collect_scores_for_responder(driver, df: pd.DataFrame, responder_col: str):
    """
    For a single responder column:
      - reloads the page (fresh form)
      - fills all questions using the values in responder_col
      - after finishing all answers, reads the two scores
      - returns (econ_score, soc_score)
    """
    log.info("=== Responder: %s ===", responder_col)
    open_form(driver)

    answered = 0
    for _, row in df.iterrows():
        qid = str(row["question_id"]).strip().lower()  # e.g., 'q3'
        # Treat blanks/NaN as 'a' (Agree) by default
        raw_val = row[responder_col]
        if pd.isna(raw_val) or str(raw_val).strip() == "":
            val = "a"
            log.debug("Blank value for %s; defaulting to 'a'", qid)
        else:
            val = str(raw_val).strip().lower()

        # normalize values; allow synonyms if any creep in
        if val in {"strongly agree", "str_agree", "sagree"}:
            val = "sa"
        elif val in {"agree"}:
            val = "a"
        elif val in {"disagree"}:
            val = "d"
        elif val in {"strongly disagree", "str_disagree", "sdisagree"}:
            val = "sd"

        if val not in VALID_ANS:
            log.warning("Skipping %s: invalid value %r (expected one of %s)", qid, val, sorted(VALID_ANS))
            continue

        try:
            click_answer(driver, qid, val)
            answered += 1
            log.debug("Answered %s -> %s", qid, val)
        except Exception as e:
            log.error("Failed to answer %s -> %s: %s", qid, val, e)

    log.info("Answered %d items for %s. Now reading scores (post-62).", answered, responder_col)
    econ, soc = read_scores(driver)
    log.info("Scores for %s | econ=%.4f, soc=%.4f", responder_col, econ if econ is not None else float('nan'),
             soc if soc is not None else float('nan'))
    return econ, soc


def main():
    # Load data
    df = load_dataframe(CSV_PATH)
    all_cols = list(df.columns)
    responder_cols = [c for c in all_cols if c not in KEYS]

    if not responder_cols:
        raise ValueError("No responder columns found (only keys present).")

    log.info("Found %d responder columns.", len(responder_cols))

    # Start browser once for efficiency
    driver = make_driver(headless=HEADLESS)

    results = []
    try:
        for idx, col in enumerate(responder_cols, 1):
            if idx > 1:  # Add blank lines between responders (not before the first one)
                print("\n" + "="*50 + "\n")
            
            log.info("Processing responder %d/%d: %s", idx, len(responder_cols), col)
            econ, soc = collect_scores_for_responder(driver, df, col)
            results.append({
                "responder": col,
                "econ_score": econ,
                "soc_score": soc,
            })
            time.sleep(WAIT_BETWEEN_RESPONDERS_SEC)
    finally:
        driver.quit()
        log.info("Browser closed.")

    # Write JSON array
    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log.info("Wrote %d results to %s", len(results), RESULTS_JSON_PATH)


if __name__ == "__main__":
    main()
