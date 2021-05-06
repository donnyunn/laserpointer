import cv2
import numpy
cap = cv2.VideoCapture(-1)



#filename : 파일 이름
#fourcc : 코덱
#fps : 초당 프레임 수
#width : 넓이
#height : 높이
cap.set(3, 1280)
cap.set(4, 720)
# 비디오 매 프레임 처리
while True:  # 무한 루프
    ret, frame = cap.read()  # 두 개의 값을 반환하므로 두 변수 지정


    if not ret:  # 새로운 프레임을 못받아 왔을 때 braek
        break

    cv2.imshow('frame', frame)
   # cv2.imshow('inversed', inversed)
   # cv2.imshow('edge', edge)

    # 10ms 기다리고 다음 프레임으로 전환, Esc누르면 while 강제 종료
    if cv2.waitKey(10) == 27:
        break

cap.release()  # 사용한 자원 해제
cv2.destroyAllWindows()