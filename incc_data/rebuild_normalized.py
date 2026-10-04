"""Rebuild from verified original responses: python incc_data/rebuild_normalized.py."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cvm_imobilizado.incc_provider import normalize_sources
if __name__ == '__main__':
    data_dir = ROOT / 'incc_data'
    frame = normalize_sources(data_dir)
    frame.to_csv(data_dir / 'monthly_official.csv', index=False)
    print(f'monthly_official.csv: {len(frame)} official monthly observations')
