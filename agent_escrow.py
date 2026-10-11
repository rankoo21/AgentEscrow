# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""AgentEscrow: consensus-reviewed delivery acceptance for autonomous work."""
from genlayer import *
from urllib.parse import urlparse
import hashlib, json

STATES = ("OPEN", "ACCEPTED", "REVISION", "REJECTED")

def clean_id(v):
    v = v.strip().upper()
    if not 3 <= len(v) <= 64 or not all(c.isalnum() or c in "-_" for c in v):
        raise gl.vm.UserError("invalid job id")
    return v

def https(v):
    v = v.strip(); p = urlparse(v)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment:
        raise gl.vm.UserError("clean HTTPS URL required")
    return v

def digest(v): return hashlib.sha256(v.encode()).hexdigest()

def parse_review(raw):
    x = json.loads(raw)
    if type(x) is not dict or set(x) != {"decision", "score", "summary", "missing"}:
        raise ValueError("bad review")
    if x["decision"] not in ("ACCEPT", "REVISION", "REJECT"):
        raise ValueError("bad decision")
    score = int(x["score"])
    if score < 0 or score > 100: raise ValueError("bad score")
    if type(x["missing"] ) is not list or len(x["missing"]) > 12: raise ValueError("bad missing")
    return {"decision": x["decision"], "score": score, "summary": str(x["summary"])[:600], "missing": [str(v)[:160] for v in x["missing"]]}

class AgentEscrow(gl.Contract):
    jobs: TreeMap[str, str]
    def __init__(self): pass
    def _key(self, owner, job_id): return str(owner).lower() + ":" + clean_id(job_id)

    @gl.public.write
    def open_job(self, job_id: str, brief_url: str, deliverable_url: str, acceptance_url: str, instructions: str) -> None:
        owner = str(gl.message.sender_address).lower(); jid = clean_id(job_id); key = self._key(owner, jid)
        if self.jobs.get(key, ""): raise gl.vm.UserError("job already exists")
        urls = [https(brief_url), https(deliverable_url), https(acceptance_url)]
        if len({urlparse(v).hostname for v in urls}) != 3: raise gl.vm.UserError("sources need three distinct hosts")
        instructions = instructions.strip()
        if not 20 <= len(instructions) <= 2000: raise gl.vm.UserError("instructions must be 20-2000 characters")
        self.jobs[key] = json.dumps({"job_id": jid, "owner": owner, "brief": urls[0], "deliverable": urls[1], "acceptance": urls[2], "instructions": instructions, "state": "OPEN", "decision": "", "score": 0, "summary": "", "missing": [], "digests": []}, sort_keys=True, separators=(",", ":"))

    @gl.public.write
    def review_delivery(self, job_id: str) -> None:
        key = self._key(gl.message.sender_address, job_id); record = json.loads(self.jobs.get(key, "{}"))
        if not record or record["state"] != "OPEN": raise gl.vm.UserError("job is not open")
        captured = {}
        def run():
            bodies = [gl.nondet.web.get(u).body.decode("utf-8") for u in (record["brief"], record["deliverable"], record["acceptance"])]
            if any(not 2 <= len(v) <= 120000 for v in bodies): raise gl.vm.UserError("evidence unavailable")
            captured["bodies"] = bodies
            prompt = ("Review an autonomous agent delivery against the supplied brief and acceptance policy. "
                      "Return JSON only with decision ACCEPT, REVISION, or REJECT; score 0-100; concise summary; "
                      "and missing list. Use REJECT only when the delivery is unusable.\nINSTRUCTIONS:\n" + record["instructions"] +
                      "\nBRIEF:\n" + bodies[0] + "\nDELIVERABLE:\n" + bodies[1] + "\nACCEPTANCE POLICY:\n" + bodies[2])
            return {**parse_review(gl.nondet.exec_prompt(prompt).strip()), "digests": [digest(v) for v in bodies]}
        def validate(leader_result):
            if not isinstance(leader_result, gl.vm.Return): return False
            own = run()
            leader = leader_result.calldata
            return leader["decision"] == own["decision"] and abs(int(leader["score"]) - int(own["score"])) <= 15
        result = gl.vm.run_nondet_unsafe(run, validate)
        bodies = captured["bodies"]
        record.update({"decision": result["decision"], "score": result["score"], "summary": result["summary"], "missing": result["missing"], "digests": result["digests"], "state": {"ACCEPT": "ACCEPTED", "REVISION": "REVISION", "REJECT": "REJECTED"}[result["decision"]]})
        self.jobs[key] = json.dumps(record, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_job(self, owner: str, job_id: str) -> str: return self.jobs.get(self._key(owner, job_id), "{}")




