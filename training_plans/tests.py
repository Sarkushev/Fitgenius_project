from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, UserProfile


class AuthAndSecurityTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.user1 = CustomUser.objects.create_user(username='user1', email='user1@example.com', password='testpass123')
		self.user2 = CustomUser.objects.create_user(username='user2', email='user2@example.com', password='testpass123')

		self.profile1 = UserProfile.objects.create(user=self.user1, age=25, height=175, weight=70, gender='male', goal='health', fitness_level='beginner')
		self.profile2 = UserProfile.objects.create(user=self.user2, age=30, height=180, weight=80, gender='male', goal='muscle_gain', fitness_level='intermediate')

	def test_login_with_email(self):
		# Login using email (username field carries email)
		resp = self.client.post(reverse('training_plans:login'), {'username': 'user1@example.com', 'password': 'testpass123'})
		# Successful login should redirect
		self.assertIn(resp.status_code, (302, 301))

	def test_cannot_view_other_profile(self):
		# Login as user1
		self.client.login(username='user1@example.com', password='testpass123')
		# Attempt to access user2's profile detail
		resp = self.client.get(reverse('training_plans:profile_detail', kwargs={'pk': self.profile2.pk}))
		self.assertEqual(resp.status_code, 404)

	def test_export_pdf_owner_only(self):
		# User1 should be able to export own profile
		self.client.login(username='user1@example.com', password='testpass123')
		resp = self.client.get(reverse('training_plans:export_pdf', kwargs={'pk': self.profile1.pk}))
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp['Content-Type'], 'application/pdf')

		# User1 should NOT be able to export user2's profile
		resp = self.client.get(reverse('training_plans:export_pdf', kwargs={'pk': self.profile2.pk}))
		self.assertEqual(resp.status_code, 404)

	def test_short_login_redirect(self):
		# requesting /l should redirect to /login/ instead of 404
		resp = self.client.get('/l')
		# should be a redirect (302)
		self.assertIn(resp.status_code, (301, 302))
		# redirected URL should include the login path
		self.assertTrue('/login' in resp['Location'])


class TrainingCrudTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.user1 = CustomUser.objects.create_user(username='u1', email='u1@example.com', password='pw')
		self.user2 = CustomUser.objects.create_user(username='u2', email='u2@example.com', password='pw')

	def test_create_training_and_export_by_owner(self):
		self.client.login(username='u1@example.com', password='pw')
		# create training (simple create without exercises)
		resp = self.client.post(reverse('training_plans:training_create'), {'title': 'My Plan', 'description': 'Test'}, follow=True)
		self.assertIn(resp.status_code, (200, 302))
		from .models import Training
		training = Training.objects.get(title='My Plan')
		# export by owner
		resp2 = self.client.get(reverse('training_plans:training_export', kwargs={'pk': training.pk}))
		self.assertEqual(resp2.status_code, 200)
		self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resp2['Content-Type'])

	def test_other_user_cannot_edit_or_export(self):
		# create a training as u1
		training = __import__('training_plans.models', fromlist=['Training']).Training.objects.create(user=self.user1, title='U1 Plan')
		# login as u2
		self.client.login(username='u2@example.com', password='pw')
		# try to access update view
		resp = self.client.get(reverse('training_plans:training_update', kwargs={'pk': training.pk}))
		# Should be forbidden by UserPassesTestMixin -> 403
		self.assertEqual(resp.status_code, 403)
		# try to export (view uses get_object_or_404 with user filter)
		resp2 = self.client.get(reverse('training_plans:training_export', kwargs={'pk': training.pk}))
		self.assertEqual(resp2.status_code, 404)

