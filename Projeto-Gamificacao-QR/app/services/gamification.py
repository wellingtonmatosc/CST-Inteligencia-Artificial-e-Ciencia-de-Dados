"""Regras centrais de QR, questões, tentativas, bônus e ranking."""
from __future__ import annotations

import secrets
from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.errors import AppError
from app.repositories.supabase_repo import SupabaseRepository
from app.services.questions import evaluate_answer
from app.services.scoring import MILESTONES, score_for_attempt


class GamificationService:
    def __init__(self, repo: SupabaseRepository, timezone_name: str):
        self.repo = repo
        self.tz = ZoneInfo(timezone_name)

    def _today(self) -> str:
        return datetime.now(self.tz).date().isoformat()

    def _now_iso(self) -> str:
        return datetime.now(self.tz).isoformat()

    def get_qr(self, participant_id: str, code: str) -> dict:
        qrs = self.repo.select("qr_points", code=code, active=True)
        if not qrs:
            raise AppError("QR Code inválido ou inativo.", 404)
        qr = qrs[0]
        if qr["kind"] == "normal":
            return self._get_normal_activity(participant_id, qr)
        return self._get_bonus(participant_id, qr)

    def _get_normal_activity(self, participant_id: str, qr: dict) -> dict:
        today = self._today()
        existing = (
            self.repo.raw_table("activity_runs").select("*")
            .eq("participant_id", participant_id).eq("qr_point_id", qr["id"])
            .eq("activity_date", today).limit(1).execute().data or []
        )
        if existing:
            return self._run_response(existing[0], qr)

        pool = self.repo.select("qr_question_pool", qr_point_id=qr["id"])
        if not pool:
            raise AppError("Este QR ainda não possui questões configuradas.", 409)
        pool_ids = [row["question_id"] for row in pool]
        history = self.repo.select("participant_question_history", participant_id=participant_id)
        seen = {row["question_id"] for row in history}
        unseen = [qid for qid in pool_ids if qid not in seen]
        if not unseen:
            raise AppError("Você já respondeu todas as questões inéditas disponíveis neste ponto.", 409)

        questions = self.repo.raw_table("questions").select("*").in_("id", unseen).eq("active", True).execute().data or []
        if not questions:
            raise AppError("Não há questões ativas e inéditas disponíveis.", 409)
        question = secrets.choice(questions)
        self.repo.insert("participant_question_history", {
            "participant_id": participant_id,
            "question_id": question["id"],
            "source_qr_point_id": qr["id"],
        })
        run = self.repo.insert("activity_runs", {
            "participant_id": participant_id,
            "qr_point_id": qr["id"],
            "question_id": question["id"],
            "activity_date": today,
            "status": "in_progress",
        })
        return self._run_response(run, qr, question)

    def _run_response(self, run: dict, qr: dict, question: dict | None = None) -> dict:
        if question is None and run.get("question_id"):
            rows = self.repo.select("questions", id=run["question_id"])
            question = rows[0] if rows else None
        public_question = self._public_question(question) if question else None
        return {
            "mode": "normal",
            "qr": {"code": qr["code"], "name": qr["name"]},
            "run_id": run["id"],
            "status": run["status"],
            "attempts": run.get("attempts_count", 0),
            "points_awarded": run.get("points_awarded", 0),
            "question": public_question if run["status"] == "in_progress" else None,
        }

    def answer_normal(self, participant_id: str, run_id: str, answer) -> dict:
        rows = self.repo.select("activity_runs", id=run_id, participant_id=participant_id)
        if not rows:
            raise AppError("Atividade não encontrada.", 404)
        run = rows[0]
        if run["status"] != "in_progress":
            raise AppError("Esta atividade já foi finalizada.", 409)
        question = self.repo.select("questions", id=run["question_id"])[0]
        attempt_no = int(run.get("attempts_count", 0)) + 1
        correct = evaluate_answer(question, answer)
        self.repo.insert("attempts", {
            "participant_id": participant_id,
            "activity_run_id": run_id,
            "question_id": question["id"],
            "attempt_number": attempt_no,
            "answer": {"value": answer},
            "correct": correct,
        })
        if correct:
            points = score_for_attempt(10, attempt_no)
            self.repo.update("activity_runs", {
                "status": "completed", "attempts_count": attempt_no,
                "points_awarded": points, "completed_at": self._now_iso(),
            }, id=run_id)
            self._ledger(participant_id, "normal_activity", run_id, points, f"activity:{run_id}")
            milestones = self._award_milestones(participant_id)
            return {"correct": True, "completed": True, "points": points, "milestones": milestones}

        status = "failed" if attempt_no >= 3 else "in_progress"
        self.repo.update("activity_runs", {"status": status, "attempts_count": attempt_no}, id=run_id)
        return {"correct": False, "completed": status == "failed", "attempts": attempt_no, "remaining": max(0, 3-attempt_no), "points": 0}

    def _get_bonus(self, participant_id: str, qr: dict) -> dict:
        now = self._now_iso()
        locs = (
            self.repo.raw_table("bonus_locations")
            .select("*,bonus_campaigns(*)")
            .eq("qr_point_id", qr["id"]).lte("starts_at", now).gt("ends_at", now)
            .eq("active", True).execute().data or []
        )
        if not locs:
            raise AppError("Este QR bônus não está ativo neste horário.", 409)
        loc = locs[0]
        campaign = loc.get("bonus_campaigns") or {}
        if not campaign or not campaign.get("active"):
            raise AppError("Bônus indisponível.", 409)
        existing = self.repo.select("bonus_runs", participant_id=participant_id, campaign_id=campaign["id"])
        if existing:
            run = existing[0]
            return self._bonus_response(run, campaign, qr)

        categories = self.repo.select("categories", active=True)
        if len(categories) < 3:
            raise AppError("Cadastre pelo menos três categorias ativas para o bônus.", 409)
        choices = secrets.SystemRandom().sample(categories, 3)
        run = self.repo.insert("bonus_runs", {
            "participant_id": participant_id,
            "campaign_id": campaign["id"],
            "bonus_location_id": loc["id"],
            "choice_category_ids": [c["id"] for c in choices],
            "status": "choosing",
        })
        return self._bonus_response(run, campaign, qr, choices)

    def _bonus_response(self, run: dict, campaign: dict, qr: dict, choices: list[dict] | None = None) -> dict:
        if choices is None:
            ids = run.get("choice_category_ids") or []
            choices = self.repo.raw_table("categories").select("id,name,slug").in_("id", ids).execute().data or [] if ids else []
        question = None
        if run.get("question_id") and run["status"] == "in_progress":
            q = self.repo.select("questions", id=run["question_id"])
            question = self._public_question(q[0]) if q else None
        return {
            "mode": "bonus",
            "qr": {"code": qr["code"], "name": qr["name"]},
            "bonus_run_id": run["id"],
            "campaign": {"name": campaign["name"], "type": campaign["bonus_type"], "points": campaign["points"]},
            "status": run["status"],
            "categories": [{"id": c["id"], "name": c["name"]} for c in choices],
            "question": question,
            "points_awarded": run.get("points_awarded", 0),
        }

    def choose_bonus_category(self, participant_id: str, bonus_run_id: str, category_id: str) -> dict:
        runs = self.repo.select("bonus_runs", id=bonus_run_id, participant_id=participant_id)
        if not runs:
            raise AppError("Bônus não encontrado.", 404)
        run = runs[0]
        if run["status"] != "choosing":
            raise AppError("A categoria deste bônus já foi escolhida.", 409)
        if category_id not in (run.get("choice_category_ids") or []):
            raise AppError("Categoria não disponível para este bônus.", 422)
        history = self.repo.select("participant_question_history", participant_id=participant_id)
        seen = {r["question_id"] for r in history}
        questions = self.repo.select("questions", category_id=category_id, active=True)
        unseen = [q for q in questions if q["id"] not in seen]
        if not unseen:
            raise AppError("Não há questões inéditas nesta categoria. Escolha outra opção disponível.", 409)
        question = secrets.choice(unseen)
        self.repo.insert("participant_question_history", {
            "participant_id": participant_id,
            "question_id": question["id"],
            "source_bonus_run_id": run["id"],
        })
        self.repo.update("bonus_runs", {"category_id": category_id, "question_id": question["id"], "status": "in_progress"}, id=run["id"])
        return {"bonus_run_id": run["id"], "status": "in_progress", "question": self._public_question(question)}

    def answer_bonus(self, participant_id: str, bonus_run_id: str, answer) -> dict:
        runs = self.repo.select("bonus_runs", id=bonus_run_id, participant_id=participant_id)
        if not runs:
            raise AppError("Bônus não encontrado.", 404)
        run = runs[0]
        if run["status"] != "in_progress":
            raise AppError("Este bônus já foi finalizado.", 409)
        question = self.repo.select("questions", id=run["question_id"])[0]
        campaign = self.repo.select("bonus_campaigns", id=run["campaign_id"])[0]
        attempt_no = int(run.get("attempts_count", 0)) + 1
        correct = evaluate_answer(question, answer)
        self.repo.insert("attempts", {
            "participant_id": participant_id,
            "bonus_run_id": run["id"],
            "question_id": question["id"],
            "attempt_number": attempt_no,
            "answer": {"value": answer},
            "correct": correct,
        })
        if correct:
            points = score_for_attempt(int(campaign["points"]), attempt_no)
            self.repo.update("bonus_runs", {
                "status": "completed", "attempts_count": attempt_no,
                "points_awarded": points, "completed_at": self._now_iso(),
            }, id=run["id"])
            self._ledger(participant_id, campaign["bonus_type"], run["id"], points, f"bonus:{run['id']}")
            return {"correct": True, "completed": True, "points": points}
        status = "failed" if attempt_no >= 3 else "in_progress"
        self.repo.update("bonus_runs", {"status": status, "attempts_count": attempt_no}, id=run["id"])
        return {"correct": False, "completed": status == "failed", "attempts": attempt_no, "remaining": max(0, 3-attempt_no), "points": 0}

    def _award_milestones(self, participant_id: str) -> list[dict]:
        today = self._today()
        completed = (
            self.repo.raw_table("activity_runs").select("id", count="exact")
            .eq("participant_id", participant_id).eq("activity_date", today).eq("status", "completed")
            .execute()
        )
        count = completed.count or len(completed.data or [])
        awarded = []
        for threshold, points in MILESTONES.items():
            if count < threshold:
                continue
            key = f"milestone:{participant_id}:{today}:{threshold}"
            existing = self.repo.select("point_ledger", dedupe_key=key)
            if not existing:
                self._ledger(participant_id, "milestone", None, points, key, {"threshold": threshold})
                awarded.append({"threshold": threshold, "points": points})
        return awarded

    def _ledger(self, participant_id: str, event_type: str, source_id: str | None, points: int, dedupe_key: str, metadata: dict | None = None):
        if self.repo.select("point_ledger", dedupe_key=dedupe_key):
            return
        self.repo.insert("point_ledger", {
            "participant_id": participant_id, "event_type": event_type,
            "source_id": source_id, "points": points, "activity_date": self._today(),
            "dedupe_key": dedupe_key, "metadata": metadata or {},
        })

    @staticmethod
    def _public_question(question: dict | None) -> dict | None:
        if not question:
            return None
        return {
            "id": question["id"], "kind": question["kind"], "prompt": question["prompt"],
            "options": question.get("options") or [], "media_url": question.get("media_url"),
            "media_type": question.get("media_type"), "accessibility": question.get("accessibility") or {},
            "difficulty": question.get("difficulty", 1),
        }

    def ranking(self, limit: int = 100) -> list[dict]:
        participants = {p["id"]: p for p in self.repo.raw_table("participants").select("id,nick").eq("active", True).execute().data or []}
        ledgers = self.repo.raw_table("point_ledger").select("participant_id,points").execute().data or []
        runs = self.repo.raw_table("activity_runs").select("participant_id,question_id,status").eq("status", "completed").execute().data or []
        bonus_runs = self.repo.raw_table("bonus_runs").select("participant_id,question_id,status").eq("status", "completed").execute().data or []
        questions = self.repo.raw_table("questions").select("id,category_id").execute().data or []
        attempts = self.repo.raw_table("attempts").select("participant_id,attempt_number,correct").eq("correct", True).eq("attempt_number", 1).execute().data or []

        question_category = {q["id"]: q["category_id"] for q in questions}
        totals: dict[str, int] = {}
        normal_completed: dict[str, int] = {}
        categories_seen: dict[str, set[str]] = {}
        first_try: dict[str, int] = {}
        for row in ledgers:
            totals[row["participant_id"]] = totals.get(row["participant_id"], 0) + int(row["points"])
        for row in runs:
            pid=row["participant_id"]; normal_completed[pid]=normal_completed.get(pid,0)+1
            cat=question_category.get(row.get("question_id"))
            if cat: categories_seen.setdefault(pid,set()).add(cat)
        for row in bonus_runs:
            pid=row["participant_id"]; cat=question_category.get(row.get("question_id"))
            if cat: categories_seen.setdefault(pid,set()).add(cat)
        for row in attempts:
            first_try[row["participant_id"]]=first_try.get(row["participant_id"],0)+1

        rows=[]
        for pid, participant in participants.items():
            if pid not in totals:
                continue
            rows.append({
                "nick": participant["nick"],
                "points": totals.get(pid,0),
                "normal_completed": normal_completed.get(pid,0),
                "category_diversity": len(categories_seen.get(pid,set())),
                "first_try_correct": first_try.get(pid,0),
            })
        rows.sort(key=lambda r: (-r["points"], -r["normal_completed"], -r["category_diversity"], -r["first_try_correct"], r["nick"].lower()))
        previous_metrics=None; previous_position=0
        for idx,row in enumerate(rows,1):
            metrics=(row["points"],row["normal_completed"],row["category_diversity"],row["first_try_correct"])
            if metrics != previous_metrics:
                previous_position=idx; previous_metrics=metrics
            row["position"]=previous_position
        return rows[:limit]

    def participant_summary(self, participant_id: str) -> dict:
        today = self._today()
        ledger = self.repo.select("point_ledger", participant_id=participant_id)
        points = sum(int(x["points"]) for x in ledger)
        runs = self.repo.select("activity_runs", participant_id=participant_id, activity_date=today)
        bonuses = self.repo.select("bonus_runs", participant_id=participant_id)
        return {
            "points": points,
            "normal_completed_today": sum(1 for r in runs if r["status"] == "completed"),
            "bonuses_completed": sum(1 for r in bonuses if r["status"] == "completed"),
        }
