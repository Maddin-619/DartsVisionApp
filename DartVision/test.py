import cv2, time

cv2.destroyAllWindows()
img = cv2.imread('TestImage.png', 1)
test = cv2.circle(img.copy(), (100, 100), 6, (0,0,255), -1)
cv2.namedWindow('Hit_point', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Hit_point', 1200,700)
cv2.imshow("Hit_point", test)
cv2.waitKey(160) & 0xFF
input("wait")
