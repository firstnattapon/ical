import os
import sys
import logging
from datetime import datetime
import ical_engine as ical

# Set up logging
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'background_sync.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_sync():
    """Run fully automated synchronization of all active iCal sources."""
    logging.info("Starting background iCal synchronization process...")
    try:
        results = ical.sync_all_sources()
        if not results:
            logging.info("No active auto-sync sources found.")
            
        for r in results:
            if r.get("status") == "success":
                logging.info(f"SUCCESS [Room: {r.get('room_name')} | Platform: {r.get('platform')}]: {r.get('message')}")
            else:
                logging.error(f"ERROR: {r.get('message', 'Unknown Error')} [Room: {r.get('room_name', 'Unknown')} | Platform: {r.get('platform', 'Unknown')}]")
                
        logging.info("Background iCal synchronization process completed.")
    except Exception as e:
        logging.error(f"CRITICAL ERROR during background sync: {str(e)}", exc_info=True)

if __name__ == "__main__":
    run_sync()
