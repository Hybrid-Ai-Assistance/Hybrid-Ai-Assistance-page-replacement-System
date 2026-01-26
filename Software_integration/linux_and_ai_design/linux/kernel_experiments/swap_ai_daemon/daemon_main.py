# daemon_main.py
import sys, time
import os
from config import MODEL_PATH
from swap_reader import SwapDeviceReader
from orchestrator import AIDaemonOrchestrator

def main(model_path: str = MODEL_PATH):
    print("💡 AI Swap Predictor Daemon (V3) starting…")
    try:
        orch = AIDaemonOrchestrator(model_path=model_path)
    except Exception as e:
        print(f"WARNING: model not found - please check model path")

    reader = None
    error = False
    while True:
        try:
            # ---- State: Device missing ---------------------------------
            if reader is None :
                # ---- State: Device exists but reader not ready -----
                try:
                    reader = SwapDeviceReader()
                    if reader:
                        print("✅ Device detected & mmap successful!")
                        print("🔍 Listening for kernel page-fault events…")
                    error = False

                except Exception as e:
                    if not error:
                        error = True
                        print("⏳ Waiting for /dev/swap_ai… (kernel module not loaded yet)")
                        raise RuntimeWarning (f"{e} - please do checkout kernel connectivity")
                    time.sleep(2)
                    continue

            # ---- Normal event loop -----------------------------------
            ev = reader.next_event(timeout_sec=1.0)
            if ev is None:
                continue

            pid, row = ev
            try:  
                status = orch.process(pid, row)
                if status:
                    print(f"[PID {status['pid']}] events={status['events']} FUTURE={status['future_pfns']}")
            except Exception as e:
                print(f"orch.process(pid, row) - throw error")
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")
            break
        except RuntimeWarning as e: 
            print(f"WARNING:{e}")   

        if reader:
            reader.close()
            
if __name__ == "__main__":
    # Allow overriding model path via CLI
    mp = sys.argv[1] if len(sys.argv) > 1 else MODEL_PATH
    main(mp)
