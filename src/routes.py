"""Route handlers for the application tracker, registered onto the Flask app in app.py."""

from datetime import date, datetime

from flask import flash, g, redirect, render_template, request, url_for

from src import crud
from src.stats import compute_stats

STATUS_CHOICES = ["applied", "interviewing", "offer", "rejected", "withdrawn"]
SOON_THRESHOLD_DAYS = 3


def register_routes(app):
    @app.route("/")
    def index():
        status_filter = request.args.get("status") or None
        sort_by = request.args.get("sort", "date_applied")
        sort_dir = request.args.get("dir", "desc")
        applications = crud.list_applications(
            g.db, status=status_filter, sort_by=sort_by, sort_dir=sort_dir
        )
        return render_template(
            "index.html",
            applications=applications,
            status_choices=STATUS_CHOICES,
            status_filter=status_filter,
            sort_by=sort_by,
            sort_dir=sort_dir,
            today=date.today(),
            soon_threshold=SOON_THRESHOLD_DAYS,
        )

    @app.route("/stats")
    def stats():
        return render_template("stats.html", stats=compute_stats(g.db), status_choices=STATUS_CHOICES)

    @app.route("/applications/new", methods=["GET", "POST"])
    def new_application():
        if request.method == "POST":
            form_data = _parse_form(request.form)
            error = _validate(form_data)
            if error:
                flash(error, "error")
                return render_template(
                    "form.html", application=form_data, status_choices=STATUS_CHOICES, mode="new"
                )
            crud.add_application(g.db, **form_data)
            flash(f"Added {form_data['company']} - {form_data['role']}.", "success")
            return redirect(url_for("index"))
        return render_template("form.html", application=None, status_choices=STATUS_CHOICES, mode="new")

    @app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
    def edit_application(application_id):
        application = crud.get_application(g.db, application_id)
        if application is None:
            flash("Application not found.", "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            form_data = _parse_form(request.form)
            error = _validate(form_data)
            if error:
                flash(error, "error")
                return render_template(
                    "form.html",
                    application=form_data,
                    status_choices=STATUS_CHOICES,
                    mode="edit",
                    application_id=application_id,
                )
            crud.update_application(g.db, application_id, **form_data)
            flash("Application updated.", "success")
            return redirect(url_for("index"))

        return render_template(
            "form.html",
            application=application,
            status_choices=STATUS_CHOICES,
            mode="edit",
            application_id=application_id,
        )

    @app.route("/applications/<int:application_id>/delete", methods=["POST"])
    def delete_application(application_id):
        deleted = crud.delete_application(g.db, application_id)
        flash("Application deleted." if deleted else "Application not found.", "success" if deleted else "error")
        return redirect(url_for("index"))


def _parse_date(form, field):
    raw = (form.get(field) or "").strip()
    if not raw:
        return None
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _parse_form(form):
    return {
        "company": (form.get("company") or "").strip(),
        "role": (form.get("role") or "").strip(),
        "date_applied": _parse_date(form, "date_applied") or date.today(),
        "status": form.get("status") or "applied",
        "deadline": _parse_date(form, "deadline"),
        "follow_up_date": _parse_date(form, "follow_up_date"),
        "notes": (form.get("notes") or "").strip() or None,
        "job_link": (form.get("job_link") or "").strip() or None,
        "tech_tags": (form.get("tech_tags") or "").strip() or None,
    }


def _validate(form_data):
    if not form_data["company"] or not form_data["role"]:
        return "Company and role are required."
    return None
