#!/usr/bin/env python3

import time
import json
import os
from datetime import datetime

def monitor_progress():
    """
    Monitor the progress of network generation by checking log files and temp data
    """
    print("🔍 Monitoring Network Generation Progress...")
    print("=" * 50)
    
    start_time = time.time()
    last_update = 0
    
    while True:
        try:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Check if there are any temporary progress files
            progress_info = []
            
            # Look for any JSON files that might contain progress
            for filename in os.listdir('.'):
                if filename.startswith('test_network_data') or filename.startswith('monad_nft_network'):
                    if filename.endswith('.json'):
                        try:
                            with open(filename, 'r') as f:
                                data = json.load(f)
                                if 'graph' in data and 'nodes' in data['graph']:
                                    nodes = len(data['graph']['nodes'])
                                    edges = len(data['graph']['edges'])
                                    progress_info.append((filename, nodes, edges))
                        except:
                            pass
            
            # Clear screen and show progress
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("🚀 Monad NFT Network Generation Monitor")
            print("=" * 50)
            print(f"⏱️  Elapsed time: {elapsed/60:.1f} minutes")
            print(f"🎯 Target: 1000 collections")
            print()
            
            if progress_info:
                print("📊 Current Progress:")
                for filename, nodes, edges in progress_info:
                    print(f"   • {filename}: {nodes} nodes, {edges} edges")
                    if nodes > 0:
                        progress_pct = (nodes / 1000) * 100
                        print(f"     Progress: {progress_pct:.1f}% complete")
                print()
            else:
                print("⏳ Waiting for progress data...")
                print("   (This is normal during initial API calls)")
                print()
            
            print("💡 Tips:")
            print("   • The process takes 25-30 minutes due to API rate limiting")
            print("   • Each collection requires ~1.5 seconds for holder data")
            print("   • Network analysis happens after all data is collected")
            print("   • Press Ctrl+C to stop monitoring (won't stop generation)")
            print()
            
            print(f"🕐 Last updated: {datetime.now().strftime('%H:%M:%S')}")
            
            time.sleep(10)  # Update every 10 seconds
            
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped. Network generation continues in background.")
            break
        except Exception as e:
            print(f"⚠️  Monitor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_progress() 