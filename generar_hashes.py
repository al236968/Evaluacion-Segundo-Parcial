from werkzeug.security import generate_password_hash

password1 = "veterinaria123"
password2 = "patitas456"

hash1 = generate_password_hash(password1)
hash2 = generate_password_hash(password2)

print("Usuario 1:")
print(hash1)

print("\nUsuario 2:")
print(hash2)