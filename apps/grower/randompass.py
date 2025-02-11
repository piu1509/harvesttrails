"""For generating random password"""

import string
import random


characters = list(string.ascii_letters + string.digits + "@#$%")

def generate_random_password():
	length = 8

	random.shuffle(characters)

	password = []
	for i in range(length):
		password.append(random.choice(characters))

	return "".join(password)