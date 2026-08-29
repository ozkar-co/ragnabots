# Bots — pool + muestra + all-maps

```bash
python staging/market/npc_shops/extract_npc_shops.py
python staging/market/bots/build_sellable_pool.py
python staging/market/bots/preview_sim.py                 # ×10
python staging/market/bots/build_and_simulate_all.py      # todos + sim 100d
```

- Pool: [docs/10-sellable-pool.md](../../docs/10-sellable-pool.md)
- All-bots: [docs/11-all-bots-sim.md](../../docs/11-all-bots-sim.md)
- Salida: `pool/`, `sample/`, `all_bots/`
