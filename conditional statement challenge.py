# 1. Email and password should not have empty spaces
# 2. Password should have at least 8 characters
# 3. Password cannot have empty spaces.
# 4. Email and password cannot be same.
# 5. Password should start with letter or a number.
# 6. Password should have at least one upper case and one lower case letter.

email = input("Enter your email: ")
password = input("Enter your password: ")

if not(password != '' and email != ''):
    print('Email/Password cannot be empty')
elif len(password) < 8:
    print('Password must be at least 8 characters')
elif ' ' in password:
    print('Password cannot contain spaces')
elif password == email:
    print("Password and email cannot be the same")
elif not(password[0].isalnum and password[-1].isalnum):
    print('Password should start with letter/number')
elif not(any(char.isupper() for char in password) and any(char.islower() for char in password)):
    print('Password should contain uppercase and lowercase letters')
else:

    print('Credentials are valid')