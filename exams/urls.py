from django.urls import path

from .views import (
    exam_list,
    take_exam,
    submit_exam,
    exam_result,
    reattempt_exam, begin_exam, autosave_mcq
)


urlpatterns = [
    path('<int:exam_id>/begin/', begin_exam, name='begin_exam'),
    path('<int:exam_id>/autosave/', autosave_mcq, name='autosave_mcq'),
    path('', exam_list, name='exam_list'),

    path(
        '<int:exam_id>/take/',
        take_exam,
        name='take_exam'
    ),

    path(
        '<int:exam_id>/submit/',
        submit_exam,
        name='submit_exam'
    ),

    path(
        'result/<int:result_id>/',
        exam_result,
        name='exam_result'
    ),

    path(
        'result/<int:result_id>/reattempt/',
        reattempt_exam,
        name='reattempt_exam'
    ),
]
