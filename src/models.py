"""Pydantic models shared across the pipeline."""

from pydantic import BaseModel, Field


class JobEvaluation(BaseModel):
    """Structured critical evaluation result for a single job listing."""

    is_relevant: bool = Field(
        description="True if role is a viable target (match_score >= 6) fitting candidate's profile; False if disqualified or irrelevant"
    )
    match_score: int = Field(
        description="Calibrated score 1-10 evaluated critically against candidate CV and career tracks (1-3 disqualified, 4-5 poor fit, 6 viable baseline, 7-8 strong match, 9-10 exceptional dream fit)"
    )
    role_category: str = Field(
        description="One of: Asset Management, Wealth Management, Investment Research, Risk & Quantitative, Corporate Finance / PE, Fintech & Markets, Operations / Compliance, Other"
    )
    degree_fit: str = Field(
        description="Degree & seniority badge: 'MSc / CFA Suitable', 'Charterholder / CFA Level II+', 'Senior Director / PM Lead', 'Entry / Junior Analyst', 'Overqualified (MD/Partner Req)', or 'Retail / Non-professional'"
    )
    language_req: str = Field(
        description="Language badge: 'English (C1/C2)', 'EN + DE B1/B2 OK', or 'Fluent DE Required (C1/C2)'"
    )
    track_alignment: str = Field(
        default="General finance role",
        description="Specific career direction: which of Envisioned Financial Tracks 1-12 it advances, or if it deviates/tangential",
    )
    fit_strengths: str = Field(
        default="Matches financial and quantitative background.",
        description="Concrete verified CV skills, track record, or credentials directly matching the vacancy duties (e.g. Cambridge MPhil, CFA Charterholder, UBS GWM Director, $4B+ direct fund track record, Python/cvxpy factor models, GRE 170 Quant)",
    )
    career_gaps: str = Field(
        default="No major disqualifiers noted.",
        description="Critical, honest assessment of what candidate lacks: specific asset class/geography mismatch, MD/Partner requirement, or native German C2 requirement",
    )
    one_line_summary: str = Field(
        description="Structured critical assessment formatted exactly as: '🎯 Track: <track_alignment> | ✅ Fit: <fit_strengths> | ⚠️ Gaps: <career_gaps>'",
    )
    scorer: str = Field(
        default="gemini",
        description="Evaluator engine used: 'gemini' or 'heuristic'",
    )
