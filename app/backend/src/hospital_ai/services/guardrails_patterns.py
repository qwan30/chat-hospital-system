"""Safety guardrail regex patterns.
Tập hợp các biểu thức chính quy (regex patterns) nhằm phát hiện tấn công
tiêm nhiễm prompt, vượt rào (jailbreak), rò rỉ PHI và chẩn đoán y tế trái phép.
"""

import re

# Comprehensive list of patterns for detecting prompt injection attempts
# Danh sách toàn diện các mẫu regex dùng để phát hiện các nỗ lực tiêm nhiễm prompt (prompt injection)
INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"ignore previous instructions",
        r"ignore all prior",
        r"you are now",
        r"act as",
        r"pretend you are",
        r"forget your instructions",
        r"system prompt",
        r"DAN mode",
        r"jailbreak",
        r"bypass",
        r"override",
        r"disregard",
        r"new persona",
        r"roleplay as",
        r"ignore the above",
        r"forget everything",
        r"print your instructions",
        r"what are your instructions",
        r"what is your system prompt",
        r"reveal your instructions",
        r"developer mode",
        r"do anything now",
        r"always comply",
        r"no restrictions",
        r"without limits",
        r"unfiltered",
        r"unrestricted",
        r"disable filters",
        r"turn off safety",
        r"safety off",
    ]
]

# Patterns for detecting role-play or jailbreak attempts
# Các mẫu phát hiện hành vi cố tình yêu cầu nhập vai (role-play) hoặc vượt rào an toàn (jailbreak)
JAILBREAK_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"you are DAN",
        r"you can do anything",
        r"let's play a game",
        r"imagine you are",
        r"in this hypothetical",
        r"for educational purposes only",
        r"write a story where you",
        r"translate the following from",
        r"encode the following",
        r"decode the following",
        r"base64",
        r"hex encoded",
        r"rot13",
        r"respond only with",
        r"start your response with",
    ]
]

# Patterns for detecting Protected Health Information (PHI)
# Các mẫu regex phát hiện Thông tin Y tế Được bảo vệ (PHI) như SSN, Email, SĐT, mã bệnh án (MRN), Ngày sinh
PHI_PATTERNS = {
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # Simple email regex for detection
    "Email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    # Basic phone number pattern (US format)
    "Phone": re.compile(r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b"),
    # MRN pattern (assuming typical formats, adjust as needed)
    "MRN": re.compile(r"\b(?:MRN|Medical Record Number)[\s:]*([A-Z0-9-]{5,15})\b", re.IGNORECASE),
    # Date of Birth
    "DOB": re.compile(r"\b(?:DOB|Date of Birth)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", re.IGNORECASE),
}

# Indicators of providing uncited medical advice
# Các dấu hiệu phát hiện việc đưa ra lời khuyên/chẩn đoán y tế thiếu căn cứ hoặc trích dẫn
MEDICAL_ADVICE_INDICATORS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"you should take",
        r"I prescribe",
        r"dosage",
        r"administer",
        r"treatment plan",
        r"my recommendation is",
        r"you need to",
        r"take \d+(?:mg|g|mcg|ml)",
        r"stop taking",
        r"start taking",
        r"diagnosis is",
        r"you have (?!been)",
    ]
]
