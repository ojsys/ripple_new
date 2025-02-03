from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='project_images/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

class Reward(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rewards')
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title} (${self.amount})"

class Pledge(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pledges')
    backer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reward = models.ForeignKey(Reward, on_delete=models.SET_NULL, null=True, blank=True)
    pledged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.backer} pledged ${self.amount} to {self.project}"

class Update(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title