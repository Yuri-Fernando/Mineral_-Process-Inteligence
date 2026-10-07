"""Read-only Streamlit presentation of engine outputs."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mineral_process.pipeline import run_end_to_end  # noqa: E402

st.set_page_config(page_title="Mineral Process Intelligence", page_icon="⛏️", layout="wide")
st.title("Mineral Process Intelligence")
st.caption("Applied research • synthetic demo • advisory only")

output = ROOT / "reports" / "generated"
summary_path = output / "run_summary.json"
if not summary_path.exists():
    with st.spinner("Generating the deterministic local demo..."):
        run_end_to_end(output)

trajectory = pd.read_csv(output / "digital_twin_trajectory.csv")
pareto = pd.read_csv(output / "optimization_pareto.csv")

latest = trajectory.iloc[-1]
columns = st.columns(5)
columns[0].metric("Recovery", f"{latest['recovery']:.1%}")
columns[1].metric("Concentrate grade", f"{latest['concentrate_grade']:.2%}")
columns[2].metric("P80", f"{latest['p80_um']:.0f} µm")
columns[3].metric("Throughput", f"{latest['throughput_tph']:.1f} t/h")
columns[4].metric("Specific energy", f"{latest['specific_energy_kwh_t']:.1f} kWh/t")

overview, real_cases, optimization, control, provenance = st.tabs(
    ["Plant overview", "Real case studies", "Optimization", "Control benchmark", "Boundaries"]
)
with overview:
    st.plotly_chart(
        px.line(
            trajectory,
            y=["recovery", "concentrate_grade"],
            color_discrete_sequence=["#20c997", "#ffc107"],
        ),
        use_container_width=True,
    )
    st.plotly_chart(px.line(trajectory, y=["p80_um", "throughput_tph"]), use_container_width=True)
with real_cases:
    st.info("Each table is a separate operation/study. Metrics are never pooled across datasets.")
    geomet_path = output / "geomet" / "geomet_metrics.csv"
    poly_path = output / "polymetallic" / "grinding_recovery_metrics.csv"
    if geomet_path.exists():
        st.subheader("Copper GeoMet — spatial holdout")
        st.dataframe(pd.read_csv(geomet_path), use_container_width=True)
    if poly_path.exists():
        st.subheader("Polymetallic grinding — ordered holdout")
        st.dataframe(pd.read_csv(poly_path), use_container_width=True)
    if not geomet_path.exists() or not poly_path.exists():
        st.code("python -m mineral_process.cli run-real-cases")

with optimization:
    st.plotly_chart(
        px.scatter(
            pareto, x="cost", y="recovery", color="grade", hover_data=["reagent_gpt", "air_flow"]
        ),
        use_container_width=True,
    )
    st.dataframe(pareto.sort_values("recovery", ascending=False).head(20), use_container_width=True)
    nsga_path = output / "advanced_optimization" / "nsga2_pareto.csv"
    if nsga_path.exists():
        st.subheader("NSGA-II evolved Pareto set")
        nsga = pd.read_csv(nsga_path)
        st.plotly_chart(
            px.scatter(
                nsga,
                x="cost_proxy",
                y="neg_recovery_penalized",
                color="neg_grade_penalized",
            ),
            use_container_width=True,
        )

with control:
    benchmark_path = output / "mpc" / "mpc_benchmark.csv"
    if benchmark_path.exists():
        benchmark = pd.read_csv(benchmark_path)
        st.dataframe(benchmark, use_container_width=True)
        st.plotly_chart(
            px.bar(benchmark, x="controller", y="average_recovery", color="grade_violations"),
            use_container_width=True,
        )
        st.warning(
            "All tested controllers violated the grade specification in this seeded scenario; "
            "therefore no production-safe conclusion is claimed."
        )
    else:
        st.code("python -m mineral_process.cli benchmark-control")

with provenance:
    st.warning("No dashboard action is written to a plant. All recommendations are advisory-only.")
    st.markdown(
        "The displayed trajectory is synthetic and deterministic. Public real datasets are separate case studies. "  # noqa: E501
        "See `PROJECT_LEDGER.md`, `docs/dataset_cards.md`, and the provenance manifest."
    )
