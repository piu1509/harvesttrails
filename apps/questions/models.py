from django.db import models


QUESTION_CATEGORIES =(
    ('Whole Farm Question', 'Whole Farm Question'),
    ('Enrolled Fields Question', 'Enrolled Fields Question'))


QUESTION_TYPE =(('single_select', 'Single Select'),
                ('multi_select', 'Multi Select'))

class Question(models.Model):
    """Database model for question model"""
    category = models.CharField(max_length=200, choices=QUESTION_CATEGORIES)
    type = models.CharField(max_length=200, choices=QUESTION_TYPE)
    survey_type = models.ManyToManyField('survey.SurveyType')
    order = models.IntegerField(null=True, blank=True) #order of the question
    text = models.TextField(null=True, blank=True) #text of the question
    max_points = models.IntegerField(null=True, blank=True)


    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"


    def get_options(self):
        """this method gets all the options of a questions and sort them via order"""
        return self.options.filter(is_active=True).order_by('order')

    def __str__(self):
        """String representation for question model object"""
        return f'{self.id}:- {self.text}'


class Option(models.Model):
    """Database model for questions options"""
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        null=True, blank=True, related_name='options'
    )
    order = models.CharField(help_text='Example: a, b, c etc.', max_length=1) #order of the option a, b , c etc.
    text = models.TextField(help_text="Option's text", null=True, blank=True) #text of the option
    points = models.IntegerField() #points associated with the option
    is_active = models.BooleanField(help_text='Enable/Disable Option', default=True)


    class Meta:
        verbose_name = "Option"
        verbose_name_plural = "Options"


    def __str__(self):
        """string representation of option object"""
        return f'({self.order}):{self.id}- {self.text}'
