from django.db import migrations, models
import django.db.models.deletion


def populate_links(apps, schema_editor):
    Question = apps.get_model('exams', 'Question')
    ExamQuestion = apps.get_model('exams', 'ExamQuestion')
    Exam = apps.get_model('exams', 'Exam')
    StudentAnswer = apps.get_model('exams', 'StudentAnswer')
    # Preserve the visibility existing MCQ students already had, but new exams start private.
    for exam in Exam.objects.all().iterator():
        if exam.exam_type == 'mcq':
            exam.publish_marks = True
            exam.publish_ranks = True
            exam.publish_answer_keys = exam.show_answer_review
        else:
            exam.publish_marks = exam.result_published
            exam.publish_ranks = exam.result_published
        exam.save(update_fields=['publish_marks', 'publish_ranks', 'publish_answer_keys'])
    exams_by_id = {e.pk: (e.class_level_id, e.subject_id) for e in Exam.objects.all().only('pk', 'class_level_id', 'subject_id')}
    batch = []
    question_updates = []
    for q in Question.objects.exclude(exam_id__isnull=True).iterator():
        q.class_level_id, q.subject_id = exams_by_id[q.exam_id]
        question_updates.append(q)
        if len(question_updates) >= 500:
            Question.objects.bulk_update(question_updates, ['class_level', 'subject'])
            question_updates.clear()
        batch.append(ExamQuestion(exam_id=q.exam_id, question_id=q.pk, mark=q.mark, position=q.pk))
        if len(batch) >= 500:
            ExamQuestion.objects.bulk_create(batch, ignore_conflicts=True)
            batch.clear()
    if batch:
        ExamQuestion.objects.bulk_create(batch, ignore_conflicts=True)
    if question_updates:
        Question.objects.bulk_update(question_updates, ['class_level', 'subject'])
    answer_updates = []
    for a in StudentAnswer.objects.exclude(selected_choice_id__isnull=True).iterator():
        a.selected_choice_id_snapshot = a.selected_choice_id
        answer_updates.append(a)
        if len(answer_updates) >= 500:
            StudentAnswer.objects.bulk_update(answer_updates, ['selected_choice_id_snapshot'])
            answer_updates.clear()
    if answer_updates:
        StudentAnswer.objects.bulk_update(answer_updates, ['selected_choice_id_snapshot'])

    # Freeze the old MCQ question and marking definitions for historical attempts.
    # This does not change existing marks, submissions, or student answers.
    Choice = apps.get_model('exams', 'Choice')
    ExamResult = apps.get_model('exams', 'ExamResult')
    snapshots = {}
    for exam in Exam.objects.filter(exam_type='mcq').iterator():
        links = (ExamQuestion.objects.filter(exam_id=exam.pk)
                 .select_related('question').order_by('position', 'pk'))
        qs = list(links)
        choices_by_question = {}
        for choice in Choice.objects.filter(question_id__in=[link.question_id for link in qs]).order_by('pk'):
            choices_by_question.setdefault(choice.question_id, []).append({
                'id': choice.pk,
                'choice_text': choice.choice_text,
                'correct': choice.is_correct,
            })
        snapshot = []
        for link in qs:
            question = link.question
            try:
                image_url = question.question_image.url if question.question_image else ''
            except Exception:
                image_url = ''
            snapshot.append({
                'id': question.pk,
                'question_text': question.question_text,
                'question_image': image_url,
                'mark': link.mark,
                'choices': choices_by_question.get(question.pk, []),
            })
        snapshots[exam.pk] = snapshot
    result_updates = []
    for result in ExamResult.objects.filter(exam__exam_type='mcq', question_snapshot=[]).iterator():
        result.question_snapshot = snapshots.get(result.exam_id, [])
        result_updates.append(result)
        if len(result_updates) >= 200:
            ExamResult.objects.bulk_update(result_updates, ['question_snapshot'])
            result_updates.clear()
    if result_updates:
        ExamResult.objects.bulk_update(result_updates, ['question_snapshot'])


class Migration(migrations.Migration):
    dependencies = [('exams', '0009_increase_exam_filefield_length')]
    operations = [
        migrations.AddField('exam', 'publish_marks', models.BooleanField(default=False)),
        migrations.AddField('exam', 'publish_ranks', models.BooleanField(default=False)),
        migrations.AddField('exam', 'publish_answer_keys', models.BooleanField(default=False)),
        migrations.AddField('exam', 'instructions_enabled', models.BooleanField(default=False)),
        migrations.AddField('exam', 'declaration_required', models.BooleanField(default=True)),
        migrations.AddField('exam', 'candidate_instructions', models.TextField(blank=True, default='')),
        migrations.AddField('question', 'class_level', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bank_questions', to='materials.classlevel')),
        migrations.AddField('question', 'subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bank_questions', to='materials.subject')),
        migrations.AddField('question', 'topic', models.CharField(blank=True, default='', max_length=120)),
        migrations.AddField('question', 'difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='medium', max_length=10)),
        migrations.AlterField('question', 'exam', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='legacy_questions', to='exams.exam')),
        migrations.CreateModel(name='ExamQuestion', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('position', models.PositiveIntegerField(default=0)),
            ('mark', models.PositiveIntegerField(default=1)),
            ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_questions', to='exams.exam')),
            ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='exam_links', to='exams.question')),
        ], options={'ordering': ('position', 'id')}),
        migrations.AddConstraint('examquestion', models.UniqueConstraint(fields=('exam', 'question'), name='unique_exam_question')),
        migrations.AddField('exam', 'question_bank', models.ManyToManyField(blank=True, related_name='mapped_exams', through='exams.ExamQuestion', to='exams.question')),
        migrations.AddField('examresult', 'instructions_accepted_at', models.DateTimeField(blank=True, null=True)),
        migrations.AddField('examresult', 'question_snapshot', models.JSONField(blank=True, default=list)),
        migrations.AddField('studentanswer', 'selected_choice_id_snapshot', models.BigIntegerField(blank=True, null=True)),
        migrations.AddField('studentanswer', 'client_revision', models.PositiveIntegerField(default=0)),
        migrations.RunPython(populate_links, migrations.RunPython.noop),
        migrations.AlterField('studentanswer', 'question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='exams.question')),
    ]
