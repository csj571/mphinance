import subprocess
import os
import glob
import pandas as pd

PROJECT_ROOT = "/home/sam/Antigravity/empty/mphinance"
HISTORY_DIR = os.path.join(PROJECT_ROOT, "data/screens_history")
VENUS_SOURCE = "venus:/home/mnt/Download2/docs/Momentum/anti/scheduling/scans/*_History.csv"

def get_row_counts():
    counts = {}
    for f in glob.glob(os.path.join(HISTORY_DIR, "*.csv")):
        try:
            df = pd.read_csv(f, on_bad_lines='skip')
            counts[os.path.basename(f)] = len(df)
        except:
            pass
    return counts

def sync_from_venus() -> dict:
    """
    Syncs latest scanner history CSVs from Venus home server via SCP.
    """
    before = get_row_counts()
    
    print(f"Syncing from Venus: {VENUS_SOURCE}...")
    try:
        # -q for quiet, -p to preserve times
        cmd = ["scp", "-q", VENUS_SOURCE, HISTORY_DIR]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"SCP failed: {result.stderr}")
            return {"synced": False, "error": result.stderr}
            
        after = get_row_counts()
        
        diff = {}
        total_new = 0
        for f, count in after.items():
            prev = before.get(f, 0)
            new_rows = count - prev
            if new_rows > 0:
                diff[f] = new_rows
                total_new += new_rows
        
        print(f"Sync complete. New rows: {total_new}")
        return {
            "synced": True,
            "new_rows": total_new,
            "files_updated": diff
        }
        
    except subprocess.TimeoutExpired:
        print("SCP timed out. Venus might be offline.")
        return {"synced": False, "error": "timeout"}
    except Exception as e:
        print(f"Sync error: {e}")
        return {"synced": False, "error": str(e)}

def ingest_to_backtest():
    """
    Automatically runs the backtest engine after sync.
    """
    bt_script = os.path.join(PROJECT_ROOT, "dossier/backtesting/screens_backtest.py")
    if os.path.exists(bt_script):
        print("Running screens_backtest.py...")
        venv_python = os.path.join(PROJECT_ROOT, "venv/bin/python3")
        subprocess.run([venv_python, bt_script])
    else:
        print("Backtest script not found.")

if __name__ == "__main__":
    res = sync_from_venus()
    if res.get("synced") and res.get("new_rows", 0) > 0:
        ingest_to_backtest()
