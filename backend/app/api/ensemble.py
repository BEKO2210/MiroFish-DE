"""HTTP-Vertrag für V3/V4-Mehrfachläufe."""

from flask import Blueprint, jsonify, request

from ..services.ensemble import EnsembleService
from ..utils.logger import get_logger

ensemble_bp = Blueprint("ensemble", __name__)
logger = get_logger("mirofish.api.ensemble")
service = EnsembleService()

START_FIELDS = {
    "simulation_id", "runs", "hours", "variants", "start_hour",
    "minutes_per_round", "custom_outcomes", "primary_outcome_id",
    "text_model", "arm_model", "strict_second_rater", "min_classified",
    "min_posts", "max_agent_error_rate", "second_rater",
}


def _error(message: str, status: int):
    return jsonify({"success": False, "error": message}), status


@ensemble_bp.route("/start", methods=["POST"])
def start_ensemble():
    data = request.get_json(silent=True) or {}
    try:
        if not isinstance(data, dict):
            raise TypeError("JSON-Anfrage muss ein Objekt sein")
        unknown = sorted(set(data) - START_FIELDS)
        if unknown:
            raise ValueError("Unbekannte Startparameter: " + ", ".join(unknown))
        result = service.start(
            simulation_id=data.get("simulation_id"),
            runs=data.get("runs", 10),
            hours=data.get("hours", 24),
            variants=data.get("variants", ["baseline"]),
            start_hour=data.get("start_hour", 7),
            minutes_per_round=data.get("minutes_per_round", 60),
            custom_outcomes=data.get("custom_outcomes"),
            primary_outcome_id=data.get("primary_outcome_id"),
            text_model=data.get("text_model"),
            arm_model=data.get("arm_model"),
            strict_second_rater=data.get("strict_second_rater", False),
            second_rater=data.get("second_rater"),
            min_classified=data.get("min_classified"),
            min_posts=data.get("min_posts", 1),
            max_agent_error_rate=data.get("max_agent_error_rate", 0.5),
        )
        return jsonify({"success": True, "data": result})
    except FileNotFoundError as error:
        return _error(str(error), 404)
    except (TypeError, ValueError) as error:
        return _error(str(error), 400)
    except Exception as error:
        logger.exception("Ensemble konnte nicht gestartet werden")
        return _error(str(error), 500)


@ensemble_bp.route("/list", methods=["GET"])
def list_ensembles():
    return jsonify(
        {
            "success": True,
            "data": service.list(request.args.get("simulation_id") or None),
        }
    )


@ensemble_bp.route("/<ensemble_id>", methods=["GET"])
def get_ensemble(ensemble_id: str):
    try:
        data = service.get(ensemble_id)
    except ValueError as error:
        return _error(str(error), 400)
    if data is None:
        return _error(f"Ensemble nicht gefunden: {ensemble_id}", 404)
    return jsonify({"success": True, "data": data})


@ensemble_bp.route("/<ensemble_id>/cancel", methods=["POST"])
def cancel_ensemble(ensemble_id: str):
    try:
        service.cancel(ensemble_id)
        return jsonify({"success": True})
    except FileNotFoundError:
        return _error(f"Ensemble nicht gefunden: {ensemble_id}", 404)
    except ValueError as error:
        return _error(str(error), 400)


@ensemble_bp.route("/<ensemble_id>/resume", methods=["POST"])
def resume_ensemble(ensemble_id: str):
    try:
        return jsonify({"success": True, "data": service.resume(ensemble_id)})
    except FileNotFoundError:
        return _error(f"Ensemble nicht gefunden: {ensemble_id}", 404)
    except RuntimeError as error:
        return _error(str(error), 409)
    except ValueError as error:
        return _error(str(error), 400)
    except Exception as error:
        logger.exception("Ensemble konnte nicht fortgesetzt werden")
        return _error(str(error), 500)


@ensemble_bp.route("/<ensemble_id>/reclassify", methods=["POST"])
def reclassify_ensemble(ensemble_id: str):
    try:
        return jsonify({"success": True, "data": service.reclassify(ensemble_id)})
    except FileNotFoundError as error:
        return _error(str(error), 404)
    except RuntimeError as error:
        return _error(str(error), 409)
    except ValueError as error:
        return _error(str(error), 400)
    except Exception as error:
        logger.exception("Ensemble konnte nicht neu klassifiziert werden")
        return _error(str(error), 500)


@ensemble_bp.route("/<ensemble_id>", methods=["DELETE"])
def delete_ensemble(ensemble_id: str):
    try:
        service.delete(ensemble_id)
        return jsonify({"success": True})
    except FileNotFoundError:
        return _error(f"Ensemble nicht gefunden: {ensemble_id}", 404)
    except RuntimeError as error:
        return _error(str(error), 409)
    except ValueError as error:
        return _error(str(error), 400)


def mark_stale_ensembles() -> int:
    """Beim Backend-Start verlorene Hintergrundthreads sichtbar abschließen."""
    return service.mark_stale_runs()
