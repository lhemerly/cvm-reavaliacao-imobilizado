"""Official pipeline CLI. Never generates sample data or guesses missing inputs."""
import argparse,json
from .pipeline import CVMImobilizadoPipeline
from .config import YEARS_DEFAULT

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true',help='Download current official CVM annual ZIPs and replace selected-source cache')
    parser.add_argument('--output-dir',help='Alternative output directory for reproduction checks')
    args=parser.parse_args(argv)
    pipeline=CVMImobilizadoPipeline(output_dir=args.output_dir)
    if args.refresh:
        for year in YEARS_DEFAULT:
            if not pipeline.downloader.download_dfp_year(year,force=True):
                raise RuntimeError(f'Official CVM retrieval failed for {year}')
    result=pipeline.run_multiyear_pipeline()
    summary=pipeline.export_results(result)
    print(json.dumps({k:summary[k] for k in ('target_n','income_n','adjusted_n','means')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
