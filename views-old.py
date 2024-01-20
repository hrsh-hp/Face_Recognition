from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt #to disable CSRF for now 
from .models import *

#for face recognition
import cv2
import face_recognition
import dlib
import base64
from io import BytesIO
import numpy as np
from PIL import Image


#these are the known faces for now
known_face_names = ["Harsh","Dipen"]
known_face_encodings = []

for name in known_face_names:
    image = face_recognition.load_image_file(f"static/images/{name}.jpeg")
    face_encoding = face_recognition.face_encodings(image)[0]
    known_face_encodings.append(face_encoding)
    
#initialize to use webcame as camera
# cap = cv2.VideoCapture('http://IPaddress of you cam:port/video') #for using additional cam of mobile
cap = cv2.VideoCapture(0)
#declaring a set of recognized users to avoide duplicate
recognized_users = set()

face_detector = dlib.get_frontal_face_detector()

# Create your views here.
@csrf_exempt
def recognize_face(request):
    print('Reached recogimze_faceview')
    if request.method == 'POST':
        try: 
            
            print("Inside try and if block")
            #got the base64 image data and decoded it 
            image_data = request.POST.get('imageData')
            img_data = base64.b64decode(image_data.split(',')[1])
            image = Image.open(BytesIO(img_data))
            print(image.size)
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            print("After geeting image data")
            
            #actual face recognition
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            print(face_locations)
            print(face_encodings)
            print("Inside face recognize")
            
            recognized_names = []
            print("going in for loop")
            for face_encoding in face_encodings:
                print("inside for loop")
                print("Face encodings:", face_encoding,flush=True)
                
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                print("Matches:",matches,flush=True)
                
                name = 'unknown'
                age = 'undefined'
                gender = 'undefined'
                
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]
                    if name not in recognized_users:
                        recognized_face = FaceRecognition.objects.create(name=name)
                        recognized_face.save()
                        print(f"Welcome {name}",flush=True)
                        recognized_users.add(name)
                        recognized_names.append(name)
                        print(recognized_users,flush=True)
                        print(recognized_names)
                        
                    face_image = frame[top:bottom, left:right]
                    dlib_faces = face_detector(frame, 1)
                    if len(dlib_faces)>0:
                        face = dlib_faces[0]
                        # age, gender = face_recognition.face_utils.age_and_gender(frame, [face])[0]
                
                else:
                    print("Not match")
                    
            

            # Convert a frame to Jpeg
            _ , jpeg = cv2.imencode('.jpeg',frame)
            response = jpeg.tobytes()
            return HttpResponse(response, content_type= 'image/jpg')
        
            #     cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
            #     font = cv2.FONT_HERSHEY_DUPLEX
            #     cv2.putText(frame,f"{name}", (left+2, top-5), font, 1, (255,255,255), 1)
            
            cv2.imshow('Face Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows() 
            
            # return JsonResponse({'name':name})
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'err':str(e)})
    else:
        print('Request must be a POST request')
        return JsonResponse({'error':'Invalid request method only POST allowed'})


def index(request):
    return render(request, 'Auth/index.html')