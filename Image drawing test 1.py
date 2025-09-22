import cv2

image_path = input('Enter image path: ')
image = cv2.imread(image_path)

if image is None:
    print("Error: Could not load image. Check the path again.")
else:
    Choice = input('Enter your choice (Text/Circle/Rectangle/Line): ')

    if Choice == 'Text':
        cv2.putText(image, 'Hi Vaibhav', (300, 100),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
        cv2.imshow('Image', image)

    elif Choice == 'Circle':
        cv2.circle(image, (100, 100), 100, (255, 255, 255), 2)
        cv2.imshow('Image', image)

    elif Choice == 'Rectangle':
        cv2.rectangle(image, (100, 50), (200, 50), (255, 255, 255), 2)
        cv2.imshow('Image', image)

    elif Choice == 'Line':
        cv2.line(image, (100, 100), (200, 200), (255, 255, 255), 2)
        cv2.imshow('Image', image)

    else:
        print('Invalid Choice')

    cv2.waitKey(0)
    cv2.destroyAllWindows()