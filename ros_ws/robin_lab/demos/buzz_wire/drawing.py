import cv2
import numpy as np

n_vertical_ticks = 10
n_horizontal_ticks = 20
n_pixels = 30
img = np.zeros((n_pixels*(n_vertical_ticks+2), n_pixels*(n_horizontal_ticks+1), 3), np.uint8)
cv2.namedWindow("trajectory")
cv2.imshow("trajectory", img)

trajectory = [4, 4, 5, 6, 5, 4, 5, 4, 5, 6, 5, 4, 3, 2, 3, 4, 3, 3, 4, 4]
c = 0

while True:
    img.fill(0)

    for i in xrange(1, len(trajectory)):
        pt1 = (n_pixels*(1+i-1), n_pixels*(n_vertical_ticks - (1+trajectory[i-1])) - 3)
        pt2 = (n_pixels*(1+i), n_pixels*(n_vertical_ticks - (1+trajectory[i])) - 3)
        cv2.line(img, pt1, pt2, (255, 255, 255), 8)

    for i in xrange(1, len(trajectory)):
        pt1 = (n_pixels*(1+i-1), n_pixels*(n_vertical_ticks - (1+trajectory[i-1])))
        pt2 = (n_pixels*(1+i), n_pixels*(n_vertical_ticks - (1+trajectory[i])))
        cv2.line(img, pt1, pt2, (51, 115, 184), 8)

    for i in xrange(1, len(trajectory)):
        pt1 = (n_pixels*(1+i-1), n_pixels*(n_vertical_ticks - (1+trajectory[i-1])) - 2)
        pt2 = (n_pixels*(1+i), n_pixels*(n_vertical_ticks - (1+trajectory[i])) - 2)
        cv2.line(img, pt1, pt2, (71, 160, 255), 2)

    c = (c + 1) % n_horizontal_ticks
    
    pt1 = (n_pixels*(1+c)-15, n_pixels*(n_vertical_ticks - (1+trajectory[c]))-15)
    pt2 = (n_pixels*(1+c)+15, n_pixels*(n_vertical_ticks - (1+trajectory[c]))+15)
    
    cv2.rectangle(img, pt1, pt2, (50, 50, 255), 3)

    cv2.imshow("trajectory", img)
    k = cv2.waitKey(700) & 0xFF
    if k == 27: break

cv2.destroyAllWindows()
