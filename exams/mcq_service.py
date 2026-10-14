"""MCQ attempt snapshots, answer persistence and server-side grading.

The client NEVER receives the `correct` value from the attempt snapshot.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Choice, ExamQuestion, ExamResult, Question, StudentAnswer



def snapshot_for_exam(exam):
    mappings = (ExamQuestion.objects.filter(exam=exam)
                .select_related('question')
                .prefetch_related('question__choices')
                .order_by('position', 'pk'))
    result = []
    for link in mappings:
        q = link.question
        result.append({
            'id': q.pk,
            'question_text': q.question_text,
            'question_image': q.question_image.url if q.question_image else '',
            'mark': link.mark,
            'choices': [
                {'id': c.pk, 'choice_text': c.choice_text, 'correct': c.is_correct}
                for c in q.choices.all()
            ],
        })
    return result


def public_questions(snapshot):
    """Only questions/options/marks are included, never correctness information."""
    return [{
        'id': q['id'], 'question_text': q['question_text'],
        'question_image': q.get('question_image', ''), 'mark': q['mark'],
        'options': [{'id': c['id'], 'choice_text': c['choice_text']}
                    for c in q.get('choices', [])],
    } for q in snapshot]


def ensure_snapshot(result):
    if not result.question_snapshot:
        result.question_snapshot = snapshot_for_exam(result.exam)
        result.save(update_fields=['question_snapshot'])
    return result.question_snapshot


def deadline(result):
    return result.started_at + timedelta(minutes=result.exam.duration_minutes)


def past_deadline(result):
    return timezone.now() >= deadline(result)


def save_batch_locked(result, updates, *, force=False):
    """Caller must hold a row lock on ExamResult inside transaction.atomic.

    Revision checks stop delayed autosaves overwriting newer answers. Answers are
    scoped to this attempt's immutable question and choice identifiers.
    """
    snapshot = {str(q['id']): q for q in ensure_snapshot(result)}
    if not isinstance(updates, list) or len(updates) > len(snapshot) + 5:
        raise ValueError('Invalid answer batch')
    latest = {}
    for entry in updates:
        if not isinstance(entry, dict):
            raise ValueError('Invalid answer')
        try:
            qid = int(entry['question_id'])
            cid = int(entry['choice_id'])
            revision = int(entry.get('revision', 0))
        except (TypeError, ValueError, KeyError, OverflowError):
            raise ValueError('Invalid question/choice/revision')
        if revision < 0 or revision > 2147483647:
            raise ValueError('Invalid revision')
        q = snapshot.get(str(qid))
        if not q or cid not in [int(c['id']) for c in q['choices']]:
            raise ValueError('Answer does not belong to this exam')
        if qid not in latest or revision >= latest[qid]['revision']:
            latest[qid] = {'question_id': qid, 'choice_id': cid, 'revision': revision}

    existing = {a.question_id: a for a in StudentAnswer.objects.filter(
        result=result, question_id__in=latest.keys()
    )}
    choice_ids = [v['choice_id'] for v in latest.values()]
    available = set(Choice.objects.filter(pk__in=choice_ids).values_list('pk', flat=True))
    added, changed = [], []
    for qid, value in latest.items():
        answer = existing.get(qid)
        if answer and not force and value['revision'] < answer.client_revision:
            continue
        if answer is None:
            answer = StudentAnswer(result=result, question_id=qid)
            added.append(answer)
        else:
            changed.append(answer)
        answer.selected_choice_id_snapshot = value['choice_id']
        answer.selected_choice_id = value['choice_id'] if value['choice_id'] in available else None
        answer.client_revision = max(value['revision'], answer.client_revision)
    if added:
        StudentAnswer.objects.bulk_create(added)
    if changed:
        StudentAnswer.objects.bulk_update(
            changed, ['selected_choice', 'selected_choice_id_snapshot', 'client_revision']
        )
    return len(added) + len(changed)


def finalize_locked(result):
    """Compute from stored answers using the marking key frozen at attempt start."""
    if result.is_submitted:
        return result
    snapshot = ensure_snapshot(result)
    answers = {a.question_id: a for a in StudentAnswer.objects.filter(result=result)}
    total = 0
    changed = []
    for q in snapshot:
        a = answers.get(q['id'])
        if a is None:
            continue
        correct = {c['id'] for c in q['choices'] if c.get('correct')}
        marks = q['mark'] if a.selected_choice_id_snapshot in correct else 0
        a.marks_awarded = marks
        total += marks
        changed.append(a)
    if changed:
        StudentAnswer.objects.bulk_update(changed, ['marks_awarded'])
    result.score = total
    result.is_submitted = True
    result.is_evaluated = True
    result.submitted_at = timezone.now()
    result.save(update_fields=['score', 'is_submitted', 'is_evaluated', 'submitted_at'])
    return result


def finalize_expired(result):
    if not result.started_at or result.is_submitted or not past_deadline(result):
        return False
    with transaction.atomic():
        locked = (ExamResult.objects.select_for_update().select_related('exam')
                  .get(pk=result.pk))
        if locked.exam.exam_type == 'mcq' and not locked.is_submitted and past_deadline(locked):
            finalize_locked(locked)
        elif not locked.is_submitted and past_deadline(locked):
            locked.is_submitted = True
            locked.submitted_at = timezone.now()
            locked.save(update_fields=['is_submitted', 'submitted_at'])
    return True
