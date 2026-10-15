"""
Requirement 3: Unstructured Maintenance Notes Analyzer
Course: 23IF02 System Automation — Bonus Challenge

Parses free-text technician logs, filtering out irrelevant facility notes,
and extracting an independent semantic risk signal per robotic arm and joint.
"""

import os
import re
from typing import Dict, List, Any, Optional

DEFAULT_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_notes.txt")

# Lexicons for severity extraction
CRITICAL_KEYWORDS = [
    "urgent", "grinding", "leakage", "grease", "backlash", "seizure",
    "excessively hot", "smoke", "stripped", "failure", "severe", "galling"
]

WARNING_KEYWORDS = [
    "warm", "clicking", "whining", "chatter", "slight", "heat spot",
    "monitor", "elevated", "intermittent", "vibrating", "friction", "jerkiness"
]

NORMAL_KEYWORDS = [
    "routine", "smooth", "clean", "nominal", "within spec", "standard",
    "operating well", "no anomalous", "tolerance"
]

IRRELEVANT_TOPICS = [
    "lunch", "paper towel", "safety signs", "wiped down", "cable ties",
    "dust cover", "vacuumed", "handover checklist", "cabinet", "camera lens"
]

class MaintenanceLogAnalyzer:
    """Free-text log scanner extracting independent health signals for robotic arms."""

    def __init__(self, log_file_path: Optional[str] = None):
        self.log_file_path = log_file_path or DEFAULT_LOG_PATH
        self.entries: List[Dict[str, Any]] = []
        if os.path.exists(self.log_file_path):
            self.load_log_file(self.log_file_path)

    def load_log_file(self, path: str):
        """Parse raw log text into structured entry records."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split entries by timestamp header [YYYY-MM-DD HH:MM]
        raw_blocks = re.split(r"(?=\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\])", content)
        self.entries = []

        for block in raw_blocks:
            block = block.strip()
            if not block or block.startswith("#"):
                continue

            header_match = re.match(r"\[([\d\-:\s]+)\]\s+([^\n:]+):?\n?(.*)", block, re.DOTALL)
            if header_match:
                timestamp = header_match.group(1).strip()
                author = header_match.group(2).strip()
                text = header_match.group(3).strip()
            else:
                timestamp = "UNKNOWN"
                author = "Technician"
                text = block

            analysis = self.analyze_text(text)
            self.entries.append({
                "timestamp": timestamp,
                "author": author,
                "text": text,
                **analysis
            })

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze a single free-text sentence or paragraph.
        Identifies mentioned arms, joints, relevance, and risk classification.
        """
        text_lower = text.lower()

        # Identify mentioned arm IDs (e.g. Arm-1, Arm-2, arm 3)
        arms_found = re.findall(r"\barm[\s\-]?(\d+)\b", text_lower)
        arm_ids = [f"Arm-{num}" for num in arms_found]

        # Identify mentioned joints
        joints_found = []
        for j in ["shoulder", "elbow", "wrist"]:
            if j in text_lower:
                joints_found.append(j)

        # Check for irrelevant facility / housekeeping notes
        is_irrelevant = any(irr in text_lower for irr in IRRELEVANT_TOPICS) and not arms_found

        # Filter out negated patterns like "no leakage", "no visible ... leakage", "no abnormal"
        cleaned_text = re.sub(r"\bno\s+[\w\s]{0,15}(leakage|grease|backlash|grinding|chatter|vibration)", "", text_lower)

        matched_crit = [kw for kw in CRITICAL_KEYWORDS if kw in cleaned_text]
        matched_warn = [kw for kw in WARNING_KEYWORDS if kw in cleaned_text]
        matched_norm = [kw for kw in NORMAL_KEYWORDS if kw in text_lower]

        if matched_crit:
            risk_level = "CRITICAL"
            risk_score = 0.90
            recommendation = "SCHEDULE_MAINTENANCE"
        elif matched_warn:
            risk_level = "WARNING"
            risk_score = 0.50
            recommendation = "MONITOR"
        elif matched_norm and not matched_warn and not matched_crit:
            risk_level = "NORMAL"
            risk_score = 0.05
            recommendation = "SAFE"
        elif is_irrelevant or not arms_found:
            risk_level = "NONE"
            risk_score = 0.0
            recommendation = "NO_ACTION"
        else:
            risk_level = "LOW"
            risk_score = 0.15
            recommendation = "SAFE"

        return {
            "arm_ids": arm_ids,
            "joints": joints_found,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "matched_keywords": matched_crit + matched_warn + matched_norm,
            "is_irrelevant": is_irrelevant,
            "recommendation": recommendation
        }

    def get_signal_for_arm(self, arm_id: str) -> Dict[str, Any]:
        """
        Retrieve the latest, most pertinent maintenance signal for a specific arm.
        """
        relevant_entries = [e for e in self.entries if arm_id.lower() in [a.lower() for a in e.get("arm_ids", [])]]

        if not relevant_entries:
            return {
                "arm_id": arm_id,
                "has_notes": False,
                "risk_level": "NONE",
                "risk_score": 0.0,
                "summary": "No maintenance log entries recorded for this arm.",
                "matched_keywords": [],
                "target_joints": []
            }

        # Select most severe entry
        severity_rank = {"CRITICAL": 3, "WARNING": 2, "LOW": 1, "NORMAL": 0, "NONE": 0}
        top_entry = max(relevant_entries, key=lambda e: severity_rank.get(e["risk_level"], 0))

        return {
            "arm_id": arm_id,
            "has_notes": True,
            "risk_level": top_entry["risk_level"],
            "risk_score": top_entry["risk_score"],
            "summary": top_entry["text"],
            "timestamp": top_entry["timestamp"],
            "matched_keywords": top_entry["matched_keywords"],
            "target_joints": top_entry["joints"]
        }

if __name__ == "__main__":
    analyzer = MaintenanceLogAnalyzer()
    print(f"Loaded {len(analyzer.entries)} log entries.\n")
    for arm in ["Arm-1", "Arm-2", "Arm-3", "Arm-4", "Arm-5"]:
        sig = analyzer.get_signal_for_arm(arm)
        print(f"[{arm}] Risk: {sig['risk_level']} (Score: {sig['risk_score']}) | Keywords: {sig['matched_keywords']}")
        print(f"      Notes: {sig['summary']}\n")
