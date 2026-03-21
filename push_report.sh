#!/bin/bash
cd /home/ubuntu/futures-report
python3 analysis_script.py
git add report.json
git commit -m "Update report: $(date +'%Y-%m-%d %H:%M')"
git push origin main
