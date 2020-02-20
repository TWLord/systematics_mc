#bsub -W 240:00 -n 1 -q scarf-ibis -o run_all.log -e run_all.log \
#bsub -M 10000 -G micegrp -q xxl -o run_all.log -e run_all.log \
ulimit -t `ulimit -t -H`
ulimit -u `ulimit -u -H`
    python scripts/run_all.py
