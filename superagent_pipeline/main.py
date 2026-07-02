#!/usr/bin/env python3
"""
Superagent Pipeline — Entry Point

Cara pake:
  python3 main.py
  python3 main.py "topik yang mau dibahas"
"""

import sys
import os
import time

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Load .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from superagent_pipeline.crew import SuperagentPipeline


def run():
    """Jalanin content pipeline — riset → tulis → review"""
    start = time.time()
    
    # Input dari user
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not topic:
        print("🎯 Masukkan topik thread:")
        topic = sys.stdin.readline().strip()
    if not topic:
        topic = "AI Superagent — masa depan artificial intelligence"
    
    print(f"\n{'='*50}")
    print(f"🚀 SUPERAGENT PIPELINE")
    print(f"📋 Topik: {topic}")
    print(f"{'='*50}\n")

    # Jalanin crew (supervisor style: Researcher → Writer → Reviewer)
    pipeline = SuperagentPipeline()
    result = pipeline.crew().kickoff(inputs={"topic": topic})
    
    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"✅ SELESAI dalam {elapsed:.1f} detik!")
    print(f"📁 Cek folder output/ untuk file thread")
    print(f"{'='*50}")
    
    return result


if __name__ == "__main__":
    run()
