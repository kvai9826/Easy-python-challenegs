emails = input('Enter your email :')
if not emails.endswith('@gmail.com'):
    print('Invalid email')
else:
    print('Valid email')
    attempts = 0
    while attempts < 3:
        password = input('Enter your password :')
        if password =='Vaibhav':
            print('Valid password')
            break
        else:
            print('Password is invalid')
            attempts += 1
    else:
        print('Too many attempts')
