"""Client types, deal stages, and the rules that turn an email into a client."""
import hashlib
import os
from email.utils import parseaddr

CLIENT_TYPES = ["Large business", "Small business", "Team member"]
UNSORTED = "Unsorted"  # new from email; someone on the team picks the type

STAGES = [
    "Unconfirmed deal",
    "Awaiting client approval",
    "Completed, awaiting invoice",
    "Fully complete",
]

# Free email providers: a sender here is more likely a person or small business.
PERSONAL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
                    "aol.com", "proton.me", "protonmail.com", "me.com", "live.com"}


def _env_list(name: str) -> set[str]:
    return {x.strip().lower() for x in os.getenv(name, "").split(",") if x.strip()}


def parse_sender(header: str) -> tuple[str, str]:
    """'Ana Ruiz <ana@cbre.com>' -> ('Ana Ruiz', 'ana@cbre.com')."""
    name, addr = parseaddr(header or "")
    addr = addr.strip().lower()
    return (name.strip() or addr.split("@")[0]), addr


def domain(addr: str) -> str:
    return addr.rsplit("@", 1)[-1].lower() if "@" in addr else ""


def suggest_type(addr: str) -> str:
    """A first guess the team confirms. Team members are listed in TEAM_EMAILS / TEAM_DOMAINS."""
    d = domain(addr)
    if addr.lower() in _env_list("TEAM_EMAILS") or (d and d in _env_list("TEAM_DOMAINS")):
        return "Team member"
    if d in _env_list("LARGE_CLIENT_DOMAINS"):
        return "Large business"
    if d in PERSONAL_DOMAINS:
        return "Small business"
    return UNSORTED


def company_from(addr: str) -> str:
    d = domain(addr)
    if not d or d in PERSONAL_DOMAINS:
        return ""
    return d.split(".")[0].replace("-", " ").title()


def masked(client: dict) -> str:
    """A stable public label that never reveals the name, e.g. 'Large business · C-4F2A'."""
    h = hashlib.sha256(str(client.get("id", "")).encode()).hexdigest()[:4].upper()
    return f"{client.get('client_type') or UNSORTED} · C-{h}"
