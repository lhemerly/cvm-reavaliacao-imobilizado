"""Official FGV monthly inflation, distributed through BCB SGS.

SGS 7456 is INCC-M; SGS 189 is IGP-M. No curated or simulated fallback
is permitted. Packaged response bytes and provenance are checked before use.
A window from base month t to reference month T compounds t+1 through T.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
from http.cookiejar import CookieJar

import pandas as pd

SGS_SERIE_INCC_M = 7456
SGS_SERIE_IGP_M = 189
# The BCB catalog calls 192 generic INCC. It is not used as an INCC-M fallback.
SGS_SERIE_INCC = 192
SUPPORTED_INDICES = {"INCC-M": SGS_SERIE_INCC_M, "IGP-M": SGS_SERIE_IGP_M}
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "incc_data"
SGS_URL = "https://www3.bcb.gov.br/sgspub/consultarvalores/consultarValoresSeries.do"


class IndexCoverageError(ValueError):
    """The requested monthly window contains unpublished/unavailable observations."""

    def __init__(self, index: str, missing_months: list[str]):
        self.index = index
        self.missing_months = missing_months
        super().__init__(f"{index}: missing monthly observations: {', '.join(missing_months)}")


def _read_official_csv(payload: bytes, code: int) -> dict[str, float]:
    rows = list(csv.reader(payload.decode("utf-8-sig").splitlines(), delimiter=";"))
    identity = {7456: "INCC-M", 189: "IGP-M"}[code]
    if not rows or len(rows[0]) != 2 or not rows[0][1].startswith(f"{code} - "):
        raise ValueError(f"Official CSV does not identify SGS {code}")
    if identity not in rows[0][1] or "Monthly % var." not in rows[0][1]:
        raise ValueError(f"Unexpected identity or unit for SGS {code}")
    if not rows[-1] or rows[-1] != ["Source", "FGV"]:
        raise ValueError("Official CSV must identify FGV as source")
    result = {}
    for row in rows[1:-1]:
        if len(row) != 2:
            raise ValueError("Malformed official monthly observation")
        month = datetime.strptime(row[0], "%m/%Y").strftime("%Y-%m")
        rate = float(row[1])
        if month in result or not math.isfinite(rate) or rate <= -100:
            raise ValueError(f"Invalid or duplicate observation: {month}")
        result[month] = rate
    if not result:
        raise ValueError("No official observations retrieved")
    return result


def normalize_sources(data_dir: str | Path) -> pd.DataFrame:
    """Verify original bytes and merge overlapping official responses without guessing."""
    base = Path(data_dir)
    manifest = json.loads((base / "source_provenance.json").read_text())
    series: dict[str, dict[str, float]] = {name: {} for name in SUPPORTED_INDICES}
    for item in manifest["observations"]:
        name = item["index"]
        if name not in SUPPORTED_INDICES or item["sgs_code"] != SUPPORTED_INDICES[name]:
            raise ValueError("Unsupported series in provenance manifest")
        relative = Path(item["file"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Source paths must remain inside the data package")
        payload = (base / relative).read_bytes()
        if hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise ValueError(f"Source hash mismatch: {relative}")
        for month, rate in _read_official_csv(payload, item["sgs_code"]).items():
            if month in series[name] and series[name][month] != rate:
                raise ValueError(f"Conflicting official observations: {name} {month}")
            series[name][month] = rate
    rows = []
    for name, observations in series.items():
        if not observations:
            raise ValueError(f"Missing official series: {name}")
        level = 100.0
        first = pd.Period(min(observations), freq="M")
        base_month = str(first - 1)
        for month, rate in sorted(observations.items()):
            level *= 1 + rate / 100
            rows.append({"date": month + "-01", "index": name,
                         "sgs_code": SUPPORTED_INDICES[name], "monthly_pct": rate,
                         "number_index": level, "index_base_month": base_month})
    return pd.DataFrame(rows)


class INCCProvider:
    """Load the audited offline package; refresh only on an explicit retrieval call."""

    def __init__(self, cache_dir: str | Path | None = None):
        self.cache_dir = Path(cache_dir) if cache_dir is not None else DEFAULT_DATA_DIR
        derived = normalize_sources(self.cache_dir)
        saved = pd.read_csv(self.cache_dir / "monthly_official.csv")
        pd.testing.assert_frame_equal(saved, derived, check_exact=False,
                                      rtol=1e-12, atol=1e-12)
        self._monthly = derived
        self._df_incc_monthly = self.get_monthly_series()

    def get_monthly_series(self, index: str = "INCC-M") -> pd.DataFrame:
        """Compatibility columns, with a disclosed base before the first rate."""
        self._check_index(index)
        frame = self._monthly[self._monthly["index"] == index].copy()
        frame["DATA"] = pd.to_datetime(frame["date"])
        frame["ANO"] = frame["DATA"].dt.year
        frame["MES"] = frame["DATA"].dt.month
        frame["TAXA_MENSAL_PCT"] = frame["monthly_pct"]
        frame["TAXA_MENSAL_DECIMAL"] = frame["monthly_pct"] / 100
        frame["NUMERO_INDICE"] = frame["number_index"]
        return frame[["DATA", "ANO", "MES", "TAXA_MENSAL_PCT",
                      "TAXA_MENSAL_DECIMAL", "NUMERO_INDICE", "index_base_month"]]

    @staticmethod
    def _check_index(index: str):
        if index not in SUPPORTED_INDICES:
            raise ValueError(f"Unsupported index {index!r}; choose INCC-M or IGP-M")

    def get_annual_rates(self, index: str = "INCC-M") -> pd.DataFrame:
        """Only complete January–December years count as annual observations."""
        records = []
        for year, group in self.get_monthly_series(index).groupby("ANO"):
            if list(group["MES"]) != list(range(1, 13)):
                continue
            factor = math.prod(1 + float(v) for v in group["TAXA_MENSAL_DECIMAL"])
            records.append({"ANO": year, "TAXA_ANUAL_PCT": (factor - 1) * 100,
                            "FATOR_ANUAL": factor,
                            "INDICE_DEZEMBRO": group["NUMERO_INDICE"].iloc[-1]})
        return pd.DataFrame(records, columns=["ANO", "TAXA_ANUAL_PCT", "FATOR_ANUAL", "INDICE_DEZEMBRO"])

    def calculate_month_window(self, reference_year: int, months: int,
                               reference_month: int = 12, index: str = "INCC-M") -> dict:
        """Compound exactly N calendar months ending in the reference month.

        Missing months raise IndexCoverageError, including leading/interior gaps.
        A zero-length window has factor 1; negative/noninteger lengths are invalid.
        DATA_INICIO_CORRECAO denotes the first included rate; BASE_MONTH is excluded.
        """
        self._check_index(index)
        if isinstance(months, bool) or not isinstance(months, int) or months < 0:
            raise ValueError("months must be a nonnegative integer")
        if not 1 <= reference_month <= 12:
            raise ValueError("reference_month must be between 1 and 12")
        end = pd.Period(year=reference_year, month=reference_month, freq="M")
        base = end - months
        expected = [str(base + n) for n in range(1, months + 1)]
        values = self._monthly[self._monthly["index"] == index].set_index("date")["monthly_pct"]
        available = {date[:7]: float(rate) for date, rate in values.items()}
        missing = [month for month in expected if month not in available]
        if missing:
            raise IndexCoverageError(index, missing)
        factor = math.prod(1 + available[month] / 100 for month in expected)
        prefix = "INCC" if index == "INCC-M" else "IGPM"
        return {"INDEX": index, "SGS_CODE": SUPPORTED_INDICES[index],
                "FACTOR": factor, "INFLATION_PCT": (factor - 1) * 100,
                f"FATOR_{prefix}": factor,
                f"INFLACAO_ACUM_{prefix}_PCT": (factor - 1) * 100,
                "MESES_RETROATIVOS": months,
                "BASE_MONTH": str(base), "REFERENCE_MONTH": str(end),
                "DATA_INICIO_CORRECAO": expected[0] + "-01" if expected else str(end.start_time.date()),
                "STATUS": "official_window_complete"}

    def calculate_cumulative_inflation(self, reference_year: int, age_years: float,
                                       reference_month: int = 12,
                                       index: str = "INCC-M") -> dict:
        """Age proxy rounded to nearest month using Python round (ties to even)."""
        if not math.isfinite(age_years) or age_years < 0:
            raise ValueError("age_years must be finite and nonnegative")
        months = int(round(age_years * 12))
        return self.calculate_month_window(reference_year, months, reference_month, index)

    def get_comparison_summary(self, years: list[int]) -> pd.DataFrame:
        """Computed annual INCC-M/IGP-M; IPCA is unavailable, never fabricated."""
        annual = {name: self.get_annual_rates(name).set_index("ANO")["TAXA_ANUAL_PCT"]
                  for name in SUPPORTED_INDICES}
        return pd.DataFrame([{"ANO": year,
                              "INCC_ANUAL_PCT": annual["INCC-M"].get(year, float("nan")),
                              "IGPM_ANUAL_PCT": annual["IGP-M"].get(year, float("nan")),
                              "IPCA_ANUAL_PCT": float("nan")}
                             for year in years])

    @staticmethod
    def retrieve_official_csv(serie_id: int, start_date: str, end_date: str,
                              output_path: str | Path) -> dict:
        """Explicit BCB SGS public download route; errors propagate, no fallback.

        Dates use dd/mm/YYYY. The download is session-bound: GET selection,
        POST consultarValores, GET downLoad. Caller reviews the response and adds
        provenance to the package; this method never overwrites loaded observations.
        """
        if serie_id not in SUPPORTED_INDICES.values():
            raise ValueError("Only verified SGS 7456 and 189 are supported")
        start, end = (datetime.strptime(value, "%d/%m/%Y") for value in (start_date, end_date))
        if start > end:
            raise ValueError("start_date must not follow end_date")
        opener = build_opener(HTTPCookieProcessor(CookieJar()))
        selection = SGS_URL + "?" + urlencode({"method": "consultarGraficoPorId", "hdOidSeriesSelecionadas": serie_id})
        query = SGS_URL + "?method=consultarValores"
        download = SGS_URL + "?method=downLoad"
        params = {"dataInicio": start_date, "dataFim": end_date, "selFuncao": 0,
                  "selTipoArqDownload": 1, "hdOidSeriesSelecionadas": serie_id,
                  "graficoEstatico": "true"}
        started = datetime.now(timezone.utc).isoformat()
        with opener.open(selection, timeout=30) as response:
            response.read()
        with opener.open(Request(query, data=urlencode(params).encode()), timeout=30) as response:
            response.read()
        with opener.open(download, timeout=30) as response:
            payload = response.read()
        _read_official_csv(payload, serie_id)
        output = Path(output_path)
        if output.exists():
            raise FileExistsError("Preserve existing raw responses; choose a new output path")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        record = {"file": output.name, "sgs_code": serie_id, "source": "FGV via BCB SGS",
                  "selection_url": selection, "query_url": query, "post_parameters": params,
                  "url": download, "request_started_utc": started,
                  "response_saved_utc": datetime.now(timezone.utc).isoformat(),
                  "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
        output.with_suffix(output.suffix + ".provenance.json").write_text(json.dumps(record, indent=2))
        return record
