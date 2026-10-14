# Master X's Academy — Examination Upgrade

This ZIP is the updated Django **source project**, based on the supplied `tuition_website (3)(1).7z` archive. It **does not contain** the previous Windows `venv`, Git history, `.env`, SQLite database, media/student uploads, or credentials. Your existing production database and Cloudinary assets were not modified.

## What was changed

- **Independent MCQ result controls** in Django Admin → Exams → Edit: Publish marks, Publish ranks, Publish answer keys. The student result URL now respects these controls even when reopened after submission.
- **Per-exam instructions and declaration:** enable/disable instruction page and require/omit acceptance checkbox. The timer starts only on Start Examination; acceptance time is saved when required.
- **Reusable question pool:** Django Admin → Questions is the central bank. Create a question and options once, then link it to multiple exams using each exam's *Questions selected from the shared question bank* inline. Marks and sequence are per-exam. Optional class/subject/topic/difficulty tags aid search.
- **Legacy questions migrated:** migration 0010 maps existing questions to their current exams and retains old question/answer/result IDs. Historical MCQ question definitions are snapshotted to protect earlier result review if the shared question later changes. Attempts started after the upgrade also receive immutable per-attempt question/answer-key snapshots.
- **MCQ low-network protection:** answers saved immediately to this browser's localStorage, then sent to the server in small revisioned batches (autosave). Full answers are also transmitted during final submit, and local data is cleared **only after confirmed submission**. Server marks and submits atomically.
- **Refresh-safe countdown:** timer based on the server-recorded attempt start and deadline. Reloading doesn't restart the clock. The server enforces the deadline.
- **Other exam types:** old written/photo/PDF-upload workflows, student login, dashboard, teaching materials and registration apps have been retained. No changes to third-party hosting settings.

## Critical deployment safety steps

1. **Back up the live Render PostgreSQL database** and preserve the original deployed source/commit and env variables **before** deploying. Do not run `flush`, delete the database, or discard your Cloudinary files.
2. In a **separate staging environment** using a copy of production data if possible, install this project, set the same required environment variables as production, then run:

   ```bash
   python manage.py check
   python manage.py makemigrations --check --dry-run
   python manage.py migrate
   python manage.py test exams
   python manage.py collectstatic --noinput
   ```

3. In Django Admin, check **Questions** and the **Exam → Questions selected from the shared question bank** inline, especially existing questions. Create a new MCQ test and attempt it using 2 student logins. Check hidden/published marks, keys and rank; refresh mid-exam and simulate temporary disconnection before publishing.
4. After staging passes, deploy the code to Render through your normal Git deployment process, run the migrations **exactly once** against the live database, verify the site and student login, and keep the backup available for rollback.
5. For the planned NMMS exam, **explicitly disable Publish marks / Publish ranks / Publish answer keys** until you wish to release them. **New exams default to all three disabled. Existing MCQ exams are initialized to their *previous* visibility behavior** (marks and ranks enabled) so their existing published results are not unexpectedly hidden during migration. Set old exam checkboxes manually if you want to withhold those results.
6. Configure **Enable instructions** and **Require declaration** on the NMMS exam and enter candidate instructions. Other exams can leave them disabled.
7. **Do not edit shared question text/options or exam mappings once the exam starts for students.** Snapshots protect already-started attempts, but a student starting after a bank edit could see the newer version. Prepare/freeze questions before opening the exam.

## Low-network and scalability limitations

- This is **offline-tolerant**, **not a guaranteed fully offline examination**. Once loaded, questions and choices remain available in the open page and selected MCQ answers are stored locally. Reloading the page *while fully offline* may fail because HTML or assets might not be cached. Losing browser storage, using incognito, or switching devices can lose **unsynced** selections.
- Answers that have **not reached the server before the server deadline cannot be guaranteed to be marked**. Students should verify the **All selected answers saved on MXA server** message before the deadline. A failed final submission keeps local answers and lets the student retry while time remains.
- The server sends only questions and choices to students, **not the grading key**. Saving/marking is performed server-side with per-attempt locking. No real 100-user concurrency load test was run here; Render service size, Gunicorn workers, DB connections and network conditions must be tested before the live NMMS exam.
- Bootstrap styles load from a CDN. Limited/offline network access may delay styles, though existing loaded pages should retain exam functionality.
- Student answers from other browser/device tabs can conflict. For reliable recovery, use the **same browser and device** during an attempt.

## Development verification

- Python source files passed Python syntax compilation.
- New MCQ JavaScript passed Node.js syntax checking.
- `exams/tests.py` contains Django functional regression tests for result visibility, instructions, question reuse, revision-safe autosave, deadline and answer-key snapshots.
- **Django runtime checks/migrations/tests and live load testing were not executed in this environment** because the necessary compatible Django runtime packages were not installed here. These must run in staging before production deployment.

## Files principally changed

`exams/models.py`, `exams/migrations/0010_exam_upgrades.py`, `exams/mcq_service.py`, `exams/views.py`, `exams/admin.py`, `exams/urls.py`, `exams/tests.py`, `templates/take_exam.html`, `templates/exam_result.html`, `templates/exam_list.html`, `templates/exam_instructions.html`, `static/js/mxa_mcq.js`.
