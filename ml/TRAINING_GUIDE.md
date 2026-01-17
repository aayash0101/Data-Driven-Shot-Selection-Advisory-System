# Training Guide

## Quick Training (Recommended for First Run)

Train on 10% of data (takes ~2-5 minutes):

```bash
cd ml
python train_model.py
```

Or explicitly specify sampling:

```bash
python train_model.py --sample 0.1
```

## Training Options

### 1. Fast Training (10% of data)
```bash
python train_model.py --sample 0.1
```
- Time: ~2-5 minutes
- Good for testing and development
- Still provides reasonable model performance

### 2. Medium Training (25% of data)
```bash
python train_model.py --sample 0.25
```
- Time: ~5-10 minutes
- Better model performance
- Good balance between speed and accuracy

### 3. Full Dataset Training
```bash
python train_model.py --full-data
```
- Time: ~30-60 minutes
- Best model performance
- Use when you have time and want maximum accuracy

### 4. Filter by Position (Point Guards Only)
```bash
python train_model.py --sample 0.1 --position PG
```
- Trains only on point guard shots
- Faster training (fewer rows)
- More relevant for PG-specific advice

## Performance vs Speed Trade-offs

| Sampling | Rows (approx) | Time | Accuracy | Use Case |
|----------|---------------|------|----------|----------|
| 0.1 (10%) | ~400k | 2-5 min | Good | Testing, quick iteration |
| 0.25 (25%) | ~1M | 5-10 min | Better | Development |
| 0.5 (50%) | ~2M | 15-20 min | Very Good | Production (if time allows) |
| Full | ~4M | 30-60 min | Best | Final production model |

## Tips

1. **Start with 10%**: Always start with `--sample 0.1` to verify everything works
2. **Increase gradually**: If 10% works well, try 25% or 50%
3. **Use full data only when needed**: Full dataset training takes much longer with diminishing returns
4. **Monitor memory**: If you get memory errors, reduce sampling or filter by position

## Troubleshooting

**Training too slow?**
- Use `--sample 0.1` or `--sample 0.05` for faster training
- Filter by position: `--position PG`

**Out of memory?**
- Reduce sampling: `--sample 0.05`
- Filter by position: `--position PG`
- Close other applications

**KeyboardInterrupt errors?**
- Training was interrupted (Ctrl+C)
- Just restart with sampling: `python train_model.py --sample 0.1`


