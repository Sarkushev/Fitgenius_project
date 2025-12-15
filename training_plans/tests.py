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

