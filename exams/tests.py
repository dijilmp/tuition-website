"""Regression checks for the upgraded MXA examination system.
Run after installing requirements: python manage.py test exams
"""
import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import StudentProfile
from materials.models import ClassLevel, Subject
from .models import Choice, Exam, ExamQuestion, ExamResult, Question, StudentAnswer


class MCQUpgradeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='exam_student', password='test-only-password')
        self.level = ClassLevel.objects.create(name='NMMS Class 8')
        self.subject = Subject.objects.create(name='MAT', class_level=self.level)
        StudentProfile.objects.create(user=self.user, class_level=self.level)
        self.exam = Exam.objects.create(
            title='Model Examination', class_level=self.level, subject=self.subject,
            exam_type='mcq', duration_minutes=30, total_marks=2, is_published=True,
        )
        self.exam.allowed_students.add(self.user)
        self.question = Question.objects.create(question_text='What is 2 + 2?', mark=2, subject=self.subject)
        self.right = Choice.objects.create(question=self.question, choice_text='4', is_correct=True)
        self.wrong = Choice.objects.create(question=self.question, choice_text='5', is_correct=False)
        ExamQuestion.objects.create(exam=self.exam, question=self.question, mark=2, position=1)
        self.client.force_login(self.user)

    def test_instructions_require_acceptance_without_starting_timer(self):
        self.exam.instructions_enabled = True
        self.exam.declaration_required = True
        self.exam.candidate_instructions = 'Follow examination rules.'
        self.exam.save()
        page = self.client.get(reverse('take_exam', args=[self.exam.id]))
        self.assertContains(page, 'Follow examination rules.')
        self.assertFalse(ExamResult.objects.filter(student=self.user, exam=self.exam).exists())
        rejected = self.client.post(reverse('begin_exam', args=[self.exam.id]), follow=True)
        self.assertContains(rejected, 'Follow examination rules.')
        self.assertFalse(ExamResult.objects.filter(student=self.user, exam=self.exam).exists())
        self.client.post(reverse('begin_exam', args=[self.exam.id]), {'accepted': 'yes'})
        result = ExamResult.objects.get(student=self.user, exam=self.exam)
        self.assertIsNotNone(result.started_at)
        self.assertIsNotNone(result.instructions_accepted_at)
        first_start = result.started_at
        self.client.get(reverse('take_exam', args=[self.exam.id]))
        result.refresh_from_db()
        self.assertEqual(result.started_at, first_start)

    def test_instruction_page_can_be_disabled_per_exam(self):
        self.exam.instructions_enabled = False
        self.exam.save()
        response = self.client.get(reverse('take_exam', args=[self.exam.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ExamResult.objects.filter(student=self.user, exam=self.exam, started_at__isnull=False).exists())

    def test_marks_ranks_and_keys_require_admin_publication(self):
        self.client.get(reverse('take_exam', args=[self.exam.id]))
        self.client.post(reverse('submit_exam', args=[self.exam.id]),
                         {f'question_{self.question.id}': str(self.right.id),
                          f'revision_{self.question.id}': '1'})
        result = ExamResult.objects.get(student=self.user, exam=self.exam)
        self.assertEqual(result.score, 2)
        self.assertTrue(result.is_submitted)
        hidden = self.client.get(reverse('exam_result', args=[result.id]))
        self.assertContains(hidden, 'Results will be published')
        self.assertNotContains(hidden, 'Score:')
        self.assertNotContains(hidden, 'Rank:')
        self.assertNotContains(hidden, 'Correct Answer:')
        self.exam.publish_marks = True
        self.exam.save()
        marks_page = self.client.get(reverse('exam_result', args=[result.id]))
        self.assertContains(marks_page, 'Score:')
        self.assertNotContains(marks_page, 'Correct Answer:')
        self.exam.publish_ranks = True
        self.exam.publish_answer_keys = True
        self.exam.save()
        published = self.client.get(reverse('exam_result', args=[result.id]))
        self.assertContains(published, 'Rank:')
        self.assertContains(published, 'Correct Answer:')
        self.assertContains(published, 'What is 2 + 2?')

    def test_question_can_be_used_in_multiple_exams(self):
        other = Exam.objects.create(title='Second Exam', class_level=self.level,
                                    subject=self.subject, exam_type='mcq')
        ExamQuestion.objects.create(exam=other, question=self.question, mark=1, position=1)
        self.assertEqual(self.question.exam_links.count(), 2)
        self.assertEqual(self.exam.exam_questions.get().mark, 2)
        self.assertEqual(other.exam_questions.get().mark, 1)

    def test_autosave_idempotent_and_deadline_enforced(self):
        self.client.get(reverse('take_exam', args=[self.exam.id]))
        url = reverse('autosave_mcq', args=[self.exam.id])
        payload = {'answers': [{'question_id': self.question.id,
                                'choice_id': self.wrong.id, 'revision': 1}]}
        for _ in range(2):
            saved = self.client.post(url, data=json.dumps(payload), content_type='application/json')
            self.assertEqual(saved.status_code, 200)
        self.assertEqual(StudentAnswer.objects.filter(result__exam=self.exam).count(), 1)
        newer = {'answers': [{'question_id': self.question.id,
                              'choice_id': self.right.id, 'revision': 2}]}
        self.client.post(url, data=json.dumps(newer), content_type='application/json')
        self.client.post(url, data=json.dumps(payload), content_type='application/json')
        answer = StudentAnswer.objects.get(result__exam=self.exam, question=self.question)
        self.assertEqual(answer.selected_choice_id_snapshot, self.right.id)
        result = ExamResult.objects.get(student=self.user, exam=self.exam)
        result.started_at = timezone.now() - timedelta(minutes=31)
        result.save(update_fields=['started_at'])
        expired = self.client.post(url, data=json.dumps(newer), content_type='application/json')
        self.assertEqual(expired.status_code, 409)
        result.refresh_from_db()
        self.assertTrue(result.is_submitted)
        self.assertEqual(result.score, 2)

    def test_snapshot_preserves_marking_after_bank_edit(self):
        self.client.get(reverse('take_exam', args=[self.exam.id]))
        # New edits to shared question options cannot affect an already started attempt.
        self.right.is_correct = False
        self.right.save()
        self.wrong.is_correct = True
        self.wrong.save()
        self.client.post(reverse('submit_exam', args=[self.exam.id]),
                         {f'question_{self.question.id}': str(self.right.id),
                          f'revision_{self.question.id}': '1'})
        result = ExamResult.objects.get(student=self.user, exam=self.exam)
        self.assertEqual(result.score, 2)
