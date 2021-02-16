import os
import cv2
from imutils.video import FileVideoStream
from glob import glob

# Opens the video file
cap = cv2.VideoCapture('F:/Videos/CUTE GSD PUPPY SLEEPING.mp4')
i = 0
while(cap.isOpened()):
    ret, frame = cap.read()
    if ret == False:
        break
    cv2.imwrite('kang'+str(i)+'.jpg',frame)
    i += 1
cap.release()
cv2.destroyAllWindows()

# video_dir = 'F:/Datasets/doggy_dataset/testvideos/'
# frame_dir = 'F:/GIT/28_12_2020/2020-045/Resting/ReadingFrames/'
#
# for entry in os.listdir(video_dir):
#     if os.path.isfile(os.path.join(video_dir, entry)):
#         cap = cv2.VideoCapture(entry)
#         i = 0
#         while (cap.isOpened()):
#             ret, frame = cap.read()
#             if ret == False:
#                 break
#             cv2.imwrite(os.path.join(frame_dir, 'kang' + str(i) + '.jpg'), frame)
#             i += 1
#         cap.release()
#         cv2.destroyAllWindows()