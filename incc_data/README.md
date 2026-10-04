# Official inflation data

Original public BCB SGS CSV bytes, source metadata and a derived monthly table. Producer: FGV. No simulated rates or fallback factors.

| Index | SGS code | Packaged observations |
|---|---:|---|
| INCC-M | 7456 | September 1994–December 2025, 376 months |
| IGP-M | 189 | June 1994–December 2025, 379 months |

SGS 7447 is IGP-10, not INCC-M. Identity metadata are in `raw/`. SGS 192 is not used as a fallback.

`source_provenance.json` records original URLs, request parameters, timestamps and SHA256. Original response bytes are in `raw/`. UTC request intervals also appear in the TSV logs. Field names distinguish request intervals from completion times derived from local file modification times.

`monthly_official.csv` is rebuilt solely from hash-verified observations. Overlapping responses must agree. Dates identify reference months. Constructed index base 100 is August 1994 for INCC-M and May 1994 for IGP-M, before their first available change. Arbitrary bases cancel in covered cumulative factors. Compounding changes rounded to 0.01 percentage point may differ slightly from producer accumulated rates based on unrounded levels.

From the repository root, with requirements installed:

```bash
python incc_data/rebuild_normalized.py
python -m unittest discover -s tests -p test_indices.py -v
```

The provider resolves the packaged data independently of the working directory. A custom directory must provide the manifest/raw/normalized contract; missing or inconsistent data raises an error.

Explicit acquisition of a new original response:

```python
from cvm_imobilizado.incc_provider import INCCProvider
record = INCCProvider.retrieve_official_csv(
    7456, '01/01/1995', '31/12/2025', 'incc_data/new_incc_m.csv'
)
```

Route: GET `consultarGraficoPorId`, POST `consultarValores` with linear function 0, GET session-bound `downLoad`. Saves untouched CSV bytes and adjacent provenance JSON without overwriting existing responses. Review identity, coverage and metadata before adding the file to the manifest, then rebuild. Network errors propagate. This route succeeded when `api.bcb.gov.br` failed DNS resolution.

A window compounds exactly the calendar months after its excluded base month. Missing leading, interior or ending observations raise `IndexCoverageError`. Eletrobras 2022's 342 months have base June 1994 and require July 1994–December 2022: INCC-M lacks July/August 1994; IGP-M covers the window. No truncation, zero filling or index substitution. IGP-M may be an independently labeled sensitivity.
